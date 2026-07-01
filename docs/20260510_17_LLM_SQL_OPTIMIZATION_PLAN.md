# LLM SQL 生成模块优化方案

## Context

sales-agent 项目的 LLM SQL 生成管道有 7 个 task_type，但只有 3 个硬编码模板（rep_ranking、region_ranking、product_ranking）。其余 4 个 task_type（sales_summary、monthly_trend、refund_rates、order_detail）每次都调用 LLM 生成 SQL，耗时 4-5 秒且消耗 token。此外，生成器每次调用都新建 LLM 实例、模板有不必要的 JOIN、执行器无超时保护、JSON 解析无容错等问题也需要修复。

**目标：** 优化 LLM SQL 生成性能和正确性，并通过基准脚本对比优化前后的耗时和正确性。

---

## Phase 0: 基准脚本（先测量"优化前"基线）

**创建文件：** `scripts/benchmark_sql_optimization.py`

复用 `scripts/compare_sql_modes_full.py` 中的 `SqlCapture`、`CapturingGenerator`、`CapturingExecutor` 等组件，新建一个专项基准脚本：

- 支持 `--phase before|after` 参数标记运行阶段
- 对 7 个 task_type 分别运行 template 路径和 generator 路径，各跑 3 轮取 min/avg/max
- 捕获指标：generation_ms、total_ms、prompt_tokens、completion_tokens、validation_pass/fail、result_hash
- 输出到 `logs/benchmark_{phase}_{timestamp}.json`
- 支持 `--compare` 模式读取两个 JSON 文件生成对比表

**运行：** `python scripts/benchmark_sql_optimization.py --phase before`

---

## Phase 1: P0 — 补全模板（最高收益）

**修改文件：** `app/logic/sql_agent/template_registry.py`

在 `_templates` 字典中新增 3 个模板：

### sales_summary 模板
```sql
SELECT COALESCE(SUM(o.amount), 0) AS total_amount
FROM sa_sales_order o
WHERE o.status = 'COMPLETED'
AND o.order_date BETWEEN :start_date AND :end_date
```
- 无需 JOIN，result_columns=["total_amount"]

### monthly_trend 模板
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
       SUM(o.amount) AS total_amount,
       COUNT(o.id) AS order_count
FROM sa_sales_order o
WHERE o.status = 'COMPLETED'
AND o.order_date BETWEEN :start_date AND :end_date
GROUP BY month
ORDER BY month
```
- 无需 JOIN，result_columns=["month", "total_amount", "order_count"]

### refund_rates 模板
```sql
SELECT o.rep_id,
       SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded,
       COUNT(o.id) AS total
FROM sa_sales_order o
WHERE o.order_date BETWEEN :start_date AND :end_date
GROUP BY o.rep_id
```
- 无需 JOIN，不过滤 COMPLETED（refund_rates 不在 `sales_metric_tasks` 集合中，不会触发 validator 的 COMPLETED 检查）
- result_columns=["rep_id", "refunded", "total"]

**预期效果：** 6/7 个 task_type 走模板，消除 LLM 调用。sales_summary 从 ~4358ms 降至 <10ms，monthly_trend 从 ~5101ms 降至 <10ms。

**新建测试：** `tests/test_llm_sql_templates.py`
- 3 个 match 测试（模板能匹配对应 task_type）
- 3 个 validate 测试（模板 SQL 通过 SqlValidator 校验）
- 3 个 service 集成测试（确认不调用 generator）

---

## Phase 2: P0 — SQL 执行超时保护

**修改文件：** `app/logic/sql_agent/executor.py`

- `__init__` 新增 `timeout_seconds` 参数（默认 5）
- `execute()` 方法在执行查询前设置 `SET SESSION MAX_EXECUTION_TIME = {ms}`
- 新增 `explain_validate()` 方法用于可选的 EXPLAIN 预检

**修改文件：** `app/logic/sql_agent/service.py`
- `__init__` 中将 `settings.llm_sql_timeout_seconds` 传给 SqlExecutor

**修改测试：** `tests/test_llm_sql_service.py`
- 新增 2 个测试验证超时设置和 EXPLAIN 方法

---

## Phase 3: P1 — Generator LLM 实例缓存

**修改文件：** `app/logic/sql_agent/generator.py`

- 新增 `_llm` 和 `_llm_model_name` 实例属性
- 新增 `_get_llm()` 方法：如果 `_llm` 为 None 或 model_name 变化则新建，否则复用
- `generate()` 中将 `build_chat_model(...)` 替换为 `self._get_llm()`

**新建测试：** `tests/test_llm_sql_generator.py`
- 验证两次 generate() 调用复用同一 LLM 实例

---

## Phase 4: P1 — 去除模板中不必要的 JOIN

**修改文件：** `app/logic/sql_agent/template_registry.py`

| 模板 | 当前 JOIN | 优化后 JOIN |
|------|-----------|-------------|
| rep_ranking | sa_sales_rep + sa_sales_region + sa_product | sa_sales_rep + sa_sales_region（去掉 sa_product） |
| region_ranking | sa_sales_rep + sa_sales_region + sa_product | sa_sales_region（去掉 sa_sales_rep 和 sa_product） |
| product_ranking | sa_sales_rep + sa_sales_region + sa_product | sa_product（去掉 sa_sales_rep 和 sa_sales_region） |

**验证：** 现有测试 `test_llm_sql_service_uses_ranking_template_without_generator` 断言 SQL 中包含 `SUM(o.amount) AS total_amount`，新 SQL 仍满足。运行全部现有测试确认无回归。

---

## Phase 5: P1 — Generator JSON 解析容错

**修改文件：** `app/logic/sql_agent/generator.py`

将第 92-93 行的裸 `json.loads()` + `model_validate()` 包裹在 try/except 中：
- `JSONDecodeError` → 抛出 `RuntimeError`，附带 LLM 返回内容前 200 字符
- `ValidationError` → 抛出 `RuntimeError`，附带 payload 和错误详情

**修改测试：** `tests/test_llm_sql_generator.py`
- 2 个测试：畸形 JSON、缺失字段

---

## Phase 6: P2 — 内存缓存容量限制

**修改文件：** `app/logic/sql_agent/cache.py`

- `__init__` 新增 `max_memory_entries` 参数（默认 256）
- `set()` 方法插入前检查容量，先清理过期条目，仍满则淘汰最早过期的条目
- 新增 `_evict_expired()` 辅助方法

**新建测试：** `tests/test_llm_sql_cache.py`
- 2 个测试：满容量淘汰、过期优先清理

---

## Phase 7: P2 — Repair 循环区分可修复/不可修复错误

**修改文件：** `app/logic/sql_agent/service.py`

- 定义 `_UNREPAIRABLE_PATTERNS` 元组（"危险关键词"、"未授权表"、"不允许查询系统库"、"SQL 不能为空"、"不允许包含分号"）
- 新增 `_is_repairable()` 静态方法
- repair 循环中遇到不可修复错误立即抛出，不重试

**修改测试：** `tests/test_llm_sql_service.py`
- 2 个测试：不可修复错误立即失败、可修复错误正常重试

---

## Phase 8: P3 — 状态检查改用精确正则

**修改文件：** `app/logic/sql_agent/validator.py`

将第 118-120 行的 `"completed" not in lower` 替换为：
```python
has_completed_filter = bool(re.search(
    r"o\.status\s*=\s*['\"]?completed['\"]?", sql, re.IGNORECASE
))
```

**修改测试：** `tests/test_llm_sql_validator.py`
- 1 个测试：别名中包含 "completed" 但无实际 status 过滤时应拒绝

---

## Phase 9: 提取公共工具函数

**新建文件：** `app/logic/sql_agent/utils.py`

提取 `content_to_text()` 函数，消除 4 处重复定义：
- `app/logic/sql_agent/generator.py`
- `app/graph/nodes/react_agent.py`
- `app/graph/nodes/memory.py`
- `scripts/compare_sql_modes_full.py`

---

## Phase 10: 运行"优化后"基准并对比

1. `python scripts/benchmark_sql_optimization.py --phase after`
2. `python scripts/benchmark_sql_optimization.py --compare logs/benchmark_before_*.json logs/benchmark_after_*.json`

**预期对比结果：**

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 模板命中率 | 3/7 task_type | 6/7 task_type |
| sales_summary 耗时 | ~4358ms | <10ms |
| monthly_trend 耗时 | ~5101ms | <10ms |
| refund_rates 耗时 | ~4000ms+ | <10ms |
| LLM token 消耗 | 每次调用消耗 token | 仅 order_detail 消耗 token |
| 结果正确性 | 基线 | 与基线一致 |

---

## 实施顺序

```
Phase 0: 基准脚本 + 测量 before 基线
    ↓
Phase 1 + Phase 2: 并行（P0 模板 + P0 超时）
    ↓
Phase 3 + Phase 4 + Phase 5: 并行（P1 优化）
    ↓
Phase 6 + Phase 7 + Phase 8: 并行（P2/P3 优化）
    ↓
Phase 9: 提取公共函数
    ↓
Phase 10: 运行 after 基准 + 对比报告
```

## 关键文件清单

| 文件 | 操作 |
|------|------|
| `scripts/benchmark_sql_optimization.py` | 新建 |
| `app/logic/sql_agent/template_registry.py` | 修改（新增 3 模板 + 优化 3 模板 JOIN） |
| `app/logic/sql_agent/executor.py` | 修改（加超时） |
| `app/logic/sql_agent/generator.py` | 修改（LLM 缓存 + JSON 容错） |
| `app/logic/sql_agent/service.py` | 修改（repair 循环 + 超时传参） |
| `app/logic/sql_agent/validator.py` | 修改（正则改进） |
| `app/logic/sql_agent/cache.py` | 修改（容量限制） |
| `app/logic/sql_agent/utils.py` | 新建 |
| `tests/test_llm_sql_templates.py` | 新建 |
| `tests/test_llm_sql_generator.py` | 新建 |
| `tests/test_llm_sql_cache.py` | 新建 |
| `tests/test_llm_sql_service.py` | 修改 |
| `tests/test_llm_sql_validator.py` | 修改 |

## 验证方式

1. **单元测试：** `py -3.13 -m pytest tests/test_llm_sql_* -q` 全部通过
2. **基准对比：** 运行 Phase 10 的对比脚本，确认模板命中率提升、耗时下降、结果一致
3. **回归测试：** `py -3.13 -m pytest -q` 全量测试无失败
