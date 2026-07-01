# 写死 SQL vs LLM 生成 SQL 评估报告

## 运行范围

- 运行日期：2026-05-08
- 覆盖角色：销售总监、区域经理、普通销售员
- 覆盖 tool：12 个 tool 全量覆盖
- 图表类额外覆盖维度分支：region / rep / product / category
- 对比内容：SQL 文本、最终结果、工具总耗时、数据库耗时、LLM/static token 消耗、LLM命中形态（bypass/template/cache/generator）

## 总体结论

- 总场景数：28
- 结果完全一致：26
- LLM SQL 失败：0
- 写死 SQL 失败：0
- 静态方案总耗时：3838.4 ms
- LLM 方案总耗时：71160.57 ms
- 静态总 token：0（写死 SQL 不调用模型）
- LLM 总 token：11748（prompt 9054 / completion 2694 / reasoning 0）

> 说明：SQL 文本不同是正常现象。写死方案通常是多条小查询加 Python 拼装，LLM SQL 更常生成一条带 JOIN / GROUP BY 的 SQL。这里更看重结果一致性、权限范围和成本。

## 场景覆盖清单

| 角色 | tool | 业务场景 | 结果一致 | 静态耗时(ms) | LLM耗时(ms) | LLM模式 | 命中情况 | 静态token | LLM总token |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 销售总监 | query_sales_data | 全公司订单明细 | 否 | 1268.46 | 9771.94 | generator | template=0, cache=0, generator=1 | 0 | 960 |
| 销售总监 | get_sales_summary | 全公司销售额汇总 | 是 | 43.0 | 4019.49 | generator | template=0, cache=0, generator=1 | 0 | 843 |
| 销售总监 | get_top_reps | 全公司销售员排名 | 是 | 107.6 | 36.3 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | get_region_ranking | 全公司大区排名 | 是 | 55.94 | 26.45 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | get_top_products | 全公司产品 Top5 | 是 | 51.63 | 25.21 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | calc_month_over_month | 全公司环比 | 是 | 49.16 | 4183.97 | generator+cache | template=0, cache=1, generator=1 | 0 | 844 |
| 销售总监 | calc_year_over_year | 全公司同比 | 是 | 60.32 | 4034.78 | generator+cache | template=0, cache=1, generator=1 | 0 | 843 |
| 销售总监 | get_monthly_trend | 全公司 6 个月趋势 | 是 | 37.25 | 4925.73 | generator | template=0, cache=0, generator=1 | 0 | 898 |
| 销售总监 | generate_line_chart | 趋势折线图 | 是 | 34.68 | 5788.24 | generator | template=0, cache=0, generator=1 | 0 | 918 |
| 销售总监 | generate_bar_chart | 大区柱状图 | 是 | 66.35 | 37.36 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | generate_bar_chart | 销售员柱状图 | 是 | 110.08 | 35.98 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | generate_bar_chart | 产品柱状图 | 是 | 66.19 | 37.71 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | generate_bar_chart | 品类柱状图 | 是 | 73.66 | 38.31 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | generate_pie_chart | 大区饼图 | 是 | 61.71 | 32.49 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | generate_pie_chart | 销售员饼图 | 是 | 107.77 | 35.08 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | generate_pie_chart | 产品饼图 | 是 | 68.68 | 37.36 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | generate_pie_chart | 品类饼图 | 是 | 76.02 | 39.25 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 销售总监 | detect_sales_anomalies | 异常检测 | 是 | 627.91 | 5354.59 | generator | template=0, cache=0, generator=1 | 0 | 942 |
| 区域经理 | get_sales_summary | 区域销售额汇总 | 是 | 42.5 | 4336.04 | generator | template=0, cache=0, generator=1 | 0 | 854 |
| 区域经理 | query_sales_data | 区域订单明细 | 是 | 325.05 | 6477.41 | generator | template=0, cache=0, generator=1 | 0 | 970 |
| 区域经理 | get_top_reps | 区域销售员排名 | 是 | 94.09 | 35.78 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 区域经理 | get_top_products | 区域产品 Top5 | 是 | 67.12 | 33.1 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 区域经理 | generate_line_chart | 区域趋势折线图 | 是 | 31.58 | 5417.8 | generator | template=0, cache=0, generator=1 | 0 | 912 |
| 普通销售员 | get_sales_summary | 个人销售额汇总 | 是 | 36.66 | 4720.0 | generator | template=0, cache=0, generator=1 | 0 | 866 |
| 普通销售员 | query_sales_data | 个人订单明细 | 是 | 115.13 | 6065.61 | generator | template=0, cache=0, generator=1 | 0 | 981 |
| 普通销售员 | get_top_reps | 个人排名视角 | 是 | 71.77 | 39.26 | template | template=1, cache=0, generator=0 | 0 | 0 |
| 普通销售员 | get_region_ranking | 大区排名权限 | 是 | 53.83 | 297.19 | bypass | bypass | 0 | 0 |
| 普通销售员 | get_monthly_trend | 个人趋势 | 否 | 34.26 | 5278.14 | generator | template=0, cache=0, generator=1 | 0 | 917 |

## 按 Tool 聚合

| Tool | 场景数 | 一致率 | 平均静态耗时(ms) | 平均LLM耗时(ms) | 平均静态DB耗时(ms) | 平均LLM生成耗时(ms) | 平均LLMDB耗时(ms) | bypass次 | template次 | cache次 | generator次 | 平均静态token | 平均LLM总token |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calc_month_over_month | 1 | 100% | 49.16 | 4183.97 | 47.44 | 4116.91 | 64.83 | 0 | 0 | 1 | 1 | 0 | 844.0 |
| calc_year_over_year | 1 | 100% | 60.32 | 4034.78 | 58.74 | 3960.36 | 72.43 | 0 | 0 | 1 | 1 | 0 | 843.0 |
| detect_sales_anomalies | 1 | 100% | 627.91 | 5354.59 | 614.7 | 4976.54 | 36.47 | 0 | 0 | 0 | 1 | 0 | 942.0 |
| generate_bar_chart | 4 | 100% | 79.07 | 37.34 | 76.85 | 0.0 | 36.38 | 0 | 4 | 0 | 0 | 0 | 0.0 |
| generate_line_chart | 2 | 100% | 33.13 | 5603.02 | 31.36 | 5566.38 | 34.67 | 0 | 0 | 0 | 2 | 0 | 915.0 |
| generate_pie_chart | 4 | 100% | 78.55 | 36.05 | 76.64 | 0.0 | 35.11 | 0 | 4 | 0 | 0 | 0 | 0.0 |
| get_monthly_trend | 2 | 50% | 35.75 | 5101.93 | 33.94 | 5064.67 | 35.59 | 0 | 0 | 0 | 2 | 0 | 907.5 |
| get_region_ranking | 2 | 100% | 54.88 | 161.82 | 52.98 | 0.0 | 12.82 | 1 | 1 | 0 | 0 | 0 | 0.0 |
| get_sales_summary | 3 | 100% | 40.72 | 4358.51 | 38.98 | 4322.5 | 34.24 | 0 | 0 | 0 | 3 | 0 | 854.33 |
| get_top_products | 2 | 100% | 59.38 | 29.16 | 55.85 | 0.0 | 28.27 | 0 | 2 | 0 | 0 | 0 | 0.0 |
| get_top_reps | 3 | 100% | 91.15 | 37.11 | 88.08 | 0.0 | 36.32 | 0 | 3 | 0 | 0 | 0 | 0.0 |
| query_sales_data | 3 | 67% | 569.55 | 7438.32 | 422.21 | 5908.17 | 33.17 | 0 | 0 | 0 | 3 | 0 | 970.33 |

## 偏差场景

- `销售总监 / query_sales_data / 全公司订单明细`：静态方案先查全量订单再在文本层截前 N 条；当前 LLM SQL 在 SQL 层直接 `LIMIT 20`，导致“共找到 N 条订单”口径不同。
- `普通销售员 / get_monthly_trend / 个人趋势`：静态方案对销售员趋势按 `region_id` 查区域趋势；LLM SQL 经过权限注入后额外加了 `o.rep_id = :scope_rep_id`，返回的是个人趋势。

## 上线建议

### 继续写死 SQL

`calc_month_over_month`, `calc_year_over_year`, `detect_sales_anomalies`, `generate_bar_chart`, `generate_line_chart`, `generate_pie_chart`, `get_monthly_trend`, `get_sales_summary`, `query_sales_data`

### 可优先切到 LLM SQL

`get_region_ranking`, `get_top_products`, `get_top_reps`

| Tool | 建议 | 一致率 | 平均静态耗时(ms) | 平均LLM耗时(ms) | 平均静态token | 平均LLM总token | 原因 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| calc_month_over_month | 继续写死 SQL | 100% | 49.16 | 4183.97 | 0 | 844.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 85.1 倍，新增灵活性收益有限。 |
| calc_year_over_year | 继续写死 SQL | 100% | 60.32 | 4034.78 | 0 | 843.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 66.9 倍，新增灵活性收益有限。 |
| detect_sales_anomalies | 继续写死 SQL | 100% | 627.91 | 5354.59 | 0 | 942.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 8.5 倍，新增灵活性收益有限。 |
| generate_bar_chart | 继续写死 SQL | 100% | 79.07 | 37.34 | 0 | 0.0 | 这是图表包装层 tool，灵活性主要来自底层 ranking/product 查询，没必要把图表组装本身切到 LLM 主链路。 |
| generate_line_chart | 继续写死 SQL | 100% | 33.13 | 5603.02 | 0 | 915.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 169.1 倍，新增灵活性收益有限。 |
| generate_pie_chart | 继续写死 SQL | 100% | 78.55 | 36.05 | 0 | 0.0 | 这是图表包装层 tool，灵活性主要来自底层 ranking/product 查询，没必要把图表组装本身切到 LLM 主链路。 |
| get_monthly_trend | 继续写死 SQL | 50% | 35.75 | 5101.93 | 0 | 907.5 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 142.7 倍，新增灵活性收益有限。 |
| get_region_ranking | 可优先切到 LLM SQL | 100% | 54.88 | 161.82 | 0 | 0.0 | 结果一致性已经足够高，且这类查询/图表维度更容易继续扩展过滤条件、排序和组合维度。 |
| get_sales_summary | 继续写死 SQL | 100% | 40.72 | 4358.51 | 0 | 854.33 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 107.0 倍，新增灵活性收益有限。 |
| get_top_products | 可优先切到 LLM SQL | 100% | 59.38 | 29.16 | 0 | 0.0 | 结果一致性已经足够高，且这类查询/图表维度更容易继续扩展过滤条件、排序和组合维度。 |
| get_top_reps | 可优先切到 LLM SQL | 100% | 91.15 | 37.11 | 0 | 0.0 | 结果一致性已经足够高，且这类查询/图表维度更容易继续扩展过滤条件、排序和组合维度。 |
| query_sales_data | 继续写死 SQL | 67% | 569.55 | 7438.32 | 0 | 970.33 | 当前一致性或可观测性还不够稳，继续保留确定性查询更合适。 |

## 典型观察

1. 写死 SQL 的优势
- 汇总、趋势、环比、同比这类口径固定查询更稳定，耗时也明显更低。
- 图表 tool 本身只是把底层查询结果包装成 artifact，LLM 在这里新增的价值很有限。

2. LLM SQL 的优势
- 明细、排名、分维度图表这类查询更容易继续扩展过滤条件、组合维度和口径变体。
- 在结果一致时，LLM SQL 可以减少一部分仓库层模板代码，并把多条小查询收敛为一条聚合 SQL。

3. 生产落地建议
- 先把 `get_top_reps / get_region_ranking / get_top_products` 放在影子模式观察；图表 tool 跟随底层查询一起验证即可。
- 在日志中补齐 request_id、tool_name、task_type、最终 SQL、参数、token 和耗时，再考虑主链路切换。
- `detect_sales_anomalies` 暂不建议切主链路，它是组合型分析，当前更适合保留确定性实现。

4. 命中形态解读
- `bypass`：当前场景按白名单直接回写死 SQL，没有发生任何 SQL 生成。
- `template`：命中 ranking 类受控模板，仍属于 LLM SQL 链路，但 token 应接近 0。
- `cache`：命中缓存模板，不再重新生成 SQL。
- `generator`：真正调用了模型生成 SQL，这一类最能反映 token 和生成耗时。

## 每个场景的 SQL 对比

### 销售总监 / query_sales_data / 全公司订单明细

- 用户问题：列出本月全公司前 8 条订单
- 结果一致：否
- 静态耗时：1268.46 ms
- LLM耗时：9771.94 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：960（prompt 726 / completion 234 / reasoning 0）

静态结果预览：
```text
订单查询结果（2026-05-01 至 2026-05-31）： 共找到 34 条订单，以下显示前 8 条 - 订单号：ORD-JS-CM-016 | 日期：2026-05-07 | 销售员：林岚-华东直播运营 | 客户：华东直播母婴爆品专场 | 金额：¥95,940 | 状态：已完成 - 订单号：ORD-JS-CM-014 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原月嫂服务企业团购 | 金额：¥55,992 | 状态：已完成 - 订单号：ORD-JS-CM-009 | 日期：2026-05-07 | 销售员：刘珊-华南电商顾问 | 客户：广州宝妈福利社群 | 金额：¥13,980 | 状态：已完成 - 订单号：ORD-JS-CM-006 | 日期：2026-05-07 | 销售员：陈悦-华东商城顾问 | 客户：杭州母婴商城团购客户 | 金额：¥19,188 | 状态：已完成 - 订单号：ORD-JS-CM-004 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原五峰国际产康客户 | 金额：¥8,997 | 状态：已完成 - 订单号：ORD-JS-CM-001 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原小店区宝妈社群A | 金额：¥13,998 | 状态：已完成 - 订单号：ORD...[truncated]
```

LLM 结果预览：
```text
订单查询结果（2026-05-01 至 2026-05-31）： 共找到 20 条订单，以下显示前 8 条 - 订单号：ORD-JS-CM-016 | 日期：2026-05-07 | 销售员：林岚-华东直播运营 | 客户：华东直播母婴爆品专场 | 金额：¥95,940 | 状态：已完成 - 订单号：ORD-JS-CM-014 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原月嫂服务企业团购 | 金额：¥55,992 | 状态：已完成 - 订单号：ORD-JS-CM-009 | 日期：2026-05-07 | 销售员：刘珊-华南电商顾问 | 客户：广州宝妈福利社群 | 金额：¥13,980 | 状态：已完成 - 订单号：ORD-JS-CM-006 | 日期：2026-05-07 | 销售员：陈悦-华东商城顾问 | 客户：杭州母婴商城团购客户 | 金额：¥19,188 | 状态：已完成 - 订单号：ORD-JS-CM-004 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原五峰国际产康客户 | 金额：¥8,997 | 状态：已完成 - 订单号：ORD-JS-CM-001 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原小店区宝妈社群A | 金额：¥13,998 | 状态：已完成 - 订单号：ORD...[truncated]
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.id, sa_sales_order.order_no, sa_sales_order.rep_id, sa_sales_order.product_id, sa_sales_order.region_id, sa_sales_order.customer_name, sa_sales_order.quantity, sa_sales_order.unit_price, sa_sales_order.amount, sa_sales_order.cost, sa_sales_order.profit, sa_sales_order.status, sa_sales_order.order_date, sa_sales_order.created_at FROM sa_sales_order WHERE sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s ORDER BY sa_sales_order.order_date DESC, sa_sales_order.id DESC
```
参数：`{'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`346.06` ms

2.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9109}`
耗时：`32.49` ms

3.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`30.02` ms

4.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9111}`
耗时：`33.49` ms

5.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9108}`
耗时：`266.78` ms

6.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`31.17` ms

7.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`31.04` ms

8.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9111}`
耗时：`30.65` ms

9.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`35.54` ms

LLM SQL：

1. generated / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "limit": 20}`
耗时：`5599.85` ms
token：`prompt=726, completion=234, reasoning=0, total=960`

2. executed
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "limit": 20}`
耗时：`37.71` ms
返回行数：`20`

3. audit / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "limit": 20}`
返回行数：`20`

### 销售总监 / get_sales_summary / 全公司销售额汇总

- 用户问题：本月全公司销售额是多少
- 结果一致：是
- 静态耗时：43.0 ms
- LLM耗时：4019.49 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：843（prompt 674 / completion 169 / reasoning 0）

静态结果预览：
```text
销售额汇总（2026-05-01 至 2026-05-31，全公司）： 总销售额：¥648,720
```

LLM 结果预览：
```text
销售额汇总（2026-05-01 至 2026-05-31，全公司）： 总销售额：¥648,720
```

静态 SQL：

1.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`40.83` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`3983.4` ms
token：`prompt=674, completion=169, reasoning=0, total=843`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`34.53` ms
返回行数：`1`

3. audit / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
返回行数：`1`

### 销售总监 / get_top_reps / 全公司销售员排名

- 用户问题：本月全公司销售员 TOP5
- 结果一致：是
- 静态耗时：107.6 ms
- LLM耗时：36.3 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
销售员业绩排名（2026-05-01 至 2026-05-31，全公司）： 第 1 名：林岚-华东直播运营（华东区） 销售额：¥115,890 第 2 名：张伟（华东区） 销售额：¥108,987 第 3 名：李娜-太原产康顾问（华北区） 销售额：¥78,987 第 4 名：刘珊-华南电商顾问（华南区） 销售额：¥77,860 第 5 名：刘洋（华南区） 销售额：¥70,943
```

LLM 结果预览：
```text
销售员业绩排名（2026-05-01 至 2026-05-31，全公司）： 第 1 名：林岚-华东直播运营（华东区） 销售额：¥115,890 第 2 名：张伟（华东区） 销售额：¥108,987 第 3 名：李娜-太原产康顾问（华北区） 销售额：¥78,987 第 4 名：刘珊-华南电商顾问（华南区） 销售额：¥77,860 第 5 名：刘洋（华南区） 销售额：¥70,943
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.rep_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`33.06` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`36.32` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`33.86` ms

LLM SQL：

1. executed
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`35.6` ms
返回行数：`5`

2. audit / rep_ranking
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
返回行数：`5`

### 销售总监 / get_region_ranking / 全公司大区排名

- 用户问题：本月全公司大区排名
- 结果一致：是
- 静态耗时：55.94 ms
- LLM耗时：26.45 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
大区业绩排名（2026-05-01 至 2026-05-31）： 第 1 名：华东区 销售额：¥262,833 占比：40.5% 第 2 名：华南区 销售额：¥182,789 占比：28.2% 第 3 名：华北区 销售额：¥152,363 占比：23.5% 第 4 名：西南区 销售额：¥50,735 占比：7.8% 全公司合计：¥648,720
```

LLM 结果预览：
```text
大区业绩排名（2026-05-01 至 2026-05-31）： 第 1 名：华东区 销售额：¥262,833 占比：40.5% 第 2 名：华南区 销售额：¥182,789 占比：28.2% 第 3 名：华北区 销售额：¥152,363 占比：23.5% 第 4 名：西南区 销售额：¥50,735 占比：7.8% 全公司合计：¥648,720
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.region_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.region_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`29.72` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`24.17` ms

LLM SQL：

1. executed
```sql
SELECT o.region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.region_id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`25.65` ms
返回行数：`4`

2. audit / region_ranking
```sql
SELECT o.region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.region_id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
返回行数：`4`

### 销售总监 / get_top_products / 全公司产品 Top5

- 用户问题：本月全公司产品 TOP5
- 结果一致：是
- 静态耗时：51.63 ms
- LLM耗时：25.21 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
产品销售排名（最佳）（2026-05-01 至 2026-05-31，全公司）： 第 1 名：电商直播母婴爆品礼包 [SKU-JS-5001] 品类：直播电商 销售额：¥115,128 数量：72 件 第 2 名：咪婴伴侣月嫂到家服务包 [SKU-JS-1001] 品类：同城母婴服务 销售额：¥69,990 数量：10 件 第 3 名：孕产营养礼包 [SKU-JS-2001] 品类：母婴用品 销售额：¥69,900 数量：100 件 第 4 名：产后修复基础疗程 [SKU-JS-1002] 品类：产后修复服务 销售额：¥55,986 数量：14 件 第 5 名：联想 ThinkPad X1 笔记本 [SKU-1003] 品类：数码产品 销售额：¥49,995 数量：5 件
```

LLM 结果预览：
```text
产品销售排名（最佳）（2026-05-01 至 2026-05-31，全公司）： 第 1 名：电商直播母婴爆品礼包 [SKU-JS-5001] 品类：直播电商 销售额：¥115,128 数量：72 件 第 2 名：咪婴伴侣月嫂到家服务包 [SKU-JS-1001] 品类：同城母婴服务 销售额：¥69,990 数量：10 件 第 3 名：孕产营养礼包 [SKU-JS-2001] 品类：母婴用品 销售额：¥69,900 数量：100 件 第 4 名：产后修复基础疗程 [SKU-JS-1002] 品类：产后修复服务 销售额：¥55,986 数量：14 件 第 5 名：联想 ThinkPad X1 笔记本 [SKU-1003] 品类：数码产品 销售额：¥49,995 数量：5 件
```

静态 SQL：

1.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product
```
参数：`{}`
耗时：`23.99` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`22.93` ms

LLM SQL：

1. executed
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "region_id": null}`
耗时：`24.36` ms
返回行数：`5`

2. audit / product_ranking
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "region_id": null}`
返回行数：`5`

### 销售总监 / calc_month_over_month / 全公司环比

- 用户问题：本月和上月环比
- 结果一致：是
- 静态耗时：49.16 ms
- LLM耗时：4183.97 ms
- LLM模式：generator+cache
- 命中情况：template=0 / cache=1 / generator=1
- 静态 token：0
- LLM token：844（prompt 674 / completion 170 / reasoning 0）

静态结果预览：
```text
环比分析（全公司）： 当前周期（2026-05-01 至 2026-05-31）：¥648,720 对比周期（2026-04-01 至 2026-04-30）：¥520,442 环比变化：↑ 增长 24.6%（增加 ¥128,278）
```

LLM 结果预览：
```text
环比分析（全公司）： 当前周期（2026-05-01 至 2026-05-31）：¥648,720 对比周期（2026-04-01 至 2026-04-30）：¥520,442 环比变化：↑ 增长 24.6%（增加 ¥128,278）
```

静态 SQL：

1.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`22.02` ms

2.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 1), 'order_date_2': datetime.date(2026, 4, 30)}`
耗时：`25.42` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`4116.91` ms
token：`prompt=674, completion=170, reasoning=0, total=844`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`34.36` ms
返回行数：`1`

3. audit / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
返回行数：`1`

4. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-04-01", "end_date": "2026-04-30"}`
耗时：`30.47` ms
返回行数：`1`

5. audit / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-04-01", "end_date": "2026-04-30"}`
返回行数：`1`

### 销售总监 / calc_year_over_year / 全公司同比

- 用户问题：本月同比去年同期
- 结果一致：是
- 静态耗时：60.32 ms
- LLM耗时：4034.78 ms
- LLM模式：generator+cache
- 命中情况：template=0 / cache=1 / generator=1
- 静态 token：0
- LLM token：843（prompt 674 / completion 169 / reasoning 0）

静态结果预览：
```text
同比分析（全公司）： 今年（2026-05-01 至 2026-05-31）：¥648,720 去年（2025-05-01 至 2025-05-31）：¥87,641 同比变化：↑ 同比增长 640.2%
```

LLM 结果预览：
```text
同比分析（全公司）： 今年（2026-05-01 至 2026-05-31）：¥648,720 去年（2025-05-01 至 2025-05-31）：¥87,641 同比变化：↑ 同比增长 640.2%
```

静态 SQL：

1.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`28.45` ms

2.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2025, 5, 1), 'order_date_2': datetime.date(2025, 5, 31)}`
耗时：`30.29` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`3960.36` ms
token：`prompt=674, completion=169, reasoning=0, total=843`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`35.84` ms
返回行数：`1`

3. audit / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
返回行数：`1`

4. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2025-05-01", "end_date": "2025-05-31"}`
耗时：`36.59` ms
返回行数：`1`

5. audit / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date
```
参数：`{"start_date": "2025-05-01", "end_date": "2025-05-31"}`
返回行数：`1`

### 销售总监 / get_monthly_trend / 全公司 6 个月趋势

- 用户问题：全公司近 6 个月趋势
- 结果一致：是
- 静态耗时：37.25 ms
- LLM耗时：4925.73 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：898（prompt 691 / completion 207 / reasoning 0）

静态结果预览：
```text
月度销售趋势（近 6 个月，全公司）： 2025-11：¥313,379 订单数：11 2025-12：¥499,868 订单数：15 (↑59.5%) 2026-01：¥308,687 订单数：10 (↓38.2%) 2026-02：¥217,707 订单数：10 (↓29.5%) 2026-03：¥576,626 订单数：27 (↑164.9%) 2026-04：¥520,442 订单数：37 (↓9.7%) 2026-05：¥648,720 订单数：30 (↑24.6%) 整体趋势：上升 107.0%（2025-11 至 2026-05）
```

LLM 结果预览：
```text
月度销售趋势（近 6 个月，全公司）： 2025-11：¥313,379 订单数：11 2025-12：¥499,868 订单数：15 (↑59.5%) 2026-01：¥308,687 订单数：10 (↓38.2%) 2026-02：¥217,707 订单数：10 (↓29.5%) 2026-03：¥576,626 订单数：27 (↑164.9%) 2026-04：¥520,442 订单数：37 (↓9.7%) 2026-05：¥648,720 订单数：30 (↑24.6%) 整体趋势：上升 107.0%（2025-11 至 2026-05）
```

静态 SQL：

1.
```sql
SELECT date_format(sa_sales_order.order_date, %(date_format_1)s) AS month, sum(sa_sales_order.amount) AS total, count(sa_sales_order.id) AS order_count FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY date_format(sa_sales_order.order_date, %(date_format_1)s) ORDER BY date_format(sa_sales_order.order_date, %(date_format_1)s)
```
参数：`{'date_format_1': '%Y-%m', 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2025, 11, 1), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`34.71` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`4888.27` ms
token：`prompt=691, completion=207, reasoning=0, total=898`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`35.73` ms
返回行数：`7`

3. audit / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
返回行数：`7`

### 销售总监 / generate_line_chart / 趋势折线图

- 用户问题：给我近 6 个月折线图
- 结果一致：是
- 静态耗时：34.68 ms
- LLM耗时：5788.24 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：918（prompt 691 / completion 227 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [313379, 499868, 308687, 217707, 576626, 520442, 648720], "itemStyle": {"color": "#5470c6"}, "name": "销售额", "smooth": true, "type": "line"}], "title": {"text": "全公司近6个月趋势"}, "tooltip": {"trigger": "axis"}, "xAxis": {"data": ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "全公司近6个月趋势"}, "message": "已生成折线图。"}
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [313379, 499868, 308687, 217707, 576626, 520442, 648720], "itemStyle": {"color": "#5470c6"}, "name": "销售额", "smooth": true, "type": "line"}], "title": {"text": "全公司近6个月趋势"}, "tooltip": {"trigger": "axis"}, "xAxis": {"data": ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "全公司近6个月趋势"}, "message": "已生成折线图。"}
```

静态 SQL：

1.
```sql
SELECT date_format(sa_sales_order.order_date, %(date_format_1)s) AS month, sum(sa_sales_order.amount) AS total, count(sa_sales_order.id) AS order_count FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY date_format(sa_sales_order.order_date, %(date_format_1)s) ORDER BY date_format(sa_sales_order.order_date, %(date_format_1)s)
```
参数：`{'date_format_1': '%Y-%m', 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2025, 11, 1), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`33.29` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`5754.5` ms
token：`prompt=691, completion=227, reasoning=0, total=918`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`32.06` ms
返回行数：`7`

3. audit / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
返回行数：`7`

### 销售总监 / generate_bar_chart / 大区柱状图

- 用户问题：按大区生成柱状图
- 结果一致：是
- 静态耗时：66.35 ms
- LLM耗时：37.36 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [262833, 182789, 152363, 50735], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月大区销售对比"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["华东区", "华南区", "华北区", "西南区"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月大区销售对比"}, "message": "已生成柱状图。"}
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [262833, 182789, 152363, 50735], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月大区销售对比"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["华东区", "华南区", "华北区", "西南区"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月大区销售对比"}, "message": "已生成柱状图。"}
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.region_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.region_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`31.09` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`33.08` ms

LLM SQL：

1. executed
```sql
SELECT o.region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.region_id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`36.63` ms
返回行数：`4`

2. audit / region_ranking
```sql
SELECT o.region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.region_id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
返回行数：`4`

### 销售总监 / generate_bar_chart / 销售员柱状图

- 用户问题：按销售员生成柱状图
- 结果一致：是
- 静态耗时：110.08 ms
- LLM耗时：35.98 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [115890, 108987, 78987, 77860, 70943], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月销售员Top5"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["林岚-华东直播运营", "张伟", "李娜-太原产康顾问", "刘珊-华南电商顾问", "刘洋"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月销售员Top5"}, "message": "已生成柱状图。"}
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [115890, 108987, 78987, 77860, 70943], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月销售员Top5"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["林岚-华东直播运营", "张伟", "李娜-太原产康顾问", "刘珊-华南电商顾问", "刘洋"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月销售员Top5"}, "message": "已生成柱状图。"}
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.rep_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`35.34` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`36.54` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`36.03` ms

LLM SQL：

1. executed
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`35.15` ms
返回行数：`5`

2. audit / rep_ranking
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
返回行数：`5`

### 销售总监 / generate_bar_chart / 产品柱状图

- 用户问题：按产品生成柱状图
- 结果一致：是
- 静态耗时：66.19 ms
- LLM耗时：37.71 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [115128, 69990, 69900, 55986, 49995], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月产品Top5"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["电商直播母婴爆品礼包", "咪婴伴侣月嫂到家服务包", "孕产营养礼包", "产后修复基础疗程", "联想 ThinkPad X1 笔记本"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月产品Top5"}, "message": "已生成柱状图。"}
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [115128, 69990, 69900, 55986, 49995], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月产品Top5"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["电商直播母婴爆品礼包", "咪婴伴侣月嫂到家服务包", "孕产营养礼包", "产后修复基础疗程", "联想 ThinkPad X1 笔记本"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月产品Top5"}, "message": "已生成柱状图。"}
```

静态 SQL：

1.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product
```
参数：`{}`
耗时：`33.85` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`30.61` ms

LLM SQL：

1. executed
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "region_id": null}`
耗时：`36.66` ms
返回行数：`5`

2. audit / product_ranking
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "region_id": null}`
返回行数：`5`

### 销售总监 / generate_bar_chart / 品类柱状图

- 用户问题：按品类生成柱状图
- 结果一致：是
- 静态耗时：73.66 ms
- LLM耗时：38.31 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [115128, 78886, 97810, 64983, 170978, 66040, 28568, 17970, 2995, 2970, 2392], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月品类对比"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["直播电商", "同城母婴服务", "母婴用品", "产后修复服务", "数码产品", "家用电器", "服装配饰", "育儿课程", "健康咨询服务", "其他", "陪诊服务"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月品类对比"}, "message": "已生成柱状图。"}
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [115128, 78886, 97810, 64983, 170978, 66040, 28568, 17970, 2995, 2970, 2392], "itemStyle": {"color": "#91cc75"}, "type": "bar"}], "title": {"text": "本月品类对比"}, "tooltip": {"trigger": "axis"}, "xAxis": {"axisLabel": {"rotate": 30}, "data": ["直播电商", "同城母婴服务", "母婴用品", "产后修复服务", "数码产品", "家用电器", "服装配饰", "育儿课程", "健康咨询服务", "其他", "陪诊服务"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "本月品类对比"}, "message": "已生成柱状图。"}
```

静态 SQL：

1.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product
```
参数：`{}`
耗时：`35.99` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`34.88` ms

LLM SQL：

1. executed
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100, "region_id": null}`
耗时：`37.09` ms
返回行数：`24`

2. audit / product_ranking
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100, "region_id": null}`
返回行数：`24`

### 销售总监 / generate_pie_chart / 大区饼图

- 用户问题：按大区生成饼图
- 结果一致：是
- 静态耗时：61.71 ms
- LLM耗时：32.49 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"name": "华东区", "value": 262833}, {"name": "华南区", "value": 182789}, {"name": "华北区", "value": 152363}, {"name": "西南区", "value": 50735}], "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)", "shadowOffsetX": 0}}, "radius": "55%", "type": "pie"}], "title": {"left": "center", "text": "本月大区占比"}, "tooltip": {"formatter": "{b}: ¥{c} ({d}%)", "trigger": "item"}}, "slot": "main_chart", "title": "本月大区占比"}, "message": "已生成饼图。\n图表数据：\n- 华东区：¥262,833，占比 40.5%\n- 华南区：¥...[truncated]
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"name": "华东区", "value": 262833}, {"name": "华南区", "value": 182789}, {"name": "华北区", "value": 152363}, {"name": "西南区", "value": 50735}], "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)", "shadowOffsetX": 0}}, "radius": "55%", "type": "pie"}], "title": {"left": "center", "text": "本月大区占比"}, "tooltip": {"formatter": "{b}: ¥{c} ({d}%)", "trigger": "item"}}, "slot": "main_chart", "title": "本月大区占比"}, "message": "已生成饼图。\n图表数据：\n- 华东区：¥262,833，占比 40.5%\n- 华南区：¥...[truncated]
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.region_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.region_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`29.77` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`30.45` ms

LLM SQL：

1. executed
```sql
SELECT o.region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.region_id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`31.81` ms
返回行数：`4`

2. audit / region_ranking
```sql
SELECT o.region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.region_id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
返回行数：`4`

### 销售总监 / generate_pie_chart / 销售员饼图

- 用户问题：按销售员生成饼图
- 结果一致：是
- 静态耗时：107.77 ms
- LLM耗时：35.08 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"name": "林岚-华东直播运营", "value": 115890}, {"name": "张伟", "value": 108987}, {"name": "李娜-太原产康顾问", "value": 78987}, {"name": "刘珊-华南电商顾问", "value": 77860}, {"name": "刘洋", "value": 70943}], "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)", "shadowOffsetX": 0}}, "radius": "55%", "type": "pie"}], "title": {"left": "center", "text": "本月销售员占比"}, "tooltip": {"formatter": "{b}: ¥{c} ({d}%)", "trigger": "item"}}, "slot": "main_chart", "title": "本月销售员占比"}, "message"...[truncated]
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"name": "林岚-华东直播运营", "value": 115890}, {"name": "张伟", "value": 108987}, {"name": "李娜-太原产康顾问", "value": 78987}, {"name": "刘珊-华南电商顾问", "value": 77860}, {"name": "刘洋", "value": 70943}], "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)", "shadowOffsetX": 0}}, "radius": "55%", "type": "pie"}], "title": {"left": "center", "text": "本月销售员占比"}, "tooltip": {"formatter": "{b}: ¥{c} ({d}%)", "trigger": "item"}}, "slot": "main_chart", "title": "本月销售员占比"}, "message"...[truncated]
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.rep_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`36.45` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`35.27` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`33.38` ms

LLM SQL：

1. executed
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`33.98` ms
返回行数：`5`

2. audit / rep_ranking
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
返回行数：`5`

### 销售总监 / generate_pie_chart / 产品饼图

- 用户问题：按产品生成饼图
- 结果一致：是
- 静态耗时：68.68 ms
- LLM耗时：37.36 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"category": "直播电商", "name": "电商直播母婴爆品礼包", "quantity": 72, "sku": "SKU-JS-5001", "value": 115128}, {"category": "同城母婴服务", "name": "咪婴伴侣月嫂到家服务包", "quantity": 10, "sku": "SKU-JS-1001", "value": 69990}, {"category": "母婴用品", "name": "孕产营养礼包", "quantity": 100, "sku": "SKU-JS-2001", "value": 69900}, {"category": "产后修复服务", "name": "产后修复基础疗程", "quantity": 14, "sku": "SKU-JS-1002", "value": 55986}, {"category": "数码产品", "name": "联想 ThinkPad X1 笔记本", "quantity": 5, "sku": "SKU-1003", "value"...[truncated]
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"category": "直播电商", "name": "电商直播母婴爆品礼包", "quantity": 72, "sku": "SKU-JS-5001", "value": 115128}, {"category": "同城母婴服务", "name": "咪婴伴侣月嫂到家服务包", "quantity": 10, "sku": "SKU-JS-1001", "value": 69990}, {"category": "母婴用品", "name": "孕产营养礼包", "quantity": 100, "sku": "SKU-JS-2001", "value": 69900}, {"category": "产后修复服务", "name": "产后修复基础疗程", "quantity": 14, "sku": "SKU-JS-1002", "value": 55986}, {"category": "数码产品", "name": "联想 ThinkPad X1 笔记本", "quantity": 5, "sku": "SKU-1003", "value"...[truncated]
```

静态 SQL：

1.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product
```
参数：`{}`
耗时：`32.03` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`34.97` ms

LLM SQL：

1. executed
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "region_id": null}`
耗时：`36.4` ms
返回行数：`5`

2. audit / product_ranking
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "region_id": null}`
返回行数：`5`

### 销售总监 / generate_pie_chart / 品类饼图

- 用户问题：按品类生成饼图
- 结果一致：是
- 静态耗时：76.02 ms
- LLM耗时：39.25 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"name": "直播电商", "value": 115128}, {"name": "同城母婴服务", "value": 78886}, {"name": "母婴用品", "value": 97810}, {"name": "产后修复服务", "value": 64983}, {"name": "数码产品", "value": 170978}, {"name": "家用电器", "value": 66040}, {"name": "服装配饰", "value": 28568}, {"name": "育儿课程", "value": 17970}, {"name": "健康咨询服务", "value": 2995}, {"name": "其他", "value": 2970}, {"name": "陪诊服务", "value": 2392}], "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)", "shadowOffsetX": 0}}, "radiu...[truncated]
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"legend": {"left": "left", "orient": "vertical"}, "series": [{"data": [{"name": "直播电商", "value": 115128}, {"name": "同城母婴服务", "value": 78886}, {"name": "母婴用品", "value": 97810}, {"name": "产后修复服务", "value": 64983}, {"name": "数码产品", "value": 170978}, {"name": "家用电器", "value": 66040}, {"name": "服装配饰", "value": 28568}, {"name": "育儿课程", "value": 17970}, {"name": "健康咨询服务", "value": 2995}, {"name": "其他", "value": 2970}, {"name": "陪诊服务", "value": 2392}], "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)", "shadowOffsetX": 0}}, "radiu...[truncated]
```

静态 SQL：

1.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product
```
参数：`{}`
耗时：`37.89` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`36.36` ms

LLM SQL：

1. executed
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100, "region_id": null}`
耗时：`38.24` ms
返回行数：`24`

2. audit / product_ranking
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100, "region_id": null}`
返回行数：`24`

### 销售总监 / detect_sales_anomalies / 异常检测

- 用户问题：检测当前销售异常
- 结果一致：是
- 静态耗时：627.91 ms
- LLM耗时：5354.59 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：942（prompt 733 / completion 209 / reasoning 0）

静态结果预览：
```text
异常检测结果：共发现 25 个异常 高优先级｜产品连续零销售 对象：索尼 WH-1000XM6 耳机（SKU-1004） 描述：已连续 24 天无销售订单，上次出单日期：2026-04-14 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：智能手表 Pro（SKU-8821） 描述：已连续 52 天无销售订单，上次出单日期：2026-03-17 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：优衣库羊绒大衣（SKU-3002） 描述：已连续 112 天无销售订单，上次出单日期：2026-01-16 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：金融理财书籍套装（SKU-4002） 描述：已连续 50 天无销售订单，上次出单日期：2026-03-19 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：瑜伽垫专业版（SKU-4003） 描述：已连续 28 天无销售订单，上次出单日期：2026-04-10 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：咖啡机胶囊套装（SKU-4004） 描述：已连续 173 天无销售订单，上次出单日期：2025-11-16 建议：检查产品是否下架、库存是否...[truncated]
```

LLM 结果预览：
```text
异常检测结果：共发现 25 个异常 高优先级｜产品连续零销售 对象：索尼 WH-1000XM6 耳机（SKU-1004） 描述：已连续 24 天无销售订单，上次出单日期：2026-04-14 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：智能手表 Pro（SKU-8821） 描述：已连续 52 天无销售订单，上次出单日期：2026-03-17 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：优衣库羊绒大衣（SKU-3002） 描述：已连续 112 天无销售订单，上次出单日期：2026-01-16 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：金融理财书籍套装（SKU-4002） 描述：已连续 50 天无销售订单，上次出单日期：2026-03-19 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：瑜伽垫专业版（SKU-4003） 描述：已连续 28 天无销售订单，上次出单日期：2026-04-10 建议：检查产品是否下架、库存是否充足、价格是否有竞争力 高优先级｜产品连续零销售 对象：咖啡机胶囊套装（SKU-4004） 描述：已连续 173 天无销售订单，上次出单日期：2025-11-16 建议：检查产品是否下架、库存是否...[truncated]
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.region_id, count(sa_sales_order.id) AS order_count FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.region_id
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 24), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`34.24` ms

2.
```sql
SELECT sa_sales_order.region_id, count(sa_sales_order.id) AS order_count FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.region_id
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 27), 'order_date_2': datetime.date(2026, 4, 23)}`
耗时：`34.1` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`35.0` ms

4.
```sql
SELECT sa_sales_order.product_id, max(sa_sales_order.order_date) AS last_order_date FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s GROUP BY sa_sales_order.product_id
```
参数：`{'status_1': 'COMPLETED'}`
耗时：`43.26` ms

5.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product WHERE sa_product.status = %(status_1)s
```
参数：`{'status_1': 'ACTIVE'}`
耗时：`35.84` ms

6.
```sql
SELECT sa_sales_order.rep_id, sum(CASE WHEN (sa_sales_order.status = %(status_1)s) THEN %(param_1)s ELSE %(param_2)s END) AS refunded, count(sa_sales_order.id) AS total FROM sa_sales_order WHERE sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id
```
参数：`{'status_1': 'REFUNDED', 'param_1': 1, 'param_2': 0, 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`30.8` ms

7.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 3}`
耗时：`29.46` ms

8.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9105}`
耗时：`31.15` ms

9.
```sql
SELECT sa_sales_order.rep_id, coalesce(sum(sa_sales_order.amount), %(coalesce_1)s) AS total_amount FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id
```
参数：`{'coalesce_1': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`36.19` ms

10.
```sql
SELECT sa_sales_order.rep_id, coalesce(sum(sa_sales_order.amount), %(coalesce_1)s) AS total_amount FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id
```
参数：`{'coalesce_1': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`269.26` ms

11.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep WHERE sa_sales_rep.`role` = %(role_1)s
```
参数：`{'role_1': 'SALES_REP'}`
耗时：`35.4` ms

LLM SQL：

1. generated / refund_rates
```sql
SELECT o.rep_id, SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded, COUNT(o.id) AS total FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY o.rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08"}`
耗时：`4976.54` ms
token：`prompt=733, completion=209, reasoning=0, total=942`

2. executed
```sql
SELECT o.rep_id, SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded, COUNT(o.id) AS total FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY o.rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08"}`
耗时：`36.47` ms
返回行数：`16`

3. audit / refund_rates
```sql
SELECT o.rep_id, SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded, COUNT(o.id) AS total FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date GROUP BY o.rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08"}`
返回行数：`16`

### 区域经理 / get_sales_summary / 区域销售额汇总

- 用户问题：我大区本月销售额
- 结果一致：是
- 静态耗时：42.5 ms
- LLM耗时：4336.04 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：854（prompt 674 / completion 180 / reasoning 0）

静态结果预览：
```text
销售额汇总（2026-05-01 至 2026-05-31，全公司）： 总销售额：¥152,363
```

LLM 结果预览：
```text
销售额汇总（2026-05-01 至 2026-05-31，全公司）： 总销售额：¥152,363
```

静态 SQL：

1.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'region_id_1': 3, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`40.83` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3}`
耗时：`4298.59` ms
token：`prompt=674, completion=180, reasoning=0, total=854`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "scope_region_id": 3}`
耗时：`35.21` ms
返回行数：`1`

3. audit / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "scope_region_id": 3}`
返回行数：`1`

### 区域经理 / query_sales_data / 区域订单明细

- 用户问题：列出我大区本月订单明细
- 结果一致：是
- 静态耗时：325.05 ms
- LLM耗时：6477.41 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：970（prompt 726 / completion 244 / reasoning 0）

静态结果预览：
```text
订单查询结果（2026-05-01 至 2026-05-31）： 共找到 12 条订单，以下显示前 8 条 - 订单号：ORD-JS-CM-014 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原月嫂服务企业团购 | 金额：¥55,992 | 状态：已完成 - 订单号：ORD-JS-CM-004 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原五峰国际产康客户 | 金额：¥8,997 | 状态：已完成 - 订单号：ORD-JS-CM-001 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原小店区宝妈社群A | 金额：¥13,998 | 状态：已完成 - 订单号：ORD-JS-CM-015 | 日期：2026-05-06 | 销售员：王璐-太原母婴顾问 | 客户：太原产后修复中心团购 | 金额：¥39,990 | 状态：已完成 - 订单号：ORD-JS-CM-002 | 日期：2026-05-06 | 销售员：王璐-太原母婴顾问 | 客户：太原晋源产康中心客户 | 金额：¥15,996 | 状态：已完成 - 订单号：ORD-JS-CM-005 | 日期：2026-05-05 | 销售员：王璐-太原母婴顾问 | 客户：太原高新区双职工家庭 | 金额：¥4,999 | 状态：已完成 - 订单号：OR...[truncated]
```

LLM 结果预览：
```text
订单查询结果（2026-05-01 至 2026-05-31）： 共找到 12 条订单，以下显示前 8 条 - 订单号：ORD-JS-CM-014 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原月嫂服务企业团购 | 金额：¥55,992 | 状态：已完成 - 订单号：ORD-JS-CM-004 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原五峰国际产康客户 | 金额：¥8,997 | 状态：已完成 - 订单号：ORD-JS-CM-001 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原小店区宝妈社群A | 金额：¥13,998 | 状态：已完成 - 订单号：ORD-JS-CM-015 | 日期：2026-05-06 | 销售员：王璐-太原母婴顾问 | 客户：太原产后修复中心团购 | 金额：¥39,990 | 状态：已完成 - 订单号：ORD-JS-CM-002 | 日期：2026-05-06 | 销售员：王璐-太原母婴顾问 | 客户：太原晋源产康中心客户 | 金额：¥15,996 | 状态：已完成 - 订单号：ORD-JS-CM-005 | 日期：2026-05-05 | 销售员：王璐-太原母婴顾问 | 客户：太原高新区双职工家庭 | 金额：¥4,999 | 状态：已完成 - 订单号：OR...[truncated]
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.id, sa_sales_order.order_no, sa_sales_order.rep_id, sa_sales_order.product_id, sa_sales_order.region_id, sa_sales_order.customer_name, sa_sales_order.quantity, sa_sales_order.unit_price, sa_sales_order.amount, sa_sales_order.cost, sa_sales_order.profit, sa_sales_order.status, sa_sales_order.order_date, sa_sales_order.created_at FROM sa_sales_order WHERE sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s AND sa_sales_order.region_id = %(region_id_1)s ORDER BY sa_sales_order.order_date DESC, sa_sales_order.id DESC
```
参数：`{'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31), 'region_id_1': 3}`
耗时：`37.23` ms

2.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`35.11` ms

3.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`34.48` ms

4.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`34.09` ms

5.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`33.64` ms

6.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`35.32` ms

7.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`37.85` ms

8.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9105}`
耗时：`34.39` ms

9.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9105}`
耗时：`35.42` ms

LLM SQL：

1. generated / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "limit": 20}`
耗时：`6190.07` ms
token：`prompt=726, completion=244, reasoning=0, total=970`

2. executed
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "limit": 20, "scope_region_id": 3}`
耗时：`31.89` ms
返回行数：`12`

3. audit / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "limit": 20, "scope_region_id": 3}`
返回行数：`12`

### 区域经理 / get_top_reps / 区域销售员排名

- 用户问题：我大区销售员排名
- 结果一致：是
- 静态耗时：94.09 ms
- LLM耗时：35.78 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
销售员业绩排名（2026-05-01 至 2026-05-31，全公司）： 第 1 名：李娜-太原产康顾问（华北区） 销售额：¥78,987 第 2 名：王璐-太原母婴顾问（华北区） 销售额：¥60,985 第 3 名：周丽（华北区） 销售额：¥9,999 第 4 名：周敏-陪诊顾问（华北区） 销售额：¥2,392
```

LLM 结果预览：
```text
销售员业绩排名（2026-05-01 至 2026-05-31，全公司）： 第 1 名：李娜-太原产康顾问（华北区） 销售额：¥78,987 第 2 名：王璐-太原母婴顾问（华北区） 销售额：¥60,985 第 3 名：周丽（华北区） 销售额：¥9,999 第 4 名：周敏-陪诊顾问（华北区） 销售额：¥2,392
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.rep_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`27.5` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`29.94` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`34.07` ms

LLM SQL：

1. executed
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :scope_region_id GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "scope_region_id": 3}`
耗时：`35.01` ms
返回行数：`4`

2. audit / rep_ranking
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :scope_region_id GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "scope_region_id": 3}`
返回行数：`4`

### 区域经理 / get_top_products / 区域产品 Top5

- 用户问题：我大区产品 TOP5
- 结果一致：是
- 静态耗时：67.12 ms
- LLM耗时：33.1 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
产品销售排名（最佳）（2026-05-01 至 2026-05-31，全公司）： 第 1 名：咪婴伴侣月嫂到家服务包 [SKU-JS-1001] 品类：同城母婴服务 销售额：¥69,990 数量：10 件 第 2 名：产后修复基础疗程 [SKU-JS-1002] 品类：产后修复服务 销售额：¥55,986 数量：14 件 第 3 名：联想 ThinkPad X1 笔记本 [SKU-1003] 品类：数码产品 销售额：¥9,999 数量：1 件 第 4 名：盆底肌修复专业疗程 [SKU-JS-1003] 品类：产后修复服务 销售额：¥8,997 数量：3 件 第 5 名：育儿嫂短期照护服务 [SKU-JS-1005] 品类：同城母婴服务 销售额：¥4,999 数量：1 件
```

LLM 结果预览：
```text
产品销售排名（最佳）（2026-05-01 至 2026-05-31，全公司）： 第 1 名：咪婴伴侣月嫂到家服务包 [SKU-JS-1001] 品类：同城母婴服务 销售额：¥69,990 数量：10 件 第 2 名：产后修复基础疗程 [SKU-JS-1002] 品类：产后修复服务 销售额：¥55,986 数量：14 件 第 3 名：联想 ThinkPad X1 笔记本 [SKU-1003] 品类：数码产品 销售额：¥9,999 数量：1 件 第 4 名：盆底肌修复专业疗程 [SKU-JS-1003] 品类：产后修复服务 销售额：¥8,997 数量：3 件 第 5 名：育儿嫂短期照护服务 [SKU-JS-1005] 品类：同城母婴服务 销售额：¥4,999 数量：1 件
```

静态 SQL：

1.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product
```
参数：`{}`
耗时：`35.65` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s AND sa_sales_order.region_id = %(region_id_1)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31), 'region_id_1': 3}`
耗时：`29.13` ms

LLM SQL：

1. executed
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) AND o.region_id = :scope_region_id GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "top_n": 5, "scope_region_id": 3}`
耗时：`32.17` ms
返回行数：`5`

2. audit / product_ranking
```sql
SELECT o.product_id, p.sku_code AS sku_code, p.name AS product_name, p.category AS category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND (:region_id IS NULL OR o.region_id = :region_id) AND o.region_id = :scope_region_id GROUP BY o.product_id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "top_n": 5, "scope_region_id": 3}`
返回行数：`5`

### 区域经理 / generate_line_chart / 区域趋势折线图

- 用户问题：我大区近 6 个月趋势图
- 结果一致：是
- 静态耗时：31.58 ms
- LLM耗时：5417.8 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：912（prompt 691 / completion 221 / reasoning 0）

静态结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [103578, 154473, 142978, 61890, 409025, 277553, 152363], "itemStyle": {"color": "#5470c6"}, "name": "销售额", "smooth": true, "type": "line"}], "title": {"text": "华北区近6个月趋势"}, "tooltip": {"trigger": "axis"}, "xAxis": {"data": ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "华北区近6个月趋势"}, "message": "已生成折线图。"}
```

LLM 结果预览：
```text
{"artifact": {"kind": "echarts", "option": {"series": [{"data": [103578, 154473, 142978, 61890, 409025, 277553, 152363], "itemStyle": {"color": "#5470c6"}, "name": "销售额", "smooth": true, "type": "line"}], "title": {"text": "华北区近6个月趋势"}, "tooltip": {"trigger": "axis"}, "xAxis": {"data": ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"], "type": "category"}, "yAxis": {"name": "销售额（元）", "type": "value"}}, "slot": "main_chart", "title": "华北区近6个月趋势"}, "message": "已生成折线图。"}
```

静态 SQL：

1.
```sql
SELECT date_format(sa_sales_order.order_date, %(date_format_1)s) AS month, sum(sa_sales_order.amount) AS total, count(sa_sales_order.id) AS order_count FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s AND sa_sales_order.region_id = %(region_id_1)s GROUP BY date_format(sa_sales_order.order_date, %(date_format_1)s) ORDER BY date_format(sa_sales_order.order_date, %(date_format_1)s)
```
参数：`{'date_format_1': '%Y-%m', 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2025, 11, 1), 'order_date_2': datetime.date(2026, 5, 8), 'region_id_1': 3}`
耗时：`29.42` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3}`
耗时：`5378.26` ms
token：`prompt=691, completion=221, reasoning=0, total=912`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3, "scope_region_id": 3}`
耗时：`37.29` ms
返回行数：`7`

3. audit / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3, "scope_region_id": 3}`
返回行数：`7`

### 普通销售员 / get_sales_summary / 个人销售额汇总

- 用户问题：我本月销售额
- 结果一致：是
- 静态耗时：36.66 ms
- LLM耗时：4720.0 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：866（prompt 678 / completion 188 / reasoning 0）

静态结果预览：
```text
销售额汇总（2026-05-01 至 2026-05-31，全公司）： 总销售额：¥78,987
```

LLM 结果预览：
```text
销售额汇总（2026-05-01 至 2026-05-31，全公司）： 总销售额：¥78,987
```

静态 SQL：

1.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9103, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`35.28` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103}`
耗时：`4685.52` ms
token：`prompt=678, completion=188, reasoning=0, total=866`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id AND o.rep_id = :scope_rep_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "scope_rep_id": 9103}`
耗时：`32.99` ms
返回行数：`1`

3. audit / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id AND o.rep_id = :scope_rep_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "scope_rep_id": 9103}`
返回行数：`1`

### 普通销售员 / query_sales_data / 个人订单明细

- 用户问题：列出我的本月订单
- 结果一致：是
- 静态耗时：115.13 ms
- LLM耗时：6065.61 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：981（prompt 730 / completion 251 / reasoning 0）

静态结果预览：
```text
订单查询结果（2026-05-01 至 2026-05-31）： 共找到 3 条订单 - 订单号：ORD-JS-CM-014 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原月嫂服务企业团购 | 金额：¥55,992 | 状态：已完成 - 订单号：ORD-JS-CM-004 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原五峰国际产康客户 | 金额：¥8,997 | 状态：已完成 - 订单号：ORD-JS-CM-001 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原小店区宝妈社群A | 金额：¥13,998 | 状态：已完成 小计：完成订单 3 笔，金额合计 ¥78,987
```

LLM 结果预览：
```text
订单查询结果（2026-05-01 至 2026-05-31）： 共找到 3 条订单 - 订单号：ORD-JS-CM-014 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原月嫂服务企业团购 | 金额：¥55,992 | 状态：已完成 - 订单号：ORD-JS-CM-004 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原五峰国际产康客户 | 金额：¥8,997 | 状态：已完成 - 订单号：ORD-JS-CM-001 | 日期：2026-05-07 | 销售员：李娜-太原产康顾问 | 客户：太原小店区宝妈社群A | 金额：¥13,998 | 状态：已完成 小计：完成订单 3 笔，金额合计 ¥78,987
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.id, sa_sales_order.order_no, sa_sales_order.rep_id, sa_sales_order.product_id, sa_sales_order.region_id, sa_sales_order.customer_name, sa_sales_order.quantity, sa_sales_order.unit_price, sa_sales_order.amount, sa_sales_order.cost, sa_sales_order.profit, sa_sales_order.status, sa_sales_order.order_date, sa_sales_order.created_at FROM sa_sales_order WHERE sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s AND sa_sales_order.rep_id = %(rep_id_1)s ORDER BY sa_sales_order.order_date DESC, sa_sales_order.id DESC
```
参数：`{'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31), 'rep_id_1': 9103}`
耗时：`29.55` ms

2.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`28.17` ms

3.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`26.79` ms

4.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`27.34` ms

LLM SQL：

1. generated / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date AND o.rep_id = :rep_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "limit": 20}`
耗时：`5934.59` ms
token：`prompt=730, completion=251, reasoning=0, total=981`

2. executed
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date AND o.rep_id = :rep_id AND o.rep_id = :scope_rep_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "limit": 20, "scope_rep_id": 9103}`
耗时：`29.91` ms
返回行数：`3`

3. audit / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date >= :start_date AND o.order_date <= :end_date AND o.rep_id = :rep_id AND o.rep_id = :scope_rep_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "limit": 20, "scope_rep_id": 9103}`
返回行数：`3`

### 普通销售员 / get_top_reps / 个人排名视角

- 用户问题：我在排名中的情况
- 结果一致：是
- 静态耗时：71.77 ms
- LLM耗时：39.26 ms
- LLM模式：template
- 命中情况：template=1 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
销售员业绩排名（2026-05-01 至 2026-05-31，全公司）： 第 1 名：李娜-太原产康顾问（华北区） 销售额：¥78,987
```

LLM 结果预览：
```text
销售员业绩排名（2026-05-01 至 2026-05-31，全公司）： 第 1 名：李娜-太原产康顾问（华北区） 销售额：¥78,987
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.rep_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`25.39` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`22.2` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`21.89` ms

LLM SQL：

1. executed
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :scope_rep_id GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "scope_rep_id": 9103}`
耗时：`38.35` ms
返回行数：`1`

2. audit / rep_ranking
```sql
SELECT o.rep_id, s.name AS rep_name, s.region_id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :scope_rep_id GROUP BY o.rep_id, s.name, s.region_id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "scope_rep_id": 9103}`
返回行数：`1`

### 普通销售员 / get_region_ranking / 大区排名权限

- 用户问题：我能看大区排名吗
- 结果一致：是
- 静态耗时：53.83 ms
- LLM耗时：297.19 ms
- LLM模式：bypass
- 命中情况：template=0 / cache=0 / generator=0
- 静态 token：0
- LLM token：0（prompt 0 / completion 0 / reasoning 0）

静态结果预览：
```text
该时段内暂无数据
```

LLM 结果预览：
```text
该时段内暂无数据
```

静态 SQL：

1.
```sql
SELECT sa_sales_order.region_id, sum(sa_sales_order.amount) AS total FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.region_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`26.42` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`25.66` ms

LLM SQL：
无。

### 普通销售员 / get_monthly_trend / 个人趋势

- 用户问题：看我近 6 个月趋势
- 结果一致：否
- 静态耗时：34.26 ms
- LLM耗时：5278.14 ms
- LLM模式：generator
- 命中情况：template=0 / cache=0 / generator=1
- 静态 token：0
- LLM token：917（prompt 692 / completion 225 / reasoning 0）

静态结果预览：
```text
月度销售趋势（近 6 个月，全公司）： 2025-11：¥103,578 订单数：3 2025-12：¥154,473 订单数：2 (↑49.1%) 2026-01：¥142,978 订单数：3 (↓7.4%) 2026-02：¥61,890 订单数：3 (↓56.7%) 2026-03：¥409,025 订单数：12 (↑560.9%) 2026-04：¥277,553 订单数：8 (↓32.1%) 2026-05：¥152,363 订单数：8 (↓45.1%) 整体趋势：上升 47.1%（2025-11 至 2026-05）
```

LLM 结果预览：
```text
月度销售趋势（近 6 个月，全公司）： 2025-11：¥13,998 订单数：1 2026-04：¥7,998 订单数：1 (↓42.9%) 2026-05：¥78,987 订单数：3 (↑887.6%) 整体趋势：上升 464.3%（2025-11 至 2026-05）
```

静态 SQL：

1.
```sql
SELECT date_format(sa_sales_order.order_date, %(date_format_1)s) AS month, sum(sa_sales_order.amount) AS total, count(sa_sales_order.id) AS order_count FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s AND sa_sales_order.region_id = %(region_id_1)s GROUP BY date_format(sa_sales_order.order_date, %(date_format_1)s) ORDER BY date_format(sa_sales_order.order_date, %(date_format_1)s)
```
参数：`{'date_format_1': '%Y-%m', 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2025, 11, 1), 'order_date_2': datetime.date(2026, 5, 8), 'region_id_1': 3}`
耗时：`33.17` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3}`
耗时：`5241.06` ms
token：`prompt=692, completion=225, reasoning=0, total=917`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id AND o.rep_id = :scope_rep_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3, "scope_rep_id": 9103}`
耗时：`35.46` ms
返回行数：`3`

3. audit / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date >= :start_date AND o.order_date <= :end_date AND o.region_id = :region_id AND o.rep_id = :scope_rep_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3, "scope_rep_id": 9103}`
返回行数：`3`
