"""
LLM SQL 执行器。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class SqlExecutor:
    """使用 SQLAlchemy 参数化执行只读 SQL。"""

    def __init__(self, db: Session, max_rows: int = 200, timeout_seconds: int = 5) -> None:
        self.db = db
        self.max_rows = max(max_rows, 1)
        self.timeout_seconds = max(timeout_seconds, 1)

    def explain(self, sql: str, params: dict[str, Any]) -> None:
        self.db.execute(text(f"EXPLAIN {sql}"), params).all()

    def explain_validate(self, sql: str, params: dict[str, Any]) -> bool:
        """运行 EXPLAIN 检查查询计划，不实际执行。返回 True 表示 SQL 有效。"""
        try:
            self.db.execute(text(f"EXPLAIN {sql}"), params).all()
            return True
        except Exception:
            return False

    def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        self.db.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {self.timeout_seconds * 1000}"))
        rows = self.db.execute(text(sql), params).mappings().all()
        return [dict(row) for row in rows[: self.max_rows]]
