"""
候选 SQL 安全校验。
"""

from __future__ import annotations

import re

from app.logic.sql_agent.models import GeneratedSql, SqlTaskSpec, SqlValidationResult
from app.logic.sql_agent.schema_registry import SqlSchemaRegistry


class SqlValidator:
    """对 LLM 生成的 SQL 做只读、安全和业务口径校验。"""

    _dangerous_keywords = (
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "REPLACE",
        "GRANT",
        "REVOKE",
        "CALL",
        "EXEC",
        "LOAD",
        "OUTFILE",
        "INFILE",
        "LOCK",
        "UNLOCK",
        "SET",
        "SHOW",
        "DESCRIBE",
    )
    _system_schemas = ("mysql.", "information_schema.", "performance_schema.", "sys.")

    def __init__(self, schema: SqlSchemaRegistry | None = None) -> None:
        self.schema = schema or SqlSchemaRegistry()

    @staticmethod
    def _fail(errors: list[str] | str) -> SqlValidationResult:
        if isinstance(errors, str):
            errors = [errors]
        return SqlValidationResult(ok=False, errors=errors)

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        return identifier.strip("`").split(".")[-1].lower()

    def _extract_tables(self, sql: str) -> set[str]:
        tables: set[str] = set()
        for match in re.finditer(r"\b(?:from|join)\s+([`A-Za-z0-9_.]+)", sql, re.IGNORECASE):
            tables.add(self._normalize_identifier(match.group(1)))
        return tables

    def _validate_alias_columns(self, sql: str) -> list[str]:
        errors: list[str] = []
        for alias, column in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b", sql):
            alias = alias.lower()
            column = column.lower()
            if alias in self.schema.table_aliases and not self.schema.allows_column(alias, column):
                errors.append(f"未授权字段：{alias}.{column}")
        return errors

    @staticmethod
    def _has_result_contract(generated: GeneratedSql, task: SqlTaskSpec, sql: str) -> list[str]:
        if not task.result_contract:
            return []
        returned = {item.lower() for item in generated.result_columns}
        lower_sql = sql.lower()
        missing = [
            column
            for column in task.result_contract
            if column.lower() not in returned and f" as {column.lower()}" not in lower_sql
        ]
        return missing

    @staticmethod
    def _ensure_detail_limit(sql: str, task: SqlTaskSpec) -> str:
        if re.search(r"\blimit\b", sql, re.IGNORECASE):
            return sql
        limit = min(max(int(task.limit or 20), 1), 50)
        return f"{sql.rstrip()} LIMIT {limit}"

    def validate(self, generated: GeneratedSql, task: SqlTaskSpec) -> SqlValidationResult:
        sql = generated.sql.strip()
        errors: list[str] = []
        lower = sql.lower()

        if not sql:
            errors.append("SQL 不能为空")
        if ";" in sql:
            errors.append("SQL 不允许包含分号")
        if "--" in sql or "/*" in sql or "*/" in sql or re.search(r"(^|\s)#", sql):
            errors.append("SQL 不允许包含注释")
        if not re.match(r"^\s*(select|with)\b", sql, re.IGNORECASE):
            errors.append("只允许 SELECT 或 WITH ... SELECT 查询")
        if re.search(r"\bselect\s+\*", sql, re.IGNORECASE) or re.search(r",\s*\*", sql):
            errors.append("不允许 SELECT *")
        if any(schema in lower for schema in self._system_schemas):
            errors.append("不允许查询系统库")
        for keyword in self._dangerous_keywords:
            if re.search(rf"\b{keyword}\b", sql, re.IGNORECASE):
                errors.append(f"SQL 包含危险关键词：{keyword}")

        tables = self._extract_tables(sql)
        if not tables:
            errors.append("SQL 必须包含 FROM 表")
        unauthorized = sorted(tables - self.schema.allowed_tables)
        if unauthorized:
            errors.append("SQL 使用了未授权表：" + ", ".join(unauthorized))

        errors.extend(self._validate_alias_columns(sql))

        if task.task_type in self.schema.sales_metric_tasks:
            has_completed_filter = bool(re.search(
                r"o\.status\s*=\s*['\"]?completed['\"]?", sql, re.IGNORECASE,
            ))
            if not has_completed_filter:
                errors.append("销售指标查询必须过滤 o.status = 'COMPLETED'")

        if task.task_type in self.schema.detail_tasks:
            if re.search(r"o\.status\s*=\s*['\"]?completed['\"]?", lower, re.IGNORECASE):
                errors.append("订单明细查询不允许默认过滤 COMPLETED，必须保留 REFUNDED/CANCELLED 等状态")

        if task.start_date and task.end_date:
            if "o.order_date" not in lower or ":start_date" not in lower or ":end_date" not in lower:
                errors.append("销售查询必须使用 o.order_date 和 :start_date/:end_date")

        if task.region_id is None:
            strict_region_filter = re.search(r"\b(?:o\.region_id|r\.id)\s*=\s*:region_id\b", lower)
            optional_region_filter = ":region_id is null" in lower or ":region_id) is null" in lower
            if strict_region_filter and not optional_region_filter:
                errors.append("任务未提供 region_id，SQL 不允许强制过滤 :region_id")
        if task.rep_id is None and re.search(r"\b(?:o\.rep_id|s\.id)\s*=\s*:rep_id\b", lower):
            errors.append("任务未提供 rep_id，SQL 不允许强制过滤 :rep_id")
        if task.product_id is None and re.search(r"\bo\.product_id\s*=\s*:product_id\b", lower):
            errors.append("任务未提供 product_id，SQL 不允许强制过滤 :product_id")

        missing_contract = self._has_result_contract(generated, task, sql)
        if missing_contract:
            errors.append("SQL 返回列不满足 result_contract：" + ", ".join(missing_contract))

        if errors:
            return self._fail(errors)

        normalized_sql = self._ensure_detail_limit(sql, task) if task.task_type in self.schema.detail_tasks else sql
        return SqlValidationResult(ok=True, normalized_sql=normalized_sql)
