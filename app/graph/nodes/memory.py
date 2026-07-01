"""
文件作用：
- 负责读取和写回会话记忆，让多轮对话保持上下文连续。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.context import AgentContext
from app.graph.helpers import build_chat_model
from app.graph.middleware import AgentMiddleware
from app.graph.prompts import MEMORY_SUMMARY_SYSTEM_PROMPT
from app.graph.state import GraphState
from app.graph.utils import content_to_text, get_middleware
from langgraph.runtime import Runtime


FOLLOWUP_KEYWORDS = (
    "图呢",
    "图表呢",
    "生成图",
    "生成图表",
    "画图",
    "可视化",
    "饼图",
    "饼状图",
    "折线图",
    "柱状图",
    "柱形图",
    "继续",
    "接着",
    "上面",
    "刚才",
    "这个",
    "这些",
    "该",
    "它",
    "其",
    "进一步",
    "下钻",
    "展开",
    "详细",
    "导出",
)


def _is_followup_request(request_text: str) -> bool:
    """
    作用：判断当前问题是否明显依赖上一轮上下文。
    参数：request_text。
    返回：是否追问。
    """
    text = request_text.strip()
    return any(keyword in text for keyword in FOLLOWUP_KEYWORDS)


def _history_to_react_messages(messages: list[dict], request_text: str, limit: int = 10) -> list:
    """
    作用：把数据库里的简化消息转换为模型可直接消费的 LangChain 消息。
    参数：messages、request_text、limit。
    返回：当前轮 ReAct 流程的消息列表。
    """
    if not _is_followup_request(request_text):
        return [HumanMessage(content=request_text)]

    trimmed = messages[-limit:] if len(messages) > limit else messages
    react_messages = []
    for item in trimmed:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        if role == "user":
            react_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            react_messages.append(AIMessage(content=content))
    react_messages.append(HumanMessage(content=request_text))
    return react_messages


def _compact_history_text(text: str, max_chars: int) -> str:
    """
    作用：把历史消息压缩成更短的一行文本。
    参数：text、max_chars。
    返回：压缩后的文本。
    """
    compact = " ".join(str(text).split())
    if len(compact) <= max_chars:
        return compact
    return f"{compact[:max_chars]}..."


def _format_history_for_summary(messages: list[dict], max_chars: int) -> str:
    """
    作用：把更早历史整理成适合给摘要模型消费的文本。
    参数：messages、max_chars。
    返回：格式化后的历史文本。
    """
    lines: list[str] = []
    for item in messages:
        content = _compact_history_text(str(item.get("content", "")).strip(), max_chars)
        if not content:
            continue
        role = "用户" if item.get("role") == "user" else "助手"
        artifacts = item.get("artifacts") or []
        artifact_titles = [str(artifact.get("title", "")).strip() for artifact in artifacts if artifact.get("title")]
        artifact_text = f"；图表={', '.join(artifact_titles)}" if artifact_titles else ""
        lines.append(f"{role}：{content}{artifact_text}")
    return "\n".join(lines)


def _build_summary_context(messages: list[dict], keep_recent: int, summary_items: int, max_chars: int) -> str | None:
    """
    作用：把较早历史压缩成摘要，避免长会话直接撑爆上下文。
    参数：messages、keep_recent、summary_items、max_chars。
    返回：摘要文本或 None。
    """
    if len(messages) <= keep_recent:
        return None
    older_messages = messages[:-keep_recent]
    sampled = older_messages[-summary_items:] if len(older_messages) > summary_items else older_messages
    lines: list[str] = []
    for item in sampled:
        content = _compact_history_text(str(item.get("content", "")).strip(), max_chars)
        if not content:
            continue
        role = "用户" if item.get("role") == "user" else "助手"
        lines.append(f"{role}：{content}")
    if not lines:
        return None
    return "更早对话摘要：\n" + "\n".join(lines)


def _get_memory_summary_llm(runtime: Runtime[AgentContext]):
    """
    作用：按请求缓存历史摘要模型实例。
    参数：runtime。
    返回：模型对象。
    """
    llm = runtime.context.get("memory_summary_llm")
    if llm is not None:
        return llm
    settings = runtime.context["settings"]
    model_name = str(getattr(settings, "agent_memory_llm_summary_model", "") or "").strip() or None
    llm = build_chat_model(settings, temperature=0.0, model_name=model_name)
    try:
        runtime.context["memory_summary_llm"] = llm
    except Exception:
        pass
    return llm


def _build_llm_summary_context(
    messages: list[dict],
    request_text: str,
    runtime: Runtime[AgentContext],
    keep_recent: int,
    trigger_messages: int,
    max_chars: int,
) -> str | None:
    """
    作用：使用 LLM 把更早历史压缩成摘要。
    参数：messages、request_text、runtime、keep_recent、trigger_messages、max_chars。
    返回：摘要文本或 None。
    """
    if len(messages) <= keep_recent:
        return None

    older_messages = messages[:-keep_recent]
    if len(older_messages) < trigger_messages:
        return None

    history_text = _format_history_for_summary(older_messages, max_chars)
    if not history_text:
        return None

    middleware = get_middleware(runtime)
    try:
        llm = _get_memory_summary_llm(runtime)
        response = llm.invoke(
            [
                SystemMessage(content=MEMORY_SUMMARY_SYSTEM_PROMPT.format(current_request=request_text or "无")),
                HumanMessage(content=history_text),
            ]
        )
        summary = content_to_text(getattr(response, "content", response))
        if not summary or summary == "无":
            return None
        middleware and middleware.trace("记忆压缩使用 LLM 摘要", {"older_messages": len(older_messages)})
        return "更早对话摘要：\n" + summary
    except Exception as exc:
        middleware and middleware.trace("记忆压缩回退到规则摘要", {"reason": str(exc)})
        return None


# 定义函数 load_memory_node，负责加载已有状态、配置或持久化内容。
def load_memory_node(state: GraphState, runtime: Runtime[AgentContext]) -> GraphState:
    """
    作用：加载memory_node内容。
    参数：state、runtime。
    返回：函数执行后的结果。
    """
    settings = runtime.context["settings"]
    messages = runtime.context["memory_service"].get_messages(state["session_id"])
    followup_limit = max(int(getattr(settings, "agent_memory_followup_limit", 10)), 1)
    keep_recent = max(int(getattr(settings, "agent_memory_window_messages", 20)), followup_limit)
    summary_items = max(int(getattr(settings, "agent_memory_summary_messages", 6)), 1)
    max_chars = max(int(getattr(settings, "agent_memory_summary_chars", 80)), 20)
    llm_summary_enabled = bool(getattr(settings, "agent_memory_llm_summary_enabled", True))
    trigger_messages = max(int(getattr(settings, "agent_memory_llm_summary_trigger_messages", 8)), 1)
    summary_context = None

    if llm_summary_enabled:
        summary_context = _build_llm_summary_context(
            messages,
            state.get("request_text", ""),
            runtime,
            keep_recent,
            trigger_messages,
            max_chars,
        )
    if summary_context is None:
        summary_context = _build_summary_context(messages, keep_recent, summary_items, max_chars)
        middleware = get_middleware(runtime)
        if summary_context:
            middleware and middleware.trace("记忆压缩使用规则摘要", {"older_messages": max(len(messages) - keep_recent, 0)})

    return {
        "messages": messages,
        "react_messages": _history_to_react_messages(messages[-keep_recent:], state.get("request_text", ""), limit=followup_limit),
        "summary_context": summary_context,
    }


# 定义函数 persist_memory_node，负责把当前结果写回持久化存储。
def persist_memory_node(state: GraphState, runtime: Runtime[AgentContext]) -> GraphState:
    """
    作用：执行persist_memory_node对应的业务逻辑。
    参数：state、runtime。
    返回：函数执行后的结果。
    """
    history = list(state.get("messages") or [])
    history.append({"role": "user", "content": state.get("request_text", "")})
    assistant_message = {"role": "assistant", "content": state.get("final_answer", "")}
    if state.get("artifacts"):
        assistant_message["artifacts"] = state["artifacts"]
    runtime.context["memory_service"].save_messages(state["session_id"], history + [assistant_message])
    return {}
