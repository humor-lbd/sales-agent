"""
文件作用：
- 组装 LangGraph 工作流，定义各节点的连接顺序和执行入口。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.context import AgentContext
from app.graph.nodes.bootstrap import bootstrap_node
from app.graph.nodes.guardrails import guardrails_node
from app.graph.nodes.memory import load_memory_node, persist_memory_node
from app.graph.nodes.react_agent import react_agent_node
from app.graph.nodes.react_tool_executor import react_tool_executor_node
from app.graph.router import route_after_guardrails, route_after_react_agent
from app.graph.state import GraphState


# 定义函数 _build_graph，负责组装当前步骤需要的对象或参数。
def _build_graph(include_persist: bool):
    """
    作用：执行_build_graph对应的业务逻辑。
    参数：include_persist。
    返回：函数执行后的结果。
    """
    builder = StateGraph(GraphState, context_schema=AgentContext)
    builder.add_node("bootstrap", bootstrap_node)
    builder.add_node("load_memory", load_memory_node)
    builder.add_node("guardrails", guardrails_node)
    builder.add_node("react_agent", react_agent_node)
    builder.add_node("react_tool_executor", react_tool_executor_node)
    if include_persist:
        builder.add_node("persist_memory", persist_memory_node)

    builder.add_edge(START, "bootstrap")
    builder.add_edge("bootstrap", "load_memory")
    builder.add_edge("load_memory", "guardrails")
    terminal = "persist_memory" if include_persist else END
    if include_persist:
        builder.add_conditional_edges("guardrails", route_after_guardrails, {"react_agent": "react_agent", "persist_memory": "persist_memory"})
    else:
        builder.add_conditional_edges("guardrails", route_after_guardrails, {"react_agent": "react_agent", "persist_memory": END})
    builder.add_conditional_edges(
        "react_agent",
        route_after_react_agent,
        {"react_tool_executor": "react_tool_executor", "persist_memory": terminal},
    )
    builder.add_edge("react_tool_executor", "react_agent")
    if include_persist:
        builder.add_edge("persist_memory", END)

    return builder.compile()


# 定义函数 get_sales_graph，负责读取或返回当前上下文需要的数据。
@lru_cache(maxsize=1)
def get_sales_graph():
    """
    作用：获取sales_graph相关数据。
    参数：无。
    返回：函数执行后的结果。
    """
    return _build_graph(include_persist=True)


# 定义函数 get_sales_stream_graph，负责读取或返回当前上下文需要的数据。
@lru_cache(maxsize=1)
def get_sales_stream_graph():
    """
    作用：获取sales_stream_graph相关数据。
    参数：无。
    返回：函数执行后的结果。
    """
    return _build_graph(include_persist=False)
