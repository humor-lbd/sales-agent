# LLM SQL 优化设计文档

## 1. 文档目标

本文档用于指导 `sales-agent` 项目中 LLM 生成 SQL 能力的优化设计与分阶段落地，重点解决以下问题：

- 为什么当前 `LLM SQL` 相比写死 SQL / ORM 查询耗时大很多。
- 哪些查询适合继续保留确定性 SQL，哪些查询适合继续使用或改造为 LLM SQL。
- 如何通过缓存、模板化、Prompt 裁剪、批量查询和观测能力，把当前实现从“可用”优化为“可上线灰度”。

本文档不讨论通用 Agent 架构优化，只聚焦 `SQL 生成与执行链路`。

---

## 2. 当前实现概况

### 2.1 当前链路

当前项目中，查询链路为：

`ReAct Agent -> SalesTools -> SalesQueryService -> LlmSqlQueryService -> LlmSqlGenerator -> SqlValidator -> PermissionPolicyInjector -> SqlExecutor -> ResultMapper`

核心代码位置：

- `app/logic/services.py`
- `app/logic/sql_agent/service.py`
- `app/logic/sql_agent/generator.py`
- `app/logic/sql_agent/prompts.py`
- `app/logic/sql_agent/validator.py`
- `app/logic/sql_agent/policy.py`
- `app/logic/sql_agent/executor.py`

### 2.2 当前能力

当前实现已经具备：

- task_type 级任务抽象
- schema 白名单
- 指标口径约束
- SQL 校验
- 权限注入
- fallback 回退
- 测试覆盖

从安全性和结构上看，当前实现已经比“自然语言直连数据库”稳很多。

---

## 3. 当前问题与证据

### 3.1 直接证据

参考报告：

- `docs/12_SQL_MODE_EVALUATION_REPORT.md`

关键结论：

- 总场景：28
- 结果完全一致：26
- LLM SQL 失败：0
- 静态方案总耗时：2468.79 ms
- LLM 方案总耗时：473563.35 ms
- LLM 总 token：108889

### 3.2 结论

当前链路的主要瓶颈不是数据库执行，而是 **LLM 生成 SQL 本身**。

报告中的典型数据说明：

- `get_sales_summary`
  - 平均 LLM 总耗时：4521.21 ms
  - 平均 LLM 生成耗时：4496.18 ms
  - 平均 LLM DB 耗时：22.84 ms

- `get_top_reps`
  - 平均 LLM 总耗时：5745.7 ms
  - 平均 LLM 生成耗时：5724.45 ms
  - 平均 LLM DB 耗时：19.33 ms

- `detect_sales_anomalies`
  - 平均 LLM 总耗时：321108.93 ms
  - 平均 LLM 生成耗时：319514.38 ms
  - 平均 LLM DB 耗时：1394.88 ms

这说明：

1. 数据库执行并不是主要瓶颈。
2. 大部分时间耗在 prompt 组装、模型推理、网络往返、JSON 返回和解析上。
3. 某些工具会多次调用 SQL 生成能力，导致总耗时被放大。

### 3.3 根因总结

当前耗时大的根因主要有五个：

1. **每次任务都重新调用一次 LLM 生成 SQL**
2. **Prompt 过长，schema 和 metric context 对所有 task 都是全量注入**
3. **固定口径查询也在使用 LLM 生成 SQL**
4. **部分工具会拆成多次 SQL 生成调用**
5. **没有 SQL 结构缓存和 task 级模板机制**

---

## 4. 优化目标

### 4.1 目标

优化后的 LLM SQL 能力应满足：

1. 高频固定查询不再依赖每次 LLM 生成
2. 灵活查询保留 LLM 扩展性
3. SQL 生成结果可缓存、可复用、可观测
4. 异常检测等组合型工具避免循环式 LLM SQL 调用
5. 支持灰度、影子模式和快速回退

### 4.2 非目标

本文档不追求：

- 把所有查询都切换到 LLM SQL
- 让 LLM 自由写任意复杂 SQL
- 构建通用 BI 平台级语义查询系统

项目仍以 **业务受控、成本可控、性能可控** 为第一原则。

---

## 5. 总体优化策略

优化采用“分层收缩不确定性”的思路：

1. **先收缩使用范围**
2. **再减少重复生成**
3. **再把固定任务模板化**
4. **最后只把真正需要灵活性的任务交给 LLM**

一句话概括：

> 让 LLM 从“每次都写 SQL”变成“只在必要时选 SQL 结构或选模板”。

---

## 6. 优化方案设计

## 6.1 方案一：按 operation 白名单启用 LLM SQL

### 设计目的

不要全量为所有工具启用 LLM SQL，只对适合的任务开放。

### 当前问题

当前 `SalesQueryService._maybe_llm_sql()` 是“只要开关打开，就尽量让所有查询走 LLM SQL”。

这会导致：

- `sales_summary`
- `monthly_trend`
- `mom`
- `yoy`
- `line_chart`
- `detect_sales_anomalies`

这类固定查询也被迫付出模型调用成本。

### 优化方案

新增 `LLM_SQL_ALLOWED_OPERATIONS` 配置，例如：

```env
LLM_SQL_ALLOWED_OPERATIONS=query_rep_ranking,query_region_ranking,query_product_ranking
```

由 `SalesQueryService` 在进入 `_maybe_llm_sql()` 前判断当前操作是否允许走 LLM SQL。

### 推荐启用范围

第一阶段仅允许：

- `query_rep_ranking`
- `query_region_ranking`
- `query_product_ranking`

明确不启用：

- `query_total_amount`
- `query_monthly_trend`
- `calc_month_over_month`
- `calc_year_over_year`
- `sum_amount_by_rep`
- `query_order_count`
- `query_last_order_date`
- `query_refund_rates`

### 预期收益

- 立刻减少 60% 以上的 LLM 生成次数
- 明显压低 token 消耗
- 先把最稳定、最灵活的几个场景做深

---

## 6.2 方案二：SQL 结构缓存

### 设计目的

同类 task 的 SQL 结构通常稳定，不应该每次都重新生成。

### 缓存粒度

以 **task signature** 为 key，缓存 `validated_sql`。

建议 key 组成：

- `task_type`
- `tool_name`
- `scope.role`
- `result_contract`
- 是否包含 `region_id`
- 是否包含 `rep_id`
- 是否包含 `product_id`
- `order_by`
- 是否含 `top_n`
- 是否含 `limit`

注意：

- `start_date/end_date` 不应进入结构缓存 key
- 因为日期只影响参数，不影响 SQL 模板结构

### 缓存值

缓存内容建议包含：

```json
{
  "sql": "SELECT ... WHERE o.order_date BETWEEN :start_date AND :end_date ...",
  "result_columns": ["..."],
  "task_type": "rep_ranking",
  "version": "v1"
}
```

### 存储位置

优先级：

1. 进程内内存缓存
2. Redis 分布式缓存

建议同时支持两层：

- 本地 LRU：低延迟
- Redis：服务重启后仍可复用

### 落地点

建议新增：

- `app/logic/sql_agent/cache.py`

由 `LlmSqlQueryService._generate_valid_sql()` 先查缓存：

1. 命中：直接执行校验后的 SQL 模板
2. 未命中：走 LLM 生成，再写缓存

### 预期收益

对高频任务，二次调用后几乎可以把 LLM 生成耗时降为 0。

---

## 6.3 方案三：Prompt 裁剪

### 当前问题

当前 prompt 对所有 task 注入的是“全量 schema + 全量 metric context + 当前任务”。

这会导致：

- token 偏大
- 生成时间偏长
- 与当前任务无关的信息干扰模型

### 优化方向

#### 1. 按 task 裁剪 schema

例如：

- `sales_summary`
  - 只需要 `sa_sales_order.amount/status/order_date/region_id/rep_id`

- `monthly_trend`
  - 只需要 `order_date/amount/status`

- `rep_ranking`
  - 再额外加 `sa_sales_rep.name/region_id`

不要每次把 `product`、`region`、`rep` 全字段都给模型。

#### 2. 按 task 裁剪 metric context

例如：

- `sales_summary` 只给 `SUM(o.amount)` 口径
- `monthly_trend` 只给 `DATE_FORMAT` 规则
- `refund_rates` 只给退款率聚合规则

#### 3. 使用 task-specific prompt

对常见固定任务提供短 prompt，例如：

- `SUMMARY_PROMPT`
- `TREND_PROMPT`
- `RANKING_PROMPT`
- `ANOMALY_PROMPT`

这样可以显著缩短 prompt 长度。

### 预期收益

- 平均 token 降低 20%~40%
- 降低生成延迟
- 降低误生成概率

---

## 6.4 方案四：模板化 SQL，LLM 只做模板选择

### 设计目的

把“自由写 SQL”收敛成“选择模板 + 补充结构参数”。

### 思路

让 LLM 输出：

```json
{
  "template_id": "product_ranking_v1",
  "filters": ["date_range", "region_scope"],
  "sort": "total_amount_desc",
  "limit": 5
}
```

再由应用代码拼出最终 SQL。

### 适合模板化的 task

- `sales_summary`
- `rep_ranking`
- `region_ranking`
- `product_ranking`
- `monthly_trend`
- `order_count`
- `last_order_date`
- `refund_rates`
- `rep_amount`

### 好处

- 性能远优于自由生成 SQL
- 安全性更高
- SQL 更稳定
- validator 简化
- 更适合生产

### 代价

- 需要维护模板注册表
- 灵活性稍弱于完全自由 SQL

### 推荐

这是本项目中长期最优方案。

---

## 6.5 方案五：异常检测改为批量聚合 SQL

### 当前问题

`detect_sales_anomalies` 当前是组合型工具，而且内部有循环：

- 对每个 region 查订单量
- 对每个 product 查最后出单时间
- 对每个 rep 查销售额对比

如果这些内部查询都走 LLM SQL，就会变成“多次生成 SQL + 多次执行”。

### 优化方向

把循环查询改成批量聚合查询：

#### 1. 大区订单量骤降

一条 SQL 返回所有 region 的近 2 周、前 4 周统计。

#### 2. 连续零销售产品

一条 SQL：

```sql
SELECT product_id, MAX(order_date) AS last_order_date
FROM sa_sales_order
WHERE status = 'COMPLETED'
GROUP BY product_id
```

#### 3. 销售员业绩骤降

一条 SQL 返回所有 rep 的两个周期销售额。

#### 4. 退款率

保持单条聚合 SQL。

### 结果

异常检测不再适合自由 LLM SQL，应该回到：

- 固定批量 SQL
- 或模板化 SQL

### 预期收益

把当前 300 秒级别下降到秒级甚至亚秒级。

---

## 6.6 方案六：减少或关闭 repair 重试

### 当前问题

当前 `llm_sql_repair_attempts` 配置允许生成失败后再次让 LLM 修 SQL。

对固定 task 来说，如果第一次就不稳定，问题通常不在“需要多试一次”，而在：

- prompt 太宽
- task 不适合自由生成
- 缺乏模板化

### 建议

- 高频 task：`repair_attempts = 0`
- 中低频灵活 task：`repair_attempts = 1`

不要依赖多轮修复来解决结构问题。

---

## 6.7 方案七：增加 SQL 生成和执行观测

### 目标

让系统能够回答这些问题：

- 哪个 task 最慢
- 哪个 tool 最耗 token
- 哪个 task 缓存命中率最低
- 哪个 task fallback 最多
- 哪个 task validator 失败最多

### 建议新增指标

- `llmSql.cacheHit`
- `llmSql.cacheMiss`
- `llmSql.generated.totalTokens`
- `llmSql.generated.promptTokens`
- `llmSql.generated.completionTokens`
- `llmSql.generated.durationMs`
- `llmSql.db.durationMs`
- `llmSql.taskType.{name}.count`

### 建议新增日志字段

- `request_id`
- `tool_name`
- `task_type`
- `sql_signature`
- `cache_hit`
- `prompt_tokens`
- `completion_tokens`
- `generation_ms`
- `db_ms`
- `fallback_used`

---

## 7. 推荐的最终分层方案

## 7.1 保持写死 SQL / ORM

这些建议长期保留确定性实现：

- `get_sales_summary`
- `get_monthly_trend`
- `calc_month_over_month`
- `calc_year_over_year`
- `generate_line_chart`
- `detect_sales_anomalies`

原因：

- 口径固定
- 结果可预测
- 性能收益最明显
- 用 LLM 只是额外增加推理成本

## 7.2 可继续使用 LLM SQL 或模板化

这些建议优先改造成“缓存 + 模板化”的 LLM SQL：

- `get_top_reps`
- `get_region_ranking`
- `get_top_products`

原因：

- 结果一致性高
- 维度扩展性强
- 后续最可能继续增加过滤条件、排序规则和组合维度

## 7.3 谨慎对待的场景

- `query_sales_data`

原因：

- 目前结果口径已有偏差
- 明细类查询容易出现 `LIMIT`、分页、排序、总数口径不一致
- 更适合受控模板，而不是自由生成 SQL

---

## 8. 分阶段实施计划

## Phase 1：收缩范围

目标：

- 固定查询退出 LLM 主链路
- 只保留 ranking 类 task

改动：

- `SalesQueryService` 加 operation 白名单
- 只让 `query_rep_ranking / query_region_ranking / query_product_ranking` 走 LLM SQL

## Phase 2：加缓存

目标：

- 同类 task 第二次不再重新生成 SQL

改动：

- 新增 `cache.py`
- 增加进程内缓存
- 可选增加 Redis 缓存

## Phase 3：Prompt 裁剪

目标：

- 降 token
- 降平均生成时间

改动：

- `schema_registry.py` 支持按 task 输出局部 schema
- `prompts.py` 支持 task-specific prompt

## Phase 4：模板化

目标：

- 把高频 task 从自由 SQL 收敛为模板选择

改动：

- 新增 `template_registry.py`
- 新增模板拼装逻辑
- generator 支持输出 `template_id`

## Phase 5：异常检测重构

目标：

- 批量聚合取代循环式多次 LLM 生成

改动：

- `tools.py`
- `services.py`
- 对应 repository / SQL 模板

---

## 9. 代码改造清单

建议新增或修改：

### 新增

- `app/logic/sql_agent/cache.py`
- `app/logic/sql_agent/template_registry.py`
- `app/logic/sql_agent/template_builder.py`

### 修改

- `app/logic/services.py`
  - 增加 operation 白名单判断

- `app/logic/sql_agent/service.py`
  - 增加缓存命中逻辑
  - 生成前查缓存
  - 生成后写缓存

- `app/logic/sql_agent/prompts.py`
  - 增加 task-specific prompt

- `app/logic/sql_agent/schema_registry.py`
  - 支持按 task 输出裁剪 schema

- `app/core/config.py`
  - 增加新配置项

- `app/core/metrics.py`
  - 增加缓存和 token 指标

- `app/logic/tools.py`
  - 重构异常检测查询方式

---

## 10. 配置项设计

建议新增：

```env
LLM_SQL_ALLOWED_OPERATIONS=query_rep_ranking,query_region_ranking,query_product_ranking
LLM_SQL_CACHE_ENABLED=true
LLM_SQL_CACHE_TTL_SECONDS=3600
LLM_SQL_CACHE_BACKEND=memory
LLM_SQL_TEMPLATE_MODE=false
LLM_SQL_PROMPT_PROFILE=compact
```

可选：

```env
LLM_SQL_CACHE_BACKEND=redis
```

---

## 11. 测试方案

### 11.1 单元测试

覆盖：

- task signature 生成
- 缓存命中 / miss
- 模板选择
- prompt 裁剪结果
- operation 白名单分流

### 11.2 对比测试

复用：

- `scripts/compare_sql_modes_full.py`

新增验证项：

- cache hit 后的耗时下降比例
- token 消耗下降比例
- 结果一致率是否保持

### 11.3 性能测试

建议关注：

- `get_top_reps`
- `get_region_ranking`
- `get_top_products`
- `detect_sales_anomalies`

指标：

- P50 / P95 响应时间
- 平均 token
- fallback 率
- cache hit 率

---

## 12. 风险与回退

### 风险

1. 缓存 key 设计不当，导致不同场景复用错误 SQL
2. 模板化过早收紧，导致灵活性下降
3. 异常检测重构后结果口径变化

### 回退策略

- 保留 `LLM_SQL_ENABLED`
- 保留 `LLM_SQL_SHADOW_MODE`
- 保留 `LLM_SQL_USE_FALLBACK`
- 模板模式通过 `LLM_SQL_TEMPLATE_MODE=false` 快速关闭

---

## 13. 最终建议

本项目不应继续沿着“所有查询都自由生成 SQL”的方向推进。

推荐路线是：

1. **先缩范围**
2. **再加缓存**
3. **再做模板化**
4. **最后只保留少量真正需要灵活性的 LLM SQL 场景**

最适合优先优化的 3 个 tool：

- `get_top_reps`
- `get_region_ranking`
- `get_top_products`

最适合立即退出 LLM 主链路的 3 类场景：

- 固定汇总类
- 固定趋势类
- 异常检测类

一句话结论：

> 对这个项目来说，最优解不是“让 LLM 更频繁地写 SQL”，而是“让 LLM 更少出手，但在该出手的时候足够受控、足够快、足够可观测”。  
