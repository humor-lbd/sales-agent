"""
文件作用：
- 负责初始化 Python 版数据库、建表并按需导入演示数据。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。

整体流程（从启动到可用）：
1) 读取配置：从 Settings 中获取 MySQL 连接信息、是否需要引导、是否需要导入种子数据。
2) 连接 MySQL 管理库（默认 mysql）：确保业务库存在（CREATE DATABASE IF NOT EXISTS）。
3) 连接业务库：执行 schema.sql 建表，并校验关键表是否都已创建成功。
4) 可选导入种子数据：如果业务表已经有数据则默认跳过（除非 reseed=true）。

设计要点：
- 引导逻辑放在启动阶段（FastAPI lifespan）触发，方便“一键启动即有数据可跑通”。
- schema/data 都以 SQL 文件形式维护，减少对 ORM migrate 工具链的依赖，便于演示与快速初始化。
- 在 reseed 场景下，按业务表依赖顺序清理数据，避免外键/引用关系导致的删除失败。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, Connection, Engine

from app.core.config import Settings, get_settings


LOGGER = logging.getLogger("sales-agent.db.bootstrap")

# 业务相关的核心表（会被用于“是否已有数据”的判断，以及 reseed 清理的顺序控制）
BUSINESS_TABLES = (
    "sa_sales_region",
    "sa_sales_rep",
    "sa_product",
    "sa_sales_order",
)
# 项目所有需要校验存在的表集合（业务表 + 会话记忆表）
ALL_TABLES = BUSINESS_TABLES + ("sa_chat_memory",)


@dataclass(slots=True, frozen=True)
# 定义类 BootstrapReport，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class BootstrapReport:
    """
    数据库引导报告（用于启动日志与可观测性）

    - database_name：业务库名（例如 jc_sales_agent_py）
    - schema_applied：是否已成功执行 schema.sql
    - seed_applied：是否已成功执行 data.sql
    - skipped_seed_reason：当 seed_applied=False 时的原因（比如业务表已有数据）
    """
    database_name: str
    schema_applied: bool
    seed_applied: bool
    skipped_seed_reason: str | None = None


# 定义函数 initialize_database，负责当前文件中的一个关键步骤或对外能力。
def initialize_database(settings: Settings | None = None) -> BootstrapReport:
    """
    作用：执行initialize_database对应的业务逻辑。
    参数：settings。
    返回：函数执行后的结果。

    说明：
    - 该函数是“数据库引导”的主入口，会被 FastAPI 启动阶段调用。
    - 它会同时负责：建库、建表、导入种子数据（可选）。
    - 若建表或校验失败，会抛出异常，由上层决定是否 fail fast。
    """
    settings = settings or get_settings()
    database_name = settings.mysql_db

    LOGGER.info(
        "初始化 Python 版数据库: db=%s, seed=%s, reseed=%s",
        database_name,
        settings.db_bootstrap_with_seed,
        settings.db_bootstrap_reseed,
    )

    # 连接“mysql”管理库：用于执行 CREATE DATABASE 等管理语句
    admin_engine = create_engine(_build_url(settings, "mysql"), pool_pre_ping=True, pool_recycle=3600)
    # 连接业务库：用于执行建表、导入演示数据等业务操作
    app_engine = create_engine(_build_url(settings, database_name), pool_pre_ping=True, pool_recycle=3600)

    try:
        # 1) 先确保业务库存在（即便是空库也要先创建出来）
        with admin_engine.begin() as conn:
            conn.exec_driver_sql(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )

        # 2) 建表：执行 schema.sql（多条 CREATE TABLE/INDEX 语句）
        _execute_sql_file(app_engine, _sql_dir() / "schema.sql")
        # 3) 校验表：确保关键表都存在，避免部分建表失败导致后续查询报错
        _validate_tables(app_engine)

        seed_applied = False
        skipped_reason: str | None = None
        if settings.db_bootstrap_with_seed:
            # 4) 可选导入演示数据：
            # - 若业务表已有数据且 reseed=False：跳过导入，防止覆盖真实数据
            # - 若 reseed=True：先清理业务表，再重新导入，保证演示数据一致性
            seed_applied, skipped_reason = _seed_database(
                app_engine,
                reseed=settings.db_bootstrap_reseed,
            )

        return BootstrapReport(
            database_name=database_name,
            schema_applied=True,
            seed_applied=seed_applied,
            skipped_seed_reason=skipped_reason,
        )
    finally:
        # 显式释放连接池资源，避免在某些运行环境里出现连接泄漏或句柄占用
        admin_engine.dispose()
        app_engine.dispose()


# 定义函数 _build_url，负责组装当前步骤需要的对象或参数。
def _build_url(settings: Settings, database_name: str) -> URL:
    """
    作用：执行_build_url对应的业务逻辑。
    参数：settings、database_name。
    返回：函数执行后的结果。

    说明：
    - 使用 SQLAlchemy 的 URL.create 组装连接串，避免手工拼接导致的编码/转义问题。
    - charset 固定为 utf8mb4，保证中文与表情符号兼容。
    """
    return URL.create(
        "mysql+pymysql",
        username=settings.mysql_user,
        password=settings.mysql_password,
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=database_name,
        query={"charset": "utf8mb4"},
    )


# 定义函数 _sql_dir，作为当前文件内部的辅助函数，给主流程提供支撑。
def _sql_dir() -> Path:
    """
    作用：执行_sql_dir对应的业务逻辑。
    参数：无。
    返回：函数执行后的结果。

    说明：SQL 文件与该模块同目录下的 sql/ 目录维护，避免受运行 cwd 影响。
    """
    return Path(__file__).resolve().parent / "sql"


# 定义函数 _execute_sql_file，作为当前文件内部的辅助函数，给主流程提供支撑。
def _execute_sql_file(engine: Engine, path: Path) -> None:
    """
    作用：执行_execute_sql_file对应的业务逻辑。
    参数：engine、path。
    返回：函数执行后的结果。

    说明：
    - 先把 SQL 文件切成多条 statement，再逐条执行。
    - 使用 engine.begin() 开启事务：若某条语句失败，会整体回滚，保证建表/导入的原子性。
    """
    statements = _split_sql_statements(path.read_text(encoding="utf-8"))
    if not statements:
        raise RuntimeError(f"SQL 文件为空: {path}")

    with engine.begin() as conn:
        for statement in statements:
            conn.exec_driver_sql(statement)


# 定义函数 _split_sql_statements，作为当前文件内部的辅助函数，给主流程提供支撑。
def _split_sql_statements(sql_text: str) -> list[str]:
    """
    作用：执行_split_sql_statements对应的业务逻辑。
    参数：sql_text。
    返回：函数执行后的结果。

    说明：
    - 这里采用“按行过滤 + 按分号切分”的轻量方案：
      - 跳过空行与 `--` 单行注释；
      - 其余内容拼接后再用 `;` 分割。
    - 注意：这是为本项目 schema/data 的写法定制的简单解析器，不支持复杂的 SQL 方言（如存储过程内包含分号等）。
    """
    cleaned_lines: list[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        cleaned_lines.append(line)

    merged = "\n".join(cleaned_lines)
    return [statement.strip() for statement in merged.split(";") if statement.strip()]


# 定义函数 _seed_database，作为当前文件内部的辅助函数，给主流程提供支撑。
def _seed_database(engine: Engine, *, reseed: bool) -> tuple[bool, str | None]:
    """
    作用：执行_seed_database对应的业务逻辑。
    参数：engine。
    返回：函数执行后的结果。

    Returns:
        (seed_applied, skipped_reason)
        - seed_applied=True 表示已成功导入 data.sql
        - seed_applied=False 表示未导入（原因通过 skipped_reason 给出）
    """
    data_path = _sql_dir() / "data.sql"
    statements = _split_sql_statements(data_path.read_text(encoding="utf-8"))
    if not statements:
        return False, "种子数据文件为空"

    with engine.begin() as conn:
        # 业务表已有数据时，默认不覆盖，避免误伤真实环境
        if _business_tables_have_data(conn):
            if not reseed:
                return False, "业务表已有数据，已跳过演示数据初始化"
            # reseed=true 时先清空业务表，再写入演示数据
            _clear_business_tables(conn)

        for statement in statements:
            conn.exec_driver_sql(statement)

    return True, None


# 定义函数 _business_tables_have_data，作为当前文件内部的辅助函数，给主流程提供支撑。
def _business_tables_have_data(conn: Connection) -> bool:
    """
    作用：执行_business_tables_have_data对应的业务逻辑。
    参数：conn。
    返回：函数执行后的结果。

    说明：
    - 只要任一业务表存在且行数 > 0，就认为“业务库已有数据”，从而触发“默认跳过 seed”策略。
    - 这样做的目的是保护线上/已有数据环境，避免启动时覆盖数据。
    """
    inspector = inspect(conn)
    for table_name in BUSINESS_TABLES:
        if not inspector.has_table(table_name):
            return False
        count = conn.execute(text(f"SELECT COUNT(1) FROM {table_name}")).scalar_one()
        if int(count) > 0:
            return True
    return False


# 定义函数 _clear_business_tables，负责清理旧状态，避免影响下一次执行。
def _clear_business_tables(conn: Connection) -> None:
    """
    作用：执行_clear_business_tables对应的业务逻辑。
    参数：conn。
    返回：函数执行后的结果。

    说明：
    - 按依赖顺序清理：先订单，再产品/人员/大区，避免潜在的引用关系导致删除失败。
    - 这里使用 DELETE 而不是 TRUNCATE，兼容更多权限配置与外键约束场景。
    """
    conn.execute(text("DELETE FROM sa_sales_order"))
    conn.execute(text("DELETE FROM sa_product"))
    conn.execute(text("DELETE FROM sa_sales_rep"))
    conn.execute(text("DELETE FROM sa_sales_region"))


# 定义函数 _validate_tables，负责校验输入是否合法并尽早阻断错误。
def _validate_tables(engine: Engine) -> None:
    """
    作用：执行_validate_tables对应的业务逻辑。
    参数：engine。
    返回：函数执行后的结果。

    说明：
    - schema.sql 执行完后立即校验关键表存在性，能把问题更早暴露在“启动阶段”。
    - 如果缺表，后续 ORM/查询会出现更隐蔽的运行时错误，因此这里选择 fail fast。
    """
    existing_tables = set(inspect(engine).get_table_names())
    missing = [table_name for table_name in ALL_TABLES if table_name not in existing_tables]
    if missing:
        raise RuntimeError(f"数据库初始化失败，缺少表: {', '.join(missing)}")


if __name__ == "__main__":
    report = initialize_database()
    LOGGER.info("数据库初始化完成: %s", report)
    print(
        f"database={report.database_name}, "
        f"schema_applied={report.schema_applied}, "
        f"seed_applied={report.seed_applied}, "
        f"skipped_seed_reason={report.skipped_seed_reason}"
    )
