from datetime import date

from app.logic.sql_agent.models import GeneratedSql, QueryScope, SqlTaskSpec
from app.logic.sql_agent.validator import SqlValidator


def build_task(task_type="sales_summary", result_contract=None):
    return SqlTaskSpec(
        tool_name="get_sales_summary",
        task_type=task_type,
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 31),
        scope=QueryScope(role="ANONYMOUS"),
        result_contract=result_contract or ["total_amount"],
    )


def test_validator_accepts_safe_summary_sql():
    sql = GeneratedSql(
        sql=(
            "SELECT COALESCE(SUM(o.amount), 0) AS total_amount "
            "FROM sa_sales_order o "
            "WHERE o.status = 'COMPLETED' "
            "AND o.order_date BETWEEN :start_date AND :end_date"
        ),
        result_columns=["total_amount"],
    )

    result = SqlValidator().validate(sql, build_task())

    assert result.ok
    assert result.normalized_sql == sql.sql


def test_validator_rejects_write_sql():
    sql = GeneratedSql(sql="DROP TABLE sa_sales_order", result_columns=[])

    result = SqlValidator().validate(sql, build_task())

    assert not result.ok
    assert any("危险关键词" in error for error in result.errors)


def test_validator_rejects_select_star_and_memory_table():
    sql = GeneratedSql(sql="SELECT * FROM sa_chat_memory", result_columns=[])

    result = SqlValidator().validate(sql, build_task())

    assert not result.ok
    assert any("SELECT *" in error for error in result.errors)
    assert any("未授权表" in error for error in result.errors)


def test_validator_adds_limit_for_order_detail():
    sql = GeneratedSql(
        sql=(
            "SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status "
            "FROM sa_sales_order o "
            "WHERE o.order_date BETWEEN :start_date AND :end_date "
            "ORDER BY o.order_date DESC, o.id DESC"
        ),
        result_columns=["id", "order_no", "order_date", "rep_id", "customer_name", "amount", "status"],
    )

    result = SqlValidator().validate(sql, build_task("order_detail", ["id", "order_no", "order_date", "rep_id", "customer_name", "amount", "status"]))

    assert result.ok
    assert result.normalized_sql.endswith("LIMIT 20")


def test_validator_rejects_completed_filter_for_order_detail():
    sql = GeneratedSql(
        sql=(
            "SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status "
            "FROM sa_sales_order o "
            "WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' "
            "ORDER BY o.order_date DESC, o.id DESC"
        ),
        result_columns=["id", "order_no", "order_date", "rep_id", "customer_name", "amount", "status"],
    )

    result = SqlValidator().validate(sql, build_task("order_detail", ["id", "order_no", "order_date", "rep_id", "customer_name", "amount", "status"]))

    assert not result.ok
    assert any("订单明细查询不允许" in error for error in result.errors)


def test_validator_rejects_hallucinated_region_filter_when_task_has_no_region():
    sql = GeneratedSql(
        sql=(
            "SELECT SUM(o.amount) AS total_amount "
            "FROM sa_sales_order o JOIN sa_sales_region r ON r.id = o.region_id "
            "WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND r.id = :region_id"
        ),
        result_columns=["total_amount"],
    )
    task = SqlTaskSpec(
        tool_name="get_sales_summary",
        task_type="sales_summary",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 31),
        scope=QueryScope(role="ANONYMOUS"),
        result_contract=["total_amount"],
    )

    result = SqlValidator().validate(sql, task)

    assert not result.ok
    assert any("未提供 region_id" in error for error in result.errors)
