"""
文件作用：
- 提供 ReAct 图运行时复用的模型构造、流式分块和兜底答案函数。
- 阅读这个文件时，建议先看 build_chat_model，再看流式与兜底输出。
"""

from __future__ import annotations

from typing import Iterable

from app.core.llm import build_chat_model  # re-export 保持向后兼容


# 定义函数 stream_text_chunks，负责当前文件中的一个关键步骤或对外能力。
def stream_text_chunks(text: str, chunk_size: int = 12) -> Iterable[str]:
    """
    作用：执行stream_text_chunks对应的业务逻辑。
    参数：text、chunk_size。
    返回：函数执行后的结果。
    """
    if not text:
        return []
    chunks: list[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= chunk_size or char in "，。！？；\n":
            chunks.append(current)
            current = ""
    if current:
        chunks.append(current)
    return chunks


# 定义函数 build_fallback_answer，负责组装当前步骤需要的对象或参数。
def build_fallback_answer(state: dict) -> str:
    """
    作用：构建fallback_answer对象或结构。
    参数：state。
    返回：函数执行后的结果。
    """
    text = (state.get("tool_results") or {}).get("text") or "已完成销售数据分析。"
    artifacts = state.get("artifacts") or []
    if artifacts and "已生成图表" not in text and "请查看下方" not in text:
        text = f"{text}\n\n已生成图表，请查看下方。"
    return text
