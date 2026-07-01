"""
ReAct 图节点共享的辅助函数。

消除 react_agent / react_tool_executor / memory / generator 中的重复定义。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from app.graph.middleware import AgentMiddleware

if TYPE_CHECKING:
    from app.graph.context import AgentContext


def content_to_text(content: Any, strip: bool = True) -> str:
    """把模型消息内容统一压平成纯文本。

    Args:
        content: 模型返回的 content（str / list / 其他）。
        strip: 是否 strip 空白。流式场景传 False 以保留 token 间空格。
    """
    if isinstance(content, str):
        return content.strip() if strip else content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        text = "".join(parts)
        return text.strip() if strip else text
    text = str(content) if content is not None else ""
    return text.strip() if strip else text


def get_middleware(runtime: Runtime[AgentContext]) -> AgentMiddleware | None:
    """获取当前请求共用的 AgentMiddleware，不存在时创建并缓存。"""
    middleware = runtime.context.get("middleware")
    if isinstance(middleware, AgentMiddleware):
        return middleware
    middleware = AgentMiddleware(
        runtime.context["settings"],
        str(runtime.context.get("request_id", "local")),
        runtime.context.get("stream_sink"),
    )
    try:
        runtime.context["middleware"] = middleware
    except Exception:
        pass
    return middleware


def last_ai_message(messages: list[Any]) -> AIMessage | None:
    """从消息列表中找出最后一条 AIMessage。"""
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None
