# AI 应用开发面试题库（基于本项目）｜问题-答案一一对应

本文以本仓库的 `sales-agent` 项目为背景，整理“资深 AI 应用开发工程师”面试中高频追问点，并提供可直接复述的参考回答。每个问题都尽量落到本项目的真实实现细节（包含关键文件位置），便于面试时讲得具体、有证据。

---

## 1. 你用一句话讲清楚这个项目做什么？为什么需要它？

**答：**这是一个“面向销售管理的自然语言数据分析助手”。用户用聊天的方式提问（例如“近 6 个月趋势”“华东区本月销售额”“Top 销售员/产品”），后端通过 Agent 编排把问题转成结构化查询（MySQL/Redis）并输出可读的分析结论和可视化图表（ECharts option），同时支持同步与流式（SSE）两种交互体验。后端入口在 [app/main.py](file:///e:/develop/python_code/project/sales-agent/app/main.py) 和 [app/api/routes.py](file:///e:/develop/python_code/project/sales-agent/app/api/routes.py)，前端在 [frontend/src](file:///e:/develop/python_code/project/sales-agent/frontend/src)。

---

## 2. 你用 3 分钟画一张架构图会怎么画？数据流怎么走？

**答：**我会画 5 块：前端（Vue）→ 后端 API（FastAPI）→ 业务服务（Service/Tools）→ 数据层（SQLAlchemy/MySQL + Redis）→ Agent 编排（LangGraph + LLM）。

一次请求的典型链路是：

1) 前端调用 `/agent/chat` 或 `/agent/chat/stream`（axios 注入 Bearer token）：[frontend/src/api/index.js](file:///e:/develop/python_code/project/sales-agent/frontend/src/api/index.js)  
2) FastAPI 路由拿到 `current_user`（鉴权启用时）并构建 `SalesAgent`： [app/api/routes.py](file:///e:/develop/python_code/project/sales-agent/app/api/routes.py)  
3) `SalesAgent` 调用 LangGraph 工作流： [app/logic/agent.py](file:///e:/develop/python_code/project/sales-agent/app/logic/agent.py)  
4) 工作流里由 ReAct 节点决定是否调用工具（query / ranking / chart）：[app/graph/nodes/react_agent.py](file:///e:/develop/python_code/project/sales-agent/app/graph/nodes/react_agent.py)  
5) 工具调用落到 `SalesTools`，再调用 `SalesQueryService`，最终由仓库层执行 SQL 查询，并可走 Redis 缓存：  
   - 工具层：[app/logic/tools.py](file:///e:/develop/python_code/project/sales-agent/app/logic/tools.py)  
   - 服务层：[app/logic/services.py](file:///e:/develop/python_code/project/sales-agent/app/logic/services.py)  
   - 仓库层：[app/db/repositories.py](file:///e:/develop/python_code/project/sales-agent/app/db/repositories.py)  
6) 结果被组织成文本 +（可选）图表 artifact（ECharts option）返回给前端展示。

---

## 3. 为什么选 Agent（LangGraph/ReAct）而不是纯接口 + 报表？

**答：**核心差异是“用户表达不结构化、问题组合多、需要多步推理”。用 Agent 的收益在于：

- 问题表达自然：用户不需要知道指标口径或 API 参数；模型负责把“自然语言”映射到工具参数。
- 可组合：趋势 + 汇总 + 排行 + 异常检测可以在一次对话里按需组合调用，不用预先写死报表页面。
- 可控：LangGraph 的节点化结构让我们能把 guardrails、工具执行、错误处理、流式输出做成稳定流程（而不是散落在业务里）。

本项目的 ReAct 工具注册在 [app/graph/react_tools.py](file:///e:/develop/python_code/project/sales-agent/app/graph/react_tools.py)，工具实现集中在 [app/logic/tools.py](file:///e:/develop/python_code/project/sales-agent/app/logic/tools.py)。

---

## 4. 你怎么避免模型“乱调用工具”或“死循环调用”？

**答：**我会从“约束 + 保护 + 可观测”三方面：

1) **约束**：在 settings 里提供最大工具调用次数（`AGENT_MAX_TOOL_CALLS`），并在工作流执行逻辑里做上限控制（本项目通过配置注入到 Agent/Graph 执行上下文）：[app/core/config.py](file:///e:/develop/python_code/project/sales-agent/app/core/config.py) 与 [app/logic/agent.py](file:///e:/develop/python_code/project/sales-agent/app/logic/agent.py)  
2) **保护**：工具层对输入做强校验（日期解析、topN 边界、区域名称合法性等），即使模型传错参数也会返回稳定错误文案而不是异常崩溃：例如 [app/logic/tools.py](file:///e:/develop/python_code/project/sales-agent/app/logic/tools.py) 中对区域、topN 的校验逻辑  
3) **可观测**：把每轮模型输出、每次工具调用以及工具结果记录为 trace（便于快速定位“为什么它会这么调”）：见 [app/graph/middleware.py](file:///e:/develop/python_code/project/sales-agent/app/graph/middleware.py) 与 [app/graph/trace.py](file:///e:/develop/python_code/project/sales-agent/app/graph/trace.py)

---

## 5. 这个项目的权限模型是什么？权限控制点在哪里？

**答：**权限模型是角色驱动的“数据范围收口”：

- SALES_REP：只能看自己（rep_id）
- SALES_MANAGER：只能看自己大区（region_id）
- SALES_DIRECTOR：默认可看全局

控制点不在前端传参，而是在服务层强制覆盖查询条件（防止前端/用户传参越权）：

- 订单明细查询按角色改写 `rep_id/region_id`：[SalesQueryService.query_orders](file:///e:/develop/python_code/project/sales-agent/app/logic/services.py#L97-L117)
- 销售员排行在结果集层面做过滤：[SalesQueryService.query_rep_ranking](file:///e:/develop/python_code/project/sales-agent/app/logic/services.py#L154-L205)

鉴权启用由 `AUTH_ENABLED` 控制；JWT 的签发/解析与 `Depends(get_login_user)` 注入在 [app/core/security.py](file:///e:/develop/python_code/project/sales-agent/app/core/security.py) 与 [app/api/routes.py](file:///e:/develop/python_code/project/sales-agent/app/api/routes.py)。

---

## 6. 现在的登录为什么只用 rep_id？如果上线你会怎么改？

**答：**当前是演示/内网 demo 形态：`/auth/login` 只输入销售员 `rep_id` 就能拿到 JWT（便于快速体验）。上线我会做三类增强：

1) **身份认证要素**：接入企业 SSO/LDAP/OIDC 或至少增加密码/短信/邮箱验证，杜绝“知道 rep_id 就能冒用”。  
2) **防枚举与风控**：对登录接口做限流、失败次数封禁、验证码、人机校验；记录审计日志。  
3) **token 治理**：支持 token 失效（黑名单/版本号）、密钥轮换、设备维度会话管理。

本项目当前登录实现可参考 [app/api/routes.py:/auth/login](file:///e:/develop/python_code/project/sales-agent/app/api/routes.py#L100-L112)。

---

## 7. 你们的“流式输出”是怎么实现的？为什么不用 WebSocket？

**答：**本项目用 SSE（`text/event-stream`）实现流式输出：后端不断 `yield` 事件片段，前端持续消费。优势是：

- SSE 更轻量，浏览器原生友好，穿透代理相对容易；
- 单向流（服务端推送）足够满足“token/状态/附件”的场景；
- 与 HTTP 认证、负载均衡兼容性更好。

实现位置：

- 路由：[/agent/chat/stream](file:///e:/develop/python_code/project/sales-agent/app/api/routes.py#L145-L182) 使用 `StreamingResponse`
- 事件格式化：`format_sse()`：[routes.py](file:///e:/develop/python_code/project/sales-agent/app/api/routes.py#L46-L56)
- Agent 侧把图、token、done 等事件统一输出：[app/logic/agent.py](file:///e:/develop/python_code/project/sales-agent/app/logic/agent.py)

如果后续需要双向（客户端中断、动态调参、多人协同），再升级 WebSocket 更合适。

---

## 8. 你如何避免“模型编造数据”？哪些环节保证结果可信？

**答：**我会明确“数据结论必须来源于工具查询”，并让模型在需要数值/明细时强制走工具：

- 工具输出中直接包含订单号、金额、日期等可核验字段（明细可追溯）：`query_orders` 输出包含订单号/日期/销售员/客户/金额/状态：[app/logic/tools.py](file:///e:/develop/python_code/project/sales-agent/app/logic/tools.py)
- 汇总、排行、趋势等都由 SQL/仓库层产出，再由工具层格式化：
  - 汇总：`query_total_amount` → `get_sales_summary`
  - 排行：`find_rep_ranking`/`query_rep_ranking` → `get_top_reps`

同时用 guardrails 节点/错误兜底限制“胡说的最终答案”，实现上可追踪工作流节点：[app/graph/nodes/guardrails.py](file:///e:/develop/python_code/project/sales-agent/app/graph/nodes/guardrails.py) 与 [app/graph/helpers.py](file:///e:/develop/python_code/project/sales-agent/app/graph/helpers.py)。

---

## 9. 你们为什么用 Redis？缓存 key 怎么设计避免“串权限”？

**答：**Redis 主要用于减少重复聚合的成本（比如固定周期的排行/汇总），提升响应速度并降低 DB 压力。关键是缓存 key 必须包含“权限范围”。

本项目在 `query_total_amount` 中采用 `key_scope=rep:<id> / region:<id> / all` 组合到 cache key，避免不同角色/不同大区共享同一份缓存造成越权：[SalesQueryService.query_total_amount](file:///e:/develop/python_code/project/sales-agent/app/logic/services.py)。

上线场景我还会补充：

- 对“权限敏感/细粒度”的查询谨慎缓存或缩短 TTL；
- 增加缓存命中率与回源耗时指标；
- Redis 故障降级（直接回源 DB）与熔断策略。

---

## 10. 你如何做可观测性？出了问题怎么定位？

**答：**我会把观测分成三层：HTTP、数据库、Agent/LLM。

- HTTP：中间件记录每次请求耗时、状态码，并汇总到 runtime metrics：[app/core/logging.py](file:///e:/develop/python_code/project/sales-agent/app/core/logging.py)
- DB：SQLAlchemy event hook 记录查询耗时：[app/db/database.py](file:///e:/develop/python_code/project/sales-agent/app/db/database.py)
- Agent：记录每轮模型输出、工具调用入参/出参、首 token 等，便于还原“它为什么这么答”：见 [app/graph/middleware.py](file:///e:/develop/python_code/project/sales-agent/app/graph/middleware.py)

如果线上出现“回答不对/慢/卡住”，我会按以下顺序定位：请求耗时 → DB 耗时 → 工具链路 → 模型调用 → 是否重试/限流/报错。

---

## 11. 你们的测试怎么做？怎么 mock 大模型？

**答：**我会强调“把 LLM 当外部依赖”，单测不依赖真实模型服务：

- API 层：用 FakeAgent/FakeTools 替换真实 build 逻辑验证接口结构：[tests/test_api.py](file:///e:/develop/python_code/project/sales-agent/tests/test_api.py)
- 工具层：FakeService 固定返回值，验证输出文本/图表结构稳定：[tests/test_tools.py](file:///e:/develop/python_code/project/sales-agent/tests/test_tools.py)
- Graph/Agent：用可控的消息与工具返回验证执行流程与最终答案拼接：[tests/test_agent.py](file:///e:/develop/python_code/project/sales-agent/tests/test_agent.py)

这样能保证 CI 环境不需要 OPENAI_KEY/外网也能跑通大部分回归。

---

## 12. 本项目哪里用了异步？同步/异步混用会有什么风险？

**答：**后端运行在 ASGI 模型里（FastAPI/uvicorn），但多数业务函数是同步实现；异步主要体现在：

- HTTP 中间件与异常处理器是 `async def`（`await call_next`）：[app/core/logging.py](file:///e:/develop/python_code/project/sales-agent/app/core/logging.py)、[app/core/exceptions.py](file:///e:/develop/python_code/project/sales-agent/app/core/exceptions.py)
- 应用生命周期 `lifespan` 是 `async def`：[app/main.py](file:///e:/develop/python_code/project/sales-agent/app/main.py#L24-L49)
- SSE 流式响应通过异步框架持续推送事件：[app/api/routes.py](file:///e:/develop/python_code/project/sales-agent/app/api/routes.py#L145-L182)

风险在于：DB/Redis/部分 SDK 仍是同步客户端，如果在事件循环中直接执行，会阻塞。FastAPI 会把同步路由放线程池降低影响，但在高并发下可能出现线程池耗尽/延迟抖动。优化方向包括：异步驱动、批处理、缓存、队列化、或拆分耗时链路。

---

## 13. 你如何把这个 demo 升级成可上线系统？优先级怎么排？

**答：**我会按“安全可靠 > 成本可控 > 体验增强”排优先级：

1) **认证与权限加固**：接入真实认证体系；登录防枚举；审计与告警；token 治理。  
2) **稳定性与可观测**：完善 trace/metrics（含模型侧指标、失败重试/熔断）；完善降级策略（模型不可用时的 fallback）。  
3) **成本控制**：按用户/角色/租户做配额；缓存更精细；对高成本问题做路由（小模型优先，必要时升级大模型）。  

本项目已经具备一定基础：有 metrics、DB query timing、Agent trace、SSE 事件流、缓存入口与可开关配置。

