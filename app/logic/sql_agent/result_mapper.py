"""
LLM SQL 查询结果映射。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from app.logic.schemas import MonthlyTrendDTO, ProductSalesDTO, RegionSalesDTO, RepSalesDTO


def to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def to_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def to_date(value: Any):
    if isinstance(value, (date, datetime)):
        return value.date() if isinstance(value, datetime) else value
    return value


def map_order_rows(rows: list[dict[str, Any]]) -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            id=row.get("id"),
            order_no=row.get("order_no"),
            order_date=to_date(row.get("order_date")),
            rep_id=to_int(row.get("rep_id")),
            product_id=to_int(row.get("product_id")),
            region_id=to_int(row.get("region_id")),
            customer_name=row.get("customer_name") or "",
            amount=to_decimal(row.get("amount")),
            status=row.get("status") or "",
        )
        for row in rows
    ]


def map_region_rows(rows: list[dict[str, Any]]) -> list[RegionSalesDTO]:
    return [
        RegionSalesDTO(
            region_id=to_int(row.get("region_id")),
            region_name=str(row.get("region_name") or "未知"),
            total_amount=to_decimal(row.get("total_amount")),
            order_count=to_int(row.get("order_count")),
            total_profit=to_decimal(row.get("total_profit")),
        )
        for row in rows
    ]


def map_rep_rows(rows: list[dict[str, Any]]) -> list[RepSalesDTO]:
    return [
        RepSalesDTO(
            rep_id=to_int(row.get("rep_id")),
            rep_name=str(row.get("rep_name") or "未知销售员"),
            region_id=to_int(row.get("region_id")),
            region_name=str(row.get("region_name") or "未知"),
            total_amount=to_decimal(row.get("total_amount")),
            order_count=to_int(row.get("order_count")),
        )
        for row in rows
    ]


def map_product_rows(rows: list[dict[str, Any]]) -> list[ProductSalesDTO]:
    return [
        ProductSalesDTO(
            product_id=to_int(row.get("product_id")),
            sku_code=str(row.get("sku_code") or ""),
            product_name=str(row.get("product_name") or "未知产品"),
            category=str(row.get("category") or "未知"),
            total_amount=to_decimal(row.get("total_amount")),
            total_quantity=to_int(row.get("total_quantity")),
        )
        for row in rows
    ]


def map_monthly_trend_rows(rows: list[dict[str, Any]]) -> list[MonthlyTrendDTO]:
    return [
        MonthlyTrendDTO(
            month=str(row.get("month") or ""),
            total_amount=to_decimal(row.get("total_amount")),
            order_count=to_int(row.get("order_count")),
        )
        for row in rows
    ]
