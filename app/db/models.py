"""
文件作用：
- 定义 ORM 模型，把数据库表映射为 Python 对象。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# 定义类 Base，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class Base(DeclarativeBase):
    pass


# 定义类 SalesRegion，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class SalesRegion(Base):
    __tablename__ = "sa_sales_region"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    parent_region_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


# 定义类 SalesRep，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class SalesRep(Base):
    __tablename__ = "sa_sales_rep"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    region_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


# 定义类 Product，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class Product(Base):
    __tablename__ = "sa_product"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sku_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


# 定义类 SalesOrder，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class SalesOrder(Base):
    __tablename__ = "sa_sales_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(50), nullable=False)
    rep_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    region_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


# 定义类 ChatMemory，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class ChatMemory(Base):
    __tablename__ = "sa_chat_memory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    messages: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
