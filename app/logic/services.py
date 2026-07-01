"""
业务逻辑服务模块

该模块承接业务规则、权限过滤、缓存和多种销售分析查询逻辑。
主要包含以下服务类：
- SalesQueryService：销售数据查询服务，提供各种销售数据的查询和分析功能
- MemoryService：聊天记忆服务，管理用户聊天会话的记忆

每个服务类负责对应领域的业务逻辑处理。
"""

from __future__ import annotations

import logging
import json
import time
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import runtime_metrics
from app.db.repositories import (
    ChatMemoryRepository,
    ProductRepository,
    SalesOrderRepository,
    SalesRegionRepository,
    SalesRepRepository,
)
from app.logic.schemas import MonthlyTrendDTO, ProductSalesDTO, RegionSalesDTO, RepSalesDTO, UserInfo
from app.logic.sql_agent import LlmSqlQueryService


ZERO = Decimal("0")
logger = logging.getLogger(__name__)


class SalesQueryService:
    """
    销售数据查询服务
    
    提供各种销售数据的查询和分析功能，支持权限控制和缓存优化。
    主要功能包括：订单查询、销售额统计、销售排名、趋势分析等。
    """
    def __init__(self, db: Session, current_user: UserInfo | None = None, redis_client: Redis | None = None) -> None:
        """
        初始化销售查询服务
        
        Args:
            db: 数据库会话对象
            current_user: 当前用户信息，用于权限控制
            redis_client: Redis客户端，用于缓存
        """
        self.current_user = current_user
        self.redis = redis_client
        self.settings = get_settings()
        self.order_repo = SalesOrderRepository(db)
        self.rep_repo = SalesRepRepository(db)
        self.product_repo = ProductRepository(db)
        self.region_repo = SalesRegionRepository(db)
        self.llm_sql = LlmSqlQueryService(
            db=db,
            current_user=current_user,
            redis_client=redis_client,
            settings=self.settings,
        )

    def _runtime_settings(self):
        """
        读取运行配置。测试中通过 __new__ 构造服务时可能没有 settings 属性。
        """
        settings = getattr(self, "settings", None)
        if settings is None:
            settings = get_settings()
            try:
                self.settings = settings
            except Exception:
                pass
        return settings

    def _llm_sql_allowed_for(self, operation_name: str) -> bool:
        """
        判断当前操作是否允许走 LLM SQL。
        """
        settings = self._runtime_settings()
        allowed = getattr(settings, "llm_sql_allowed_operation_set", set())
        if not allowed:
            return True
        return operation_name in allowed

    def _maybe_llm_sql(self, operation_name, operation, fallback):
        """
        根据配置决定是否使用LLM SQL结果，并在失败时回退确定性查询。
        """
        settings = self._runtime_settings()
        llm_sql = getattr(self, "llm_sql", None)
        if not getattr(settings, "llm_sql_enabled", False) or llm_sql is None:
            return fallback()
        if not self._llm_sql_allowed_for(operation_name):
            return fallback()

        if getattr(settings, "llm_sql_shadow_mode", True):
            result = fallback()
            try:
                operation(llm_sql)
            except Exception:
                runtime_metrics.record_llm_sql_fallback()
                logger.warning("LLM SQL影子查询失败，已忽略", exc_info=True)
            return result

        try:
            return operation(llm_sql)
        except Exception:
            runtime_metrics.record_llm_sql_fallback()
            logger.warning("LLM SQL查询失败", exc_info=True)
            if getattr(settings, "llm_sql_use_fallback", True):
                return fallback()
            raise

    def _cache_get(self, key: str):
        """
        从缓存中获取数据
        
        Args:
            key: 缓存键
        
        Returns:
            缓存的数据，如果不存在则返回None
        """
        if not self.redis:
            return None
        started = time.perf_counter()
        payload = self.redis.get(key)
        duration_ms = (time.perf_counter() - started) * 1000
        if payload is None:
            runtime_metrics.record_cache_get(False, duration_ms)
            return None
        runtime_metrics.record_cache_get(True, duration_ms)
        return json.loads(payload)

    def _cache_set(self, key: str, value, ttl_seconds: int) -> None:
        """
        将数据存入缓存
        
        Args:
            key: 缓存键
            value: 要缓存的值
            ttl_seconds: 缓存过期时间（秒）
        """
        if not self.redis:
            return
        started = time.perf_counter()
        self.redis.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
        runtime_metrics.record_cache_set((time.perf_counter() - started) * 1000)

    def query_orders(self, rep_id: int | None, region_id: int | None, start: date, end: date):
        """
        查询销售订单
        
        Args:
            rep_id: 销售代表ID（可选）
            region_id: 区域ID（可选）
            start: 开始日期
            end: 结束日期
        
        Returns:
            符合条件的销售订单列表
        """
        if self.current_user:
            if self.current_user.role == "SALES_REP":
                rep_id = self.current_user.rep_id
                region_id = None
            elif self.current_user.role == "SALES_MANAGER":
                region_id = self.current_user.region_id
                rep_id = None
        return self._maybe_llm_sql(
            "query_orders",
            lambda llm_sql: llm_sql.query_orders(rep_id, region_id, start, end),
            lambda: self.order_repo.query_orders(rep_id, region_id, start, end),
        )

    def query_total_amount(self, region_id: int | None, start: date, end: date) -> Decimal:
        """
        查询总销售额
        
        Args:
            region_id: 区域ID（可选）
            start: 开始日期
            end: 结束日期
        
        Returns:
            总销售额
        """
        rep_id = None
        if self.current_user:
            if self.current_user.role == "SALES_REP" and self.current_user.rep_id is not None:
                rep_id = self.current_user.rep_id
                region_id = None
            if self.current_user.role == "SALES_MANAGER":
                region_id = self.current_user.region_id

        key_scope = f"rep:{rep_id}" if rep_id is not None else f"region:{region_id}" if region_id is not None else "all"
        cache_key = f"total-amount:{key_scope}:{start}:{end}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return Decimal(cached)

        def fallback():
            if rep_id is not None:
                return self.order_repo.sum_amount_by_rep(rep_id, start, end)
            if region_id is not None:
                return self.order_repo.sum_amount_by_region(region_id, start, end)
            return self.order_repo.sum_amount_all(start, end)

        result = self._maybe_llm_sql(
            "query_total_amount",
            lambda llm_sql: llm_sql.query_total_amount(region_id, start, end),
            fallback,
        )

        self._cache_set(cache_key, str(result), 300)
        return result

    def query_rep_ranking(self, start: date, end: date, top_n: int) -> list[RepSalesDTO]:
        """
        查询销售代表排名
        
        Args:
            start: 开始日期
            end: 结束日期
            top_n: 返回前N名
        
        Returns:
            销售代表排名列表
        """
        def fallback():
            cache_key = f"rep-ranking:{start}:{end}:{top_n}"
            cached_rows = self._cache_get(cache_key)
            if cached_rows is None:
                raw_rows = self.order_repo.find_rep_ranking(start, end)
                cached_rows = [{"rep_id": rep_id, "total_amount": str(total)} for rep_id, total in raw_rows]
                self._cache_set(cache_key, cached_rows, 300)

            rep_map = {rep.id: rep for rep in self.rep_repo.all()}
            region_map = {region.id: region.name for region in self.region_repo.all()}
            ranking: list[RepSalesDTO] = []
            for row in cached_rows:
                rep_id = int(row["rep_id"])
                total = Decimal(row["total_amount"])
                rep = rep_map.get(rep_id)
                if rep is None:
                    continue
                if self.current_user and self.current_user.role == "SALES_MANAGER" and rep.region_id != self.current_user.region_id:
                    continue
                if self.current_user and self.current_user.role == "SALES_REP" and rep_id != self.current_user.rep_id:
                    continue
                ranking.append(
                    RepSalesDTO(
                        rep_id=rep.id,
                        rep_name=rep.name,
                        region_id=rep.region_id,
                        region_name=region_map.get(rep.region_id, "未知"),
                        total_amount=total,
                    )
                )
                if len(ranking) >= top_n:
                    break
            return ranking

        return self._maybe_llm_sql(
            "query_rep_ranking",
            lambda llm_sql: llm_sql.query_rep_ranking(start, end, top_n),
            fallback,
        )

    def query_region_ranking(self, start: date, end: date) -> list[RegionSalesDTO]:
        """
        查询区域销售排名
        
        Args:
            start: 开始日期
            end: 结束日期
        
        Returns:
            区域销售排名列表
        """
        def fallback():
            cache_key = f"region-ranking:{start}:{end}"
            cached_rows = self._cache_get(cache_key)
            if cached_rows is None:
                raw_rows = self.order_repo.find_region_ranking(start, end)
                cached_rows = [{"region_id": region_id, "total_amount": str(total)} for region_id, total in raw_rows]
                self._cache_set(cache_key, cached_rows, 300)

            region_map = {region.id: region.name for region in self.region_repo.all()}
            result = [
                RegionSalesDTO(
                    region_id=int(row["region_id"]),
                    region_name=region_map.get(int(row["region_id"]), "未知"),
                    total_amount=Decimal(row["total_amount"]),
                )
                for row in cached_rows
            ]
            if self.current_user and self.current_user.role == "SALES_MANAGER":
                result = [item for item in result if item.region_id == self.current_user.region_id]
            if self.current_user and self.current_user.role == "SALES_REP":
                result = []
            return result

        if self.current_user and self.current_user.role == "SALES_REP":
            return fallback()

        return self._maybe_llm_sql(
            "query_region_ranking",
            lambda llm_sql: llm_sql.query_region_ranking(start, end),
            fallback,
        )

    def query_product_ranking(self, start: date, end: date, top_n: int, region_id: int | None = None) -> list[ProductSalesDTO]:
        """
        查询产品销售排名
        
        Args:
            start: 开始日期
            end: 结束日期
            top_n: 返回前N名
            region_id: 区域ID（可选）
        
        Returns:
            产品销售排名列表
        """
        if self.current_user and self.current_user.role == "SALES_MANAGER":
            region_id = self.current_user.region_id
        if self.current_user and self.current_user.role == "SALES_REP":
            region_id = self.current_user.region_id

        def fallback():
            product_map = {product.id: product for product in self.product_repo.all()}
            result: list[ProductSalesDTO] = []
            for product_id, total, qty in self.order_repo.find_product_ranking(start, end, region_id):
                product = product_map.get(product_id)
                if product is None:
                    continue
                result.append(
                    ProductSalesDTO(
                        product_id=product.id,
                        sku_code=product.sku_code,
                        product_name=product.name,
                        category=product.category,
                        total_amount=total,
                        total_quantity=qty,
                    )
                )
                if len(result) >= top_n:
                    break
            return result

        return self._maybe_llm_sql(
            "query_product_ranking",
            lambda llm_sql: llm_sql.query_product_ranking(start, end, top_n, region_id),
            fallback,
        )

    def query_monthly_trend(self, region_id: int | None, months: int) -> list[MonthlyTrendDTO]:
        """
        查询月度销售趋势
        
        Args:
            region_id: 区域ID（可选）
            months: 查询月数
        
        Returns:
            月度销售趋势列表
        """
        if self.current_user and self.current_user.role == "SALES_MANAGER":
            region_id = self.current_user.region_id
        if self.current_user and self.current_user.role == "SALES_REP":
            region_id = self.current_user.region_id
        end = date.today()
        month_count = max(months, 1)
        start = self._months_ago_start(end, month_count)

        def fallback():
            cache_key = f"monthly-trend:{region_id if region_id is not None else 'all'}:{months}"
            cached_rows = self._cache_get(cache_key)
            if cached_rows is None:
                rows = self.order_repo.find_monthly_trend(region_id, start, end)
                cached_rows = [{"month": month, "total_amount": str(total), "order_count": count} for month, total, count in rows]
                self._cache_set(cache_key, cached_rows, 300)
            return [
                MonthlyTrendDTO(month=row["month"], total_amount=Decimal(row["total_amount"]), order_count=int(row["order_count"]))
                for row in cached_rows
            ]

        return self._maybe_llm_sql(
            "query_monthly_trend",
            lambda llm_sql: llm_sql.query_monthly_trend(region_id, start, end, month_count),
            fallback,
        )

    @staticmethod
    def _months_ago_start(end: date, months: int) -> date:
        """
        计算几个月前的开始日期
        
        Args:
            end: 结束日期
            months: 月数
        
        Returns:
            几个月前的开始日期（当月1号）
        """
        total_months = end.year * 12 + (end.month - 1) - months
        year = total_months // 12
        month = total_months % 12 + 1
        return date(year, month, 1)

    @staticmethod
    def calc_growth_rate(current: Decimal, previous: Decimal | None) -> Decimal | None:
        """
        计算增长率
        
        Args:
            current: 当前值
            previous:  previous值
        
        Returns:
            增长率（百分比），如果previous为None或0则返回None
        """
        if previous is None or previous == ZERO:
            return None
        return ((current - previous) / previous * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def query_refund_rates(self, start: date, end: date):
        """
        查询销售代表的退款率
        
        Args:
            start: 开始日期
            end: 结束日期
        
        Returns:
            销售代表退款率列表
        """
        return self._maybe_llm_sql(
            "query_refund_rates",
            lambda llm_sql: llm_sql.query_refund_rates(start, end),
            lambda: self.order_repo.find_refund_rate_by_rep(start, end),
        )

    def query_order_count_map(self, start: date, end: date) -> dict[int, int]:
        """
        批量查询各区域订单数。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            {区域ID: 订单数}
        """
        return self.order_repo.count_completed_by_region_map(start, end)

    def query_last_order_date_map(self) -> dict[int, date]:
        """
        批量查询产品最后出单日期。

        Returns:
            {产品ID: 最后出单日期}
        """
        return self.order_repo.find_last_order_date_by_product_map()

    def sum_amount_by_rep_map(self, start: date, end: date) -> dict[int, Decimal]:
        """
        批量统计销售代表销售额。

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            {销售代表ID: 销售额}
        """
        return self.order_repo.sum_amount_by_rep_map(start, end)

    def get_rep_name(self, rep_id: int) -> str:
        """
        获取销售代表名称
        
        Args:
            rep_id: 销售代表ID
        
        Returns:
            销售代表名称，未找到则返回"未知销售员"
        """
        rep = self.rep_repo.find_by_id(rep_id)
        return rep.name if rep else "未知销售员"

    def get_region_name(self, region_id: int) -> str:
        """
        获取区域名称
        
        Args:
            region_id: 区域ID
        
        Returns:
            区域名称，未找到则返回"未知大区"
        """
        region = self.region_repo.find_by_id(region_id)
        return region.name if region else "未知大区"

    def get_region_id_by_name(self, region_name: str | None) -> int | None:
        """
        根据区域名称获取区域ID
        
        Args:
            region_name: 区域名称
        
        Returns:
            区域ID，未找到则返回None
        """
        if not region_name:
            return None
        cache_key = f"region-meta:{region_name}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return None if cached == "__missing__" else int(cached)
        region = self.region_repo.find_by_name(region_name)
        region_id = region.id if region else None
        self._cache_set(cache_key, "__missing__" if region_id is None else region_id, 1800)
        return region_id

    def get_rep_id_by_name(self, rep_name: str | None) -> int | None:
        """
        根据销售代表名称获取销售代表ID
        
        Args:
            rep_name: 销售代表名称
        
        Returns:
            销售代表ID，未找到则返回None
        """
        if not rep_name:
            return None
        rep = self.rep_repo.find_by_name(rep_name)
        return rep.id if rep else None

    def active_products(self):
        """
        获取活跃产品列表
        
        Returns:
            活跃产品列表
        """
        return self.product_repo.find_by_status("ACTIVE")

    def sales_reps(self):
        """
        获取销售代表列表
        
        Returns:
            销售代表列表
        """
        return self.rep_repo.find_by_role("SALES_REP")

    def regions(self):
        """
        获取所有区域列表
        
        Returns:
            区域列表
        """
        return self.region_repo.all()


class MemoryService:
    """
    聊天记忆服务
    
    管理用户聊天会话的记忆，包括获取、保存和清除聊天消息。
    """
    def __init__(self, db: Session) -> None:
        """
        初始化聊天记忆服务
        
        Args:
            db: 数据库会话对象
        """
        self.repo = ChatMemoryRepository(db)

    def get_messages(self, session_id: str) -> list[dict]:
        """
        获取指定会话的聊天消息
        
        Args:
            session_id: 会话ID
        
        Returns:
            聊天消息列表，未找到则返回空列表
        """
        try:
            return self.repo.get_messages(session_id)
        except Exception:
            logger.warning("读取会话记忆失败，session_id=%s", session_id, exc_info=True)
            return []

    def save_messages(self, session_id: str, messages: list[dict]) -> None:
        """
        保存聊天消息
        
        Args:
            session_id: 会话ID
            messages: 聊天消息列表
        """
        try:
            self.repo.save_messages(session_id, messages)
        except Exception:
            logger.error("保存会话记忆失败，session_id=%s", session_id, exc_info=True)

    def clear_session(self, session_id: str) -> None:
        """
        清除会话记忆
        
        Args:
            session_id: 会话ID
        """
        try:
            self.repo.delete_messages(session_id)
        except Exception:
            logger.error("清理会话记忆失败，session_id=%s", session_id, exc_info=True)
