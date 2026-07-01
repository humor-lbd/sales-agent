# Tool -> Service -> Task Type -> SQL 对照表

## 1. 说明

本文档整理 `sales-agent` 项目中 ReAct Agent 可调用的 12 个工具，说明它们在运行时如何映射到：

1. 外层 Tool 名称
2. `SalesTools` 方法
3. `SalesQueryService` 方法
4. `LlmSqlQueryService` 中的 `task_type`
5. LLM 常生成的 SQL 模板

说明：

- 不是每个 Tool 都只对应一个 `task_type`
- 图表工具通常会复用已有查询类任务
- `detect_sales_anomalies` 会拆成多个内部子查询
- 本文的 SQL 模板是“项目当前最常见、最符合校验规则的模板”，不是唯一合法 SQL

相关源码：

- `app/graph/react_tools.py`
- `app/logic/tools.py`
- `app/logic/services.py`
- `app/logic/sql_agent/service.py`
- `app/logic/sql_agent/schema_registry.py`
- `app/logic/sql_agent/prompts.py`

## 2. 总览表

| Tool 名称 | SalesTools 方法 | Service 方法 | task_type | 说明 |
|---|---|---|---|---|
| `query_sales_data` | `query_orders` | `query_orders` | `order_detail` | 查询订单明细 |
| `get_sales_summary` | `get_sales_summary` | `query_total_amount` | `sales_summary` | 查询销售额汇总 |
| `get_top_reps` | `get_top_reps` | `query_rep_ranking` | `rep_ranking` | 查询销售员排名 |
| `get_region_ranking` | `get_region_ranking` | `query_region_ranking` | `region_ranking` | 查询大区排名 |
| `get_top_products` | `get_top_products` | `query_product_ranking` | `product_ranking` | 查询产品排名 |
| `calc_month_over_month` | `calc_month_over_month` | `query_total_amount` | `sales_summary` | 通过两次汇总查询计算环比 |
| `calc_year_over_year` | `calc_year_over_year` | `query_total_amount` | `sales_summary` | 通过两次汇总查询计算同比 |
| `get_monthly_trend` | `get_monthly_trend` | `query_monthly_trend` | `monthly_trend` | 查询月度趋势 |
| `generate_line_chart` | `generate_line_chart` | `query_monthly_trend` | `monthly_trend` | 先查趋势，再生成折线图 |
| `generate_bar_chart` | `generate_bar_chart` | 多个 | 多个 | 按维度复用排名查询 |
| `generate_pie_chart` | `generate_pie_chart` | 多个 | 多个 | 按维度复用排名查询 |
| `detect_sales_anomalies` | `detect_all_anomalies` | 多个 | 多个 | 多子任务组合的异常检测 |

## 3. 明细对照

### 3.1 `query_sales_data`

| 层级 | 内容 |
|---|---|
| Tool | `query_sales_data` |
| `SalesTools` | `query_orders(start_date, end_date, region_name, rep_name, limit)` |
| `SalesQueryService` | `query_orders(rep_id, region_id, start, end)` |
| `LlmSqlQueryService` | `query_orders(...)` |
| `task_type` | `order_detail` |

SQL 模板：

```sql
SELECT o.id,
       o.order_no,
       o.order_date,
       o.rep_id,
       o.customer_name,
       o.amount,
       o.status
FROM sa_sales_order o
LEFT JOIN sa_sales_rep s ON s.id = o.rep_id
LEFT JOIN sa_sales_region r ON r.id = o.region_id
LEFT JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
ORDER BY o.order_date DESC, o.id DESC
LIMIT :limit
```

特点：

- 明细查询不能默认过滤 `COMPLETED`
- 必须保留 `REFUNDED`、`CANCELLED` 等状态
- 必须带 `LIMIT`

---

### 3.2 `get_sales_summary`

| 层级 | 内容 |
|---|---|
| Tool | `get_sales_summary` |
| `SalesTools` | `get_sales_summary(start_date, end_date, region_name)` |
| `SalesQueryService` | `query_total_amount(region_id, start, end)` |
| `LlmSqlQueryService` | `query_total_amount(...)` |
| `task_type` | `sales_summary` |

SQL 模板：

```sql
SELECT SUM(o.amount) AS total_amount
FROM sa_sales_order o
LEFT JOIN sa_sales_rep s ON s.id = o.rep_id
LEFT JOIN sa_sales_region r ON r.id = o.region_id
LEFT JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
```

特点：

- 销售额类查询默认只统计 `COMPLETED`
- 如果用户是销售员/区域经理，后续还会被注入权限过滤

---

### 3.3 `get_top_reps`

| 层级 | 内容 |
|---|---|
| Tool | `get_top_reps` |
| `SalesTools` | `get_top_reps(start_date, end_date, region_name, top_n)` |
| `SalesQueryService` | `query_rep_ranking(start, end, top_n)` |
| `LlmSqlQueryService` | `query_rep_ranking(...)` |
| `task_type` | `rep_ranking` |

SQL 模板：

```sql
SELECT o.rep_id,
       s.name AS rep_name,
       s.region_id AS region_id,
       r.name AS region_name,
       SUM(o.amount) AS total_amount
FROM sa_sales_order o
JOIN sa_sales_rep s ON s.id = o.rep_id
JOIN sa_sales_region r ON r.id = o.region_id
JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
GROUP BY o.rep_id, s.name, s.region_id, r.name
ORDER BY total_amount DESC
LIMIT :top_n
```

---

### 3.4 `get_region_ranking`

| 层级 | 内容 |
|---|---|
| Tool | `get_region_ranking` |
| `SalesTools` | `get_region_ranking(start_date, end_date)` |
| `SalesQueryService` | `query_region_ranking(start, end)` |
| `LlmSqlQueryService` | `query_region_ranking(...)` |
| `task_type` | `region_ranking` |

SQL 模板：

```sql
SELECT o.region_id,
       r.name AS region_name,
       SUM(o.amount) AS total_amount
FROM sa_sales_order o
JOIN sa_sales_rep s ON s.id = o.rep_id
JOIN sa_sales_region r ON r.id = o.region_id
JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
GROUP BY o.region_id, r.name
ORDER BY total_amount DESC
```

---

### 3.5 `get_top_products`

| 层级 | 内容 |
|---|---|
| Tool | `get_top_products` |
| `SalesTools` | `get_top_products(start_date, end_date, top_n, region_name)` |
| `SalesQueryService` | `query_product_ranking(start, end, top_n, region_id)` |
| `LlmSqlQueryService` | `query_product_ranking(...)` |
| `task_type` | `product_ranking` |

SQL 模板：

```sql
SELECT o.product_id,
       p.sku_code AS sku_code,
       p.name AS product_name,
       p.category AS category,
       SUM(o.amount) AS total_amount,
       SUM(o.quantity) AS total_quantity
FROM sa_sales_order o
JOIN sa_sales_rep s ON s.id = o.rep_id
JOIN sa_sales_region r ON r.id = o.region_id
JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
GROUP BY o.product_id, p.sku_code, p.name, p.category
ORDER BY total_amount DESC
LIMIT :top_n
```

---

### 3.6 `calc_month_over_month`

| 层级 | 内容 |
|---|---|
| Tool | `calc_month_over_month` |
| `SalesTools` | `calc_month_over_month(current_start, current_end, prev_start, prev_end, region_name)` |
| `SalesQueryService` | `query_total_amount(region_id, start, end)` |
| `LlmSqlQueryService` | `query_total_amount(...)` |
| `task_type` | `sales_summary` |

说明：

- 该 Tool 不直接对应一条 SQL
- 它会调用两次 `sales_summary`
- 一次查当前周期，一次查对比周期

当前周期 SQL 模板：

```sql
SELECT SUM(o.amount) AS total_amount
FROM sa_sales_order o
LEFT JOIN sa_sales_rep s ON s.id = o.rep_id
LEFT JOIN sa_sales_region r ON r.id = o.region_id
LEFT JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
```

对比周期 SQL 模板相同，只是参数不同。

---

### 3.7 `calc_year_over_year`

| 层级 | 内容 |
|---|---|
| Tool | `calc_year_over_year` |
| `SalesTools` | `calc_year_over_year(start_date, end_date, region_name)` |
| `SalesQueryService` | `query_total_amount(region_id, start, end)` |
| `LlmSqlQueryService` | `query_total_amount(...)` |
| `task_type` | `sales_summary` |

说明：

- 与环比一样
- 它也会做两次 `sales_summary`
- 一次查当前时间段，一次查去年同期

SQL 模板同 `sales_summary`。

---

### 3.8 `get_monthly_trend`

| 层级 | 内容 |
|---|---|
| Tool | `get_monthly_trend` |
| `SalesTools` | `get_monthly_trend(months, region_name)` |
| `SalesQueryService` | `query_monthly_trend(region_id, months)` |
| `LlmSqlQueryService` | `query_monthly_trend(region_id, start, end, months)` |
| `task_type` | `monthly_trend` |

SQL 模板：

```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
       SUM(o.amount) AS total_amount,
       COUNT(*) AS order_count
FROM sa_sales_order o
JOIN sa_sales_rep s ON s.id = o.rep_id
JOIN sa_sales_region r ON r.id = o.region_id
JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
ORDER BY month
```

---

### 3.9 `generate_line_chart`

| 层级 | 内容 |
|---|---|
| Tool | `generate_line_chart` |
| `SalesTools` | `generate_line_chart(months, region_name, title)` |
| `SalesQueryService` | `query_monthly_trend(region_id, months)` |
| `LlmSqlQueryService` | `query_monthly_trend(...)` |
| `task_type` | `monthly_trend` |

说明：

- 先查月度趋势
- 再由 Python 组装 ECharts 折线图

SQL 模板同 `monthly_trend`。

---

### 3.10 `generate_bar_chart`

`generate_bar_chart` 会根据 `dimension` 走不同分支。

#### 3.10.1 `dimension=region`

| 层级 | 内容 |
|---|---|
| Tool | `generate_bar_chart` |
| `SalesTools` | `generate_bar_chart("region", ...)` |
| `SalesQueryService` | `query_region_ranking(start, end)` |
| `task_type` | `region_ranking` |

SQL 模板同 `region_ranking`。

#### 3.10.2 `dimension=rep`

| 层级 | 内容 |
|---|---|
| Tool | `generate_bar_chart` |
| `SalesTools` | `generate_bar_chart("rep", ...)` |
| `SalesQueryService` | `query_rep_ranking(start, end, top_n)` |
| `task_type` | `rep_ranking` |

SQL 模板同 `rep_ranking`。

#### 3.10.3 `dimension=product`

| 层级 | 内容 |
|---|---|
| Tool | `generate_bar_chart` |
| `SalesTools` | `generate_bar_chart("product", ...)` |
| `SalesQueryService` | `query_product_ranking(start, end, top_n)` |
| `task_type` | `product_ranking` |

SQL 模板同 `product_ranking`。

#### 3.10.4 `dimension=category`

| 层级 | 内容 |
|---|---|
| Tool | `generate_bar_chart` |
| `SalesTools` | `generate_bar_chart("category", ...)` |
| `SalesQueryService` | `query_product_ranking(start, end, 100)` |
| `task_type` | `product_ranking` |

说明：

- SQL 层不直接查 category 聚合
- 先查产品排名明细
- 再在 Python 中按 `category` 聚合成柱状图数据

---

### 3.11 `generate_pie_chart`

和柱状图同理，也按 `dimension` 分支。

#### 3.11.1 `dimension=region`

| 层级 | 内容 |
|---|---|
| Tool | `generate_pie_chart` |
| `SalesTools` | `generate_pie_chart("region", ...)` |
| `SalesQueryService` | `query_region_ranking(start, end)` |
| `task_type` | `region_ranking` |

SQL 模板同 `region_ranking`。

#### 3.11.2 `dimension=rep`

| 层级 | 内容 |
|---|---|
| Tool | `generate_pie_chart` |
| `SalesTools` | `generate_pie_chart("rep", ...)` |
| `SalesQueryService` | `query_rep_ranking(start, end, top_n)` |
| `task_type` | `rep_ranking` |

SQL 模板同 `rep_ranking`。

#### 3.11.3 `dimension=product`

| 层级 | 内容 |
|---|---|
| Tool | `generate_pie_chart` |
| `SalesTools` | `generate_pie_chart("product", ...)` |
| `SalesQueryService` | `query_product_ranking(start, end, top_n)` |
| `task_type` | `product_ranking` |

SQL 模板同 `product_ranking`。

#### 3.11.4 `dimension=category`

| 层级 | 内容 |
|---|---|
| Tool | `generate_pie_chart` |
| `SalesTools` | `generate_pie_chart("category", ...)` |
| `SalesQueryService` | `query_product_ranking(start, end, 100)` |
| `task_type` | `product_ranking` |

说明：

- 先查产品明细
- 再在 Python 里按品类聚合为饼图占比

---

### 3.12 `detect_sales_anomalies`

这个 Tool 不是一条查询，而是多个子任务组合。

#### 3.12.1 大区订单量骤降

| 层级 | 内容 |
|---|---|
| Tool | `detect_sales_anomalies` |
| `SalesTools` | `_detect_region_drop()` |
| `SalesQueryService` | `query_order_count(region_id, start, end)` |
| `task_type` | `order_count` |

SQL 模板：

```sql
SELECT COUNT(o.id) AS order_count
FROM sa_sales_order o
JOIN sa_sales_rep s ON s.id = o.rep_id
JOIN sa_sales_region r ON r.id = o.region_id
JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
  AND o.region_id = :region_id
```

#### 3.12.2 产品连续零销售

| 层级 | 内容 |
|---|---|
| Tool | `detect_sales_anomalies` |
| `SalesTools` | `_detect_zero_sale_products()` |
| `SalesQueryService` | `query_last_order_date(product_id)` |
| `task_type` | `last_order_date` |

SQL 模板：

```sql
SELECT MAX(o.order_date) AS last_order_date
FROM sa_sales_order o
WHERE o.product_id = :product_id
  AND o.status = 'COMPLETED'
```

#### 3.12.3 销售员退单率异常

| 层级 | 内容 |
|---|---|
| Tool | `detect_sales_anomalies` |
| `SalesTools` | `_detect_high_refund_reps()` |
| `SalesQueryService` | `query_refund_rates(start, end)` |
| `task_type` | `refund_rates` |

SQL 模板：

```sql
SELECT o.rep_id,
       SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded,
       COUNT(o.id) AS total
FROM sa_sales_order o
LEFT JOIN sa_sales_rep s ON s.id = o.rep_id
LEFT JOIN sa_sales_region r ON r.id = o.region_id
LEFT JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
GROUP BY o.rep_id
```

#### 3.12.4 销售员业绩骤降

| 层级 | 内容 |
|---|---|
| Tool | `detect_sales_anomalies` |
| `SalesTools` | `_detect_rep_performance_drop()` |
| `SalesQueryService` | `sum_amount_by_rep(rep_id, start, end)` |
| `task_type` | `rep_amount` |

SQL 模板：

```sql
SELECT SUM(o.amount) AS total_amount
FROM sa_sales_order o
JOIN sa_sales_rep s ON s.id = o.rep_id
JOIN sa_sales_region r ON r.id = o.region_id
JOIN sa_product p ON p.id = o.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'COMPLETED'
  AND o.rep_id = :rep_id
```

## 4. Schema 白名单完整内容

### 4.1 允许访问的表

- `sa_sales_order`
- `sa_sales_rep`
- `sa_sales_region`
- `sa_product`

### 4.2 固定别名

- `o -> sa_sales_order`
- `s -> sa_sales_rep`
- `r -> sa_sales_region`
- `p -> sa_product`

### 4.3 字段白名单

#### `sa_sales_order`

- `id`
- `order_no`
- `rep_id`
- `product_id`
- `region_id`
- `customer_name`
- `quantity`
- `unit_price`
- `amount`
- `cost`
- `profit`
- `status`
- `order_date`
- `created_at`

#### `sa_sales_rep`

- `id`
- `name`
- `region_id`
- `role`
- `email`
- `created_at`

#### `sa_sales_region`

- `id`
- `name`
- `parent_region_id`
- `created_at`

#### `sa_product`

- `id`
- `sku_code`
- `name`
- `category`
- `unit_price`
- `cost`
- `status`
- `created_at`

### 4.4 固定 join 关系

```sql
JOIN sa_sales_rep s ON s.id = o.rep_id
JOIN sa_sales_region r ON r.id = o.region_id
JOIN sa_product p ON p.id = o.product_id
```

### 4.5 业务口径白名单

- 销售额使用 `SUM(o.amount)`，默认只统计 `o.status = 'COMPLETED'`
- 销售数量使用 `SUM(o.quantity)`，默认只统计 `COMPLETED`
- 订单数默认统计 `COMPLETED`，退款率任务除外
- 月份趋势使用 `DATE_FORMAT(o.order_date, '%Y-%m') AS month`
- 日期范围使用 `o.order_date BETWEEN :start_date AND :end_date`
- 明细查询必须 `ORDER BY o.order_date DESC, o.id DESC` 并带 `LIMIT`

### 4.6 危险限制

不允许：

- `SELECT *`
- 系统库：
  - `mysql.`
  - `information_schema.`
  - `performance_schema.`
  - `sys.`
- 危险关键词：
  - `INSERT`
  - `UPDATE`
  - `DELETE`
  - `DROP`
  - `ALTER`
  - `TRUNCATE`
  - `CREATE`
  - `REPLACE`
  - `GRANT`
  - `REVOKE`
  - `CALL`
  - `EXEC`
  - `LOAD`
  - `OUTFILE`
  - `INFILE`
  - `LOCK`
  - `UNLOCK`
  - `SET`
  - `SHOW`
  - `DESCRIBE`

## 5. 总结

从映射关系上看，这 12 个 Tool 可以分成三类：

1. **直接型**
- `query_sales_data`
- `get_sales_summary`
- `get_top_reps`
- `get_region_ranking`
- `get_top_products`
- `get_monthly_trend`

这一类通常是 Tool -> Service -> 单个 `task_type` -> 单条 SQL

2. **复用型**
- `calc_month_over_month`
- `calc_year_over_year`
- `generate_line_chart`
- `generate_bar_chart`
- `generate_pie_chart`

这一类通常不是独立 `task_type`，而是复用已有查询任务，再由 Python 进行计算或拼装图表

3. **组合型**
- `detect_sales_anomalies`

这一类不是单条 SQL，而是多个 `task_type` 子任务组合完成
