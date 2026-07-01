"""
LLM SQL 可见 schema 与业务口径白名单。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SqlSchemaRegistry:
    """描述 SQL LLM 允许访问的表、字段、关联和指标口径。"""

    version: str = "sales-v1"
    allowed_tables: frozenset[str] = frozenset(
        {
            "sa_sales_order",
            "sa_sales_rep",
            "sa_sales_region",
            "sa_product",
        }
    )
    table_aliases: dict[str, str] = field(
        default_factory=lambda: {
            "o": "sa_sales_order",
            "s": "sa_sales_rep",
            "r": "sa_sales_region",
            "p": "sa_product",
        }
    )
    allowed_columns: dict[str, frozenset[str]] = field(
        default_factory=lambda: {
            "sa_sales_order": frozenset(
                {
                    "id",
                    "order_no",
                    "rep_id",
                    "product_id",
                    "region_id",
                    "customer_name",
                    "quantity",
                    "unit_price",
                    "amount",
                    "cost",
                    "profit",
                    "status",
                    "order_date",
                    "created_at",
                }
            ),
            "sa_sales_rep": frozenset({"id", "name", "region_id", "role", "email", "created_at"}),
            "sa_sales_region": frozenset({"id", "name", "parent_region_id", "created_at"}),
            "sa_product": frozenset({"id", "sku_code", "name", "category", "unit_price", "cost", "status", "created_at"}),
        }
    )
    sales_metric_tasks: frozenset[str] = frozenset(
        {
            "sales_summary",
            "rep_ranking",
            "region_ranking",
            "product_ranking",
            "monthly_trend",
        }
    )
    detail_tasks: frozenset[str] = frozenset({"order_detail"})

    def schema_context(self, task_type: str | None = None, profile: str = "full") -> str:
        """生成给 SQL LLM 使用的 schema 文本。"""
        if (profile or "full").lower() == "compact" and task_type:
            return self._compact_schema_context(task_type)
        lines = [
            "允许表与别名：",
            "- sa_sales_order o(id, order_no, rep_id, product_id, region_id, customer_name, quantity, unit_price, amount, cost, profit, status, order_date, created_at)",
            "- sa_sales_rep s(id, name, region_id, role, email, created_at)",
            "- sa_sales_region r(id, name, parent_region_id, created_at)",
            "- sa_product p(id, sku_code, name, category, unit_price, cost, status, created_at)",
            "",
            "固定关联关系：",
            "- JOIN sa_sales_rep s ON s.id = o.rep_id",
            "- JOIN sa_sales_region r ON r.id = o.region_id",
            "- JOIN sa_product p ON p.id = o.product_id",
        ]
        return "\n".join(lines)

    def metric_context(self, task_type: str | None = None, profile: str = "full") -> str:
        """生成给 SQL LLM 使用的业务口径文本。"""
        if (profile or "full").lower() == "compact" and task_type:
            return self._compact_metric_context(task_type)
        return "\n".join(
            [
                "- 销售额使用 SUM(o.amount)，默认只统计 o.status = 'COMPLETED'。",
                "- 销售数量使用 SUM(o.quantity)，默认只统计 o.status = 'COMPLETED'。",
                "- 订单数默认统计 COMPLETED 订单，退款率任务除外。",
                "- 月份趋势使用 DATE_FORMAT(o.order_date, '%Y-%m') AS month。",
                "- 所有日期范围使用 o.order_date BETWEEN :start_date AND :end_date。",
                "- 明细查询必须 ORDER BY o.order_date DESC, o.id DESC 并带 LIMIT。",
            ]
        )

    def _compact_schema_context(self, task_type: str) -> str:
        if task_type in {"sales_summary", "monthly_trend", "refund_rates", "order_detail"}:
            return "\n".join(
                [
                    "允许表与别名：",
                    "- sa_sales_order o(id, order_no, rep_id, product_id, region_id, customer_name, quantity, amount, status, order_date)",
                    "- sa_sales_rep s(id, name, region_id)",
                    "- sa_sales_region r(id, name)",
                    "- sa_product p(id, sku_code, name, category)",
                    "",
                    "固定关联关系：",
                    "- JOIN sa_sales_rep s ON s.id = o.rep_id",
                    "- JOIN sa_sales_region r ON r.id = o.region_id",
                    "- JOIN sa_product p ON p.id = o.product_id",
                ]
            )
        if task_type in {"rep_ranking", "region_ranking", "product_ranking"}:
            return "\n".join(
                [
                    "允许表与别名：",
                    "- sa_sales_order o(rep_id, product_id, region_id, quantity, amount, status, order_date)",
                    "- sa_sales_rep s(id, name, region_id)",
                    "- sa_sales_region r(id, name)",
                    "- sa_product p(id, sku_code, name, category)",
                    "",
                    "固定关联关系：",
                    "- JOIN sa_sales_rep s ON s.id = o.rep_id",
                    "- JOIN sa_sales_region r ON r.id = o.region_id",
                    "- JOIN sa_product p ON p.id = o.product_id",
                ]
            )
        return self.schema_context()

    def _compact_metric_context(self, task_type: str) -> str:
        task_metrics = {
            "sales_summary": ["- 销售额使用 SUM(o.amount)，必须过滤 o.status = 'COMPLETED'。", "- 日期范围必须使用 o.order_date BETWEEN :start_date AND :end_date。"],
            "monthly_trend": ["- 趋势按 DATE_FORMAT(o.order_date, '%Y-%m') AS month 分组。", "- 销售额使用 SUM(o.amount)，必须过滤 o.status = 'COMPLETED'。"],
            "rep_ranking": ["- 销售员排名按 SUM(o.amount) 聚合并倒序排序。", "- 必须过滤 o.status = 'COMPLETED'。"],
            "region_ranking": ["- 大区排名按 SUM(o.amount) 聚合并倒序排序。", "- 必须过滤 o.status = 'COMPLETED'。"],
            "product_ranking": ["- 产品排名按 SUM(o.amount)、SUM(o.quantity) 聚合并倒序排序。", "- 必须过滤 o.status = 'COMPLETED'。"],
            "order_detail": ["- 明细查询不能默认过滤 COMPLETED。", "- 必须 ORDER BY o.order_date DESC, o.id DESC 并带 LIMIT。"],
            "refund_rates": ["- refunded 使用 SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END)。", "- total 使用 COUNT(o.id)，不要过滤 COMPLETED。"],
        }
        lines = task_metrics.get(task_type)
        if lines:
            return "\n".join(lines)
        return self.metric_context()

    def allows_column(self, alias_or_table: str, column: str) -> bool:
        """判断 alias.column 是否在白名单内。"""
        table = self.table_aliases.get(alias_or_table, alias_or_table)
        return column in self.allowed_columns.get(table, frozenset())
