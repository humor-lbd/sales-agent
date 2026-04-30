"""
文件作用：
- 在每轮图执行开始时初始化状态，补齐后续节点需要的默认值。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from app.graph.state import GraphState


# 定义函数 bootstrap_node，负责当前文件中的一个关键步骤或对外能力。
def bootstrap_node(state: GraphState) -> GraphState:
    """
    作用：执行bootstrap_node对应的业务逻辑。
    参数：state。
    返回：函数执行后的结果。
    """
    return {
        "session_id": state["session_id"],
        "request_text": state["request_text"],
        "messages": [],
        "react_messages": [],
        "summary_context": None,
        "tool_results": {},
        "artifacts": [],
        "final_answer": None,
        "streamed_final_answer": False,
        "error": None,
        "rejected": False,
        "tool_call_count": 0,
        "react_round_count": 0,
    }
