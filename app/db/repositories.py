"""
数据访问层模块

该模块封装了底层数据库查询细节，为上层业务提供稳定的数据读取接口。
主要包含以下仓库类：
- SalesRegionRepository：销售区域数据仓库
- SalesRepRepository：销售代表数据仓库
- ProductRepository：产品数据仓库
- ChatMemoryRepository：聊天记忆数据仓库
- SalesOrderRepository：销售订单数据仓库

每个仓库类负责对应实体的CRUD操作和特定业务查询。
"""

from __future__ import annotations

import logging
import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models import ChatMemory, Product, SalesOrder, SalesRegion, SalesRep


logger = logging.getLogger(__name__)


class SalesRegionRepository:
    """
    销售区域数据仓库
    
    负责销售区域相关的数据访问操作，如获取所有区域、根据名称或ID查找区域等。
    """
    def __init__(self, db: Session) -> None:
        """
        初始化销售区域仓库
        
        Args:
            db: 数据库会话对象
        """
        self.db = db

    def all(self) -> list[SalesRegion]:
        """
        获取所有销售区域
        
        Returns:
            销售区域列表
        """
        return list(self.db.scalars(select(SalesRegion)).all())

    def find_by_name(self, name: str) -> SalesRegion | None:
        """
        根据名称查找销售区域
        
        Args:
            name: 区域名称
        
        Returns:
            找到的销售区域对象，未找到则返回None
        """
        return self.db.scalar(select(SalesRegion).where(SalesRegion.name == name))

    def find_by_id(self, region_id: int) -> SalesRegion | None:
        """
        根据ID查找销售区域
        
        Args:
            region_id: 区域ID
        
        Returns:
            找到的销售区域对象，未找到则返回None
        """
        return self.db.get(SalesRegion, region_id)


class SalesRepRepository:
    """
    销售代表数据仓库
    
    负责销售代表相关的数据访问操作，如获取所有代表、根据ID/名称/角色查找代表等。
    """
    def __init__(self, db: Session) -> None:
        """
        初始化销售代表仓库
        
        Args:
            db: 数据库会话对象
        """
        self.db = db

    def all(self) -> list[SalesRep]:
        """
        获取所有销售代表
        
        Returns:
            销售代表列表
        """
        return list(self.db.scalars(select(SalesRep)).all())

    def find_by_id(self, rep_id: int) -> SalesRep | None:
        """
        根据ID查找销售代表
        
        Args:
            rep_id: 代表ID
        
        Returns:
            找到的销售代表对象，未找到则返回None
        """
        return self.db.get(SalesRep, rep_id)

    def find_by_name(self, name: str) -> SalesRep | None:
        """
        根据名称查找销售代表
        
        Args:
            name: 代表名称
        
        Returns:
            找到的销售代表对象，未找到则返回None
        """
        return self.db.scalar(select(SalesRep).where(SalesRep.name == name))

    def find_by_role(self, role: str) -> list[SalesRep]:
        """
        根据角色查找销售代表
        
        Args:
            role: 角色名称
        
        Returns:
            符合条件的销售代表列表
        """
        return list(self.db.scalars(select(SalesRep).where(SalesRep.role == role)).all())


class ProductRepository:
    """
    产品数据仓库
    
    负责产品相关的数据访问操作，如获取所有产品、根据状态查找产品等。
    """
    def __init__(self, db: Session) -> None:
        """
        初始化产品仓库
        
        Args:
            db: 数据库会话对象
        """
        self.db = db

    def all(self) -> list[Product]:
        """
        获取所有产品
        
        Returns:
            产品列表
        """
        return list(self.db.scalars(select(Product)).all())

    def find_by_status(self, status: str) -> list[Product]:
        """
        根据状态查找产品
        
        Args:
            status: 产品状态
        
        Returns:
            符合条件的产品列表
        """
        return list(self.db.scalars(select(Product).where(Product.status == status)).all())


class ChatMemoryRepository:
    """
    聊天记忆数据仓库
    
    负责聊天记忆相关的数据访问操作，如获取、保存、删除聊天消息等。
    """
    def __init__(self, db: Session) -> None:
        """
        初始化聊天记忆仓库
        
        Args:
            db: 数据库会话对象
        """
        self.db = db

    def get_messages(self, session_id: str) -> list[dict]:
        """
        获取指定会话的聊天消息
        
        Args:
            session_id: 会话ID
        
        Returns:
            聊天消息列表，未找到则返回空列表
        """
        entity = self.db.scalar(select(ChatMemory).where(ChatMemory.session_id == session_id))
        if not entity:
            return []
        try:
            return json.loads(entity.messages)
        except json.JSONDecodeError:
            logger.warning("反序列化会话记忆失败，session_id=%s", session_id, exc_info=True)
            return []

    def save_messages(self, session_id: str, messages: list[dict]) -> None:
        """
        保存聊天消息
        
        Args:
            session_id: 会话ID
            messages: 聊天消息列表
        """
        entity = self.db.scalar(select(ChatMemory).where(ChatMemory.session_id == session_id))
        payload = json.dumps(messages, ensure_ascii=False)
        if entity is None:
            entity = ChatMemory(session_id=session_id, messages=payload, updated_at=datetime.now())
            self.db.add(entity)
        else:
            entity.messages = payload
            entity.updated_at = datetime.now()
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.error("提交会话记忆失败，session_id=%s", session_id, exc_info=True)
            raise

    def delete_messages(self, session_id: str) -> None:
        """
        删除聊天消息
        
        Args:
            session_id: 会话ID
        """
        entity = self.db.scalar(select(ChatMemory).where(ChatMemory.session_id == session_id))
        if entity:
            self.db.delete(entity)
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.error("删除会话记忆失败，session_id=%s", session_id, exc_info=True)
                raise


class SalesOrderRepository:
    """
    销售订单数据仓库
    
    负责销售订单相关的数据访问操作，如查询订单、统计销售额、获取排名等。
    """
    def __init__(self, db: Session) -> None:
        """
        初始化销售订单仓库
        
        Args:
            db: 数据库会话对象
        """
        self.db = db

    def query_orders(self, rep_id: int | None, region_id: int | None, start: date, end: date) -> list[SalesOrder]:
        """
        查询销售订单
        
        Args:
            rep_id: 销售代表ID（可选）
            region_id: 区域ID（可选）
            start: 开始日期
            end: 结束日期
        
        Returns:
            符合条件的销售订单列表，按订单日期和ID降序排列
        """
        stmt = select(SalesOrder).where(SalesOrder.order_date.between(start, end))
        if rep_id is not None:
            stmt = stmt.where(SalesOrder.rep_id == rep_id)
        elif region_id is not None:
            stmt = stmt.where(SalesOrder.region_id == region_id)
        stmt = stmt.order_by(SalesOrder.order_date.desc(), SalesOrder.id.desc())
        return list(self.db.scalars(stmt).all())

    def sum_amount_by_region(self, region_id: int, start: date, end: date) -> Decimal:
        """
        统计指定区域的销售额
        
        Args:
            region_id: 区域ID
            start: 开始日期
            end: 结束日期
        
        Returns:
            销售额总和
        """
        stmt = select(func.coalesce(func.sum(SalesOrder.amount), 0)).where(
            SalesOrder.region_id == region_id,
            SalesOrder.status == "COMPLETED",
            SalesOrder.order_date.between(start, end),
        )
        return Decimal(str(self.db.scalar(stmt) or 0))

    def sum_amount_by_rep(self, rep_id: int, start: date, end: date) -> Decimal:
        """
        统计指定销售代表的销售额
        
        Args:
            rep_id: 销售代表ID
            start: 开始日期
            end: 结束日期
        
        Returns:
            销售额总和
        """
        stmt = select(func.coalesce(func.sum(SalesOrder.amount), 0)).where(
            SalesOrder.rep_id == rep_id,
            SalesOrder.status == "COMPLETED",
            SalesOrder.order_date.between(start, end),
        )
        return Decimal(str(self.db.scalar(stmt) or 0))

    def sum_amount_all(self, start: date, end: date) -> Decimal:
        """
        统计所有销售额
        
        Args:
            start: 开始日期
            end: 结束日期
        
        Returns:
            销售额总和
        """
        stmt = select(func.coalesce(func.sum(SalesOrder.amount), 0)).where(
            SalesOrder.status == "COMPLETED",
            SalesOrder.order_date.between(start, end),
        )
        return Decimal(str(self.db.scalar(stmt) or 0))

    def find_rep_ranking(self, start: date, end: date) -> list[tuple[int, Decimal]]:
        """
        获取销售代表销售额排名
        
        Args:
            start: 开始日期
            end: 结束日期
        
        Returns:
            (销售代表ID, 销售额)元组列表，按销售额降序排列
        """
        stmt = (
            select(SalesOrder.rep_id, func.sum(SalesOrder.amount).label("total"))
            .where(SalesOrder.status == "COMPLETED", SalesOrder.order_date.between(start, end))
            .group_by(SalesOrder.rep_id)
            .order_by(func.sum(SalesOrder.amount).desc())
        )
        return [(int(rep_id), Decimal(str(total))) for rep_id, total in self.db.execute(stmt).all()]

    def find_region_ranking(self, start: date, end: date) -> list[tuple[int, Decimal]]:
        """
        获取区域销售额排名
        
        Args:
            start: 开始日期
            end: 结束日期
        
        Returns:
            (区域ID, 销售额)元组列表，按销售额降序排列
        """
        stmt = (
            select(SalesOrder.region_id, func.sum(SalesOrder.amount).label("total"))
            .where(SalesOrder.status == "COMPLETED", SalesOrder.order_date.between(start, end))
            .group_by(SalesOrder.region_id)
            .order_by(func.sum(SalesOrder.amount).desc())
        )
        return [(int(region_id), Decimal(str(total))) for region_id, total in self.db.execute(stmt).all()]

    def find_product_ranking(self, start: date, end: date, region_id: int | None = None) -> list[tuple[int, Decimal, int]]:
        """
        获取产品销售额排名
        
        Args:
            start: 开始日期
            end: 结束日期
            region_id: 区域ID（可选）
        
        Returns:
            (产品ID, 销售额, 数量)元组列表，按销售额降序排列
        """
        stmt = (
            select(
                SalesOrder.product_id,
                func.sum(SalesOrder.amount).label("total"),
                func.sum(SalesOrder.quantity).label("qty"),
            )
            .where(SalesOrder.status == "COMPLETED", SalesOrder.order_date.between(start, end))
            .group_by(SalesOrder.product_id)
            .order_by(func.sum(SalesOrder.amount).desc())
        )
        if region_id is not None:
            stmt = stmt.where(SalesOrder.region_id == region_id)
        return [(int(pid), Decimal(str(total)), int(qty)) for pid, total, qty in self.db.execute(stmt).all()]

    def find_monthly_trend(self, region_id: int | None, start: date, end: date) -> list[tuple[str, Decimal, int]]:
        """
        获取月度销售趋势
        
        Args:
            region_id: 区域ID（可选）
            start: 开始日期
            end: 结束日期
        
        Returns:
            (月份, 销售额, 订单数)元组列表，按月份升序排列
        """
        month_expr = func.date_format(SalesOrder.order_date, "%Y-%m")
        stmt = (
            select(
                month_expr.label("month"),
                func.sum(SalesOrder.amount).label("total"),
                func.count(SalesOrder.id).label("order_count"),
            )
            .where(SalesOrder.status == "COMPLETED", SalesOrder.order_date.between(start, end))
            .group_by(month_expr)
            .order_by(month_expr)
        )
        if region_id is not None:
            stmt = stmt.where(SalesOrder.region_id == region_id)
        return [(month, Decimal(str(total)), int(count)) for month, total, count in self.db.execute(stmt).all()]

    def find_last_order_date_by_product(self, product_id: int):
        """
        获取产品的最后订单日期
        
        Args:
            product_id: 产品ID
        
        Returns:
            最后订单日期，未找到则返回None
        """
        stmt = select(func.max(SalesOrder.order_date)).where(
            SalesOrder.product_id == product_id,
            SalesOrder.status == "COMPLETED",
        )
        return self.db.scalar(stmt)

    def find_refund_rate_by_rep(self, start: date, end: date) -> list[tuple[int, int, int]]:
        """
        获取销售代表的退款率
        
        Args:
            start: 开始日期
            end: 结束日期
        
        Returns:
            (销售代表ID, 退款数, 总订单数)元组列表
        """
        refunded_case = case((SalesOrder.status == "REFUNDED", 1), else_=0)
        stmt = (
            select(
                SalesOrder.rep_id,
                func.sum(refunded_case).label("refunded"),
                func.count(SalesOrder.id).label("total"),
            )
            .where(SalesOrder.order_date.between(start, end))
            .group_by(SalesOrder.rep_id)
        )
        return [(int(rep_id), int(refunded), int(total)) for rep_id, refunded, total in self.db.execute(stmt).all()]

    def count_completed_by_region(self, region_id: int, start: date, end: date) -> int:
        """
        统计指定区域的已完成订单数
        
        Args:
            region_id: 区域ID
            start: 开始日期
            end: 结束日期
        
        Returns:
            已完成订单数
        """
        stmt = select(func.count(SalesOrder.id)).where(
            SalesOrder.region_id == region_id,
            SalesOrder.status == "COMPLETED",
            SalesOrder.order_date.between(start, end),
        )
        return int(self.db.scalar(stmt) or 0)
