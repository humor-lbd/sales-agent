"""
SQL 权限过滤注入。
"""

from __future__ import annotations

import re
from typing import Any

from app.logic.sql_agent.models import QueryScope


class PermissionPolicyInjector:
    """根据当前用户角色向 SQL 中追加强制权限条件。"""

    _insert_before_clauses = (" group by ", " order by ", " limit ")

    @staticmethod
    def _contains_order_table(sql: str) -> bool:
        return bool(re.search(r"\bsa_sales_order\b", sql, re.IGNORECASE))

    @classmethod
    def _append_condition(cls, sql: str, condition: str) -> str:
        lower = sql.lower()
        insert_at = len(sql)
        for clause in cls._insert_before_clauses:
            pos = lower.find(clause)
            if pos >= 0:
                insert_at = min(insert_at, pos)

        head = sql[:insert_at].rstrip()
        tail = sql[insert_at:]
        if re.search(r"\bwhere\b", head, re.IGNORECASE):
            return f"{head} AND {condition}{tail}"
        return f"{head} WHERE {condition}{tail}"

    def apply(self, sql: str, params: dict[str, Any], scope: QueryScope) -> tuple[str, dict[str, Any]]:
        if scope.role == "SALES_REP":
            if scope.rep_id is None:
                raise ValueError("SALES_REP 缺少 rep_id，无法注入权限")
            if not self._contains_order_table(sql):
                raise ValueError("销售员权限查询必须包含 sa_sales_order")
            scoped_params = dict(params)
            scoped_params["scope_rep_id"] = scope.rep_id
            return self._append_condition(sql, "o.rep_id = :scope_rep_id"), scoped_params

        if scope.role == "SALES_MANAGER":
            if scope.region_id is None:
                raise ValueError("SALES_MANAGER 缺少 region_id，无法注入权限")
            if not self._contains_order_table(sql):
                raise ValueError("销售经理权限查询必须包含 sa_sales_order")
            scoped_params = dict(params)
            scoped_params["scope_region_id"] = scope.region_id
            return self._append_condition(sql, "o.region_id = :scope_region_id"), scoped_params

        return sql, dict(params)
