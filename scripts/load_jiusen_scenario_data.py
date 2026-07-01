"""
文件作用：
- 加载基于山西玖森百立科技服务有限公司“咪婴伴侣”业务构造的销售场景数据。
- 数据写入 app/db/sql/jiusen_scenario_coverage.sql 中的 SKU-JS / ORD-JS / 9100 段销售员。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.db.bootstrap import _split_sql_statements


SCENARIO_SQL = PROJECT_ROOT / "app" / "db" / "sql" / "jiusen_scenario_coverage.sql"


def build_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=3600)


def pymysql_safe(sql: str) -> str:
    return sql.replace("%", "%%")


def load_sql(engine: Engine, sql_path: Path) -> int:
    statements = _split_sql_statements(sql_path.read_text(encoding="utf-8"))
    if not statements:
        raise RuntimeError(f"SQL 文件为空: {sql_path}")

    with engine.begin() as conn:
        for statement in statements:
            conn.exec_driver_sql(pymysql_safe(statement))
    return len(statements)


def scalar_int(engine: Engine, sql: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(sql)).scalar_one() or 0)


def scalar_text(engine: Engine, sql: str) -> str:
    with engine.connect() as conn:
        value = conn.execute(text(sql)).scalar_one()
        return "" if value is None else str(value)


def fetch_rows(engine: Engine, sql: str) -> list[dict[str, object]]:
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(text(sql)).all()]


def print_rows(title: str, rows: Iterable[dict[str, object]]) -> None:
    print(f"\n{title}")
    for row in rows:
        print("  " + " | ".join(f"{key}={value}" for key, value in row.items()))


def verify_coverage(engine: Engine) -> None:
    scenario_count = scalar_int(engine, "SELECT COUNT(1) FROM sa_sales_order WHERE order_no LIKE 'ORD-JS-%'")
    product_count = scalar_int(engine, "SELECT COUNT(1) FROM sa_product WHERE sku_code LIKE 'SKU-JS-%'")
    rep_count = scalar_int(engine, "SELECT COUNT(1) FROM sa_sales_rep WHERE id BETWEEN 9101 AND 9115")
    current_month_count = scalar_int(
        engine,
        """
        SELECT COUNT(1)
        FROM sa_sales_order
        WHERE order_no LIKE 'ORD-JS-%'
          AND order_date BETWEEN DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH)
                             AND CURDATE()
        """,
    )
    current_month_amount = scalar_text(
        engine,
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM sa_sales_order
        WHERE order_no LIKE 'ORD-JS-%'
          AND status = 'COMPLETED'
          AND order_date BETWEEN DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH)
                             AND CURDATE()
        """,
    )
    yoy_count = scalar_int(
        engine,
        """
        SELECT COUNT(1)
        FROM sa_sales_order
        WHERE order_no LIKE 'ORD-JS-YOY-%'
          AND order_date BETWEEN DATE_SUB(DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH), INTERVAL 1 YEAR)
                             AND DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        """,
    )
    trend_months = scalar_int(
        engine,
        """
        SELECT COUNT(DISTINCT EXTRACT(YEAR_MONTH FROM order_date))
        FROM sa_sales_order
        WHERE order_no LIKE 'ORD-JS-%'
          AND status = 'COMPLETED'
          AND order_date BETWEEN DATE_SUB(DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH), INTERVAL 6 MONTH)
                             AND CURDATE()
        """,
    )

    print("\n玖森百立业务场景数据总览")
    print(f"  SKU-JS 产品数: {product_count}")
    print(f"  9100 段销售/服务人员数: {rep_count}")
    print(f"  ORD-JS 订单数: {scenario_count}")
    print(f"  本月 ORD-JS 订单数: {current_month_count}")
    print(f"  本月 ORD-JS 完成销售额: {current_month_amount}")
    print(f"  去年同期 ORD-JS-YOY 订单数: {yoy_count}")
    print(f"  近 6 个月 ORD-JS 有完成订单月份数: {trend_months}")

    print_rows(
        "订单状态覆盖",
        fetch_rows(
            engine,
            """
            SELECT status, COUNT(1) AS orders
            FROM sa_sales_order
            WHERE order_no LIKE 'ORD-JS-%'
            GROUP BY status
            ORDER BY status
            """,
        ),
    )
    print_rows(
        "本月大区销售额覆盖",
        fetch_rows(
            engine,
            """
            SELECT r.name AS region_name, COUNT(o.id) AS completed_orders, COALESCE(SUM(o.amount), 0) AS amount
            FROM sa_sales_region r
            LEFT JOIN sa_sales_order o
              ON o.region_id = r.id
             AND o.order_no LIKE 'ORD-JS-%'
             AND o.status = 'COMPLETED'
             AND o.order_date BETWEEN DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH)
                                  AND CURDATE()
            GROUP BY r.id, r.name
            ORDER BY amount DESC
            """,
        ),
    )
    print_rows(
        "本月品类销售额覆盖",
        fetch_rows(
            engine,
            """
            SELECT p.category, COUNT(o.id) AS completed_orders, COALESCE(SUM(o.amount), 0) AS amount
            FROM sa_sales_order o
            JOIN sa_product p ON p.id = o.product_id
            WHERE o.order_no LIKE 'ORD-JS-%'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH)
                                   AND CURDATE()
            GROUP BY p.category
            ORDER BY amount DESC
            """,
        ),
    )
    print_rows(
        "异常检测前置条件",
        fetch_rows(
            engine,
            """
            SELECT '西南近2周完成订单' AS item, COUNT(1) AS value
            FROM sa_sales_order o
            JOIN sa_sales_region r ON r.id = o.region_id
            WHERE r.name = '西南区'
              AND o.order_no LIKE 'ORD-JS-%'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND CURDATE()
            UNION ALL
            SELECT '西南过去4周完成订单', COUNT(1)
            FROM sa_sales_order o
            JOIN sa_sales_region r ON r.id = o.region_id
            WHERE r.name = '西南区'
              AND o.order_no LIKE 'ORD-JS-%'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 6 WEEK)
                                  AND DATE_SUB(CURDATE(), INTERVAL 15 DAY)
            UNION ALL
            SELECT '周敏近30天退款订单', COUNT(1)
            FROM sa_sales_order o
            JOIN sa_sales_rep s ON s.id = o.rep_id
            WHERE s.name = '周敏-陪诊顾问'
              AND o.status = 'REFUNDED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE()
            UNION ALL
            SELECT '张蕾近30天完成销售额', COALESCE(SUM(o.amount), 0)
            FROM sa_sales_order o
            JOIN sa_sales_rep s ON s.id = o.rep_id
            WHERE s.name = '张蕾-华北BD顾问'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE()
            UNION ALL
            SELECT '张蕾前30天完成销售额', COALESCE(SUM(o.amount), 0)
            FROM sa_sales_order o
            JOIN sa_sales_rep s ON s.id = o.rep_id
            WHERE s.name = '张蕾-华北BD顾问'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                                  AND DATE_SUB(CURDATE(), INTERVAL 31 DAY)
            UNION ALL
            SELECT '老版课程距今无完成销售天数', DATEDIFF(CURDATE(), MAX(o.order_date))
            FROM sa_sales_order o
            JOIN sa_product p ON p.id = o.product_id
            WHERE p.sku_code = 'SKU-JS-9001'
              AND o.status = 'COMPLETED'
            """,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="加载玖森百立/咪婴伴侣业务场景覆盖数据")
    parser.add_argument("--verify-only", action="store_true", help="只校验当前数据库，不写入数据")
    args = parser.parse_args()

    engine = build_engine()
    try:
        if args.verify_only:
            print("跳过写入，仅校验当前数据库。")
        else:
            executed = load_sql(engine, SCENARIO_SQL)
            print(f"已执行 {executed} 条 SQL 语句: {SCENARIO_SQL}")
        verify_coverage(engine)
        print("\n提示：项目业务查询有 300 秒 Redis 缓存，刚加载后相同问题可能要等缓存过期才看到新数据。")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
