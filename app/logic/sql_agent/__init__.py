"""
LLM SQL 查询子模块。

该模块把“由模型生成 SQL”限制在工具内部使用，并提供 schema 白名单、
安全校验、权限注入、执行和结果映射能力。
"""

from app.logic.sql_agent.models import GeneratedSql, QueryScope, SqlResolutionAudit, SqlTaskSpec, SqlValidationResult
from app.logic.sql_agent.cache import CachedSqlTemplate, SqlTemplateCache
from app.logic.sql_agent.service import LlmSqlQueryService
from app.logic.sql_agent.template_registry import SqlTemplateDefinition, SqlTemplateRegistry

__all__ = [
    "CachedSqlTemplate",
    "GeneratedSql",
    "LlmSqlQueryService",
    "QueryScope",
    "SqlResolutionAudit",
    "SqlTemplateCache",
    "SqlTemplateDefinition",
    "SqlTemplateRegistry",
    "SqlTaskSpec",
    "SqlValidationResult",
]
