# LLM SQL 全链路演进：从写死 SQL 到优化后的 LLM SQL（面试专用）

> 本文档覆盖 sales-agent 项目中 SQL 查询的完整演进过程，适合面试时按阶段讲解。

---

## 目录

1. [项目一句话介绍](#1-项目一句话介绍)
2. [第一阶段：写死 SQL / ORM 查询](#2-第一阶段写死-sql--orm-查询)
3. [第二阶段：引入 LLM 生成 SQL](#3-第二阶段引入-llm-生成-sql)
4. [第三阶段：LLM SQL 优化](#4-第三阶段llm-sql-优化)
5. [三阶段对比数据](#5-三阶段对比数据)
6. [核心架构设计决策](#6-核心架构设计决策)
7. [安全与权限体系](#7-安全与权限体系)
8. [面试高频追问与参考回答](#8-面试高频追问与参考回答)
9. [关键代码位置速查](#9-关键代码位置速查)

---

## 1. 项目一句话介绍

> 这是一个面向销售管理的自然语言数据分析助手。用户用聊天提问（如"近 6 个月趋势""华东区本月销售额""Top 销售员"），后端通过 ReAct Agent 编排，把问题转成结构化 MySQL 查询，返回可读分析结论和 ECharts 可视化图表。核心挑战之一是：如何让 SQL 查询既灵活又可控、既快速又安全。

---

## 2. 第一阶段：写死 SQL / ORM 查询

### 2.1 架构

```
用户 → ReAct Agent → SalesTools → SalesQueryService → SalesOrderRepository → SQLAlchemy ORM → MySQL
```

- Agent（LangGraph ReAct）负责理解用户意图、选择工具
- 工具层 (`app/logic/tools.py`) 负责参数校验和结果格式化
- 服务层 (`app/logic/services.py`) 负责权限过滤和缓存
- 仓储层 (`app/db/repositories.py`) 用 SQLAlchemy 写死查询逻辑

### 2.2 典型代码

```python
# repositories.py - 写死的 ORM 查询
stmt = select(func.coalesce(func.sum(SalesOrder.amount), 0)).where(
    SalesOrder.status == "COMPLETED",
    SalesOrder.order_date.between(start, end),
)
```

### 2.3 优点

| 维度 | 表现 |
| --- | --- |
| 性能 | 最快，28 场景总耗时 ~2469ms |
| 成本 | 0 token，不调用 LLM |
| 稳定性 | SQL 结构固定，结果 100% 可预测 |
| 排障 | 最简单，只看代码和数据库 |

### 2.4 痛点

| 问题 | 具体表现 |
| --- | --- |
| 扩展成本高 | 每新增一个维度/过滤/聚合，都要改 Repository / Service / Tool |
| 查询模板散落 | ranking / summary / trend 查询本质相似，但散落成多个手写逻辑 |
| 不支持灵活分析 | 用户问"按品类+大区+时间组合查询"时，需要新增大量代码 |
| 难以统一治理 | 权限、模板、审计分散在各处 |

### 2.5 12 个工具的查询方式

| 工具 | 类型 | 查询方式 |
| --- | --- | --- |
| `query_sales_data` | 直接型 | ORM 查询订单表 |
| `get_sales_summary` | 直接型 | `SUM(amount)` |
| `get_top_reps` | 直接型 | JOIN + GROUP BY + ORDER BY |
| `get_region_ranking` | 直接型 | JOIN + GROUP BY |
| `get_top_products` | 直接型 | JOIN + GROUP BY |
| `get_monthly_trend` | 直接型 | `DATE_FORMAT` + GROUP BY |
| `calc_month_over_month` | 复用型 | 两次 `get_sales_summary` + Python 计算增长率 |
| `calc_year_over_year` | 复用型 | 两次 `get_sales_summary` + Python 计算 |
| `generate_line_chart` | 复用型 | 复用 `get_monthly_trend` + ECharts |
| `generate_bar_chart` | 复用型 | 复用 ranking 查询 + ECharts |
| `generate_pie_chart` | 复用型 | 复用 ranking 查询 + ECharts |
| `detect_sales_anomalies` | 组合型 | 多个子查询 + 业务规则判断 |

---

## 3. 第二阶段：引入 LLM 生成 SQL

### 3.1 为什么引入

1. **灵活性需求**：用户问法越来越多样，纯写死 SQL 维护成本线性增长
2. **统一治理**：希望在 SQL 生成层统一处理权限、校验、审计
3. **可扩展性**：ranking 类查询维度组合多（region/rep/product/category），写死方案会指数膨胀

### 3.2 核心设计原则

> LLM 只负责生成候选 SQL；系统负责 schema 约束、权限注入、安全校验、执行控制、结果映射和失败回退。

### 3.3 两层 LLM 分工

| LLM 层 | 职责 | 是否直接访问数据库 |
| --- | --- | --- |
| ReAct LLM | 理解用户问题，决定调用哪个工具，判断工具结果是否够用 | 否 |
| SQL LLM | 根据工具意图、参数、受限 schema 生成 SQL JSON | 否，只生成 SQL 文本 |

**关键设计**：SQL LLM 不直接接收"无限制自然语言问题"，而是由工具先把参数解析成结构化任务 (`SqlTaskSpec`)，再交给 SQL LLM。

### 3.4 查询链路

```
react_agent → react_tool_executor → SalesTools → SalesQueryService
  → LlmSqlQueryService
    → SqlTaskSpec（结构化任务）
    → SqlSchemaRegistry（白名单 schema）
    → LlmSqlGenerator（调 LLM 生成 SQL JSON）
    → SqlValidator（安全校验）
    → PermissionPolicyInjector（权限注入）
    → SqlExecutor（参数化执行）
    → ResultMapper（rows → DTO）
  → 格式化结果
→ react_agent 判断是否继续调用工具
```

### 3.5 安全体系（5 层防护）

```
第 1 层：Schema 白名单
  - 只允许 4 张表：sa_sales_order, sa_sales_rep, sa_sales_region, sa_product
  - 每张表字段白名单
  - 固定别名：o, s, r, p

第 2 层：SQL 校验器 (SqlValidator)
  - 只允许 SELECT / WITH ... SELECT
  - 禁止分号、注释、SELECT *
  - 禁止危险关键词：INSERT/UPDATE/DELETE/DROP/ALTER 等 20+ 个
  - 禁止系统库：mysql/information_schema/performance_schema
  - 表名白名单校验
  - 字段白名单校验
  - 业务口径校验：销售额必须过滤 o.status = 'COMPLETED'
  - result_contract 校验：必须返回约定列

第 3 层：权限注入 (PermissionPolicyInjector)
  - SALES_REP → 注入 o.rep_id = :scope_rep_id
  - SALES_MANAGER → 注入 o.region_id = :scope_region_id
  - SALES_DIRECTOR → 不注入额外条件
  - 权限由后端强制注入，不由 LLM 推断

第 4 层：执行保护
  - 命名参数绑定（:start_date），禁止拼接用户输入
  - MAX_EXECUTION_TIME 超时保护（默认 5 秒）
  - 最大返回行数限制（默认 200 行）

第 5 层：失败回退
  - LLM SQL 失败时自动回退到写死 SQL
  - 配置开关：LLM_SQL_ENABLED, LLM_SQL_USE_FALLBACK
  - 影子模式：LLM_SQL_SHADOW_MODE 只对比不使用
```

### 3.6 数据模型

```python
class SqlTaskSpec(BaseModel):
    """结构化查询任务 - 来自工具参数，不直接等于用户原始输入"""
    tool_name: str          # "get_top_reps"
    task_type: str          # "rep_ranking"
    start_date: date | None
    end_date: date | None
    region_id: int | None
    rep_id: int | None
    top_n: int | None
    scope: QueryScope       # 来自后端鉴权，不由 LLM 推断
    result_contract: list[str]  # 约束必须返回哪些列

class GeneratedSql(BaseModel):
    """LLM 生成的 SQL 结构"""
    sql: str
    params: dict[str, Any]  # 命名参数
    result_columns: list[str]
```

### 3.7 引入后的效果（优化前 LLM SQL）

28 场景实测数据（2026-05-08）：

| 指标 | 写死 SQL | LLM SQL（优化前） | 差距 |
| --- | --- | --- | --- |
| 总耗时 | 2,469 ms | 473,563 ms | LLM 慢 192 倍 |
| 总 token | 0 | 108,889 | — |
| 结果一致率 | — | 26/28 (93%) | — |
| LLM SQL 失败 | — | 0 | — |

**瓶颈分析**：DB 执行只占 ~2%，98% 的时间花在 LLM 生成 SQL 上。

典型数据：

| 工具 | LLM 平均耗时 | LLM 生成耗时 | DB 所占 |
| --- | --- | --- | --- |
| `get_sales_summary` | 4,521 ms | 4,496 ms | 0.6% |
| `get_top_reps` | 5,746 ms | 5,724 ms | 0.4% |
| `detect_sales_anomalies` | 321,109 ms | 319,514 ms | 0.5% |

---

## 4. 第三阶段：LLM SQL 优化

### 4.1 优化思路

> 不是让 LLM 更频繁地写 SQL，而是让 LLM 更少出手，但在该出手的时候足够受控、足够快、足够可观测。

核心策略：**分层收缩不确定性**

```
1. 先收缩使用范围（白名单分流）
2. 再减少重复生成（SQL 结构缓存）
3. 再把固定任务模板化（模板注册表）
4. 最后只把真正需要灵活性的任务交给 LLM
```

### 4.2 优化项清单（10 项）

| 序号 | 优化项 | 优先级 | 文件 | 效果 |
| --- | --- | --- | --- | --- |
| 1 | 补全 3 个 SQL 模板 | P0 | `template_registry.py` | 6/7 task_type 走模板 |
| 2 | 去除模板中不必要的 JOIN | P0 | `template_registry.py` | 减少 DB 查询开销 |
| 3 | SQL 执行超时保护 | P0 | `executor.py` | 防止慢查询拖垮 DB |
| 4 | Generator LLM 实例缓存 | P1 | `generator.py` | 避免每次新建实例 |
| 5 | Generator JSON 解析容错 | P1 | `generator.py` | 更好的错误信息 |
| 6 | 内存缓存容量限制 | P2 | `cache.py` | 防止 OOM |
| 7 | Repair 循环区分可修复/不可修复 | P2 | `service.py` | 节省无意义重试 |
| 8 | 状态检查精确正则 | P3 | `validator.py` | 避免误匹配 |
| 9 | 基准对比脚本 | P0 | `benchmark_sql_optimization.py` | 量化优化效果 |
| 10 | Prompt 裁剪（按 task 裁剪 schema） | P1 | `prompts.py` | 降低 token |

### 4.3 优化一：补全 SQL 模板（最高收益）

**问题**：7 个 task_type 只有 3 个有模板（rep_ranking, region_ranking, product_ranking），其余 4 个每次都调 LLM。

**解决**：新增 3 个模板。

#### sales_summary 模板

```sql
SELECT COALESCE(SUM(o.amount), 0) AS total_amount
FROM sa_sales_order o
WHERE o.status = 'COMPLETED'
  AND o.order_date BETWEEN :start_date AND :end_date
```

#### monthly_trend 模板

```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
       SUM(o.amount) AS total_amount,
       COUNT(o.id) AS order_count
FROM sa_sales_order o
WHERE o.status = 'COMPLETED'
  AND o.order_date BETWEEN :start_date AND :end_date
GROUP BY month ORDER BY month
```

#### refund_rates 模板

```sql
SELECT o.rep_id,
       SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded,
       COUNT(o.id) AS total
FROM sa_sales_order o
WHERE o.order_date BETWEEN :start_date AND :end_date
GROUP BY o.rep_id
```

**效果**：模板命中率从 43%（3/7）提升到 86%（6/7）。

### 4.4 优化二：去除模板中不必要的 JOIN

| 模板 | 优化前 JOIN | 优化后 JOIN | 减少 |
| --- | --- | --- | --- |
| rep_ranking | rep + region + product | rep + region | -product |
| region_ranking | rep + region + product | region | -rep, -product |
| product_ranking | rep + region + product | product | -rep, -region |

### 4.5 优化三：SQL 执行超时保护

```python
def execute(self, sql, params):
    self.db.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {self.timeout_seconds * 1000}"))
    rows = self.db.execute(text(sql), params).mappings().all()
    return [dict(row) for row in rows[:self.max_rows]]
```

### 4.6 优化四：Generator LLM 实例缓存

```python
def _get_llm(self):
    """避免每次 generate 都新建 LLM 实例"""
    model_name = self.settings.llm_sql_model or self.settings.openai_model
    if self._llm is None or self._llm_model_name != model_name:
        self._llm = build_chat_model(self.settings, ...)
        self._llm_model_name = model_name
    return self._llm
```

### 4.7 优化五：Repair 循环智能重试

```python
_UNREPAIRABLE_PATTERNS = (
    "危险关键词", "未授权表", "不允许查询系统库", "SQL 不能为空", "不允许包含分号",
)

@staticmethod
def _is_repairable(errors):
    """不可修复错误（如 DROP TABLE）立即抛出，不浪费重试次数"""
    return not any(
        any(pattern in error for pattern in _UNREPAIRABLE_PATTERNS)
        for error in errors
    )
```

### 4.8 三级解析策略

```
Level 1: 模板注册表 (template_registry)
  → 精确匹配 task_type，直接返回受控 SQL
  → 耗时：<10ms，token：0

Level 2: SQL 结构缓存 (template_cache)
  → 相同 task signature 命中缓存
  → 耗时：<5ms，token：0

Level 3: LLM 生成器 (generator)
  → 调用 LLM 生成 SQL，经过校验后缓存
  → 耗时：3000-7000ms，token：~900
  → 仅 order_detail 等灵活查询走此路径
```

---

## 5. 三阶段对比数据

### 5.1 总体指标

| 指标 | 第一阶段（写死 SQL） | 第二阶段（LLM SQL 优化前） | 第三阶段（LLM SQL 优化后） |
| --- | --- | --- | --- |
| 总场景 | 28 | 28 | 28 |
| 总耗时 | 2,469 ms | 473,563 ms | ~8,000 ms（预估） |
| 总 token | 0 | 108,889 | ~2,910（预估） |
| 模板覆盖率 | — | 43%（3/7 task_type） | 86%（6/7 task_type） |
| 结果一致率 | 基线 | 93%（26/28） | 93%+（与优化前一致） |

### 5.2 优化后 LLM SQL vs 写死 SQL

| 维度 | 写死 SQL | 优化后 LLM SQL |
| --- | --- | --- |
| 性能 | 最快（~2.5s） | 接近（~8s，模板路径 <10ms） |
| 成本 | 0 token | ~2,910 token（仅 order_detail） |
| 灵活性 | 低，需改代码 | 高，LLM 可生成新 SQL |
| 可治理性 | 分散 | 统一 schema/权限/审计 |
| 安全性 | 依赖代码审查 | 5 层自动化防护 |

### 5.3 各 tool 优化前后对比

| Tool | 优化前 LLM 平均(ms) | 优化后预期(ms) | 优化前 token | 优化后 token |
| --- | --- | --- | --- | --- |
| `get_sales_summary` | 4,359 | **<10** | 854 | **0** |
| `get_monthly_trend` | 5,102 | **<10** | 908 | **0** |
| `detect_sales_anomalies` | 5,355 | **<10** | 942 | **0** |
| `get_top_reps` | 37 | ~37 | 0 | 0 |
| `get_region_ranking` | 162 | ~27 | 0 | 0 |
| `get_top_products` | 29 | ~29 | 0 | 0 |
| `query_sales_data` | 7,438 | ~7,438 | 970 | ~970 |

### 5.4 优化后的命中分布（28 场景）

| 模式 | 场景数 | 说明 |
| --- | --- | --- |
| `template` | ~22 | 直接命中 SQL 模板，不调用模型 |
| `generator` | ~3 | 仅 order_detail 走 LLM |
| `generator+cache` | ~2 | 首次生成，后续命中缓存 |
| `bypass` | ~1 | 直接走写死 SQL |

---

## 6. 核心架构设计决策

### 6.1 为什么选 ReAct Agent 而不是纯接口 + 报表

| 维度 | 纯接口 + 报表 | ReAct Agent |
| --- | --- | --- |
| 用户表达 | 必须结构化 | 自然语言 |
| 问题组合 | 预定义报表 | 动态组合 |
| 扩展成本 | 每个报表单独开发 | Agent 自动组合工具 |
| 适合场景 | 固定 BI | 灵活分析 |

### 6.2 为什么不全用 LLM SQL，也不全用写死 SQL

**纯写死 SQL 的问题**：
- 扩展新分析需求需要持续改代码
- 查询模板越堆越多
- 对开放式分析支持差

**纯 LLM SQL 的问题**：
- 固定查询浪费 token 和时间
- 生成结果不稳定
- 安全风险更高

**混合方案的收益**：
- 写死 SQL：负责稳定、高频、固定口径查询
- 模板 SQL：负责高频稳定但希望统一治理的聚合类查询
- LLM SQL：负责真正需要灵活性的分析查询

### 6.3 为什么不直接用 Text-to-SQL

| 维度 | Text-to-SQL（自然语言→SQL） | 本项目方案 |
| --- | --- | --- |
| 输入 | 自由自然语言 | 结构化 SqlTaskSpec |
| Schema | 全量暴露 | 白名单裁剪 |
| 权限 | 依赖 LLM 自觉 | 后端强制注入 |
| 校验 | 事后校验 | 5 层防护 |
| 结果 | 不确定 | result_contract 约束 |

### 6.4 SQL 生成 Prompt 设计

```
System: 你是 MySQL SQL 生成器，只能生成只读 SELECT，使用命名参数...
User:
  数据库方言：MySQL 8
  允许访问的表、字段、join 关系：{schema_context}
  业务指标口径：{metric_context}
  当前查询任务：{task_spec_json}
  返回 JSON：{sql, params, result_columns, reason, confidence}
```

关键设计：
- `task_spec_json` 来自工具参数，不是用户原始输入
- `schema_context` 按 task_type 裁剪，不是全量 schema
- `metric_context` 包含业务口径（如"销售额只统计 COMPLETED"）
- 输出强制 JSON 格式

---

## 7. 安全与权限体系

### 7.1 权限模型

| 角色 | 数据范围 | 注入方式 |
| --- | --- | --- |
| SALES_REP | 只能看自己的数据 | 注入 `o.rep_id = :scope_rep_id` |
| SALES_MANAGER | 只能看自己大区 | 注入 `o.region_id = :scope_region_id` |
| SALES_DIRECTOR | 可看全公司 | 不注入额外条件 |

**关键设计**：权限由后端强制注入，不由 LLM 推断，也不由前端传参。

### 7.2 灰度迁移策略

```
阶段 0：LLM_SQL_ENABLED=false（只开发，不启用）
阶段 1：LLM_SQL_SHADOW_MODE=true（影子模式，只对比不使用）
阶段 2：低风险聚合查询启用（get_sales_summary, get_region_ranking, get_top_products）
阶段 3：明细查询启用（query_sales_data，额外要求 LIMIT）
阶段 4：同比/环比/图表启用
阶段 5：异常检测局部启用
```

### 7.3 回退机制

- 配置开关：`LLM_SQL_ENABLED=false` 立即回退
- 失败回退：`LLM_SQL_USE_FALLBACK=true` 时自动回退写死 SQL
- 影子模式：`LLM_SQL_SHADOW_MODE=true` 只对比不使用

---

## 8. 面试高频追问与参考回答

### Q1: 你为什么要在项目里引入 LLM 生成 SQL？

> 因为项目有 12 个查询工具，ranking 类（销售员/大区/产品排名）的维度组合越来越多。如果每种组合都写死 SQL，代码会指数膨胀。引入 LLM SQL 后，ranking 类查询可以灵活组合维度，同时通过模板化把高频固定查询（汇总、趋势、退单率）的成本降下来。最终效果是：模板命中率 86%，token 消耗降低 75%，模板路径延迟 <10ms。

### Q2: LLM 生成 SQL 安全吗？你怎么保证不会出问题？

> 我做了 5 层防护：Schema 白名单 → SQL 校验器 → 权限注入 → 执行保护 → 失败回退。具体来说：
> - 只允许访问 4 张业务表，字段级白名单
> - 校验器禁止 20+ 危险关键词、禁止 SELECT *、禁止系统库
> - 权限由后端强制注入（SALES_REP 只能看自己数据），不依赖 LLM 自觉
> - 执行前设置 MAX_EXECUTION_TIME 超时，最大返回 200 行
> - 失败时自动回退到写死 SQL，用户无感知

### Q3: 你优化的核心思路是什么？

> 核心思路是"分层收缩不确定性"。不是优化 prompt 让 LLM 写得更好，而是从架构上减少 LLM 出场次数：
> 1. 补全 3 个高频模板（sales_summary, monthly_trend, refund_rates），模板命中率从 43% 到 86%
> 2. 去除模板中不必要的 JOIN，减少 DB 开销
> 3. SQL 结构缓存，相同任务不重复生成
> 4. Repair 循环区分可修复/不可修复错误，避免无意义重试

### Q4: 模板 SQL 和写死 SQL 有什么区别？

> 写死 SQL 直接硬编码在 Repository 里，改起来要动代码。模板 SQL 是注册在 `SqlTemplateRegistry` 里的受控 SQL，它走的是 LlmSqlQueryService 的统一链路（校验 → 权限注入 → 执行），享受统一的安全和审计能力。换句话说，模板 SQL 吸收了写死 SQL 的稳定性，同时保留了统一治理能力。

### Q5: 你怎么处理 LLM 生成 SQL 失败的情况？

> 三层处理：
> 1. **Repair 重试**：校验失败后，把错误信息反馈给 LLM 让它修正，最多重试 1 次
> 2. **不可修复错误立即抛出**：如危险关键词、未授权表等，不浪费重试次数
> 3. **Fallback 回退**：LLM SQL 整体失败时，自动回退到写死 SQL，用户无感知

### Q6: 这个项目最终是 LLM SQL 好还是写死 SQL 好？

> 这不是一个二选一的问题。最终结论是：混合方案最优。
> - 写死 SQL 负责稳定、高频、固定口径查询（汇总、趋势、环比）
> - 模板 SQL 负责高频稳定但需要统一治理的聚合查询（ranking 类）
> - LLM SQL 负责真正需要灵活性的分析查询（order_detail）
>
> 如果项目目标只是固定 BI 查询，纯写死 SQL 是最优选择。但如果希望系统具备扩展能力，混合分层方案更合理。

### Q7: 你怎么做可观测性？

> 结构化审计日志，每次 SQL 查询记录：
> - `source`：template / cache / generator（SQL 从哪来）
> - `generation_ms`：LLM 生成耗时
> - `execution_ms`：DB 执行耗时
> - `prompt_tokens / completion_tokens`：token 消耗
> - `row_count`：返回行数
> - `task_signature`：缓存签名
>
> 还有基准对比脚本 (`benchmark_sql_optimization.py`)，可以量化对比优化前后的效果。

### Q8: 这个项目用了哪些技术栈？

> - **Agent 框架**：LangGraph（ReAct 模式）
> - **LLM**：OpenAI GPT（通过 LangChain）
> - **后端**：FastAPI + SQLAlchemy + MySQL
> - **缓存**：Redis（可选）+ 内存 LRU
> - **前端**：Vue.js + ECharts
> - **流式输出**：SSE（Server-Sent Events）
> - **配置管理**：Pydantic BaseSettings + .env

### Q9: 如果面试官问"你在这个项目中最大的技术挑战是什么"？

> 最大的技术挑战是：如何让 LLM 生成 SQL 既灵活又安全。
>
> 灵活性和安全性本质上是矛盾的——越自由的 SQL 生成越危险，越严格的限制越不灵活。我的解决方案是"分层治理"：
> - 对高频固定查询，用模板消除 LLM 调用
> - 对灵活查询，用 5 层安全体系（白名单/校验/权限/超时/回退）控制风险
> - 对 LLM 输出，用 result_contract 强制列名，用命名参数防注入
>
> 最终把 LLM SQL 从"能工作"优化成了"有边界、可治理、可观测、适合落地"的版本。

### Q10: 如果让你继续优化，你会怎么做？

> 按优先级：
> 1. 把 `order_detail` 也做成模板（目前唯一走 generator 的 task_type）
> 2. Prompt 裁剪：按 task_type 只给相关的 schema 和指标口径，进一步降低 token
> 3. 把 SQL 审计日志接入独立观测系统（如 ELK/Prometheus）
> 4. 支持 SQL 注入防护升级：用 sqlglot 做 AST 级校验，替代正则

---

## 9. 关键代码位置速查

| 模块 | 文件 | 核心类/函数 |
| --- | --- | --- |
| Agent 图定义 | `app/graph/builder.py` | LangGraph workflow |
| ReAct 节点 | `app/graph/nodes/react_agent.py` | 决定调用哪个工具 |
| 工具执行 | `app/graph/nodes/react_tool_executor.py` | 执行 tool_calls |
| 工具定义 | `app/graph/react_tools.py` | 12 个工具的 schema |
| 工具实现 | `app/logic/tools.py` | SalesTools |
| 业务服务 | `app/logic/services.py` | SalesQueryService |
| SQL 生成入口 | `app/logic/sql_agent/service.py` | LlmSqlQueryService |
| SQL 生成器 | `app/logic/sql_agent/generator.py` | LlmSqlGenerator |
| SQL 校验器 | `app/logic/sql_agent/validator.py` | SqlValidator |
| 权限注入 | `app/logic/sql_agent/policy.py` | PermissionPolicyInjector |
| SQL 执行器 | `app/logic/sql_agent/executor.py` | SqlExecutor |
| Schema 白名单 | `app/logic/sql_agent/schema_registry.py` | SqlSchemaRegistry |
| 模板注册表 | `app/logic/sql_agent/template_registry.py` | SqlTemplateRegistry |
| SQL 缓存 | `app/logic/sql_agent/cache.py` | SqlTemplateCache |
| Prompt 定义 | `app/logic/sql_agent/prompts.py` | SQL_GENERATION_SYSTEM_PROMPT |
| 数据模型 | `app/logic/sql_agent/models.py` | SqlTaskSpec, GeneratedSql |
| 结果映射 | `app/logic/sql_agent/result_mapper.py` | map_order_rows 等 |
| 配置 | `app/core/config.py` | Settings (15+ llm_sql_* 字段) |
| 指标 | `app/core/metrics.py` | runtime_metrics |
| 基准脚本 | `scripts/benchmark_sql_optimization.py` | before/after 对比 |
| 评估脚本 | `scripts/compare_sql_modes_full.py` | 28 场景全量对比 |

---

## 附录：一张图总结演进

```
第一阶段（写死 SQL）
  优点：快、稳、0 成本
  痛点：扩展难、维护散

      ↓ 引入 LLM SQL

第二阶段（LLM SQL 优化前）
  优点：灵活、统一治理
  痛点：慢（473s）、贵（10.9 万 token）

      ↓ 分层优化

第三阶段（LLM SQL 优化后）
  模板覆盖：43% → 86%
  LLM 调用：4 个 task_type → 1 个
  耗时：473s → ~8s（预估）
  token：10.9 万 → ~0.3 万（预估）

  最终形态：
    template（6/7 task_type）→ <10ms, 0 token
    cache（命中时）→ <5ms, 0 token
    generator（仅 order_detail）→ ~7s, ~970 token
```
