"""
文件作用：
- 执行 ReAct 模型发起的工具调用，并把工具结果写回消息列表。
- 阅读这个文件时，建议先看 react_tool_executor_node 的工具调用循环。
"""

from __future__ import annotations

import json
import time
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.runtime import Runtime

from app.core.metrics import runtime_metrics
from app.graph.context import AgentContext
from app.graph.middleware import AgentMiddleware
from app.graph.react_tools import build_react_tools
from app.graph.state import GraphState
from app.graph.utils import get_middleware, last_ai_message


def _tool_map(runtime: Runtime[AgentContext]) -> dict[str, StructuredTool]:
    """
    作用：构建工具名到工具对象的映射。
    参数：runtime。
    返回：工具映射。
    """
    tool_map = runtime.context.get("tool_map")
    if tool_map is not None:
        return tool_map
    react_tools = runtime.context.get("react_tools") or build_react_tools(runtime.context["tools"])
    try:
        runtime.context["react_tools"] = react_tools
    except Exception:
        pass
    tool_map = {tool.name: tool for tool in react_tools}
    try:
        runtime.context["tool_map"] = tool_map
    except Exception:
        pass
    return tool_map


def _result_to_message_text(result: Any) -> tuple[str, dict | None]:
    """
    作用：把工具返回值拆成给模型看的文本和给前端看的 artifact。
    参数：result。
    返回：文本、artifact。
    """
    if isinstance(result, dict):
        artifact = result.get("artifact")
        message = result.get("message")
        if isinstance(message, str):
            return message, artifact
        return json.dumps(result, ensure_ascii=False), artifact
    return str(result), None


def react_tool_executor_node(state: GraphState, runtime: Runtime[AgentContext]) -> GraphState:
    """
    作用：执行模型请求的工具调用，并追加 ToolMessage。
    参数：state、runtime。
    返回：更新后的 GraphState。
    """
    messages = list(state.get("react_messages") or [])
    ai_message = last_ai_message(messages)
    if ai_message is None:
        return {
            "react_messages": messages,
            "final_answer": "服务暂时无法识别下一步工具调用，请稍后重试。",
        }

    available_tools = _tool_map(runtime)
    tool_calls = getattr(ai_message, "tool_calls", None) or []
    artifacts = list(state.get("artifacts") or [])
    result_texts: list[str] = []
    executed_count = int(state.get("tool_call_count") or 0)
    settings = runtime.context["settings"]
    middleware = get_middleware(runtime)
    max_tool_calls = max(int(settings.agent_max_tool_calls), 1)

    for call in tool_calls:
        name = call.get("name")
        args = call.get("args") or {}
        tool_call_id = call.get("id") or f"tool-call-{executed_count + 1}"
        if executed_count >= max_tool_calls:
            content = "已达到本轮最大工具调用次数，停止继续执行工具。"
            middleware.trace("工具调用被跳过", {"name": name, "reason": content})
            messages.append(ToolMessage(content=content, tool_call_id=tool_call_id, name=name or "unknown"))
            result_texts.append(content)
            break
        tool = available_tools.get(name)

        if tool is None:
            content = f"工具不存在：{name}"
            middleware.trace("工具调用失败", {"name": name, "args": args, "reason": content})
            messages.append(ToolMessage(content=content, tool_call_id=tool_call_id, name=name or "unknown"))
            result_texts.append(content)
            continue

        middleware.before_tool(executed_count + 1, name, args)
        started = time.perf_counter()
        try:
            result = tool.invoke(args)
            content, artifact = _result_to_message_text(result)
            if artifact:
                artifacts.append(artifact)
        except Exception as exc:
            content = f"工具执行失败：{exc}"
            artifact = None
            middleware.on_tool_error(executed_count + 1, name, str(exc))
        finally:
            runtime_metrics.record_tool_call(f"react:{name}", (time.perf_counter() - started) * 1000)

        middleware.after_tool(executed_count + 1, name, content, artifact is not None)
        messages.append(ToolMessage(content=content, tool_call_id=tool_call_id, name=name))
        result_texts.append(content)
        executed_count += 1

    previous_text = (state.get("tool_results") or {}).get("text") or ""
    merged_text = "\n\n".join([item for item in [previous_text, *result_texts] if item])

    return {
        "react_messages": messages,
        "artifacts": artifacts,
        "tool_results": {"text": merged_text},
        "tool_call_count": executed_count,
    }
