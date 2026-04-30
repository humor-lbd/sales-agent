"""
文件作用：
- 验证工具层查询、汇总和图表输出的确定性。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from datetime import date
from decimal import Decimal

from app.logic.schemas import MonthlyTrendDTO, ProductSalesDTO, RegionSalesDTO, RepSalesDTO
from app.logic.tools import SalesTools


# 定义类 FakeService，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeService:
    def get_region_id_by_name(self, region_name):
        """
        作用：获取region_id_by_name相关数据。
        参数：region_name。
        返回：函数执行后的结果。
        """
        return 1 if region_name == "华东区" else None

    def get_rep_id_by_name(self, rep_name):
        """
        作用：获取rep_id_by_name相关数据。
        参数：rep_name。
        返回：函数执行后的结果。
        """
        return 2 if rep_name == "张伟" else None

    def query_orders(self, rep_id, region_id, start, end):
        """
        作用：执行query_orders对应的业务逻辑。
        参数：rep_id、region_id、start、end。
        返回：函数执行后的结果。
        """
        class Order:
            order_no = "ORD-001"
            order_date = date(2026, 4, 1)
            rep_id = 2
            customer_name = "测试客户"
            amount = Decimal("1000")
            status = "COMPLETED"

        return [Order()]

    def get_rep_name(self, rep_id):
        """
        作用：获取rep_name相关数据。
        参数：rep_id。
        返回：函数执行后的结果。
        """
        return "张伟"

    def query_rep_ranking(self, start, end, top_n):
        """
        作用：执行query_rep_ranking对应的业务逻辑。
        参数：start、end、top_n。
        返回：函数执行后的结果。
        """
        return [RepSalesDTO(rep_id=2, rep_name="张伟", region_id=1, region_name="华东区", total_amount=Decimal("1000"))]

    def query_region_ranking(self, start, end):
        """
        作用：执行query_region_ranking对应的业务逻辑。
        参数：start、end。
        返回：函数执行后的结果。
        """
        return [RegionSalesDTO(region_id=1, region_name="华东区", total_amount=Decimal("1000"))]

    def query_product_ranking(self, start, end, top_n, region_id=None):
        """
        作用：执行query_product_ranking对应的业务逻辑。
        参数：start、end、top_n、region_id。
        返回：函数执行后的结果。
        """
        if region_id == 1:
            return [
                ProductSalesDTO(
                    product_id=1,
                    sku_code="SKU-1001",
                    product_name="测试产品",
                    category="数码产品",
                    total_amount=Decimal("1000"),
                    total_quantity=2,
                )
            ]
        return [
            ProductSalesDTO(
                product_id=2,
                sku_code="SKU-1002",
                product_name="公共产品",
                category="家电",
                total_amount=Decimal("900"),
                total_quantity=1,
            ),
            ProductSalesDTO(
                product_id=3,
                sku_code="SKU-1003",
                product_name="第二产品",
                category="数码产品",
                total_amount=Decimal("800"),
                total_quantity=2,
            ),
        ]

    def query_total_amount(self, region_id, start, end):
        """
        作用：执行query_total_amount对应的业务逻辑。
        参数：region_id、start、end。
        返回：函数执行后的结果。
        """
        return Decimal("1000")

    def calc_growth_rate(self, current, previous):
        """
        作用：执行calc_growth_rate对应的业务逻辑。
        参数：current、previous。
        返回：函数执行后的结果。
        """
        if previous == 0:
            return None
        return Decimal("25.0")

    def query_monthly_trend(self, region_id, months):
        """
        作用：执行query_monthly_trend对应的业务逻辑。
        参数：region_id、months。
        返回：函数执行后的结果。
        """
        return [
            MonthlyTrendDTO(month="2026-03", total_amount=Decimal("800"), order_count=2),
            MonthlyTrendDTO(month="2026-04", total_amount=Decimal("1000"), order_count=3),
        ]

    def active_products(self):
        """
        作用：执行active_products对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return []

    def query_last_order_date(self, product_id):
        """
        作用：执行query_last_order_date对应的业务逻辑。
        参数：product_id。
        返回：函数执行后的结果。
        """
        return None

    def query_refund_rates(self, start, end):
        """
        作用：执行query_refund_rates对应的业务逻辑。
        参数：start、end。
        返回：函数执行后的结果。
        """
        return []

    def sales_reps(self):
        """
        作用：执行sales_reps对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return []

    def sum_amount_by_rep(self, rep_id, start, end):
        """
        作用：执行sum_amount_by_rep对应的业务逻辑。
        参数：rep_id、start、end。
        返回：函数执行后的结果。
        """
        return Decimal("0")

    def regions(self):
        """
        作用：执行regions对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return []


# 定义函数 test_sales_summary，负责当前文件中的一个关键步骤或对外能力。
def test_sales_summary():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    tools = SalesTools(FakeService())
    result = tools.get_sales_summary("2026-04-01", "2026-04-30", "华东区")
    assert "总销售额：¥1,000" in result


# 定义函数 test_line_chart_returns_artifact，负责当前文件中的一个关键步骤或对外能力。
def test_line_chart_returns_artifact():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    tools = SalesTools(FakeService())
    result = tools.generate_line_chart(2, "华东区", "测试趋势")
    assert result["message"] == "已生成折线图。"
    assert result["artifact"]["kind"] == "echarts"
    assert result["artifact"]["option"]["series"][0]["type"] == "line"


def test_monthly_trend_rejects_unknown_region():
    """
    作用：验证月度趋势工具会先校验大区名称。
    参数：无。
    返回：无。
    """
    tools = SalesTools(FakeService())
    result = tools.get_monthly_trend(6, "东北区")
    assert "无效的大区名称" in result or "东北区" in result


def test_line_chart_rejects_unknown_region():
    """
    作用：验证折线图工具在无效大区时返回稳定提示。
    参数：无。
    返回：无。
    """
    tools = SalesTools(FakeService())
    result = tools.generate_line_chart(6, "东北区", "测试趋势")
    assert result["message"].startswith("无效的大区名称")


# 定义函数 test_query_orders_contains_order_no，负责当前文件中的一个关键步骤或对外能力。
def test_query_orders_contains_order_no():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    tools = SalesTools(FakeService())
    result = tools.query_orders("2026-04-01", "2026-04-30", "华东区", "张伟", 10)
    assert "ORD-001" in result


# 定义函数 test_top_products_respects_region_scope，负责当前文件中的一个关键步骤或对外能力。
def test_top_products_respects_region_scope():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    tools = SalesTools(FakeService())
    result = tools.get_top_products("2026-01-13", "2026-04-13", 10, "华东区")
    assert "华东区" in result
    assert "测试产品" in result


def test_product_pie_chart_uses_product_names():
    """
    作用：验证产品TopN饼图使用产品名称作为扇区，而不是大区或品类。
    参数：无。
    返回：无。
    """
    tools = SalesTools(FakeService())
    result = tools.generate_pie_chart(
        "product",
        "2026-03-24",
        "2026-04-23",
        "最畅销产品Top10销售额占比",
        10,
    )

    data = result["artifact"]["option"]["series"][0]["data"]
    names = {item["name"] for item in data}
    assert "公共产品" in names
    assert "第二产品" in names
    assert "华东区" not in names


def test_product_pie_chart_corrects_conflicting_region_dimension_from_title():
    """
    作用：验证当模型把“产品TopN”误传为 region 时，工具会按标题修正为产品维度。
    参数：无。
    返回：无。
    """
    tools = SalesTools(FakeService())
    result = tools.generate_pie_chart(
        "region",
        "2026-03-24",
        "2026-04-23",
        "最畅销产品Top10销售额占比",
        10,
    )

    data = result["artifact"]["option"]["series"][0]["data"]
    assert data[0]["name"] == "公共产品"
