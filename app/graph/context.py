"""
文件作用：
- 定义图执行期间共享的上下文字段，方便各节点复用依赖。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from typing import Any, Callable, TypedDict

try:
    from typing import NotRequired
except ImportError:  # pragma: no cover - Python < 3.11 compatibility
    from typing_extensions import NotRequired

from app.core.config import Settings
from app.logic.schemas import UserInfo
from app.logic.services import MemoryService
from app.logic.tools import SalesTools


# 定义类 AgentContext，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class AgentContext(TypedDict):
    current_user: UserInfo | None
    settings: Settings
    tools: SalesTools
    memory_service: MemoryService
    today: str
    request_id: str
    llm_with_tools: NotRequired[Any]
    react_tools: NotRequired[list[Any]]
    tool_map: NotRequired[dict[str, Any]]
    memory_summary_llm: NotRequired[Any]
    middleware: NotRequired[Any]
    stream_sink: NotRequired[Callable[[str, Any], None]]
