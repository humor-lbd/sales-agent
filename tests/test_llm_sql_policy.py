from app.logic.sql_agent.models import QueryScope
from app.logic.sql_agent.policy import PermissionPolicyInjector


def test_manager_scope_is_injected_before_group_by():
    sql = (
        "SELECT r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount "
        "FROM sa_sales_order o JOIN sa_sales_region r ON r.id = o.region_id "
        "WHERE o.status = 'COMPLETED' "
        "GROUP BY r.id, r.name ORDER BY total_amount DESC"
    )

    scoped_sql, params = PermissionPolicyInjector().apply(sql, {}, QueryScope(role="SALES_MANAGER", region_id=2))

    assert "o.region_id = :scope_region_id GROUP BY" in scoped_sql
    assert params["scope_region_id"] == 2


def test_rep_scope_is_injected_before_order_by():
    sql = (
        "SELECT o.id, o.order_no FROM sa_sales_order o "
        "WHERE o.order_date BETWEEN :start_date AND :end_date "
        "ORDER BY o.order_date DESC LIMIT :limit"
    )

    scoped_sql, params = PermissionPolicyInjector().apply(sql, {}, QueryScope(role="SALES_REP", rep_id=9))

    assert "o.rep_id = :scope_rep_id ORDER BY" in scoped_sql
    assert params["scope_rep_id"] == 9


def test_director_scope_leaves_sql_unchanged():
    sql = "SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o WHERE o.status = 'COMPLETED'"

    scoped_sql, params = PermissionPolicyInjector().apply(sql, {"x": 1}, QueryScope(role="SALES_DIRECTOR"))

    assert scoped_sql == sql
    assert params == {"x": 1}
