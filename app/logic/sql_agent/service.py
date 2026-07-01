"""
LLM SQL 查询服务，对 SalesQueryService 提供稳定的查询方法。
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import date
from decimal import Decimal
from typing import Any

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.metrics import runtime_metrics
from app.logic.schemas import UserInfo
from app.logic.sql_agent.cache import CachedSqlTemplate, SqlTemplateCache
from app.logic.sql_agent.executor import SqlExecutor
from app.logic.sql_agent.generator import LlmSqlGenerator
from app.logic.sql_agent.models import GeneratedSql, QueryScope, SqlResolutionAudit, SqlTaskSpec
from app.logic.sql_agent.policy import PermissionPolicyInjector
from app.logic.sql_agent.result_mapper import (
    map_monthly_trend_rows,
    map_order_rows,
    map_product_rows,
    map_region_rows,
    map_rep_rows,
    to_decimal,
    to_int,
)
from app.logic.sql_agent.schema_registry import SqlSchemaRegistry
from app.logic.sql_agent.template_registry import SqlTemplateRegistry
from app.logic.sql_agent.validator import SqlValidator


logger = logging.getLogger(__name__)

_UNREPAIRABLE_PATTERNS = (
    "危险关键词",
    "未授权表",
    "不允许查询系统库",
    "SQL 不能为空",
    "不允许包含分号",
)


class LlmSqlQueryService:
    """执行由 LLM 生成 SQL 的销售查询。"""

    def __init__(
        self,
        db: Session,
        current_user: UserInfo | None,
        redis_client: Redis | None,
        settings: Settings,
        generator: LlmSqlGenerator | None = None,
        executor: SqlExecutor | None = None,
    ) -> None:
        self.db = db
        self.current_user = current_user
        self.redis = redis_client
        self.settings = settings
        self.schema = SqlSchemaRegistry()
        self.generator = generator or LlmSqlGenerator(settings)
        self.validator = SqlValidator(self.schema)
        self.policy = PermissionPolicyInjector()
        self.executor = executor or SqlExecutor(db, settings.llm_sql_max_rows, settings.llm_sql_timeout_seconds)
        self.template_registry = SqlTemplateRegistry()
        self.template_cache = SqlTemplateCache(
            enabled=settings.llm_sql_cache_enabled,
            ttl_seconds=settings.llm_sql_cache_ttl_seconds,
            backend=settings.llm_sql_cache_backend,
            redis_client=redis_client,
        )

    @staticmethod
    def _is_repairable(errors: list[str]) -> bool:
        """判断校验错误是否可通过重试修复。"""
        return not any(
            any(pattern in error for pattern in _UNREPAIRABLE_PATTERNS)
            for error in errors
        )

    def _scope(self) -> QueryScope:
        if self.current_user is None:
            return QueryScope(role="ANONYMOUS")
        role = self.current_user.role if self.current_user.role in {"SALES_REP", "SALES_MANAGER", "SALES_DIRECTOR"} else "ANONYMOUS"
        return QueryScope(
            role=role,
            user_id=self.current_user.user_id,
            region_id=self.current_user.region_id,
            rep_id=self.current_user.rep_id,
        )

    @staticmethod
    def _merge_app_params(generated: GeneratedSql, task: SqlTaskSpec) -> dict[str, Any]:
        # 参数值必须由应用侧从工具入参生成，不能信任 LLM 自带的 params。
        params: dict[str, Any] = {}
        if task.start_date is not None:
            params["start_date"] = task.start_date
        if task.end_date is not None:
            params["end_date"] = task.end_date
        if task.region_id is not None:
            params["region_id"] = task.region_id
        if task.rep_id is not None:
            params["rep_id"] = task.rep_id
        if task.product_id is not None:
            params["product_id"] = task.product_id
        if task.category is not None:
            params["category"] = task.category
        if task.top_n is not None:
            params["top_n"] = max(abs(int(task.top_n)), 1)
        if task.limit is not None:
            params["limit"] = min(max(int(task.limit), 1), 50)
        placeholders = set(re.findall(r":([A-Za-z_][A-Za-z0-9_]*)", generated.sql))
        defaults = {
            "region_id": task.region_id,
            "rep_id": task.rep_id,
            "product_id": task.product_id,
            "category": task.category,
            "top_n": max(abs(int(task.top_n)), 1) if task.top_n is not None else None,
            "limit": min(max(int(task.limit), 1), 50) if task.limit is not None else None,
        }
        for name, value in defaults.items():
            if name in placeholders and name not in params:
                params[name] = value
        return params

    def _build_template_sql(self, task: SqlTaskSpec, signature: str) -> tuple[str, dict[str, Any], SqlResolutionAudit] | None:
        if not self.settings.llm_sql_template_mode:
            return None
        template = self.template_registry.match(task)
        if template is None:
            return None
        runtime_metrics.record_llm_sql_template_hit()
        generated = GeneratedSql(sql=template.sql, params={}, result_columns=template.result_columns)
        params = self._merge_app_params(generated, task)
        sql, params = self.policy.apply(template.sql, params, task.scope)
        scoped = GeneratedSql(sql=sql, params=params, result_columns=template.result_columns)
        scoped_validation = self.validator.validate(scoped, task)
        if not scoped_validation.ok:
            raise RuntimeError("SQL 模板校验失败：" + "; ".join(scoped_validation.errors))
        return (
            scoped_validation.normalized_sql or sql,
            params,
            SqlResolutionAudit(
                source="template",
                task_signature=signature,
                cache_hit=False,
                template_id=template.template_id,
            ),
        )

    def _audit_log(self, task: SqlTaskSpec, sql: str, params: dict[str, Any], row_count: int, audit: SqlResolutionAudit, execution_ms: float) -> None:
        if not self.settings.llm_sql_audit_log_enabled:
            return
        payload = {
            "event": "llm_sql_audit",
            "tool_name": task.tool_name,
            "task_type": task.task_type,
            "source": audit.source,
            "cache_hit": audit.cache_hit,
            "template_id": audit.template_id,
            "task_signature": audit.task_signature,
            "scope_role": task.scope.role,
            "scope_user_id": task.scope.user_id,
            "scope_region_id": task.scope.region_id,
            "scope_rep_id": task.scope.rep_id,
            "generation_ms": round(audit.generation_ms, 2),
            "execution_ms": round(execution_ms, 2),
            "prompt_tokens": audit.prompt_tokens,
            "completion_tokens": audit.completion_tokens,
            "total_tokens": audit.total_tokens,
            "row_count": row_count,
            "sql": sql,
            "params": {key: str(value) for key, value in params.items()},
        }
        logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def _generate_valid_sql(self, task: SqlTaskSpec) -> tuple[str, dict[str, Any], SqlResolutionAudit]:
        signature = self.template_cache.build_signature(task)
        template_sql = self._build_template_sql(task, signature)
        if template_sql is not None:
            return template_sql
        cached = self.template_cache.get(signature)
        if cached is not None:
            runtime_metrics.record_llm_sql_cache(True)
            generated = GeneratedSql(sql=cached.sql, params={}, result_columns=cached.result_columns)
            params = self._merge_app_params(generated, task)
            sql, params = self.policy.apply(cached.sql, params, task.scope)
            scoped = GeneratedSql(sql=sql, params=params, result_columns=cached.result_columns)
            scoped_validation = self.validator.validate(scoped, task)
            if scoped_validation.ok:
                runtime_metrics.record_llm_sql_validation(True)
                return (
                    scoped_validation.normalized_sql or sql,
                    params,
                    SqlResolutionAudit(
                        source="cache",
                        task_signature=signature,
                        cache_hit=True,
                    ),
                )
        runtime_metrics.record_llm_sql_cache(False)
        errors: list[str] | None = None
        attempts = max(int(self.settings.llm_sql_repair_attempts), 0) + 1
        for _ in range(attempts):
            generated = self.generator.generate(task, self.schema, errors)
            params = self._merge_app_params(generated, task)
            validation = self.validator.validate(generated, task)
            if not validation.ok:
                if not self._is_repairable(validation.errors):
                    raise RuntimeError(
                        "LLM SQL 生成了不可修复的错误：" + "; ".join(validation.errors)
                    )
                errors = validation.errors
                runtime_metrics.record_llm_sql_validation(False)
                continue
            sql = validation.normalized_sql or generated.sql
            sql, params = self.policy.apply(sql, params, task.scope)
            scoped = GeneratedSql(sql=sql, params=params, result_columns=generated.result_columns)
            scoped_validation = self.validator.validate(scoped, task)
            if scoped_validation.ok:
                runtime_metrics.record_llm_sql_validation(True)
                self.template_cache.set(
                    signature,
                    CachedSqlTemplate(
                        sql=validation.normalized_sql or generated.sql,
                        result_columns=list(generated.result_columns),
                        task_type=task.task_type,
                        tool_name=task.tool_name,
                        created_at=time.time(),
                    ),
                )
                usage = getattr(self.generator, "last_usage", {}) or {}
                return (
                    scoped_validation.normalized_sql or sql,
                    params,
                    SqlResolutionAudit(
                        source="generator",
                        task_signature=signature,
                        cache_hit=False,
                        generation_ms=float(getattr(self.generator, "last_duration_ms", 0.0) or 0.0),
                        prompt_tokens=int(usage.get("prompt_tokens") or 0),
                        completion_tokens=int(usage.get("completion_tokens") or 0),
                        total_tokens=int(usage.get("total_tokens") or 0),
                    ),
                )
            errors = scoped_validation.errors
            runtime_metrics.record_llm_sql_validation(False)
        raise RuntimeError("LLM SQL 校验失败：" + "; ".join(errors or []))

    def _execute_task(self, task: SqlTaskSpec) -> list[dict[str, Any]]:
        started = time.perf_counter()
        sql, params, audit = self._generate_valid_sql(task)
        try:
            rows = self.executor.execute(sql, params)
        except Exception:
            runtime_metrics.record_llm_sql_execution(False, (time.perf_counter() - started) * 1000)
            raise
        total_ms = (time.perf_counter() - started) * 1000
        execution_ms = max(total_ms - audit.generation_ms, 0.0)
        runtime_metrics.record_llm_sql_execution(True, total_ms)
        self._audit_log(task, sql, params, len(rows), audit, execution_ms)
        return rows

    def _task(self, *, tool_name: str, task_type: str, result_contract: list[str], **kwargs: Any) -> SqlTaskSpec:
        return SqlTaskSpec(
            tool_name=tool_name,
            task_type=task_type,
            scope=self._scope(),
            result_contract=result_contract,
            **kwargs,
        )

    def query_orders(self, rep_id: int | None, region_id: int | None, start: date, end: date, limit: int = 20):
        task = self._task(
            tool_name="query_sales_data",
            task_type="order_detail",
            start_date=start,
            end_date=end,
            rep_id=rep_id,
            region_id=region_id,
            limit=limit,
            result_contract=["id", "order_no", "order_date", "rep_id", "customer_name", "amount", "status"],
        )
        return map_order_rows(self._execute_task(task))

    def query_total_amount(self, region_id: int | None, start: date, end: date) -> Decimal:
        scope = self._scope()
        task = self._task(
            tool_name="get_sales_summary",
            task_type="sales_summary",
            start_date=start,
            end_date=end,
            region_id=region_id,
            rep_id=scope.rep_id if scope.role == "SALES_REP" else None,
            result_contract=["total_amount"],
        )
        rows = self._execute_task(task)
        return to_decimal(rows[0].get("total_amount") if rows else 0)

    def query_rep_ranking(self, start: date, end: date, top_n: int):
        task = self._task(
            tool_name="get_top_reps",
            task_type="rep_ranking",
            start_date=start,
            end_date=end,
            top_n=top_n,
            result_contract=["rep_id", "rep_name", "region_id", "region_name", "total_amount"],
        )
        return map_rep_rows(self._execute_task(task))[:top_n]

    def query_region_ranking(self, start: date, end: date):
        task = self._task(
            tool_name="get_region_ranking",
            task_type="region_ranking",
            start_date=start,
            end_date=end,
            result_contract=["region_id", "region_name", "total_amount"],
        )
        return map_region_rows(self._execute_task(task))

    def query_product_ranking(self, start: date, end: date, top_n: int, region_id: int | None = None):
        order_by = "total_amount_asc" if top_n < 0 else "total_amount_desc"
        task = self._task(
            tool_name="get_top_products",
            task_type="product_ranking",
            start_date=start,
            end_date=end,
            region_id=region_id,
            top_n=abs(top_n),
            order_by=order_by,
            result_contract=["product_id", "sku_code", "product_name", "category", "total_amount", "total_quantity"],
        )
        return map_product_rows(self._execute_task(task))[: abs(top_n)]

    def query_monthly_trend(self, region_id: int | None, start: date, end: date, months: int):
        task = self._task(
            tool_name="get_monthly_trend",
            task_type="monthly_trend",
            start_date=start,
            end_date=end,
            region_id=region_id,
            months=months,
            result_contract=["month", "total_amount", "order_count"],
        )
        return map_monthly_trend_rows(self._execute_task(task))

    def query_refund_rates(self, start: date, end: date):
        task = self._task(
            tool_name="detect_sales_anomalies",
            task_type="refund_rates",
            start_date=start,
            end_date=end,
            result_contract=["rep_id", "refunded", "total"],
        )
        rows = self._execute_task(task)
        return [(to_int(row.get("rep_id")), to_int(row.get("refunded")), to_int(row.get("total"))) for row in rows]
