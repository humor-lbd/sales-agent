"""
文件作用：
- 定义 GraphState 等状态结构，描述一轮 Agent 执行过程中的中间结果。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from typing import Any, TypedDict


# 定义类 GraphState，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class GraphState(TypedDict, total=False):
    session_id: str
    request_text: str
    messages: list[dict[str, Any]]
    react_messages: list[Any]
    summary_context: str | None
    tool_results: dict[str, Any]
    artifacts: list[dict[str, Any]]
    final_answer: str | None
    streamed_final_answer: bool
    error: str | None
    rejected: bool
    tool_call_count: int
    react_round_count: int
