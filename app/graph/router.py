"""
文件作用：
- 定义图节点之间的分支路由条件，决定后续走哪条执行路径。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from app.graph.state import GraphState


# 定义函数 route_after_guardrails，负责决定流程在当前节点之后走向哪条分支。
def route_after_guardrails(state: GraphState) -> str:
    """
    作用：执行route_after_guardrails对应的业务逻辑。
    参数：state。
    返回：函数执行后的结果。
    """
    return "persist_memory" if state.get("rejected") else "react_agent"


# 定义函数 route_after_react_agent，负责决定 ReAct 模型节点之后继续调工具还是结束。
def route_after_react_agent(state: GraphState) -> str:
    """
    作用：执行route_after_react_agent对应的业务逻辑。
    参数：state。
    返回：下一节点名称。
    """
    if state.get("final_answer"):
        return "persist_memory"

    messages = state.get("react_messages") or []
    if not messages:
        return "persist_memory"

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []
    return "react_tool_executor" if tool_calls else "persist_memory"
