"""
文件作用：
- 集中维护工具层复用的输入校验和归一化逻辑。
- 阅读这个文件时，建议先看常量，再看各个 validate/clamp 函数。
"""

from __future__ import annotations

from datetime import date


VALID_REGIONS = {"华东区", "华南区", "华北区", "西南区"}
VALID_DIMENSIONS = {"region", "rep", "category", "product"}


def parse_date(value: str) -> date:
    """
    作用：把 ISO 日期字符串转换为 date 对象。
    参数：value。
    返回：date。
    """
    return date.fromisoformat(value)


def validate_region_name(region_name: str | None) -> str | None:
    """
    作用：校验大区名称是否合法。
    参数：region_name。
    返回：原样返回合法的大区名称，或 None。
    """
    if not region_name:
        return None
    if region_name not in VALID_REGIONS:
        raise ValueError(f"无效的大区名称：{region_name}，有效值为：{sorted(VALID_REGIONS)}")
    return region_name


def validate_dimension(dimension: str) -> str:
    """
    作用：校验图表或统计维度是否合法。
    参数：dimension。
    返回：合法维度。
    """
    if dimension not in VALID_DIMENSIONS:
        raise ValueError(f"无效的维度：{dimension}，有效值为：region/rep/category/product")
    return dimension


def validate_top_n(top_n: int) -> int:
    """
    作用：把 top_n 归一化到 1-20 范围内。
    参数：top_n。
    返回：归一化后的数量。
    """
    return min(max(abs(top_n), 1), 20)


def clamp_months(months: int, minimum: int = 1, maximum: int = 24) -> int:
    """
    作用：把月份范围限制在允许区间内。
    参数：months、minimum、maximum。
    返回：归一化后的月份数。
    """
    return min(max(int(months), minimum), maximum)
