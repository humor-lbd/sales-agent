"""
文件作用：
- 集中管理 ReAct 调试轨迹打印，方便观察每轮模型输出和工具调用。
- 阅读这个文件时，建议先看 trace_event，再看格式化辅助函数。
"""

from __future__ import annotations

import json
import sys
from typing import Any


def trace_enabled(settings: Any) -> bool:
    """
    作用：判断当前是否启用 Agent 调试轨迹。
    参数：settings。
    返回：是否打印轨迹。
    """
    return bool(getattr(settings, "agent_trace_enabled", True))


def compact_text(value: Any, limit: int = 800) -> str:
    """
    作用：把任意值压缩成适合控制台查看的一行文本。
    参数：value、limit。
    返回：压缩后的文本。
    """
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            text = str(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def trace_event(settings: Any, title: str, payload: Any | None = None) -> None:
    """
    作用：打印统一格式的 Agent 轨迹。
    参数：settings、title、payload。
    返回：无。
    """
    if not trace_enabled(settings):
        return
    if payload is None:
        print(_console_text(f"[agent-trace] {title}"), flush=True)
        return
    print(_console_text(f"[agent-trace] {title}: {compact_text(payload)}"), flush=True)


def _console_text(text: str) -> str:
    """
    作用：把文本转换成当前控制台可安全输出的编码范围。
    参数：text。
    返回：可打印文本。
    """
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
