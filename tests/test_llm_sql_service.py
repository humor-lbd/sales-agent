from datetime import date
from decimal import Decimal
import json

from app.logic.schemas import UserInfo
from app.logic.services import SalesQueryService
from app.logic.sql_agent.cache import SqlTemplateCache
from app.logic.sql_agent.models import GeneratedSql
from app.logic.sql_agent.service import LlmSqlQueryService


class FakeSqlSettings:
    llm_sql_enabled = True
    llm_sql_shadow_mode = False
    llm_sql_model = ""
    llm_sql_temperature = 0.0
    llm_sql_repair_attempts = 1
    llm_sql_max_rows = 200
    llm_sql_timeout_seconds = 5
    llm_sql_use_fallback = True
    llm_sql_allowed_operation_set = set()
    llm_sql_cache_enabled = True
    llm_sql_cache_ttl_seconds = 3600
    llm_sql_cache_backend = "memory"
    llm_sql_prompt_profile = "compact"
    llm_sql_template_mode = True
    llm_sql_audit_log_enabled = True
    openai_api_key = "test"
    openai_model = "fake"
    openai_base_url = ""
    openai_timeout_seconds = 60


class FakeGenerator:
    def __init__(self, sql, columns):
        self.sql = sql
        self.columns = columns
        self.tasks = []
        self.last_usage = {}
        self.last_duration_ms = 0.0

    def generate(self, task, schema, errors=None):
        self.tasks.append(task)
        return GeneratedSql(sql=self.sql, params={}, result_columns=self.columns, confidence=1)


class FakeExecutor:
    def __init__(self, rows):
        self.rows = rows
        self.sql = None
        self.params = None

    def execute(self, sql, params):
        self.sql = sql
        self.params = params
        return self.rows


def test_llm_sql_service_executes_summary_with_manager_scope():
    generator = FakeGenerator(
        (
            "SELECT COALESCE(SUM(o.amount), 0) AS total_amount "
            "FROM sa_sales_order o "
            "WHERE o.status = 'COMPLETED' "
            "AND o.order_date BETWEEN :start_date AND :end_date"
        ),
        ["total_amount"],
    )
    executor = FakeExecutor([{"total_amount": "1234.50"}])
    service = LlmSqlQueryService(
        db=None,
        current_user=UserInfo(user_id=1, username="经理", role="SALES_MANAGER", region_id=2),
        redis_client=None,
        settings=FakeSqlSettings(),
        generator=generator,
        executor=executor,
    )

    result = service.query_total_amount(None, date(2026, 5, 1), date(2026, 5, 31))

    assert result == Decimal("1234.50")
    assert "o.region_id = :scope_region_id" in executor.sql
    assert executor.params["scope_region_id"] == 2
    assert executor.params["start_date"] == date(2026, 5, 1)


def test_sales_query_service_uses_llm_result_when_enabled():
    class FakeOrderRepo:
        def __init__(self):
            self.called = False

        def sum_amount_all(self, start, end):
            self.called = True
            return Decimal("1")

    class FakeLlmSql:
        def query_total_amount(self, region_id, start, end):
            return Decimal("99")

    service = SalesQueryService.__new__(SalesQueryService)
    service.current_user = None
    service.redis = None
    service.settings = FakeSqlSettings()
    service.llm_sql = FakeLlmSql()
    service.order_repo = FakeOrderRepo()

    result = service.query_total_amount(None, date(2026, 5, 1), date(2026, 5, 31))

    assert result == Decimal("99")
    assert not service.order_repo.called


def test_sales_query_service_falls_back_when_llm_fails():
    class FakeOrderRepo:
        def sum_amount_all(self, start, end):
            return Decimal("7")

    class BrokenLlmSql:
        def query_total_amount(self, region_id, start, end):
            raise RuntimeError("boom")

    service = SalesQueryService.__new__(SalesQueryService)
    service.current_user = None
    service.redis = None
    service.settings = FakeSqlSettings()
    service.llm_sql = BrokenLlmSql()
    service.order_repo = FakeOrderRepo()

    result = service.query_total_amount(None, date(2026, 5, 1), date(2026, 5, 31))

    assert result == Decimal("7")


def test_sales_query_service_respects_allowed_operations():
    class RestrictedSettings(FakeSqlSettings):
        llm_sql_allowed_operation_set = {"query_rep_ranking"}

    class FakeOrderRepo:
        def __init__(self):
            self.called = False

        def sum_amount_all(self, start, end):
            self.called = True
            return Decimal("12")

    class FakeLlmSql:
        def query_total_amount(self, region_id, start, end):
            return Decimal("99")

    service = SalesQueryService.__new__(SalesQueryService)
    service.current_user = None
    service.redis = None
    service.settings = RestrictedSettings()
    service.llm_sql = FakeLlmSql()
    service.order_repo = FakeOrderRepo()

    result = service.query_total_amount(None, date(2026, 5, 1), date(2026, 5, 31))

    assert result == Decimal("12")
    assert service.order_repo.called


def test_llm_sql_service_caches_validated_sql_template():
    class NoTemplateSettings(FakeSqlSettings):
        llm_sql_template_mode = False

    generator = FakeGenerator(
        (
            "SELECT COALESCE(SUM(o.amount), 0) AS total_amount "
            "FROM sa_sales_order o "
            "WHERE o.status = 'COMPLETED' "
            "AND o.order_date BETWEEN :start_date AND :end_date"
        ),
        ["total_amount"],
    )
    executor = FakeExecutor([{"total_amount": "12.00"}])
    service = LlmSqlQueryService(
        db=None,
        current_user=UserInfo(user_id=1, username="总监", role="SALES_DIRECTOR", region_id=2, rep_id=1),
        redis_client=None,
        settings=NoTemplateSettings(),
        generator=generator,
        executor=executor,
    )

    first = service.query_total_amount(None, date(2026, 5, 1), date(2026, 5, 31))
    second = service.query_total_amount(None, date(2026, 6, 1), date(2026, 6, 30))

    assert first == Decimal("12.00")
    assert second == Decimal("12.00")
    assert len(generator.tasks) == 1
    signature = SqlTemplateCache.build_signature(generator.tasks[0])
    cached = service.template_cache.get(signature)
    assert cached is not None
    assert "SUM(o.amount)" in cached.sql


def test_llm_sql_service_uses_ranking_template_without_generator():
    generator = FakeGenerator("SELECT 1", ["ignored"])
    executor = FakeExecutor(
        [
            {
                "rep_id": 9,
                "rep_name": "李雷",
                "region_id": 2,
                "region_name": "华北区",
                "total_amount": "888.00",
            }
        ]
    )
    service = LlmSqlQueryService(
        db=None,
        current_user=UserInfo(user_id=1, username="总监", role="SALES_DIRECTOR", region_id=2, rep_id=1),
        redis_client=None,
        settings=FakeSqlSettings(),
        generator=generator,
        executor=executor,
    )

    result = service.query_rep_ranking(date(2026, 5, 1), date(2026, 5, 31), 5)

    assert len(generator.tasks) == 0
    assert result[0].rep_name == "李雷"
    assert "SUM(o.amount) AS total_amount" in executor.sql
    assert executor.params["top_n"] == 5


def test_llm_sql_service_writes_structured_audit_log(caplog):
    class NoTemplateSettings(FakeSqlSettings):
        llm_sql_template_mode = False

    generator = FakeGenerator(
        (
            "SELECT COALESCE(SUM(o.amount), 0) AS total_amount "
            "FROM sa_sales_order o "
            "WHERE o.status = 'COMPLETED' "
            "AND o.order_date BETWEEN :start_date AND :end_date"
        ),
        ["total_amount"],
    )
    executor = FakeExecutor([{"total_amount": "456.00"}])
    service = LlmSqlQueryService(
        db=None,
        current_user=UserInfo(user_id=1, username="总监", role="SALES_DIRECTOR", region_id=2, rep_id=1),
        redis_client=None,
        settings=NoTemplateSettings(),
        generator=generator,
        executor=executor,
    )

    with caplog.at_level("INFO"):
        result = service.query_total_amount(None, date(2026, 5, 1), date(2026, 5, 31))

    assert result == Decimal("456.00")
    entries = [json.loads(record.message) for record in caplog.records if '"event": "llm_sql_audit"' in record.message]
    assert entries
    audit = entries[-1]
    assert audit["tool_name"] == "get_sales_summary"
    assert audit["task_type"] == "sales_summary"
    assert audit["source"] == "generator"
    assert "SUM(o.amount)" in audit["sql"]
