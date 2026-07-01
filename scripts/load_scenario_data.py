"""
文件作用：
- 把 app/db/sql/scenario_coverage.sql 追加到当前配置的 MySQL 数据库。
- 执行后打印覆盖校验，方便确认所有核心业务场景都有数据支撑。

使用方式：
    python scripts/load_scenario_data.py
    python scripts/load_scenario_data.py --verify-only
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.db.bootstrap import _split_sql_statements


SCENARIO_SQL = PROJECT_ROOT / "app" / "db" / "sql" / "scenario_coverage.sql"


@dataclass(frozen=True)
class RequiredSeed:
    table_name: str
    column_name: str
    values: tuple[str, ...]


REQUIRED_SEEDS: tuple[RequiredSeed, ...] = (
    RequiredSeed("sa_sales_region", "name", ("华东区", "华南区", "华北区", "西南区")),
    RequiredSeed(
        "sa_sales_rep",
        "name",
        ("张伟", "王芳", "刘洋", "赵雪", "张磊", "周丽", "郑华", "林敏"),
    ),
    RequiredSeed(
        "sa_product",
        "sku_code",
        (
            "SKU-1001",
            "SKU-1002",
            "SKU-1003",
            "SKU-1004",
            "SKU-1005",
            "SKU-2001",
            "SKU-2002",
            "SKU-2003",
            "SKU-3001",
            "SKU-3003",
            "SKU-3004",
            "SKU-4001",
            "SKU-4002",
            "SKU-4005",
        ),
    ),
)


def build_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=3600)


def pymysql_safe(sql: str) -> str:
    return sql.replace("%", "%%")


def missing_seed_values(engine: Engine) -> list[str]:
    missing: list[str] = []
    with engine.connect() as conn:
        for seed in REQUIRED_SEEDS:
            rows = conn.execute(
                text(
                    f"SELECT {seed.column_name} FROM {seed.table_name} "
                    f"WHERE {seed.column_name} IN :values"
                ).bindparams(bindparam("values", expanding=True)),
                {"values": seed.values},
            ).scalars()
            existing = {str(value) for value in rows}
            missing.extend(
                f"{seed.table_name}.{seed.column_name}={value}"
                for value in seed.values
                if value not in existing
            )
    return missing


def load_sql(engine: Engine, sql_path: Path) -> int:
    statements = _split_sql_statements(sql_path.read_text(encoding="utf-8"))
    if not statements:
        raise RuntimeError(f"SQL 文件为空: {sql_path}")

    with engine.begin() as conn:
        for statement in statements:
            conn.exec_driver_sql(pymysql_safe(statement))
    return len(statements)


def scalar_int(engine: Engine, sql: str, **params: object) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(sql), params).scalar_one() or 0)


def scalar_text(engine: Engine, sql: str, **params: object) -> str:
    with engine.connect() as conn:
        value = conn.execute(text(sql), params).scalar_one()
        return "" if value is None else str(value)


def fetch_rows(engine: Engine, sql: str, **params: object) -> list[dict[str, object]]:
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(text(sql), params).all()]


def print_rows(title: str, rows: Iterable[dict[str, object]]) -> None:
    print(f"\n{title}")
    for row in rows:
        print("  " + " | ".join(f"{key}={value}" for key, value in row.items()))


def verify_coverage(engine: Engine) -> None:
    scenario_count = scalar_int(
        engine,
        "SELECT COUNT(1) FROM sa_sales_order WHERE order_no LIKE 'ORD-SC-%'",
    )
    current_month_count = scalar_int(
        engine,
        """
        SELECT COUNT(1)
        FROM sa_sales_order
        WHERE order_no LIKE 'ORD-SC-%'
          AND order_date BETWEEN DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH)
                             AND CURDATE()
        """,
    )
    current_month_amount = scalar_text(
        engine,
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM sa_sales_order
        WHERE status = 'COMPLETED'
          AND order_date BETWEEN DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH)
                             AND CURDATE()
        """,
    )
    last_year_same_period = scalar_int(
        engine,
        """
        SELECT COUNT(1)
        FROM sa_sales_order
        WHERE order_no LIKE 'ORD-SC-YOY-%'
          AND order_date BETWEEN DATE_SUB(DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH), INTERVAL 1 YEAR)
                             AND DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        """,
    )
    months_with_data = scalar_int(
        engine,
        """
        SELECT COUNT(DISTINCT EXTRACT(YEAR_MONTH FROM order_date))
        FROM sa_sales_order
        WHERE status = 'COMPLETED'
          AND order_date BETWEEN DATE_SUB(DATE_ADD(MAKEDATE(YEAR(CURDATE()), 1), INTERVAL (MONTH(CURDATE()) - 1) MONTH), INTERVAL 6 MONTH)
                             AND CURDATE()
        """,
    )

    print("\n场景数据总览")
    print(f"  ORD-SC-* 订单数: {scenario_count}")
    print(f"  本月 ORD-SC-* 订单数: {current_month_count}")
    print(f"  本月全公司完成销售额: {current_month_amount}")
    print(f"  去年同期 ORD-SC-YOY-* 订单数: {last_year_same_period}")
    print(f"  近 6 个月有完成订单的月份数: {months_with_data}")

    print_rows(
        "订单状态覆盖",
        fetch_rows(
            engine,
            """
            SELECT status, COUNT(1) AS orders
            FROM sa_sales_order
            WHERE order_no LIKE 'ORD-SC-%'
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
            WHERE o.status = 'COMPLETED'
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
            SELECT '华北近2周完成订单' AS item, COUNT(1) AS value
            FROM sa_sales_order o
            JOIN sa_sales_region r ON r.id = o.region_id
            WHERE r.name = '华北区'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 14 DAY) AND CURDATE()
            UNION ALL
            SELECT '华北过去4周完成订单', COUNT(1)
            FROM sa_sales_order o
            JOIN sa_sales_region r ON r.id = o.region_id
            WHERE r.name = '华北区'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 6 WEEK)
                                  AND DATE_SUB(CURDATE(), INTERVAL 15 DAY)
            UNION ALL
            SELECT '王芳近30天退款订单', COUNT(1)
            FROM sa_sales_order o
            JOIN sa_sales_rep s ON s.id = o.rep_id
            WHERE s.name = '王芳'
              AND o.status = 'REFUNDED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE()
            UNION ALL
            SELECT '张磊近30天完成销售额', COALESCE(SUM(o.amount), 0)
            FROM sa_sales_order o
            JOIN sa_sales_rep s ON s.id = o.rep_id
            WHERE s.name = '张磊'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND CURDATE()
            UNION ALL
            SELECT '张磊前30天完成销售额', COALESCE(SUM(o.amount), 0)
            FROM sa_sales_order o
            JOIN sa_sales_rep s ON s.id = o.rep_id
            WHERE s.name = '张磊'
              AND o.status = 'COMPLETED'
              AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                                  AND DATE_SUB(CURDATE(), INTERVAL 31 DAY)
            UNION ALL
            SELECT 'SKU-4002距今无完成销售天数', DATEDIFF(CURDATE(), MAX(o.order_date))
            FROM sa_sales_order o
            JOIN sa_product p ON p.id = o.product_id
            WHERE p.sku_code = 'SKU-4002'
              AND o.status = 'COMPLETED'
            """,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="加载 sales-agent 业务场景覆盖数据")
    parser.add_argument("--verify-only", action="store_true", help="只校验当前数据库覆盖情况，不写入数据")
    args = parser.parse_args()

    engine = build_engine()
    try:
        missing = missing_seed_values(engine)
        if missing:
            print("当前数据库缺少基础 seed 数据，先执行 app/db/sql/data.sql 或启动项目完成初始化。")
            for item in missing:
                print(f"  - {item}")
            return 1

        if args.verify_only:
            print("跳过写入，仅校验当前数据库。")
        else:
            executed = load_sql(engine, SCENARIO_SQL)
            print(f"已执行 {executed} 条 SQL 语句: {SCENARIO_SQL}")

        verify_coverage(engine)
        print("\n提示：项目业务查询有 300 秒 Redis 缓存，刚问过的同一问题可能需要等缓存过期后才看到新数据。")
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
