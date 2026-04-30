"""
文件作用：
- 将当前请求上下文中的 SalesTools 包装为 LangChain 可调用工具。
- 阅读这个文件时，建议先看工具名称和参数模型，再看 build_react_tools。
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from app.logic.tools import SalesTools


class QuerySalesDataArgs(BaseModel):
    start_date: str = Field(description="开始日期，格式 YYYY-MM-DD")
    end_date: str = Field(description="结束日期，格式 YYYY-MM-DD")
    region_name: str | None = Field(default=None, description="大区名称：华东区/华南区/华北区/西南区")
    rep_name: str | None = Field(default=None, description="销售员姓名")
    limit: int = Field(default=20, description="最多返回订单条数，建议 20 以内")


class SalesSummaryArgs(BaseModel):
    start_date: str = Field(description="开始日期，格式 YYYY-MM-DD")
    end_date: str = Field(description="结束日期，格式 YYYY-MM-DD")
    region_name: str | None = Field(default=None, description="可选大区名称")


class TopRepsArgs(SalesSummaryArgs):
    top_n: int = Field(default=5, description="返回前 N 名销售员，1 到 20")


class RangeArgs(BaseModel):
    start_date: str = Field(description="开始日期，格式 YYYY-MM-DD")
    end_date: str = Field(description="结束日期，格式 YYYY-MM-DD")


class TopProductsArgs(BaseModel):
    start_date: str = Field(description="开始日期，格式 YYYY-MM-DD")
    end_date: str = Field(description="结束日期，格式 YYYY-MM-DD")
    top_n: int = Field(default=10, description="返回前 N 名产品，1 到 20")
    region_name: str | None = Field(default=None, description="可选大区名称")


class MomArgs(BaseModel):
    current_start: str = Field(description="当前周期开始日期，格式 YYYY-MM-DD")
    current_end: str = Field(description="当前周期结束日期，格式 YYYY-MM-DD")
    prev_start: str | None = Field(default=None, description="对比周期开始日期，格式 YYYY-MM-DD；不传则自动推导")
    prev_end: str | None = Field(default=None, description="对比周期结束日期，格式 YYYY-MM-DD；不传则自动推导")
    region_name: str | None = Field(default=None, description="可选大区名称")


class YoyArgs(SalesSummaryArgs):
    pass


class MonthlyTrendArgs(BaseModel):
    months: int = Field(default=6, description="最近 N 个月，1 到 24")
    region_name: str | None = Field(default=None, description="可选大区名称")


class LineChartArgs(MonthlyTrendArgs):
    title: str | None = Field(default=None, description="图表标题")


class BarPieChartArgs(BaseModel):
    dimension: str = Field(description="维度：region/rep/category/product。产品TopN饼图必须使用 product")
    start_date: str = Field(description="开始日期，格式 YYYY-MM-DD")
    end_date: str = Field(description="结束日期，格式 YYYY-MM-DD")
    title: str | None = Field(default=None, description="图表标题")
    top_n: int = Field(default=10, description="dimension 为 product 或 rep 时返回前 N 名，1 到 20")


class EmptyArgs(BaseModel):
    pass


def build_react_tools(tools: SalesTools) -> list[StructuredTool]:
    """
    作用：把 SalesTools 包装成模型可见的 ReAct 工具列表。
    参数：tools。
    返回：LangChain StructuredTool 列表。
    """
    return [
        StructuredTool.from_function(
            func=tools.query_orders,
            name="query_sales_data",
            description="按日期范围、大区、销售员查询销售订单明细；适合回答有哪些订单、订单列表、成交明细。",
            args_schema=QuerySalesDataArgs,
        ),
        StructuredTool.from_function(
            func=tools.get_sales_summary,
            name="get_sales_summary",
            description="计算指定时间范围内的销售额汇总，可按大区过滤。",
            args_schema=SalesSummaryArgs,
        ),
        StructuredTool.from_function(
            func=tools.get_top_reps,
            name="get_top_reps",
            description="查询指定时间范围内销售员业绩排名，可按大区过滤。",
            args_schema=TopRepsArgs,
        ),
        StructuredTool.from_function(
            func=tools.get_region_ranking,
            name="get_region_ranking",
            description="查询指定时间范围内各大区销售额排名和占比。",
            args_schema=RangeArgs,
        ),
        StructuredTool.from_function(
            func=tools.get_top_products,
            name="get_top_products",
            description="查询指定时间范围内产品销售额排名，可按大区过滤。",
            args_schema=TopProductsArgs,
        ),
        StructuredTool.from_function(
            func=tools.calc_month_over_month,
            name="calc_month_over_month",
            description="计算当前周期与上一周期的环比变化。",
            args_schema=MomArgs,
        ),
        StructuredTool.from_function(
            func=tools.calc_year_over_year,
            name="calc_year_over_year",
            description="计算指定时间范围相对去年同期的同比变化。",
            args_schema=YoyArgs,
        ),
        StructuredTool.from_function(
            func=tools.get_monthly_trend,
            name="get_monthly_trend",
            description="查询近 N 个月销售趋势，返回每月销售额和订单数。",
            args_schema=MonthlyTrendArgs,
        ),
        StructuredTool.from_function(
            func=tools.generate_line_chart,
            name="generate_line_chart",
            description="生成销售趋势折线图 artifact；用户要求趋势图、折线图时调用。",
            args_schema=LineChartArgs,
        ),
        StructuredTool.from_function(
            func=tools.generate_bar_chart,
            name="generate_bar_chart",
            description="生成销售对比柱状图 artifact；用户要求排名图、对比图、柱状图时调用。产品TopN柱状图使用 dimension=product。",
            args_schema=BarPieChartArgs,
        ),
        StructuredTool.from_function(
            func=tools.generate_pie_chart,
            name="generate_pie_chart",
            description="生成销售占比饼图 artifact；用户要求占比、结构、饼图、饼状图时调用。最畅销产品TopN饼图必须使用 dimension=product 和对应 top_n，不能用 region。",
            args_schema=BarPieChartArgs,
        ),
        StructuredTool.from_function(
            func=tools.detect_all_anomalies,
            name="detect_sales_anomalies",
            description="检测销售异常和风险，包括大区订单骤降、产品连续零销售、退单率异常、销售员业绩骤降。",
            args_schema=EmptyArgs,
        ),
    ]
