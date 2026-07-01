"""
文件作用：
- 实现 ReAct 风格的 Agent LLM 节点，由模型决定是否继续调用工具。
- 阅读这个文件时，建议先看 react_agent_node / stream_react_agent_node，再看内部辅助函数。
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.runtime import Runtime

from app.core.metrics import runtime_metrics
from app.graph.context import AgentContext
from app.graph.helpers import build_chat_model
from app.graph.middleware import AgentMiddleware
from app.graph.prompts import REACT_SYSTEM_PROMPT
from app.graph.react_tools import build_react_tools
from app.graph.state import GraphState
from app.graph.utils import content_to_text, get_middleware


def _strip_chart_claims_without_artifact(answer: str) -> str:
    """
    作用：没有图表 artifact 时，移除“图表已生成”的误导性表述。
    参数：answer。
    返回：清理后的回答。
    """
    chart_words = ("图表", "折线图", "柱状图", "柱形图", "饼图", "可视化")
    cleaned: list[str] = []
    for line in answer.splitlines():
        text = line.strip()
        if not text:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue

        has_chart_word = any(word in text for word in chart_words)
        claims_generated = (
            "已生成" in text
            or ("已为" in text and "生成" in text)
            or "请查看下方" in text
            or (has_chart_word and "下方" in text)
        )
        if has_chart_word and claims_generated:
            continue
        cleaned.append(line)

    return "\n".join(cleaned).strip() or "已完成销售数据分析。"


def _mentions_chart(answer: str) -> bool:
    """
    作用：判断回答中是否已经提到图表，避免重复追加提示。
    参数：answer。
    返回：是否提到图表。
    """
    return any(word in answer for word in ("图表", "折线图", "柱状图", "柱形图", "饼图", "饼状图", "可视化"))


def _is_chart_only_request(request_text: str) -> bool:
    """
    作用：识别“生成饼状图”这类只要求把上一轮结果可视化的短追问。
    参数：request_text。
    返回：是否图表短追问。
    """
    text = request_text.strip()
    chart_words = ("生成图", "生成图表", "画图", "可视化", "饼图", "饼状图", "折线图", "柱状图", "柱形图")
    subject_words = ("产品", "大区", "区域", "销售员", "品类", "类别", "趋势", "排名", "top", "Top", "SKU", "本月", "本季度")
    return any(word in text for word in chart_words) and not any(word in text for word in subject_words)


def _chart_done_answer(request_text: str) -> str:
    """
    作用：为图表短追问生成确定性最终回复，避免模型编造图表分析。
    参数：request_text。
    返回：最终回复。
    """
    text = request_text.strip()
    if "饼" in text:
        return "已生成饼状图，请查看下方。"
    if "折线" in text:
        return "已生成折线图，请查看下方。"
    if "柱" in text:
        return "已生成柱状图，请查看下方。"
    return "已生成图表，请查看下方。"


def _user_context(runtime: Runtime[AgentContext]) -> str:
    """
    作用：构造放入系统提示词的当前用户权限说明。
    参数：runtime。
    返回：用户上下文文本。
    """
    user = runtime.context.get("current_user")
    if user is None:
        return "未启用鉴权或匿名演示模式；实际数据范围仍以 Service 层权限控制为准。"
    return (
        f"user_id={user.user_id}, username={user.username}, role={user.role}, "
        f"region_id={user.region_id}, rep_id={user.rep_id}。实际数据范围以 Service 层强制过滤为准。"
    )


def _build_system_message(runtime: Runtime[AgentContext], state: GraphState) -> SystemMessage:
    """
    作用：构建 ReAct Agent 系统提示词。
    参数：runtime、state。
    返回：SystemMessage。
    """
    return SystemMessage(
        content=REACT_SYSTEM_PROMPT.format(
            today=runtime.context["today"],
            user_context=_user_context(runtime),
            current_request=state.get("request_text", ""),
            history_summary=state.get("summary_context") or "无",
        )
    )




def _get_react_tools(runtime: Runtime[AgentContext]) -> list[Any]:
    """
    作用：按请求缓存工具 schema。
    参数：runtime。
    返回：模型可见工具列表。
    """
    react_tools = runtime.context.get("react_tools")
    if react_tools is not None:
        return react_tools
    react_tools = build_react_tools(runtime.context["tools"])
    try:
        runtime.context["react_tools"] = react_tools
    except Exception:
        pass
    return react_tools


def _get_llm_with_tools(runtime: Runtime[AgentContext]):
    """
    作用：按请求缓存绑定工具后的模型。
    参数：runtime。
    返回：绑定工具后的模型对象。
    """
    llm_with_tools = runtime.context.get("llm_with_tools")
    if llm_with_tools is not None:
        return llm_with_tools
    llm = build_chat_model(runtime.context["settings"], temperature=0.2)
    llm_with_tools = llm.bind_tools(_get_react_tools(runtime))
    try:
        runtime.context["llm_with_tools"] = llm_with_tools
    except Exception:
        pass
    return llm_with_tools


def _ensure_react_messages(state: GraphState) -> list[Any]:
    """
    作用：确保当前轮有可发送给模型的消息列表。
    参数：state。
    返回：消息列表。
    """
    messages = list(state.get("react_messages") or [])
    if messages:
        return messages
    return [HumanMessage(content=state.get("request_text", ""))]


def _normalize_ai_response(response: Any) -> AIMessage:
    """
    作用：把模型返回值统一转换为 AIMessage。
    参数：response。
    返回：AIMessage。
    """
    if isinstance(response, AIMessage):
        return response
    return AIMessage(
        content=content_to_text(getattr(response, "content", response)),
        tool_calls=getattr(response, "tool_calls", None) or [],
    )


def _finalize_react_turn(
    state: GraphState,
    runtime: Runtime[AgentContext],
    messages: list[Any],
    response: AIMessage,
    round_no: int,
    streamed_final_answer: bool = False,
) -> GraphState:
    """
    作用：统一处理模型响应的 trace、工具分支和最终回答收尾逻辑。
    参数：state、runtime、messages、response、round_no、streamed_final_answer。
    返回：更新后的 GraphState。
    """
    middleware = get_middleware(runtime)
    messages.append(response)
    tool_calls = getattr(response, "tool_calls", None) or []
    middleware.on_llm_round(
        round_no,
        content_to_text(response.content) or "<空>",
        [{"name": call.get("name"), "args": call.get("args") or {}} for call in tool_calls] if tool_calls else "无",
    )

    max_tool_calls = max(int(runtime.context["settings"].agent_max_tool_calls), 1)
    current_count = int(state.get("tool_call_count") or 0)
    if tool_calls and current_count >= max_tool_calls:
        middleware.trace("工具调用达到上限，停止 ReAct 循环", {"max_tool_calls": max_tool_calls})
        return {
            "react_messages": messages,
            "react_round_count": round_no,
            "final_answer": "这个问题需要调用过多工具。为了避免循环执行，我先暂停处理，请缩小查询范围或拆成更具体的问题。",
            "streamed_final_answer": False,
        }

    if tool_calls:
        return {
            "react_messages": messages,
            "react_round_count": round_no,
            "final_answer": None,
            "streamed_final_answer": False,
        }

    final_answer = content_to_text(response.content)
    if not final_answer:
        tool_text = (state.get("tool_results") or {}).get("text") or ""
        final_answer = tool_text or "已完成销售数据分析。"
    request_text = str(state.get("request_text", ""))
    chart_only_request = _is_chart_only_request(request_text)
    if state.get("artifacts") and chart_only_request:
        final_answer = _chart_done_answer(request_text)
        streamed_final_answer = False
    elif state.get("artifacts") and not _mentions_chart(final_answer):
        chart_suffix = _chart_done_answer(request_text) if chart_only_request else "已生成图表，请查看下方。"
        final_answer = f"{final_answer}\n\n{chart_suffix}" if final_answer else chart_suffix
    if not state.get("artifacts"):
        final_answer = _strip_chart_claims_without_artifact(final_answer)

    return {
        "react_messages": messages,
        "react_round_count": round_no,
        "final_answer": final_answer,
        "streamed_final_answer": streamed_final_answer,
    }


def react_agent_node(state: GraphState, runtime: Runtime[AgentContext]) -> GraphState:
    """
    作用：调用绑定工具后的模型，生成最终回答或下一步工具调用。
    参数：state、runtime。
    返回：更新后的 GraphState。
    """
    llm_with_tools = _get_llm_with_tools(runtime)
    messages = _ensure_react_messages(state)
    started = time.perf_counter()
    response = _normalize_ai_response(llm_with_tools.invoke([_build_system_message(runtime, state), *messages]))
    runtime_metrics.record_llm_call("react_agent", (time.perf_counter() - started) * 1000)
    round_no = int(state.get("react_round_count") or 0) + 1
    return _finalize_react_turn(state, runtime, messages, response, round_no)


def stream_react_agent_node(state: GraphState, runtime: Runtime[AgentContext]) -> Iterator[dict[str, Any]]:
    """
    作用：在流式场景下运行 ReAct 模型节点，并在合适时把最终文本 token 逐段吐给前端。
    参数：state、runtime。
    返回：一个生成器，yield 事件并在结束时返回 GraphState。
    """
    llm_with_tools = _get_llm_with_tools(runtime)
    if not hasattr(llm_with_tools, "stream") or _is_chart_only_request(str(state.get("request_text", ""))):
        return react_agent_node(state, runtime)

    middleware = get_middleware(runtime)
    messages = _ensure_react_messages(state)
    payload = [_build_system_message(runtime, state), *messages]
    started = time.perf_counter()
    response_chunk = None
    saw_tool_calls = False
    streamed_text_parts: list[str] = []
    reply_started = False

    for chunk in llm_with_tools.stream(payload):
        response_chunk = chunk if response_chunk is None else response_chunk + chunk
        if getattr(chunk, "tool_call_chunks", None) or getattr(chunk, "tool_calls", None):
            saw_tool_calls = True
        text = content_to_text(getattr(chunk, "content", None), strip=False)
        if text and not saw_tool_calls:
            if not reply_started:
                reply_started = True
                yield {"event": "status", "data": "正在输出回答..."}
            streamed_text_parts.append(text)
            event = {"event": "token", "data": text}
            middleware.emit_token(text)
            yield event

    runtime_metrics.record_llm_call("react_agent", (time.perf_counter() - started) * 1000)
    if response_chunk is None:
        return react_agent_node(state, runtime)

    round_no = int(state.get("react_round_count") or 0) + 1
    response = _normalize_ai_response(response_chunk)
    result = _finalize_react_turn(
        state,
        runtime,
        messages,
        response,
        round_no,
        streamed_final_answer=bool(streamed_text_parts) and not getattr(response, "tool_calls", None),
    )
    return result
