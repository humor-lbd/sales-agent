"""
文件作用：
- 验证服务层的权限规则和增长率等业务细节。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.logic.schemas import UserInfo
from app.logic.services import SalesQueryService


@dataclass
# 定义类 FakeRep，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeRep:
    id: int
    name: str
    region_id: int
    role: str = "SALES_REP"


@dataclass
# 定义类 FakeRegion，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeRegion:
    id: int
    name: str


# 定义类 FakeOrderRepo，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeOrderRepo:
    def __init__(self):
        """
        作用：执行__init__对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        self.last_call = None

    def sum_amount_by_rep(self, rep_id, start, end):
        """
        作用：执行sum_amount_by_rep对应的业务逻辑。
        参数：rep_id、start、end。
        返回：函数执行后的结果。
        """
        self.last_call = ("rep", rep_id, start, end)
        return Decimal("888")

    def sum_amount_by_region(self, region_id, start, end):
        """
        作用：执行sum_amount_by_region对应的业务逻辑。
        参数：region_id、start、end。
        返回：函数执行后的结果。
        """
        self.last_call = ("region", region_id, start, end)
        return Decimal("999")

    def sum_amount_all(self, start, end):
        """
        作用：执行sum_amount_all对应的业务逻辑。
        参数：start、end。
        返回：函数执行后的结果。
        """
        self.last_call = ("all", start, end)
        return Decimal("1111")

    def find_region_ranking(self, start, end):
        """
        作用：执行find_region_ranking对应的业务逻辑。
        参数：start、end。
        返回：函数执行后的结果。
        """
        return [(1, Decimal("1200")), (2, Decimal("800"))]


# 定义类 FakeRepRepo，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeRepRepo:
    def all(self):
        """
        作用：执行all对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return [FakeRep(id=1, name="张伟", region_id=1), FakeRep(id=2, name="李雷", region_id=2)]


# 定义类 FakeRegionRepo，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class FakeRegionRepo:
    def all(self):
        """
        作用：执行all对应的业务逻辑。
        参数：无。
        返回：函数执行后的结果。
        """
        return [FakeRegion(id=1, name="华东区"), FakeRegion(id=2, name="华南区")]


# 定义函数 build_service，负责组装当前步骤需要的对象或参数。
def build_service(current_user: UserInfo | None = None) -> tuple[SalesQueryService, FakeOrderRepo]:
    """
    作用：构建service对象或结构。
    参数：current_user。
    返回：函数执行后的结果。
    """
    order_repo = FakeOrderRepo()
    service = SalesQueryService.__new__(SalesQueryService)
    service.current_user = current_user
    service.redis = None
    service.order_repo = order_repo
    service.rep_repo = FakeRepRepo()
    service.product_repo = None
    service.region_repo = FakeRegionRepo()
    return service, order_repo


# 定义函数 test_sales_rep_total_amount_uses_rep_scope，负责当前文件中的一个关键步骤或对外能力。
def test_sales_rep_total_amount_uses_rep_scope():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    current_user = UserInfo(user_id=1, username="张伟", role="SALES_REP", region_id=1, rep_id=9)
    service, order_repo = build_service(current_user)

    result = service.query_total_amount(region_id=5, start=date(2026, 4, 1), end=date(2026, 4, 30))

    assert result == Decimal("888")
    assert order_repo.last_call[0] == "rep"
    assert order_repo.last_call[1] == 9


# 定义函数 test_sales_manager_region_ranking_is_filtered，负责当前文件中的一个关键步骤或对外能力。
def test_sales_manager_region_ranking_is_filtered():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    current_user = UserInfo(user_id=2, username="经理", role="SALES_MANAGER", region_id=2, rep_id=None)
    service, _ = build_service(current_user)

    result = service.query_region_ranking(date(2026, 4, 1), date(2026, 4, 30))

    assert len(result) == 1
    assert result[0].region_id == 2
    assert result[0].region_name == "华南区"


# 定义函数 test_calc_growth_rate_rounds_half_up，负责当前文件中的一个关键步骤或对外能力。
def test_calc_growth_rate_rounds_half_up():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    growth = SalesQueryService.calc_growth_rate(Decimal("105"), Decimal("100"))

    assert growth == Decimal("5.00")


# 定义函数 test_calc_growth_rate_returns_none_when_previous_is_zero，负责当前文件中的一个关键步骤或对外能力。
def test_calc_growth_rate_returns_none_when_previous_is_zero():
    """
    作用：验证对应功能是否符合预期。
    参数：无。
    返回：函数执行后的结果。
    """
    assert SalesQueryService.calc_growth_rate(Decimal("100"), Decimal("0")) is None
