"""
文件作用：
- 在图执行出错时生成稳定的兜底状态和回复。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from app.graph.state import GraphState


# 定义函数 build_error_state，负责组装当前步骤需要的对象或参数。
def build_error_state(state: GraphState, exc: Exception) -> GraphState:
    """
    作用：构建error_state对象或结构。
    参数：state、exc。
    返回：函数执行后的结果。
    """
    return {
        "error": str(exc),
        "artifacts": [],
        "final_answer": "服务暂时不可用，请稍后重试。",
        "streamed_final_answer": False,
        "rejected": False,
    }
