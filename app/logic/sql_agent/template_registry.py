"""
LLM SQL 模板注册表。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.logic.sql_agent.models import SqlTaskSpec


@dataclass(frozen=True)
class SqlTemplateDefinition:
    """SQL 模板定义。"""

    template_id: str
    sql: str
    result_columns: list[str]


class SqlTemplateRegistry:
    """为高频稳定任务提供受控 SQL 模板。"""

    _templates: dict[str, SqlTemplateDefinition] = {
        "sales_summary": SqlTemplateDefinition(
            template_id="sales_summary_v2",
            sql=(
                "SELECT COALESCE(SUM(o.amount), 0) AS total_amount "
                "FROM sa_sales_order o "
                "WHERE o.status = 'COMPLETED' "
                "AND o.order_date BETWEEN :start_date AND :end_date "
                "AND (:region_id IS NULL OR o.region_id = :region_id)"
            ),
            result_columns=["total_amount"],
        ),
        "monthly_trend": SqlTemplateDefinition(
            template_id="monthly_trend_v2",
            sql=(
                "SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, "
                "SUM(o.amount) AS total_amount, COUNT(o.id) AS order_count "
                "FROM sa_sales_order o "
                "WHERE o.status = 'COMPLETED' "
                "AND o.order_date BETWEEN :start_date AND :end_date "
                "AND (:region_id IS NULL OR o.region_id = :region_id) "
                "GROUP BY month ORDER BY month"
            ),
            result_columns=["month", "total_amount", "order_count"],
        ),
        "refund_rates": SqlTemplateDefinition(
            template_id="refund_rates_v2",
            sql=(
                "SELECT o.rep_id, "
                "SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded, "
                "COUNT(o.id) AS total "
                "FROM sa_sales_order o "
                "WHERE o.order_date BETWEEN :start_date AND :end_date "
                "AND (:region_id IS NULL OR o.region_id = :region_id) "
                "GROUP BY o.rep_id"
            ),
            result_columns=["rep_id", "refunded", "total"],
        ),
        "rep_ranking": SqlTemplateDefinition(
            template_id="rep_ranking_v2",
            sql=(
                "SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, "
                "SUM(o.amount) AS total_amount "
                "FROM sa_sales_order o "
                "JOIN sa_sales_rep s ON s.id = o.rep_id "
                "JOIN sa_sales_region r ON r.id = o.region_id "
                "WHERE o.status = 'COMPLETED' "
                "AND o.order_date BETWEEN :start_date AND :end_date "
                "AND (:region_id IS NULL OR o.region_id = :region_id) "
                "GROUP BY o.rep_id, s.name, s.region_id, r.name "
                "ORDER BY total_amount DESC "
                "LIMIT :top_n"
            ),
            result_columns=["rep_id", "rep_name", "region_id", "region_name", "total_amount"],
        ),
        "region_ranking": SqlTemplateDefinition(
            template_id="region_ranking_v1",
            sql=(
                "SELECT o.region_id, r.name AS region_name, SUM(o.amount) AS total_amount "
                "FROM sa_sales_order o "
                "JOIN sa_sales_region r ON r.id = o.region_id "
                "WHERE o.status = 'COMPLETED' "
                "AND o.order_date BETWEEN :start_date AND :end_date "
                "GROUP BY o.region_id, r.name "
                "ORDER BY total_amount DESC"
            ),
            result_columns=["region_id", "region_name", "total_amount"],
        ),
        "product_ranking": SqlTemplateDefinition(
            template_id="product_ranking_v1",
            sql=(
                "SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, "
                "SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity "
                "FROM sa_sales_order o "
                "JOIN sa_product p ON p.id = o.product_id "
                "WHERE o.status = 'COMPLETED' "
                "AND o.order_date BETWEEN :start_date AND :end_date "
                "AND (:region_id IS NULL OR o.region_id = :region_id) "
                "GROUP BY o.product_id, p.sku_code, p.name, p.category "
                "ORDER BY total_amount DESC "
                "LIMIT :top_n"
            ),
            result_columns=["product_id", "sku_code", "product_name", "category", "total_amount", "total_quantity"],
        ),
    }

    def match(self, task: SqlTaskSpec) -> SqlTemplateDefinition | None:
        return self._templates.get(task.task_type)
