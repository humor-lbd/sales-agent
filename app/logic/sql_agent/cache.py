"""
LLM SQL 结构缓存。
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

from redis import Redis

from app.logic.sql_agent.models import SqlTaskSpec


@dataclass(frozen=True)
class CachedSqlTemplate:
    """缓存中的 SQL 模板。"""

    sql: str
    result_columns: list[str]
    task_type: str
    tool_name: str
    created_at: float


class SqlTemplateCache:
    """支持内存和 Redis 的 SQL 结构缓存。"""

    def __init__(
        self,
        *,
        enabled: bool,
        ttl_seconds: int,
        backend: str = "memory",
        redis_client: Redis | None = None,
        max_memory_entries: int = 256,
    ) -> None:
        self.enabled = enabled
        self.ttl_seconds = max(int(ttl_seconds), 1)
        self.backend = (backend or "memory").lower()
        self.redis = redis_client if self.backend == "redis" else None
        self._memory: dict[str, tuple[float, CachedSqlTemplate]] = {}
        self._max_memory_entries = max(max_memory_entries, 16)

    def _evict_expired(self) -> None:
        """清理已过期的内存缓存条目。"""
        now = time.time()
        expired = [k for k, (exp, _) in self._memory.items() if exp < now]
        for k in expired:
            self._memory.pop(k, None)

    @staticmethod
    def build_signature(task: SqlTaskSpec) -> str:
        payload = {
            "tool_name": task.tool_name,
            "task_type": task.task_type,
            "scope_role": task.scope.role,
            "scope_has_region": task.scope.region_id is not None,
            "scope_has_rep": task.scope.rep_id is not None,
            "has_region": task.region_id is not None,
            "has_rep": task.rep_id is not None,
            "has_product": task.product_id is not None,
            "has_category": task.category is not None,
            "has_months": task.months is not None,
            "has_top_n": task.top_n is not None,
            "has_limit": task.limit is not None,
            "dimension": task.dimension,
            "order_by": task.order_by,
            "result_contract": task.result_contract,
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _redis_key(self, signature: str) -> str:
        return f"llm-sql-template:{signature}"

    def get(self, signature: str) -> CachedSqlTemplate | None:
        if not self.enabled:
            return None
        if self.redis is not None:
            payload = self.redis.get(self._redis_key(signature))
            if not payload:
                return None
            data = json.loads(payload)
            return CachedSqlTemplate(
                sql=data["sql"],
                result_columns=list(data.get("result_columns") or []),
                task_type=data["task_type"],
                tool_name=data["tool_name"],
                created_at=float(data["created_at"]),
            )
        item = self._memory.get(signature)
        if item is None:
            return None
        expires_at, template = item
        if expires_at < time.time():
            self._memory.pop(signature, None)
            return None
        return template

    def set(self, signature: str, template: CachedSqlTemplate) -> None:
        if not self.enabled:
            return
        if self.redis is not None:
            payload = json.dumps(
                {
                    "sql": template.sql,
                    "result_columns": template.result_columns,
                    "task_type": template.task_type,
                    "tool_name": template.tool_name,
                    "created_at": template.created_at,
                },
                ensure_ascii=False,
            )
            self.redis.setex(self._redis_key(signature), self.ttl_seconds, payload)
            return
        if len(self._memory) >= self._max_memory_entries:
            self._evict_expired()
            if len(self._memory) >= self._max_memory_entries:
                oldest_key = min(self._memory, key=lambda k: self._memory[k][0])
                self._memory.pop(oldest_key, None)
        self._memory[signature] = (time.time() + self.ttl_seconds, template)
