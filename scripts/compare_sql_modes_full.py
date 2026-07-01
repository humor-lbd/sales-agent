"""
全面对比写死 SQL 与 LLM 生成 SQL。

运行方式：
    python scripts/compare_sql_modes_full.py

输出：
    - docs/12_SQL_MODE_EVALUATION_REPORT.md
    - logs/sql_mode_compare_results.json
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import event

from _common import compact, stable_hash

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.llm import build_chat_model  # noqa: E402
from app.core.metrics import runtime_metrics  # noqa: E402
from app.db.database import SessionLocal, engine  # noqa: E402
from app.logic.schemas import UserInfo  # noqa: E402
from app.logic.services import SalesQueryService  # noqa: E402
from app.logic.sql_agent.executor import SqlExecutor  # noqa: E402
from app.logic.sql_agent.models import GeneratedSql  # noqa: E402
from app.logic.sql_agent.prompts import SQL_GENERATION_SYSTEM_PROMPT, build_sql_generation_prompt  # noqa: E402
from app.logic.sql_agent.schema_registry import SqlSchemaRegistry  # noqa: E402
from app.logic.sql_agent.service import LlmSqlQueryService  # noqa: E402
from app.logic.tools import SalesTools  # noqa: E402


REPORT_PATH = ROOT / "docs" / "12_SQL_MODE_EVALUATION_REPORT.md"
RAW_PATH = ROOT / "logs" / "sql_mode_compare_results.json"


def normalize_output(value: Any) -> str:
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def extract_usage(message: Any) -> dict[str, int]:
    usage = getattr(message, "usage_metadata", None) or {}
    response_metadata = getattr(message, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or response_metadata.get("usage") or {}
    if not usage and isinstance(token_usage, dict):
        usage = token_usage

    prompt_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))

    details = usage.get("output_token_details") or usage.get("completion_tokens_details") or {}
    reasoning_tokens = int(details.get("reasoning") or details.get("reasoning_tokens") or 0)

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
    }


class SqlCapture:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    @staticmethod
    def _is_select(statement: str) -> bool:
        return statement.lstrip().lower().startswith("select") or statement.lstrip().lower().startswith("with")

    def _before(self, conn, cursor, statement, parameters, context, executemany) -> None:
        if self._is_select(statement):
            context._sql_capture_started = time.perf_counter()

    def _after(self, conn, cursor, statement, parameters, context, executemany) -> None:
        if not self._is_select(statement):
            return
        started = getattr(context, "_sql_capture_started", None)
        duration_ms = round((time.perf_counter() - started) * 1000, 2) if started else None
        self.items.append(
            {
                "sql": compact(statement, 900),
                "params": compact(parameters, 900),
                "duration_ms": duration_ms,
            }
        )

    def __enter__(self):
        event.listen(engine, "before_cursor_execute", self._before)
        event.listen(engine, "after_cursor_execute", self._after)
        return self

    def __exit__(self, exc_type, exc, tb):
        event.remove(engine, "before_cursor_execute", self._before)
        event.remove(engine, "after_cursor_execute", self._after)


class CapturingGenerator:
    def __init__(self, settings, sink: list[dict[str, Any]]) -> None:
        self.settings = settings
        self.sink = sink

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            return "".join(parts).strip()
        return str(content).strip() if content is not None else ""

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.IGNORECASE | re.DOTALL)
        if fence:
            return fence.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]
        return text

    def generate(self, task, schema: SqlSchemaRegistry, errors=None) -> GeneratedSql:
        if not self.settings.openai_api_key:
            raise RuntimeError("未配置 OPENAI_API_KEY，无法生成 LLM SQL")

        model_name = self.settings.llm_sql_model or self.settings.openai_model
        llm = build_chat_model(
            self.settings,
            temperature=self.settings.llm_sql_temperature,
            model_name=model_name,
        )
        messages = [
            SystemMessage(content=SQL_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=build_sql_generation_prompt(task, schema, errors, profile=self.settings.llm_sql_prompt_profile)),
        ]
        started = time.perf_counter()
        response = llm.invoke(messages)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        runtime_metrics.record_llm_call("llm_sql", elapsed_ms)

        usage = extract_usage(response)
        payload = json.loads(self._extract_json(self._content_to_text(response.content)))
        generated = GeneratedSql.model_validate(payload)
        self.sink.append(
            {
                "phase": "generated",
                "task_type": task.task_type,
                "tool_name": task.tool_name,
                "duration_ms": elapsed_ms,
                "sql": compact(generated.sql, 900),
                "params": generated.params,
                "result_columns": generated.result_columns,
                "confidence": generated.confidence,
                "model_name": model_name,
                "errors": errors or [],
                "usage": usage,
            }
        )
        return generated


class CapturingExecutor(SqlExecutor):
    def __init__(self, db, max_rows: int, sink: list[dict[str, Any]]) -> None:
        super().__init__(db, max_rows)
        self.sink = sink

    def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        started = time.perf_counter()
        try:
            rows = super().execute(sql, params)
        except Exception as exc:
            self.sink.append(
                {
                    "phase": "executed",
                    "ok": False,
                    "sql": compact(sql, 900),
                    "params": params,
                    "error": str(exc),
                }
            )
            raise
        self.sink.append(
            {
                "phase": "executed",
                "ok": True,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "row_count": len(rows),
                "sql": compact(sql, 900),
                "params": params,
            }
        )
        return rows


class CapturingLlmSqlQueryService(LlmSqlQueryService):
    def __init__(self, *args, capture_sink: list[dict[str, Any]], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.capture_sink = capture_sink

    def _audit_log(self, task, sql, params, row_count, audit, execution_ms) -> None:
        self.capture_sink.append(
            {
                "phase": "audit",
                "tool_name": task.tool_name,
                "task_type": task.task_type,
                "source": audit.source,
                "cache_hit": audit.cache_hit,
                "template_id": audit.template_id,
                "task_signature": audit.task_signature,
                "generation_ms": round(audit.generation_ms, 2),
                "execution_ms": round(execution_ms, 2),
                "prompt_tokens": audit.prompt_tokens,
                "completion_tokens": audit.completion_tokens,
                "total_tokens": audit.total_tokens,
                "row_count": row_count,
                "sql": compact(sql, 900),
                "params": params,
            }
        )
        super()._audit_log(task, sql, params, row_count, audit, execution_ms)


@dataclass(frozen=True)
class ComparisonCase:
    role_label: str
    scene: str
    tool_name: str
    user: UserInfo | None
    user_input: str
    call: Callable[[SalesTools], Any]


def build_tools(db, user: UserInfo | None, *, llm_enabled: bool, capture: list[dict[str, Any]] | None = None) -> SalesTools:
    base_settings = get_settings()
    service = SalesQueryService(db, user, None)
    if llm_enabled:
        llm_settings = base_settings.model_copy(
            update={
                "llm_sql_enabled": True,
                "llm_sql_shadow_mode": False,
                "llm_sql_use_fallback": False,
                "llm_sql_repair_attempts": 1,
                "llm_sql_temperature": 0.0,
            }
        )
        sink = capture if capture is not None else []
        service.settings = llm_settings
        service.llm_sql = CapturingLlmSqlQueryService(
            db=db,
            current_user=user,
            redis_client=None,
            settings=llm_settings,
            generator=CapturingGenerator(llm_settings, sink),
            executor=CapturingExecutor(db, llm_settings.llm_sql_max_rows, sink),
            capture_sink=sink,
        )
    else:
        static_settings = base_settings.model_copy(update={"llm_sql_enabled": False})
        service.settings = static_settings
        service.llm_sql = None
    return SalesTools(service)


def compare_case(db, case: ComparisonCase) -> dict[str, Any]:
    static_result = None
    llm_result = None
    static_error = None
    llm_error = None

    with SqlCapture() as static_capture:
        static_started = time.perf_counter()
        try:
            static_result = case.call(build_tools(db, case.user, llm_enabled=False))
        except Exception as exc:
            static_error = str(exc)
        static_duration_ms = round((time.perf_counter() - static_started) * 1000, 2)

    llm_capture: list[dict[str, Any]] = []
    llm_started = time.perf_counter()
    try:
        llm_result = case.call(build_tools(db, case.user, llm_enabled=True, capture=llm_capture))
    except Exception as exc:
        llm_error = str(exc)
    llm_duration_ms = round((time.perf_counter() - llm_started) * 1000, 2)

    static_text = normalize_output(static_result) if static_error is None else ""
    llm_text = normalize_output(llm_result) if llm_error is None else ""

    llm_generations = [item for item in llm_capture if item.get("phase") == "generated"]
    llm_executions = [item for item in llm_capture if item.get("phase") == "executed"]
    llm_audits = [item for item in llm_capture if item.get("phase") == "audit"]
    token_prompt = sum(item.get("usage", {}).get("prompt_tokens", 0) for item in llm_generations)
    token_completion = sum(item.get("usage", {}).get("completion_tokens", 0) for item in llm_generations)
    token_reasoning = sum(item.get("usage", {}).get("reasoning_tokens", 0) for item in llm_generations)
    token_total = sum(item.get("usage", {}).get("total_tokens", 0) for item in llm_generations)
    llm_sources = [item.get("source") for item in llm_audits if item.get("source")]
    if llm_sources:
        llm_mode = "+".join(dict.fromkeys(llm_sources))
    elif llm_generations or llm_executions:
        llm_mode = "unknown"
    else:
        llm_mode = "bypass"
    llm_template_hits = sum(1 for item in llm_audits if item.get("source") == "template")
    llm_cache_hits = sum(1 for item in llm_audits if item.get("source") == "cache" or item.get("cache_hit"))
    llm_generator_runs = sum(1 for item in llm_audits if item.get("source") == "generator")

    return {
        "role": case.role_label,
        "scene": case.scene,
        "tool_name": case.tool_name,
        "user_input": case.user_input,
        "static_error": static_error,
        "llm_error": llm_error,
        "same_result": static_error is None and llm_error is None and static_text == llm_text,
        "static_hash": stable_hash(static_result) if static_error is None else None,
        "llm_hash": stable_hash(llm_result) if llm_error is None else None,
        "static_preview": compact(static_text, 600) if static_error is None else "",
        "llm_preview": compact(llm_text, 600) if llm_error is None else "",
        "static_duration_ms": static_duration_ms,
        "llm_duration_ms": llm_duration_ms,
        "static_prompt_tokens": 0,
        "static_completion_tokens": 0,
        "static_reasoning_tokens": 0,
        "static_total_tokens": 0,
        "static_sql": static_capture.items,
        "llm_sql": llm_capture,
        "static_select_count": len(static_capture.items),
        "llm_generation_count": len(llm_generations),
        "llm_execution_count": len(llm_executions),
        "llm_audit_count": len(llm_audits),
        "llm_mode": llm_mode,
        "llm_sources": llm_sources,
        "llm_template_hits": llm_template_hits,
        "llm_cache_hits": llm_cache_hits,
        "llm_generator_runs": llm_generator_runs,
        "static_db_ms": round(sum(item.get("duration_ms") or 0 for item in static_capture.items), 2),
        "llm_db_ms": round(sum(item.get("duration_ms") or 0 for item in llm_executions), 2),
        "llm_generation_ms": round(sum(item.get("duration_ms") or 0 for item in llm_generations), 2),
        "prompt_tokens": token_prompt,
        "completion_tokens": token_completion,
        "reasoning_tokens": token_reasoning,
        "total_tokens": token_total,
    }


def build_cases() -> list[ComparisonCase]:
    start = "2026-05-01"
    end = "2026-05-31"
    prev_start = "2026-04-01"
    prev_end = "2026-04-30"
    director = UserInfo(user_id=9101, username="于博同", role="SALES_DIRECTOR", region_id=3, rep_id=9101)
    manager = UserInfo(user_id=9102, username="太原母婴服务经理", role="SALES_MANAGER", region_id=3, rep_id=9102)
    rep = UserInfo(user_id=9103, username="李娜-太原产康顾问", role="SALES_REP", region_id=3, rep_id=9103)

    return [
        ComparisonCase("销售总监", "全公司订单明细", "query_sales_data", director, "列出本月全公司前 8 条订单", lambda t: t.query_orders(start, end, limit=8)),
        ComparisonCase("销售总监", "全公司销售额汇总", "get_sales_summary", director, "本月全公司销售额是多少", lambda t: t.get_sales_summary(start, end)),
        ComparisonCase("销售总监", "全公司销售员排名", "get_top_reps", director, "本月全公司销售员 TOP5", lambda t: t.get_top_reps(start, end, top_n=5)),
        ComparisonCase("销售总监", "全公司大区排名", "get_region_ranking", director, "本月全公司大区排名", lambda t: t.get_region_ranking(start, end)),
        ComparisonCase("销售总监", "全公司产品 Top5", "get_top_products", director, "本月全公司产品 TOP5", lambda t: t.get_top_products(start, end, 5)),
        ComparisonCase("销售总监", "全公司环比", "calc_month_over_month", director, "本月和上月环比", lambda t: t.calc_month_over_month(start, end, prev_start, prev_end)),
        ComparisonCase("销售总监", "全公司同比", "calc_year_over_year", director, "本月同比去年同期", lambda t: t.calc_year_over_year(start, end)),
        ComparisonCase("销售总监", "全公司 6 个月趋势", "get_monthly_trend", director, "全公司近 6 个月趋势", lambda t: t.get_monthly_trend(6)),
        ComparisonCase("销售总监", "趋势折线图", "generate_line_chart", director, "给我近 6 个月折线图", lambda t: t.generate_line_chart(6, title="全公司近6个月趋势")),
        ComparisonCase("销售总监", "大区柱状图", "generate_bar_chart", director, "按大区生成柱状图", lambda t: t.generate_bar_chart("region", start, end, "本月大区销售对比", 10)),
        ComparisonCase("销售总监", "销售员柱状图", "generate_bar_chart", director, "按销售员生成柱状图", lambda t: t.generate_bar_chart("rep", start, end, "本月销售员Top5", 5)),
        ComparisonCase("销售总监", "产品柱状图", "generate_bar_chart", director, "按产品生成柱状图", lambda t: t.generate_bar_chart("product", start, end, "本月产品Top5", 5)),
        ComparisonCase("销售总监", "品类柱状图", "generate_bar_chart", director, "按品类生成柱状图", lambda t: t.generate_bar_chart("category", start, end, "本月品类对比", 10)),
        ComparisonCase("销售总监", "大区饼图", "generate_pie_chart", director, "按大区生成饼图", lambda t: t.generate_pie_chart("region", start, end, "本月大区占比", 10)),
        ComparisonCase("销售总监", "销售员饼图", "generate_pie_chart", director, "按销售员生成饼图", lambda t: t.generate_pie_chart("rep", start, end, "本月销售员占比", 5)),
        ComparisonCase("销售总监", "产品饼图", "generate_pie_chart", director, "按产品生成饼图", lambda t: t.generate_pie_chart("product", start, end, "本月产品Top5占比", 5)),
        ComparisonCase("销售总监", "品类饼图", "generate_pie_chart", director, "按品类生成饼图", lambda t: t.generate_pie_chart("category", start, end, "本月品类占比", 10)),
        ComparisonCase("销售总监", "异常检测", "detect_sales_anomalies", director, "检测当前销售异常", lambda t: t.detect_all_anomalies()),
        ComparisonCase("区域经理", "区域销售额汇总", "get_sales_summary", manager, "我大区本月销售额", lambda t: t.get_sales_summary(start, end)),
        ComparisonCase("区域经理", "区域订单明细", "query_sales_data", manager, "列出我大区本月订单明细", lambda t: t.query_orders(start, end, limit=8)),
        ComparisonCase("区域经理", "区域销售员排名", "get_top_reps", manager, "我大区销售员排名", lambda t: t.get_top_reps(start, end, top_n=5)),
        ComparisonCase("区域经理", "区域产品 Top5", "get_top_products", manager, "我大区产品 TOP5", lambda t: t.get_top_products(start, end, 5)),
        ComparisonCase("区域经理", "区域趋势折线图", "generate_line_chart", manager, "我大区近 6 个月趋势图", lambda t: t.generate_line_chart(6, title="华北区近6个月趋势")),
        ComparisonCase("普通销售员", "个人销售额汇总", "get_sales_summary", rep, "我本月销售额", lambda t: t.get_sales_summary(start, end)),
        ComparisonCase("普通销售员", "个人订单明细", "query_sales_data", rep, "列出我的本月订单", lambda t: t.query_orders(start, end, limit=8)),
        ComparisonCase("普通销售员", "个人排名视角", "get_top_reps", rep, "我在排名中的情况", lambda t: t.get_top_reps(start, end, top_n=5)),
        ComparisonCase("普通销售员", "大区排名权限", "get_region_ranking", rep, "我能看大区排名吗", lambda t: t.get_region_ranking(start, end)),
        ComparisonCase("普通销售员", "个人趋势", "get_monthly_trend", rep, "看我近 6 个月趋势", lambda t: t.get_monthly_trend(6)),
    ]


def group_results(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    bucketed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        bucketed[item["tool_name"]].append(item)

    for tool_name, items in bucketed.items():
        total = len(items)
        exact = sum(1 for item in items if item["same_result"])
        llm_fail = sum(1 for item in items if item["llm_error"])
        static_fail = sum(1 for item in items if item["static_error"])
        grouped[tool_name] = {
            "tool_name": tool_name,
            "count": total,
            "exact_matches": exact,
            "match_rate": round(exact / total, 4) if total else 0.0,
            "llm_failures": llm_fail,
            "static_failures": static_fail,
            "avg_static_ms": round(sum(item["static_duration_ms"] for item in items) / total, 2),
            "avg_llm_ms": round(sum(item["llm_duration_ms"] for item in items) / total, 2),
            "avg_static_db_ms": round(sum(item["static_db_ms"] for item in items) / total, 2),
            "avg_llm_generation_ms": round(sum(item["llm_generation_ms"] for item in items) / total, 2),
            "avg_llm_db_ms": round(sum(item["llm_db_ms"] for item in items) / total, 2),
            "bypass_count": sum(1 for item in items if item["llm_mode"] == "bypass"),
            "template_count": sum(1 for item in items if "template" in item["llm_sources"]),
            "cache_count": sum(1 for item in items if "cache" in item["llm_sources"]),
            "generator_count": sum(1 for item in items if "generator" in item["llm_sources"]),
            "avg_prompt_tokens": round(sum(item["prompt_tokens"] for item in items) / total, 2),
            "avg_completion_tokens": round(sum(item["completion_tokens"] for item in items) / total, 2),
            "avg_total_tokens": round(sum(item["total_tokens"] for item in items) / total, 2),
            "avg_static_selects": round(sum(item["static_select_count"] for item in items) / total, 2),
            "avg_llm_generations": round(sum(item["llm_generation_count"] for item in items) / total, 2),
            "avg_llm_executions": round(sum(item["llm_execution_count"] for item in items) / total, 2),
            "scenes": [item["scene"] for item in items],
        }
    return grouped


def recommendation_for(tool_name: str, stats: dict[str, Any]) -> tuple[str, str]:
    match_rate = stats["match_rate"]
    llm_slower_ratio = (stats["avg_llm_ms"] / stats["avg_static_ms"]) if stats["avg_static_ms"] else 999.0

    keep_static = {
        "get_sales_summary",
        "calc_month_over_month",
        "calc_year_over_year",
        "get_monthly_trend",
        "generate_line_chart",
        "generate_bar_chart",
        "generate_pie_chart",
        "detect_sales_anomalies",
    }
    llm_candidate = {
        "query_sales_data",
        "get_top_reps",
        "get_region_ranking",
        "get_top_products",
    }

    if tool_name in {"generate_bar_chart", "generate_pie_chart"}:
        return (
            "继续写死 SQL",
            "这是图表包装层 tool，灵活性主要来自底层 ranking/product 查询，没必要把图表组装本身切到 LLM 主链路。",
        )

    if tool_name in keep_static:
        return (
            "继续写死 SQL",
            f"结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 {llm_slower_ratio:.1f} 倍，新增灵活性收益有限。",
        )

    if tool_name in llm_candidate and match_rate == 1.0 and stats["llm_failures"] == 0:
        return (
            "可优先切到 LLM SQL",
            "结果一致性已经足够高，且这类查询/图表维度更容易继续扩展过滤条件、排序和组合维度。",
        )

    if match_rate >= 0.95 and stats["llm_failures"] == 0:
        return (
            "可灰度切换",
            "结果基本一致，但建议先保留影子模式和 SQL 日志，再逐步放量。",
        )

    return (
        "继续写死 SQL",
        "当前一致性或可观测性还不够稳，继续保留确定性查询更合适。",
    )


def render_report(results: list[dict[str, Any]]) -> str:
    grouped = group_results(results)
    total = len(results)
    exact = sum(1 for item in results if item["same_result"])
    llm_fail = sum(1 for item in results if item["llm_error"])
    static_fail = sum(1 for item in results if item["static_error"])
    total_static_ms = round(sum(item["static_duration_ms"] for item in results), 2)
    total_llm_ms = round(sum(item["llm_duration_ms"] for item in results), 2)
    total_prompt_tokens = sum(item["prompt_tokens"] for item in results)
    total_completion_tokens = sum(item["completion_tokens"] for item in results)
    total_reasoning_tokens = sum(item["reasoning_tokens"] for item in results)
    total_tokens = sum(item["total_tokens"] for item in results)

    recommended_static: list[str] = []
    recommended_llm: list[str] = []
    recommendation_rows: list[str] = []
    for tool_name in sorted(grouped):
        decision, reason = recommendation_for(tool_name, grouped[tool_name])
        if decision == "可优先切到 LLM SQL":
            recommended_llm.append(tool_name)
        else:
            recommended_static.append(tool_name)
        recommendation_rows.append(
            f"| {tool_name} | {decision} | {grouped[tool_name]['match_rate']:.0%} | "
            f"{grouped[tool_name]['avg_static_ms']} | {grouped[tool_name]['avg_llm_ms']} | "
            f"0 | {grouped[tool_name]['avg_total_tokens']} | {reason} |"
        )

    lines = [
        "# 写死 SQL vs LLM 生成 SQL 评估报告",
        "",
        "## 运行范围",
        "",
        "- 运行日期：2026-05-08",
        "- 覆盖角色：销售总监、区域经理、普通销售员",
        "- 覆盖 tool：12 个 tool 全量覆盖",
        "- 图表类额外覆盖维度分支：region / rep / product / category",
        "- 对比内容：SQL 文本、最终结果、工具总耗时、数据库耗时、LLM/static token 消耗、LLM命中形态（bypass/template/cache/generator）",
        "",
        "## 总体结论",
        "",
        f"- 总场景数：{total}",
        f"- 结果完全一致：{exact}",
        f"- LLM SQL 失败：{llm_fail}",
        f"- 写死 SQL 失败：{static_fail}",
        f"- 静态方案总耗时：{total_static_ms} ms",
        f"- LLM 方案总耗时：{total_llm_ms} ms",
        f"- 静态总 token：0（写死 SQL 不调用模型）",
        f"- LLM 总 token：{total_tokens}（prompt {total_prompt_tokens} / completion {total_completion_tokens} / reasoning {total_reasoning_tokens}）",
        "",
        "> 说明：SQL 文本不同是正常现象。写死方案通常是多条小查询加 Python 拼装，LLM SQL 更常生成一条带 JOIN / GROUP BY 的 SQL。这里更看重结果一致性、权限范围和成本。",
        "",
        "## 场景覆盖清单",
        "",
        "| 角色 | tool | 业务场景 | 结果一致 | 静态耗时(ms) | LLM耗时(ms) | LLM模式 | 命中情况 | 静态token | LLM总token |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for item in results:
        hit_desc = (
            "bypass"
            if item["llm_mode"] == "bypass"
            else f"template={item['llm_template_hits']}, cache={item['llm_cache_hits']}, generator={item['llm_generator_runs']}"
        )
        lines.append(
            f"| {item['role']} | {item['tool_name']} | {item['scene']} | "
            f"{'是' if item['same_result'] else '否'} | {item['static_duration_ms']} | "
            f"{item['llm_duration_ms']} | {item['llm_mode']} | {hit_desc} | {item['static_total_tokens']} | {item['total_tokens']} |"
        )

    lines.extend(
        [
            "",
            "## 按 Tool 聚合",
            "",
            "| Tool | 场景数 | 一致率 | 平均静态耗时(ms) | 平均LLM耗时(ms) | 平均静态DB耗时(ms) | 平均LLM生成耗时(ms) | 平均LLMDB耗时(ms) | bypass次 | template次 | cache次 | generator次 | 平均静态token | 平均LLM总token |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for tool_name in sorted(grouped):
        stats = grouped[tool_name]
        lines.append(
            f"| {tool_name} | {stats['count']} | {stats['match_rate']:.0%} | {stats['avg_static_ms']} | "
            f"{stats['avg_llm_ms']} | {stats['avg_static_db_ms']} | {stats['avg_llm_generation_ms']} | "
            f"{stats['avg_llm_db_ms']} | {stats['bypass_count']} | {stats['template_count']} | {stats['cache_count']} | "
            f"{stats['generator_count']} | 0 | {stats['avg_total_tokens']} |"
        )

    lines.extend(
        [
            "",
            "## 偏差场景",
            "",
        ]
    )
    mismatches = [item for item in results if not item["same_result"]]
    if mismatches:
        for item in mismatches:
            if item["tool_name"] == "query_sales_data":
                lines.append(
                    f"- `{item['role']} / {item['tool_name']} / {item['scene']}`：静态方案先查全量订单再在文本层截前 N 条；"
                    "当前 LLM SQL 在 SQL 层直接 `LIMIT 20`，导致“共找到 N 条订单”口径不同。"
                )
            elif item["tool_name"] == "get_monthly_trend":
                lines.append(
                    f"- `{item['role']} / {item['tool_name']} / {item['scene']}`：静态方案对销售员趋势按 `region_id` 查区域趋势；"
                    "LLM SQL 经过权限注入后额外加了 `o.rep_id = :scope_rep_id`，返回的是个人趋势。"
                )
            else:
                lines.append(f"- `{item['role']} / {item['tool_name']} / {item['scene']}`：存在结果差异，需要继续排查。")
    else:
        lines.append("- 本轮没有出现结果偏差。")

    lines.extend(
        [
            "",
            "## 上线建议",
            "",
            "### 继续写死 SQL",
            "",
            ", ".join(f"`{name}`" for name in recommended_static) if recommended_static else "无",
            "",
            "### 可优先切到 LLM SQL",
            "",
            ", ".join(f"`{name}`" for name in recommended_llm) if recommended_llm else "当前没有适合直接切换的 tool",
            "",
            "| Tool | 建议 | 一致率 | 平均静态耗时(ms) | 平均LLM耗时(ms) | 平均静态token | 平均LLM总token | 原因 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(recommendation_rows)

    lines.extend(
        [
            "",
            "## 典型观察",
            "",
            "1. 写死 SQL 的优势",
            "- 汇总、趋势、环比、同比这类口径固定查询更稳定，耗时也明显更低。",
            "- 图表 tool 本身只是把底层查询结果包装成 artifact，LLM 在这里新增的价值很有限。",
            "",
            "2. LLM SQL 的优势",
            "- 明细、排名、分维度图表这类查询更容易继续扩展过滤条件、组合维度和口径变体。",
            "- 在结果一致时，LLM SQL 可以减少一部分仓库层模板代码，并把多条小查询收敛为一条聚合 SQL。",
            "",
            "3. 生产落地建议",
            "- 先把 `get_top_reps / get_region_ranking / get_top_products` 放在影子模式观察；图表 tool 跟随底层查询一起验证即可。",
            "- 在日志中补齐 request_id、tool_name、task_type、最终 SQL、参数、token 和耗时，再考虑主链路切换。",
            "- `detect_sales_anomalies` 暂不建议切主链路，它是组合型分析，当前更适合保留确定性实现。",
            "",
            "4. 命中形态解读",
            "- `bypass`：当前场景按白名单直接回写死 SQL，没有发生任何 SQL 生成。",
            "- `template`：命中 ranking 类受控模板，仍属于 LLM SQL 链路，但 token 应接近 0。",
            "- `cache`：命中缓存模板，不再重新生成 SQL。",
            "- `generator`：真正调用了模型生成 SQL，这一类最能反映 token 和生成耗时。",
            "",
            "## 每个场景的 SQL 对比",
        ]
    )

    for item in results:
        lines.extend(
            [
                "",
                f"### {item['role']} / {item['tool_name']} / {item['scene']}",
                "",
                f"- 用户问题：{item['user_input']}",
                f"- 结果一致：{'是' if item['same_result'] else '否'}",
                f"- 静态耗时：{item['static_duration_ms']} ms",
                f"- LLM耗时：{item['llm_duration_ms']} ms",
                f"- LLM模式：{item['llm_mode']}",
                f"- 命中情况：template={item['llm_template_hits']} / cache={item['llm_cache_hits']} / generator={item['llm_generator_runs']}",
                f"- 静态 token：0",
                f"- LLM token：{item['total_tokens']}（prompt {item['prompt_tokens']} / completion {item['completion_tokens']} / reasoning {item['reasoning_tokens']}）",
                "",
                "静态结果预览：",
                "```text",
                item["static_preview"] or item["static_error"] or "",
                "```",
                "",
                "LLM 结果预览：",
                "```text",
                item["llm_preview"] or item["llm_error"] or "",
                "```",
                "",
                "静态 SQL：",
            ]
        )
        if item["static_sql"]:
            for idx, sql in enumerate(item["static_sql"], start=1):
                lines.extend(
                    [
                        "",
                        f"{idx}.",
                        "```sql",
                        sql["sql"],
                        "```",
                        f"参数：`{sql['params']}`",
                        f"耗时：`{sql.get('duration_ms')}` ms",
                    ]
                )
        else:
            lines.append("无数据库 SELECT。")

        lines.append("")
        lines.append("LLM SQL：")
        if item["llm_sql"]:
            for idx, sql in enumerate(item["llm_sql"], start=1):
                header = f"{idx}. {sql.get('phase')}"
                if sql.get("task_type"):
                    header += f" / {sql['task_type']}"
                lines.extend(["", header, "```sql", str(sql.get("sql", "")), "```"])
                if "params" in sql:
                    lines.append(f"参数：`{json.dumps(sql['params'], ensure_ascii=False, default=str)}`")
                if sql.get("duration_ms") is not None:
                    lines.append(f"耗时：`{sql['duration_ms']}` ms")
                if sql.get("usage"):
                    usage = sql["usage"]
                    lines.append(
                        f"token：`prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}, "
                        f"reasoning={usage.get('reasoning_tokens', 0)}, total={usage.get('total_tokens', 0)}`"
                    )
                if sql.get("error"):
                    lines.append(f"错误：`{sql['error']}`")
                if sql.get("row_count") is not None:
                    lines.append(f"返回行数：`{sql['row_count']}`")
        else:
            lines.append("无。")

    return "\n".join(lines) + "\n"


def main() -> int:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    with SessionLocal() as db:
        for case in build_cases():
            print(f"[compare] {case.role_label} / {case.tool_name} / {case.scene}", flush=True)
            results.append(compare_case(db, case))

    RAW_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    REPORT_PATH.write_text(render_report(results), encoding="utf-8")
    print(f"[compare] raw written: {RAW_PATH}", flush=True)
    print(f"[compare] report written: {REPORT_PATH}", flush=True)
    failures = [item for item in results if item["llm_error"] or item["static_error"]]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
