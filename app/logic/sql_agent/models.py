"""
LLM SQL 查询层的数据结构。
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


QueryScopeRole = Literal["SALES_REP", "SALES_MANAGER", "SALES_DIRECTOR", "ANONYMOUS"]


class QueryScope(BaseModel):
    """当前用户的数据权限范围。"""

    role: QueryScopeRole = "ANONYMOUS"
    user_id: int | str | None = None
    region_id: int | None = None
    rep_id: int | None = None


class SqlTaskSpec(BaseModel):
    """交给 SQL LLM 的结构化查询任务。"""

    tool_name: str
    task_type: str
    start_date: date | None = None
    end_date: date | None = None
    region_id: int | None = None
    region_name: str | None = None
    rep_id: int | None = None
    rep_name: str | None = None
    product_id: int | None = None
    product_name: str | None = None
    category: str | None = None
    top_n: int | None = None
    months: int | None = None
    dimension: str | None = None
    order_by: str | None = None
    limit: int | None = None
    scope: QueryScope = Field(default_factory=QueryScope)
    result_contract: list[str] = Field(default_factory=list)


class GeneratedSql(BaseModel):
    """LLM 生成的候选 SQL。"""

    sql: str
    params: dict[str, Any] = Field(default_factory=dict)
    result_columns: list[str] = Field(default_factory=list)
    reason: str = ""
    confidence: float = 0.0


class SqlValidationResult(BaseModel):
    """SQL 校验结果。"""

    ok: bool
    errors: list[str] = Field(default_factory=list)
    normalized_sql: str | None = None


class SqlResolutionAudit(BaseModel):
    """SQL 解析与执行审计信息。"""

    source: Literal["generator", "cache", "template"]
    task_signature: str
    cache_hit: bool = False
    template_id: str | None = None
    generation_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
