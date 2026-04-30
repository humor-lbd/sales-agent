<!--
文件作用：
- 作为 Python 版项目总说明，帮助读者快速理解启动方式、目录结构和运行边界。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

# sales-agent

Python 版销售数据分析 Agent，基于 `FastAPI + LangGraph + SQLAlchemy + MySQL + Redis`。

当前主链路已经切到一套更贴近生产的 ReAct 执行流：

- `bootstrap -> load_memory -> guardrails -> react_agent <-> react_tool_executor -> persist_memory`
- `/agent/chat/stream` 不再只是“末尾切片伪流式”，最终回答轮会优先直接使用模型 `stream()`
- 带 `tool-loop` 的分析型收尾场景，包括“先查数据再给结论”和“先查数据再结合图表总结”这类请求，也会尽量走真实流式输出
- 会话历史除了最近窗口，还会对更早历史做 LLM summary；如果摘要模型失败，会自动回退到规则摘要
- 同一请求内会复用绑定好工具的模型与工具 schema，减少每轮 ReAct 的重复构造开销

这版现在已经切到自己的数据库，不再默认依赖 Java 版使用的 `jc-ai` 库：

- 默认数据库名：`jc_sales_agent_py`
- 启动时自动执行：
  - 建库
  - 建表
  - 首次演示数据初始化
- Python 版自己的 SQL 位于 `app/db/sql/`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 1. 目录说明

- `app/`
  - `api/`：接口层
  - `core/`：配置、日志、异常、鉴权
  - `db/`：数据库连接、ORM、仓储、数据库初始化脚本
  - `graph/`：LangGraph 工作流
  - `logic/`：工具、服务、Agent 入口
- `tests/`：单元测试
- `scripts/`：烟雾测试、回归、性能与稳定性探针
- `frontend/`：前端页面

## 2. Agent 特性

当前版本的 Agent 重点能力有：

- `真流式回答`：直接把模型 token 按 SSE 推给前端，而不是等整段回答结束后再本地切片
- `tool-loop` 收尾流式：当问题需要先调工具再组织答案时，最终回答轮仍会优先走真实流式
- `请求级模型/工具复用`：同一请求内缓存 `llm_with_tools`、tool schema 和 tool map
- `LLM 记忆压缩`：较早历史会优先压缩成摘要，再注入系统提示词
- `规则降级`：LLM 摘要失败、Redis 不可用、记忆落库失败等场景都会降级，而不是直接打断主链路
- `统一中间层`：模型轮次、工具调用、流式事件和 trace 都通过 middleware 收口

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 3. 环境准备

安装依赖：

```powershell
pip install -r requirements.txt
```

准备 `.env`：

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DB`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `AGENT_MEMORY_LLM_SUMMARY_ENABLED`
- `AGENT_MEMORY_LLM_SUMMARY_MODEL`
- `AGENT_MEMORY_LLM_SUMMARY_TRIGGER_MESSAGES`

推荐直接从 `.env.example` 复制一份后再改本机配置。

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 4. 数据库说明

Python 版默认连接自己的 MySQL 库：

```env
MYSQL_DB=jc_sales_agent_py
```

启动时会自动执行数据库引导：

- `DB_BOOTSTRAP_ENABLED=true`
  - 启用启动时建库建表
- `DB_BOOTSTRAP_WITH_SEED=true`
  - 首次启动自动导入演示数据
- `DB_BOOTSTRAP_RESEED=false`
  - 默认不覆盖已有业务数据
- `DB_BOOTSTRAP_FAIL_FAST=true`
  - 初始化失败时直接阻止服务启动

数据库 SQL 文件：

- `app/db/sql/schema.sql`
- `app/db/sql/data.sql`

如果只想手动执行数据库初始化，也可以运行：

```powershell
python -m app.db.bootstrap
```

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 5. 启动方式

开发模式：

```powershell
.\run_dev.ps1
```

或直接启动：

```powershell
uvicorn app.main:app --reload --port 8088
```

服务默认地址：

- `http://127.0.0.1:8088`
- 文档地址：`http://127.0.0.1:8088/docs`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 6. 关键接口

- `GET /health`
- `GET /ops/metrics`
- `POST /auth/login`
- `POST /agent/chat`
- `POST /agent/chat/stream`
- `DELETE /agent/session/{sessionId}`

流式接口 `POST /agent/chat/stream` 当前会输出这些 SSE 事件：

- `status`：阶段性状态，例如“正在读取会话上下文...”“工具结果已返回，继续分析...”
- `token`：模型实时吐出的文本片段
- `artifacts`：图表 artifact JSON
- `done`：本轮结束
- `error`：错误信息

工具测试接口：

- `POST /test/tool/query-orders`
- `POST /test/tool/top-reps`
- `POST /test/tool/region-ranking`
- `POST /test/tool/top-products`
- `POST /test/tool/month-over-month`
- `POST /test/tool/year-over-year`
- `POST /test/tool/monthly-trend`
- `POST /test/tool/line-chart`
- `POST /test/tool/bar-chart`
- `POST /test/tool/pie-chart`
- `POST /test/tool/detect-anomalies`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 7. 记忆与流式相关配置

常用 Agent 配置：

- `AGENT_MAX_TOOL_CALLS`：单轮对话最多允许多少次工具调用
- `AGENT_MEMORY_FOLLOWUP_LIMIT`：追问场景注入模型的最近消息条数
- `AGENT_MEMORY_WINDOW_MESSAGES`：会话窗口保留条数
- `AGENT_MEMORY_LLM_SUMMARY_ENABLED`：是否启用 LLM 历史摘要
- `AGENT_MEMORY_LLM_SUMMARY_MODEL`：摘要专用模型，留空时复用 `OPENAI_MODEL`
- `AGENT_MEMORY_LLM_SUMMARY_TRIGGER_MESSAGES`：更早历史达到多少条后才触发 LLM 摘要
- `AGENT_MEMORY_SUMMARY_MESSAGES`：回退到规则摘要时最多抽取多少条旧消息
- `AGENT_MEMORY_SUMMARY_CHARS`：规则摘要中单条消息的字符上限

建议：

- 如果你更关注响应速度，可以先把 `AGENT_MEMORY_LLM_SUMMARY_ENABLED=false`
- 如果你更关注长会话一致性，保留 LLM summary，并给 `AGENT_MEMORY_LLM_SUMMARY_MODEL` 配一个更快、更便宜的模型

## 8. 验证建议

基础验证：

```powershell
$env:AUTH_ENABLED='false'
py -3.13 -m pytest -q
```

编译检查：

```powershell
py -3.13 -m compileall -q app tests
```

启动后先检查：

```powershell
curl http://127.0.0.1:8088/health
```

如果是第一次启动，还可以确认新库里已经生成以下表：

- `sa_sales_region`
- `sa_sales_rep`
- `sa_product`
- `sa_sales_order`
- `sa_chat_memory`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 9. 当前行为

当前版本默认策略是：

- Python 版使用自己的数据库
- 库不存在时自动创建
- 表不存在时自动创建
- 业务表为空时自动导入演示数据
- 业务表已有数据时不会重复覆盖，除非显式打开 `DB_BOOTSTRAP_RESEED=true`
- 独立问题默认只带当前问题；追问会带最近窗口消息和更早历史摘要
- 更早历史优先走 LLM summary，失败时回退到规则摘要
- `react_agent` 是唯一调用 LLM 的图节点；`react_tool_executor` 只负责执行工具
- 带图表 artifact 的分析型最终回答也会优先走真实流式输出，而不是统一回退到本地切片
