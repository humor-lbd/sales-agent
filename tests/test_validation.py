"""
文件作用：
- 验证参数校验逻辑，防止非法输入进入业务链路。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

import pytest

from app.logic.validators import clamp_months, validate_dimension, validate_region_name, validate_top_n


# 定义函数 test_validate_region_name_rejects_unknown_region，负责当前文件中的一个关键步骤或对外能力。
def test_validate_region_name_rejects_unknown_region():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    with pytest.raises(ValueError):
        validate_region_name("东北区")


# 定义函数 test_validate_dimension_rejects_unknown_dimension，负责当前文件中的一个关键步骤或对外能力。
def test_validate_dimension_rejects_unknown_dimension():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    with pytest.raises(ValueError):
        validate_dimension("customer")


def test_validate_dimension_accepts_product_dimension():
    """
    作用：验证产品维度可用于产品TopN图表。
    参数：无。
    返回：无。
    """
    assert validate_dimension("product") == "product"


# 定义函数 test_validate_top_n_clamps_into_range，负责当前文件中的一个关键步骤或对外能力。
def test_validate_top_n_clamps_into_range():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    assert validate_top_n(99) == 20
    assert validate_top_n(-3) == 3


def test_clamp_months_limits_to_supported_range():
    """
    作用：验证趋势月份范围会被限制到 1-24。
    参数：无。
    返回：无。
    """
    assert clamp_months(0) == 1
    assert clamp_months(99) == 24
