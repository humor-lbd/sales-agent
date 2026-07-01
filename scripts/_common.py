"""
scripts 目录共享的辅助函数。

消除 smoke_test / perf_probe / stability_probe / regression_compare /
compare_sql_modes_full / benchmark_sql_optimization 中的重复定义。
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def build_headers(token: str | None) -> dict[str, str]:
    """构建带 Bearer token 的请求头。"""
    return {"Authorization": f"Bearer {token}"} if token else {}


def stable_hash(value: Any) -> str:
    """对任意值生成稳定的短 hash（前 12 位 hex）。"""
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str) if not isinstance(value, str) else value
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def compact(text: str, limit: int = 200) -> str:
    """压缩空白并截断到指定长度。"""
    value = re.sub(r"\s+", " ", str(text)).strip()
    return value if len(value) <= limit else value[:limit] + "..."
