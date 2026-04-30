"""
配置管理模块

该模块负责统一读取环境变量并生成可复用的项目配置对象。
使用 Pydantic V2 进行配置管理，支持从 .env 文件和环境变量中读取配置。
"""

from functools import lru_cache
import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类
    
    从环境变量和 .env 文件中读取配置，提供应用所需的各种配置项。
    """
    model_config = SettingsConfigDict(
        env_file=".env" if "pytest" not in sys.modules else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用基本配置
    app_name: str = Field(default="jc-sales-agent-python", alias="APP_NAME", description="应用名称")
    app_port: int = Field(default=8088, alias="APP_PORT", description="应用端口")
    auth_enabled: bool = Field(default=False, alias="AUTH_ENABLED", description="是否启用认证")
    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET", description="JWT密钥")
    jwt_expire_minutes: int = Field(default=1440, alias="JWT_EXPIRE_MINUTES", description="JWT过期时间（分钟）")

    # 数据库配置
    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST", description="MySQL主机地址")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT", description="MySQL端口")
    mysql_db: str = Field(default="jc_sales_agent_py", alias="MYSQL_DB", description="数据库名称")
    mysql_user: str = Field(default="root", alias="MYSQL_USER", description="数据库用户名")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD", description="数据库密码")
    db_bootstrap_enabled: bool = Field(default=True, alias="DB_BOOTSTRAP_ENABLED", description="是否启用数据库引导")
    db_bootstrap_with_seed: bool = Field(default=True, alias="DB_BOOTSTRAP_WITH_SEED", description="是否使用种子数据引导数据库")
    db_bootstrap_reseed: bool = Field(default=False, alias="DB_BOOTSTRAP_RESEED", description="是否重新种子数据")
    db_bootstrap_fail_fast: bool = Field(default=True, alias="DB_BOOTSTRAP_FAIL_FAST", description="数据库引导失败是否快速失败")

    # Redis配置
    redis_enabled: bool = Field(default=True, alias="REDIS_ENABLED", description="是否启用Redis")
    redis_host: str = Field(default="127.0.0.1", alias="REDIS_HOST", description="Redis主机地址")
    redis_port: int = Field(default=6379, alias="REDIS_PORT", description="Redis端口")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD", description="Redis密码")
    redis_db: int = Field(default=0, alias="REDIS_DB", description="Redis数据库编号")

    # OpenAI配置
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL", description="OpenAI API基础地址")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY", description="OpenAI API密钥")
    openai_model: str = Field(default="qwen-max", alias="OPENAI_MODEL", description="使用的OpenAI模型")
    openai_timeout_seconds: int = Field(default=60, alias="OPENAI_TIMEOUT_SECONDS", description="OpenAI API超时时间（秒）")
    agent_max_tool_calls: int = Field(default=8, alias="AGENT_MAX_TOOL_CALLS", description="Agent最大工具调用次数")
    agent_trace_enabled: bool = Field(default=True, alias="AGENT_TRACE_ENABLED", description="是否启用Agent追踪")
    agent_memory_followup_limit: int = Field(default=10, alias="AGENT_MEMORY_FOLLOWUP_LIMIT", description="追问场景注入模型的最近消息条数")
    agent_memory_window_messages: int = Field(default=20, alias="AGENT_MEMORY_WINDOW_MESSAGES", description="会话注入前保留的最近消息窗口")
    agent_memory_llm_summary_enabled: bool = Field(default=True, alias="AGENT_MEMORY_LLM_SUMMARY_ENABLED", description="是否启用基于 LLM 的历史摘要压缩")
    agent_memory_llm_summary_model: str = Field(default="", alias="AGENT_MEMORY_LLM_SUMMARY_MODEL", description="历史摘要压缩使用的模型，留空时复用 OPENAI_MODEL")
    agent_memory_llm_summary_trigger_messages: int = Field(default=8, alias="AGENT_MEMORY_LLM_SUMMARY_TRIGGER_MESSAGES", description="超过多少条更早历史后才触发 LLM 摘要")
    agent_memory_summary_messages: int = Field(default=6, alias="AGENT_MEMORY_SUMMARY_MESSAGES", description="更早历史压缩成摘要时最多保留的消息条数")
    agent_memory_summary_chars: int = Field(default=80, alias="AGENT_MEMORY_SUMMARY_CHARS", description="单条摘要消息最多保留的字符数")

    # 业务配置
    anomaly_threshold_days: int = Field(default=5, alias="ANOMALY_THRESHOLD_DAYS", description="异常检测阈值（天）")
    trend_drop_threshold: float = Field(default=0.3, alias="TREND_DROP_THRESHOLD", description="趋势下降阈值（比例）")

    @property
    def database_url(self) -> str:
        """
        生成数据库连接URL
        
        Returns:
            数据库连接URL字符串
        """
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        """
        生成Redis连接URL
        
        Returns:
            Redis连接URL字符串
        """
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """
    获取应用配置单例
    
    使用 lru_cache 装饰器确保配置对象只被创建一次，提高性能。
    
    Returns:
        Settings 配置对象实例
    """
    return Settings()
