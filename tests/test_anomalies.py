"""
文件作用：
- 验证异常检测逻辑是否覆盖预期类型。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.logic.tools import SalesTools


@dataclass
# 定义类 FakeRegion，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeRegion:
    id: int
    name: str


@dataclass
# 定义类 FakeProduct，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeProduct:
    id: int
    name: str
    sku_code: str


@dataclass
# 定义类 FakeRep，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeRep:
    id: int
    name: str


# 定义类 FakeAnomalyService，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeAnomalyService:
    def regions(self):
        """
        作用：执行regions对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return [FakeRegion(id=1, name="华东区")]

    def query_order_count(self, region_id, start, end):
        """
        作用：执行query_order_count对应的业务逻辑。
        参数：region_id、start、end。
        返回：函数执行后的结果。
        """
        if start >= date.today() - timedelta(weeks=2):
            return 1
        return 10

    def active_products(self):
        """
        作用：执行active_products对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return [FakeProduct(id=1, name="智能音箱", sku_code="SKU-2001")]

    def query_last_order_date(self, product_id):
        """
        作用：执行query_last_order_date对应的业务逻辑。
        参数：product_id。
        返回：函数执行后的结果。
        """
        return date.today() - timedelta(days=10)

    def query_refund_rates(self, start, end):
        """
        作用：执行query_refund_rates对应的业务逻辑。
        参数：start、end。
        返回：函数执行后的结果。
        """
        return [(1, 2, 4)]

    def get_rep_name(self, rep_id):
        """
        作用：获取rep_name相关数据。
        参数：rep_id。
        返回：函数执行后的结果。
        """
        return "李雷"

    def sales_reps(self):
        """
        作用：执行sales_reps对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return [FakeRep(id=1, name="李雷")]

    def sum_amount_by_rep(self, rep_id, start, end):
        """
        作用：执行sum_amount_by_rep对应的业务逻辑。
        参数：rep_id、start、end。
        返回：函数执行后的结果。
        """
        if start >= date.today() - timedelta(days=30):
            return Decimal("100")
        return Decimal("500")

    @staticmethod
    def calc_growth_rate(current, previous):
        """
        作用：执行calc_growth_rate对应的业务逻辑。
        参数：current、previous。
        返回：函数执行后的结果。
        """
        if previous == 0:
            return None
        return ((current - previous) / previous * Decimal("100")).quantize(Decimal("0.01"))


# 定义函数 test_detect_all_anomalies_contains_expected_types，负责当前文件中的一个关键步骤或对外能力。
def test_detect_all_anomalies_contains_expected_types():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    tools = SalesTools(FakeAnomalyService())

    result = tools.detect_all_anomalies()

    assert "大区订单量骤降" in result
    assert "产品连续零销售" in result
    assert "销售员退单率异常" in result
    assert "销售员业绩骤降" in result
