# 写死 SQL vs LLM 生成 SQL 评估报告

## 运行范围

- 运行日期：2026-05-08
- 覆盖角色：销售总监、区域经理、普通销售员
- 覆盖 tool：12 个 tool 全量覆盖
- 图表类额外覆盖维度分支：region / rep / product / category
- 对比内容：SQL 文本、最终结果、工具总耗时、数据库耗时、LLM token 消耗

## 总体结论

- 总场景数：28
- 结果完全一致：26
- LLM SQL 失败：0
- 写死 SQL 失败：0
- 静态方案总耗时：2468.79 ms
- LLM 方案总耗时：473563.35 ms
- LLM 总 token：108889（prompt 90041 / completion 18848 / reasoning 0）

> 说明：SQL 文本不同是正常现象。写死方案通常是多条小查询加 Python 拼装，LLM SQL 更常生成一条带 JOIN / GROUP BY 的 SQL。这里更看重结果一致性、权限范围和成本。

## 场景覆盖清单

| 角色 | tool | 业务场景 | 结果一致 | 静态耗时(ms) | LLM耗时(ms) | LLM总token |
| --- | --- | --- | --- | --- | --- | --- |
| 销售总监 | query_sales_data | 全公司订单明细 | 否 | 606.58 | 9378.74 | 1067 |
| 销售总监 | get_sales_summary | 全公司销售额汇总 | 是 | 13.9 | 4417.5 | 968 |
| 销售总监 | get_top_reps | 全公司销售员排名 | 是 | 59.7 | 5768.46 | 1055 |
| 销售总监 | get_region_ranking | 全公司大区排名 | 是 | 63.21 | 4817.13 | 1002 |
| 销售总监 | get_top_products | 全公司产品 Top5 | 是 | 18.82 | 5754.29 | 1060 |
| 销售总监 | calc_month_over_month | 全公司环比 | 是 | 13.35 | 8437.55 | 1918 |
| 销售总监 | calc_year_over_year | 全公司同比 | 是 | 13.02 | 8457.73 | 1923 |
| 销售总监 | get_monthly_trend | 全公司 6 个月趋势 | 是 | 10.18 | 5006.36 | 1008 |
| 销售总监 | generate_line_chart | 趋势折线图 | 是 | 10.3 | 5007.36 | 1012 |
| 销售总监 | generate_bar_chart | 大区柱状图 | 是 | 15.07 | 4946.45 | 1002 |
| 销售总监 | generate_bar_chart | 销售员柱状图 | 是 | 27.32 | 5756.66 | 1055 |
| 销售总监 | generate_bar_chart | 产品柱状图 | 是 | 26.61 | 5787.88 | 1060 |
| 销售总监 | generate_bar_chart | 品类柱状图 | 是 | 48.29 | 5910.53 | 1068 |
| 销售总监 | generate_pie_chart | 大区饼图 | 是 | 31.51 | 5171.63 | 1010 |
| 销售总监 | generate_pie_chart | 销售员饼图 | 是 | 22.23 | 5747.24 | 1055 |
| 销售总监 | generate_pie_chart | 产品饼图 | 是 | 15.48 | 5789.23 | 1061 |
| 销售总监 | generate_pie_chart | 品类饼图 | 是 | 20.32 | 6023.97 | 1068 |
| 销售总监 | detect_sales_anomalies | 异常检测 | 是 | 874.59 | 321108.93 | 80095 |
| 区域经理 | get_sales_summary | 区域销售额汇总 | 是 | 23.53 | 4265.41 | 965 |
| 区域经理 | query_sales_data | 区域订单明细 | 是 | 273.36 | 6235.38 | 1099 |
| 区域经理 | get_top_reps | 区域销售员排名 | 是 | 102.71 | 5642.48 | 1050 |
| 区域经理 | get_top_products | 区域产品 Top5 | 是 | 27.32 | 6285.24 | 1083 |
| 区域经理 | generate_line_chart | 区域趋势折线图 | 是 | 31.63 | 5715.8 | 1028 |
| 普通销售员 | get_sales_summary | 个人销售额汇总 | 是 | 7.29 | 4880.71 | 992 |
| 普通销售员 | query_sales_data | 个人订单明细 | 是 | 30.01 | 5871.05 | 1097 |
| 普通销售员 | get_top_reps | 个人排名视角 | 是 | 60.68 | 5826.17 | 1055 |
| 普通销售员 | get_region_ranking | 大区排名权限 | 是 | 14.04 | 15.61 | 0 |
| 普通销售员 | get_monthly_trend | 个人趋势 | 否 | 7.74 | 5537.86 | 1033 |

## 按 Tool 聚合

| Tool | 场景数 | 一致率 | 平均静态耗时(ms) | 平均LLM耗时(ms) | 平均静态DB耗时(ms) | 平均LLM生成耗时(ms) | 平均LLMDB耗时(ms) | 平均总token |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calc_month_over_month | 1 | 100% | 13.35 | 8437.55 | 11.97 | 8421.7 | 13.52 | 1918.0 |
| calc_year_over_year | 1 | 100% | 13.02 | 8457.73 | 11.81 | 8441.56 | 13.62 | 1923.0 |
| detect_sales_anomalies | 1 | 100% | 874.59 | 321108.93 | 802.81 | 319514.38 | 1394.88 | 80095.0 |
| generate_bar_chart | 4 | 100% | 29.32 | 5600.38 | 27.14 | 5581.58 | 17.29 | 1046.25 |
| generate_line_chart | 2 | 100% | 20.96 | 5361.58 | 19.3 | 5352.51 | 7.53 | 1020.0 |
| generate_pie_chart | 4 | 100% | 22.38 | 5683.02 | 20.58 | 5673.4 | 8.05 | 1048.5 |
| get_monthly_trend | 2 | 50% | 8.96 | 5272.11 | 7.08 | 5252.28 | 18.23 | 1020.5 |
| get_region_ranking | 2 | 100% | 38.62 | 2416.37 | 36.2 | 2404.45 | 3.35 | 501.0 |
| get_sales_summary | 3 | 100% | 14.91 | 4521.21 | 12.41 | 4496.18 | 22.84 | 975.0 |
| get_top_products | 2 | 100% | 23.07 | 6019.76 | 18.71 | 5996.95 | 20.9 | 1071.5 |
| get_top_reps | 3 | 100% | 74.36 | 5745.7 | 70.63 | 5724.45 | 19.33 | 1053.33 |
| query_sales_data | 3 | 67% | 303.32 | 7161.72 | 194.44 | 5711.26 | 22.18 | 1087.67 |

## 偏差场景

- `销售总监 / query_sales_data / 全公司订单明细`：静态方案先查全量订单再在文本层截前 N 条；当前 LLM SQL 在 SQL 层直接 `LIMIT 20`，导致“共找到 N 条订单”口径不同。
- `普通销售员 / get_monthly_trend / 个人趋势`：静态方案对销售员趋势按 `region_id` 查区域趋势；LLM SQL 经过权限注入后额外加了 `o.rep_id = :scope_rep_id`，返回的是个人趋势。

## 上线建议

### 继续写死 SQL

`calc_month_over_month`, `calc_year_over_year`, `detect_sales_anomalies`, `generate_bar_chart`, `generate_line_chart`, `generate_pie_chart`, `get_monthly_trend`, `get_sales_summary`, `query_sales_data`

### 可优先切到 LLM SQL

`get_region_ranking`, `get_top_products`, `get_top_reps`

| Tool | 建议 | 一致率 | 平均静态耗时(ms) | 平均LLM耗时(ms) | 平均总token | 原因 |
| --- | --- | --- | --- | --- | --- | --- |
| calc_month_over_month | 继续写死 SQL | 100% | 13.35 | 8437.55 | 1918.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 632.0 倍，新增灵活性收益有限。 |
| calc_year_over_year | 继续写死 SQL | 100% | 13.02 | 8457.73 | 1923.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 649.6 倍，新增灵活性收益有限。 |
| detect_sales_anomalies | 继续写死 SQL | 100% | 874.59 | 321108.93 | 80095.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 367.2 倍，新增灵活性收益有限。 |
| generate_bar_chart | 继续写死 SQL | 100% | 29.32 | 5600.38 | 1046.25 | 这是图表包装层 tool，灵活性主要来自底层 ranking/product 查询，没必要把图表组装本身切到 LLM 主链路。 |
| generate_line_chart | 继续写死 SQL | 100% | 20.96 | 5361.58 | 1020.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 255.8 倍，新增灵活性收益有限。 |
| generate_pie_chart | 继续写死 SQL | 100% | 22.38 | 5683.02 | 1048.5 | 这是图表包装层 tool，灵活性主要来自底层 ranking/product 查询，没必要把图表组装本身切到 LLM 主链路。 |
| get_monthly_trend | 继续写死 SQL | 50% | 8.96 | 5272.11 | 1020.5 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 588.4 倍，新增灵活性收益有限。 |
| get_region_ranking | 可优先切到 LLM SQL | 100% | 38.62 | 2416.37 | 501.0 | 结果一致性已经足够高，且这类查询/图表维度更容易继续扩展过滤条件、排序和组合维度。 |
| get_sales_summary | 继续写死 SQL | 100% | 14.91 | 4521.21 | 975.0 | 结果稳定但查询口径非常固定，LLM 平均耗时约为静态方案的 303.2 倍，新增灵活性收益有限。 |
| get_top_products | 可优先切到 LLM SQL | 100% | 23.07 | 6019.76 | 1071.5 | 结果一致性已经足够高，且这类查询/图表维度更容易继续扩展过滤条件、排序和组合维度。 |
| get_top_reps | 可优先切到 LLM SQL | 100% | 74.36 | 5745.7 | 1053.33 | 结果一致性已经足够高，且这类查询/图表维度更容易继续扩展过滤条件、排序和组合维度。 |
| query_sales_data | 继续写死 SQL | 67% | 303.32 | 7161.72 | 1087.67 | 当前一致性或可观测性还不够稳，继续保留确定性查询更合适。 |

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

## 每个场景的 SQL 对比

### 销售总监 / query_sales_data / 全公司订单明细

- 用户问题：列出本月全公司前 8 条订单
- 结果一致：否
- 静态耗时：606.58 ms
- LLM耗时：9378.74 ms
- LLM token：1067（prompt 847 / completion 220 / reasoning 0）

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
耗时：`37.83` ms

2.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9109}`
耗时：`33.72` ms

3.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`31.98` ms

4.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9111}`
耗时：`29.06` ms

5.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9108}`
耗时：`28.71` ms

6.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`27.87` ms

7.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`31.88` ms

8.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9111}`
耗时：`35.73` ms

9.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`35.22` ms

LLM SQL：

1. generated / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o LEFT JOIN sa_sales_rep s ON s.id = o.rep_id LEFT JOIN sa_sales_region r ON r.id = o.region_id LEFT JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date ORDER BY o.order_date DESC, o.id DESC LIMIT 20
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`5399.0` ms
token：`prompt=847, completion=220, reasoning=0, total=1067`

2. executed
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o LEFT JOIN sa_sales_rep s ON s.id = o.rep_id LEFT JOIN sa_sales_region r ON r.id = o.region_id LEFT JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date ORDER BY o.order_date DESC, o.id DESC LIMIT 20
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "limit": 20}`
耗时：`9.65` ms
返回行数：`20`

### 销售总监 / get_sales_summary / 全公司销售额汇总

- 用户问题：本月全公司销售额是多少
- 结果一致：是
- 静态耗时：13.9 ms
- LLM耗时：4417.5 ms
- LLM token：968（prompt 787 / completion 181 / reasoning 0）

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
耗时：`9.52` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`4391.49` ms
token：`prompt=787, completion=181, reasoning=0, total=968`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`24.3` ms
返回行数：`1`

### 销售总监 / get_top_reps / 全公司销售员排名

- 用户问题：本月全公司销售员 TOP5
- 结果一致：是
- 静态耗时：59.7 ms
- LLM耗时：5768.46 ms
- LLM token：1055（prompt 810 / completion 245 / reasoning 0）

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
耗时：`18.45` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`18.98` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`16.04` ms

LLM SQL：

1. generated / rep_ranking
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5732.04` ms
token：`prompt=810, completion=245, reasoning=0, total=1055`

2. executed
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`34.19` ms
返回行数：`5`

### 销售总监 / get_region_ranking / 全公司大区排名

- 用户问题：本月全公司大区排名
- 结果一致：是
- 静态耗时：63.21 ms
- LLM耗时：4817.13 ms
- LLM token：1002（prompt 799 / completion 203 / reasoning 0）

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
耗时：`30.64` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`29.14` ms

LLM SQL：

1. generated / region_ranking
```sql
SELECT r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY r.id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`4808.89` ms
token：`prompt=799, completion=203, reasoning=0, total=1002`

2. executed
```sql
SELECT r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY r.id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`6.7` ms
返回行数：`4`

### 销售总监 / get_top_products / 全公司产品 Top5

- 用户问题：本月全公司产品 TOP5
- 结果一致：是
- 静态耗时：18.82 ms
- LLM耗时：5754.29 ms
- LLM token：1060（prompt 816 / completion 244 / reasoning 0）

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
耗时：`6.85` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`8.03` ms

LLM SQL：

1. generated / product_ranking
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5742.86` ms
token：`prompt=816, completion=244, reasoning=0, total=1060`

2. executed
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`10.07` ms
返回行数：`5`

### 销售总监 / calc_month_over_month / 全公司环比

- 用户问题：本月和上月环比
- 结果一致：是
- 静态耗时：13.35 ms
- LLM耗时：8437.55 ms
- LLM token：1918（prompt 1574 / completion 344 / reasoning 0）

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
耗时：`5.79` ms

2.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 1), 'order_date_2': datetime.date(2026, 4, 30)}`
耗时：`6.18` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`4507.18` ms
token：`prompt=787, completion=181, reasoning=0, total=968`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`6.94` ms
返回行数：`1`

3. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-04-01", "end_date": "2026-04-30"}`
耗时：`3914.52` ms
token：`prompt=787, completion=163, reasoning=0, total=950`

4. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-04-01", "end_date": "2026-04-30"}`
耗时：`6.58` ms
返回行数：`1`

### 销售总监 / calc_year_over_year / 全公司同比

- 用户问题：本月同比去年同期
- 结果一致：是
- 静态耗时：13.02 ms
- LLM耗时：8457.73 ms
- LLM token：1923（prompt 1574 / completion 349 / reasoning 0）

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
耗时：`6.28` ms

2.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2025, 5, 1), 'order_date_2': datetime.date(2025, 5, 31)}`
耗时：`5.53` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`4438.88` ms
token：`prompt=787, completion=181, reasoning=0, total=968`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`7.05` ms
返回行数：`1`

3. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2025-05-01", "end_date": "2025-05-31"}`
耗时：`4002.68` ms
token：`prompt=787, completion=168, reasoning=0, total=955`

4. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED'
```
参数：`{"start_date": "2025-05-01", "end_date": "2025-05-31"}`
耗时：`6.57` ms
返回行数：`1`

### 销售总监 / get_monthly_trend / 全公司 6 个月趋势

- 用户问题：全公司近 6 个月趋势
- 结果一致：是
- 静态耗时：10.18 ms
- LLM耗时：5006.36 ms
- LLM token：1008（prompt 800 / completion 208 / reasoning 0）

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
耗时：`7.83` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`4990.98` ms
token：`prompt=800, completion=208, reasoning=0, total=1008`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`14.05` ms
返回行数：`7`

### 销售总监 / generate_line_chart / 趋势折线图

- 用户问题：给我近 6 个月折线图
- 结果一致：是
- 静态耗时：10.3 ms
- LLM耗时：5007.36 ms
- LLM token：1012（prompt 800 / completion 212 / reasoning 0）

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
耗时：`9.31` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o INNER JOIN sa_sales_rep s ON s.id = o.rep_id INNER JOIN sa_sales_region r ON r.id = o.region_id INNER JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`4997.88` ms
token：`prompt=800, completion=212, reasoning=0, total=1012`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o INNER JOIN sa_sales_rep s ON s.id = o.rep_id INNER JOIN sa_sales_region r ON r.id = o.region_id INNER JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08"}`
耗时：`7.89` ms
返回行数：`7`

### 销售总监 / generate_bar_chart / 大区柱状图

- 用户问题：按大区生成柱状图
- 结果一致：是
- 静态耗时：15.07 ms
- LLM耗时：4946.45 ms
- LLM token：1002（prompt 799 / completion 203 / reasoning 0）

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
耗时：`6.2` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`7.23` ms

LLM SQL：

1. generated / region_ranking
```sql
SELECT r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY r.id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`4933.77` ms
token：`prompt=799, completion=203, reasoning=0, total=1002`

2. executed
```sql
SELECT r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY r.id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`11.21` ms
返回行数：`4`

### 销售总监 / generate_bar_chart / 销售员柱状图

- 用户问题：按销售员生成柱状图
- 结果一致：是
- 静态耗时：27.32 ms
- LLM耗时：5756.66 ms
- LLM token：1055（prompt 810 / completion 245 / reasoning 0）

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
耗时：`8.45` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`8.9` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`6.65` ms

LLM SQL：

1. generated / rep_ranking
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5744.17` ms
token：`prompt=810, completion=245, reasoning=0, total=1055`

2. executed
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`10.97` ms
返回行数：`5`

### 销售总监 / generate_bar_chart / 产品柱状图

- 用户问题：按产品生成柱状图
- 结果一致：是
- 静态耗时：26.61 ms
- LLM耗时：5787.88 ms
- LLM token：1060（prompt 816 / completion 244 / reasoning 0）

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
耗时：`11.5` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`13.33` ms

LLM SQL：

1. generated / product_ranking
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5761.06` ms
token：`prompt=816, completion=244, reasoning=0, total=1060`

2. executed
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`25.4` ms
返回行数：`5`

### 销售总监 / generate_bar_chart / 品类柱状图

- 用户问题：按品类生成柱状图
- 结果一致：是
- 静态耗时：48.29 ms
- LLM耗时：5910.53 ms
- LLM token：1068（prompt 818 / completion 250 / reasoning 0）

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
耗时：`24.59` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`21.71` ms

LLM SQL：

1. generated / product_ranking
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100}`
耗时：`5887.31` ms
token：`prompt=818, completion=250, reasoning=0, total=1068`

2. executed
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100}`
耗时：`21.58` ms
返回行数：`24`

### 销售总监 / generate_pie_chart / 大区饼图

- 用户问题：按大区生成饼图
- 结果一致：是
- 静态耗时：31.51 ms
- LLM耗时：5171.63 ms
- LLM token：1010（prompt 799 / completion 211 / reasoning 0）

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
耗时：`16.18` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`13.98` ms

LLM SQL：

1. generated / region_ranking
```sql
SELECT r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY r.id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`5163.22` ms
token：`prompt=799, completion=211, reasoning=0, total=1010`

2. executed
```sql
SELECT r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY r.id, r.name ORDER BY total_amount DESC
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31"}`
耗时：`7.04` ms
返回行数：`4`

### 销售总监 / generate_pie_chart / 销售员饼图

- 用户问题：按销售员生成饼图
- 结果一致：是
- 静态耗时：22.23 ms
- LLM耗时：5747.24 ms
- LLM token：1055（prompt 810 / completion 245 / reasoning 0）

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
耗时：`5.94` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`7.79` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`6.19` ms

LLM SQL：

1. generated / rep_ranking
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5738.72` ms
token：`prompt=810, completion=245, reasoning=0, total=1055`

2. executed
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`6.82` ms
返回行数：`5`

### 销售总监 / generate_pie_chart / 产品饼图

- 用户问题：按产品生成饼图
- 结果一致：是
- 静态耗时：15.48 ms
- LLM耗时：5789.23 ms
- LLM token：1061（prompt 816 / completion 245 / reasoning 0）

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
耗时：`6.86` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`6.85` ms

LLM SQL：

1. generated / product_ranking
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5779.62` ms
token：`prompt=816, completion=245, reasoning=0, total=1061`

2. executed
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`7.98` ms
返回行数：`5`

### 销售总监 / generate_pie_chart / 品类饼图

- 用户问题：按品类生成饼图
- 结果一致：是
- 静态耗时：20.32 ms
- LLM耗时：6023.97 ms
- LLM token：1068（prompt 818 / completion 250 / reasoning 0）

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
耗时：`9.1` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31)}`
耗时：`9.43` ms

LLM SQL：

1. generated / product_ranking
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100}`
耗时：`6012.03` ms
token：`prompt=818, completion=250, reasoning=0, total=1068`

2. executed
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 100}`
耗时：`10.36` ms
返回行数：`24`

### 销售总监 / detect_sales_anomalies / 异常检测

- 用户问题：检测当前销售异常
- 结果一致：是
- 静态耗时：874.59 ms
- LLM耗时：321108.93 ms
- LLM token：80095（prompt 67436 / completion 12659 / reasoning 0）

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
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`8.5` ms

2.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 1, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 24), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`13.69` ms

3.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 1, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 27), 'order_date_2': datetime.date(2026, 4, 23)}`
耗时：`10.81` ms

4.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 2, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 24), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`9.21` ms

5.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 2, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 27), 'order_date_2': datetime.date(2026, 4, 23)}`
耗时：`9.7` ms

6.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 3, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 24), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`11.82` ms

7.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 3, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 27), 'order_date_2': datetime.date(2026, 4, 23)}`
耗时：`12.32` ms

8.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 4, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 24), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`12.2` ms

9.
```sql
SELECT count(sa_sales_order.id) AS count_1 FROM sa_sales_order WHERE sa_sales_order.region_id = %(region_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'region_id_1': 4, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 27), 'order_date_2': datetime.date(2026, 4, 23)}`
耗时：`14.51` ms

10.
```sql
SELECT sa_product.id, sa_product.sku_code, sa_product.name, sa_product.category, sa_product.unit_price, sa_product.cost, sa_product.status, sa_product.created_at FROM sa_product WHERE sa_product.status = %(status_1)s
```
参数：`{'status_1': 'ACTIVE'}`
耗时：`16.59` ms

11.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 1, 'status_1': 'COMPLETED'}`
耗时：`20.58` ms

12.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 2, 'status_1': 'COMPLETED'}`
耗时：`16.08` ms

13.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 3, 'status_1': 'COMPLETED'}`
耗时：`15.63` ms

14.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 4, 'status_1': 'COMPLETED'}`
耗时：`16.84` ms

15.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 5, 'status_1': 'COMPLETED'}`
耗时：`14.52` ms

16.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 6, 'status_1': 'COMPLETED'}`
耗时：`13.85` ms

17.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 7, 'status_1': 'COMPLETED'}`
耗时：`16.21` ms

18.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 8, 'status_1': 'COMPLETED'}`
耗时：`13.16` ms

19.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9, 'status_1': 'COMPLETED'}`
耗时：`12.48` ms

20.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 10, 'status_1': 'COMPLETED'}`
耗时：`11.81` ms

21.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 11, 'status_1': 'COMPLETED'}`
耗时：`14.3` ms

22.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 12, 'status_1': 'COMPLETED'}`
耗时：`12.3` ms

23.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 13, 'status_1': 'COMPLETED'}`
耗时：`10.33` ms

24.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 14, 'status_1': 'COMPLETED'}`
耗时：`8.41` ms

25.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 15, 'status_1': 'COMPLETED'}`
耗时：`7.08` ms

26.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 16, 'status_1': 'COMPLETED'}`
耗时：`7.38` ms

27.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 17, 'status_1': 'COMPLETED'}`
耗时：`7.58` ms

28.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 18, 'status_1': 'COMPLETED'}`
耗时：`7.11` ms

29.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 19, 'status_1': 'COMPLETED'}`
耗时：`9.26` ms

30.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 20, 'status_1': 'COMPLETED'}`
耗时：`7.9` ms

31.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9201, 'status_1': 'COMPLETED'}`
耗时：`8.07` ms

32.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9202, 'status_1': 'COMPLETED'}`
耗时：`8.01` ms

33.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9203, 'status_1': 'COMPLETED'}`
耗时：`8.57` ms

34.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9204, 'status_1': 'COMPLETED'}`
耗时：`10.96` ms

35.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9205, 'status_1': 'COMPLETED'}`
耗时：`10.06` ms

36.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9206, 'status_1': 'COMPLETED'}`
耗时：`10.85` ms

37.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9207, 'status_1': 'COMPLETED'}`
耗时：`10.39` ms

38.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9208, 'status_1': 'COMPLETED'}`
耗时：`11.27` ms

39.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9209, 'status_1': 'COMPLETED'}`
耗时：`11.66` ms

40.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9210, 'status_1': 'COMPLETED'}`
耗时：`11.6` ms

41.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9211, 'status_1': 'COMPLETED'}`
耗时：`11.24` ms

42.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9212, 'status_1': 'COMPLETED'}`
耗时：`10.19` ms

43.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9213, 'status_1': 'COMPLETED'}`
耗时：`9.86` ms

44.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9214, 'status_1': 'COMPLETED'}`
耗时：`8.9` ms

45.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9215, 'status_1': 'COMPLETED'}`
耗时：`9.13` ms

46.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9216, 'status_1': 'COMPLETED'}`
耗时：`7.82` ms

47.
```sql
SELECT max(sa_sales_order.order_date) AS max_1 FROM sa_sales_order WHERE sa_sales_order.product_id = %(product_id_1)s AND sa_sales_order.status = %(status_1)s
```
参数：`{'product_id_1': 9217, 'status_1': 'COMPLETED'}`
耗时：`9.09` ms

48.
```sql
SELECT sa_sales_order.rep_id, sum(CASE WHEN (sa_sales_order.status = %(status_1)s) THEN %(param_1)s ELSE %(param_2)s END) AS refunded, count(sa_sales_order.id) AS total FROM sa_sales_order WHERE sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s GROUP BY sa_sales_order.rep_id
```
参数：`{'status_1': 'REFUNDED', 'param_1': 1, 'param_2': 0, 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`8.88` ms

49.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 3}`
耗时：`8.49` ms

50.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9105}`
耗时：`6.31` ms

51.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep WHERE sa_sales_rep.`role` = %(role_1)s
```
参数：`{'role_1': 'SALES_REP'}`
耗时：`7.23` ms

52.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 2, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`7.31` ms

53.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 2, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`7.93` ms

54.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 3, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`10.55` ms

55.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 3, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`7.52` ms

56.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 5, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`7.64` ms

57.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 5, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`7.5` ms

58.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 6, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.81` ms

59.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 6, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`5.4` ms

60.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 8, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.32` ms

61.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 8, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.31` ms

62.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.45` ms

63.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.03` ms

64.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 11, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.77` ms

65.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 11, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`7.15` ms

66.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 12, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.48` ms

67.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 12, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`5.91` ms

68.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9103, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`5.82` ms

69.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9103, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.29` ms

70.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9104, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.68` ms

71.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9104, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.69` ms

72.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9105, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`5.97` ms

73.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9105, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.7` ms

74.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9106, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.92` ms

75.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9106, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`5.44` ms

76.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9108, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.45` ms

77.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9108, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.01` ms

78.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9109, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.25` ms

79.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9109, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.85` ms

80.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9111, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`7.03` ms

81.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9111, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.58` ms

82.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9112, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.99` ms

83.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9112, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`7.6` ms

84.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9114, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.44` ms

85.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9114, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.7` ms

86.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9115, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 4, 8), 'order_date_2': datetime.date(2026, 5, 8)}`
耗时：`6.25` ms

87.
```sql
SELECT coalesce(sum(sa_sales_order.amount), %(coalesce_2)s) AS coalesce_1 FROM sa_sales_order WHERE sa_sales_order.rep_id = %(rep_id_1)s AND sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s
```
参数：`{'coalesce_2': 0, 'rep_id_1': 9115, 'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 3, 9), 'order_date_2': datetime.date(2026, 4, 7)}`
耗时：`6.33` ms

LLM SQL：

1. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 1}`
耗时：`4593.69` ms
token：`prompt=826, completion=187, reasoning=0, total=1013`

2. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 1}`
耗时：`14.39` ms
返回行数：`1`

3. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 1}`
耗时：`4610.73` ms
token：`prompt=826, completion=186, reasoning=0, total=1012`

4. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 1}`
耗时：`19.35` ms
返回行数：`1`

5. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 2}`
耗时：`4430.78` ms
token：`prompt=826, completion=187, reasoning=0, total=1013`

6. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 2}`
耗时：`8.26` ms
返回行数：`1`

7. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 2}`
耗时：`4374.37` ms
token：`prompt=826, completion=184, reasoning=0, total=1010`

8. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 2}`
耗时：`6.75` ms
返回行数：`1`

9. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 3}`
耗时：`4912.24` ms
token：`prompt=826, completion=187, reasoning=0, total=1013`

10. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 3}`
耗时：`14.0` ms
返回行数：`1`

11. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 3}`
耗时：`4782.51` ms
token：`prompt=826, completion=193, reasoning=0, total=1019`

12. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 3}`
耗时：`15.63` ms
返回行数：`1`

13. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 4}`
耗时：`4426.76` ms
token：`prompt=826, completion=184, reasoning=0, total=1010`

14. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-04-24", "end_date": "2026-05-08", "region_id": 4}`
耗时：`23.38` ms
返回行数：`1`

15. generated / order_count
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 4}`
耗时：`4932.59` ms
token：`prompt=826, completion=187, reasoning=0, total=1013`

16. executed
```sql
SELECT COUNT(o.id) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id
```
参数：`{"start_date": "2026-03-27", "end_date": "2026-04-23", "region_id": 4}`
耗时：`23.57` ms
返回行数：`1`

17. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 1}`
耗时：`2553.22` ms
token：`prompt=814, completion=98, reasoning=0, total=912`

18. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 1}`
耗时：`6.67` ms
返回行数：`1`

19. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 2}`
耗时：`2921.76` ms
token：`prompt=814, completion=111, reasoning=0, total=925`

20. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 2}`
耗时：`5.8` ms
返回行数：`1`

21. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 3}`
耗时：`2709.13` ms
token：`prompt=814, completion=110, reasoning=0, total=924`

22. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 3}`
耗时：`6.15` ms
返回行数：`1`

23. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 4}`
耗时：`2795.12` ms
token：`prompt=814, completion=111, reasoning=0, total=925`

24. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 4}`
耗时：`7.53` ms
返回行数：`1`

25. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 5}`
耗时：`2692.23` ms
token：`prompt=814, completion=99, reasoning=0, total=913`

26. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 5}`
耗时：`19.05` ms
返回行数：`1`

27. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 6}`
耗时：`2920.08` ms
token：`prompt=814, completion=114, reasoning=0, total=928`

28. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 6}`
耗时：`5.95` ms
返回行数：`1`

29. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 7}`
耗时：`2816.01` ms
token：`prompt=814, completion=110, reasoning=0, total=924`

30. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 7}`
耗时：`5.94` ms
返回行数：`1`

31. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 8}`
耗时：`2587.25` ms
token：`prompt=814, completion=99, reasoning=0, total=913`

32. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 8}`
耗时：`18.49` ms
返回行数：`1`

33. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9}`
耗时：`2900.68` ms
token：`prompt=814, completion=111, reasoning=0, total=925`

34. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9}`
耗时：`6.04` ms
返回行数：`1`

35. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 10}`
耗时：`2517.49` ms
token：`prompt=815, completion=99, reasoning=0, total=914`

36. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 10}`
耗时：`5.71` ms
返回行数：`1`

37. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 11}`
耗时：`2439.6` ms
token：`prompt=815, completion=94, reasoning=0, total=909`

38. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 11}`
耗时：`8.26` ms
返回行数：`1`

39. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 12}`
耗时：`2946.58` ms
token：`prompt=815, completion=112, reasoning=0, total=927`

40. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 12}`
耗时：`6.85` ms
返回行数：`1`

41. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 13}`
耗时：`3236.11` ms
token：`prompt=815, completion=115, reasoning=0, total=930`

42. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 13}`
耗时：`6.32` ms
返回行数：`1`

43. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 14}`
耗时：`2893.69` ms
token：`prompt=815, completion=112, reasoning=0, total=927`

44. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 14}`
耗时：`10.96` ms
返回行数：`1`

45. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 15}`
耗时：`2934.42` ms
token：`prompt=815, completion=117, reasoning=0, total=932`

46. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 15}`
耗时：`7.74` ms
返回行数：`1`

47. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 16}`
耗时：`2838.5` ms
token：`prompt=815, completion=111, reasoning=0, total=926`

48. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 16}`
耗时：`25.62` ms
返回行数：`1`

49. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 17}`
耗时：`4528.91` ms
token：`prompt=815, completion=112, reasoning=0, total=927`

50. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 17}`
耗时：`6.74` ms
返回行数：`1`

51. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 18}`
耗时：`2937.15` ms
token：`prompt=815, completion=116, reasoning=0, total=931`

52. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 18}`
耗时：`31.71` ms
返回行数：`1`

53. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 19}`
耗时：`3261.1` ms
token：`prompt=815, completion=117, reasoning=0, total=932`

54. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 19}`
耗时：`34.29` ms
返回行数：`1`

55. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 20}`
耗时：`2799.6` ms
token：`prompt=815, completion=111, reasoning=0, total=926`

56. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 20}`
耗时：`283.4` ms
返回行数：`1`

57. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9201}`
耗时：`2600.32` ms
token：`prompt=817, completion=101, reasoning=0, total=918`

58. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9201}`
耗时：`13.76` ms
返回行数：`1`

59. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9202}`
耗时：`2575.31` ms
token：`prompt=817, completion=101, reasoning=0, total=918`

60. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9202}`
耗时：`8.72` ms
返回行数：`1`

61. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9203}`
耗时：`2623.44` ms
token：`prompt=817, completion=101, reasoning=0, total=918`

62. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9203}`
耗时：`17.36` ms
返回行数：`1`

63. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9204}`
耗时：`2822.51` ms
token：`prompt=817, completion=113, reasoning=0, total=930`

64. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9204}`
耗时：`27.31` ms
返回行数：`1`

65. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9205}`
耗时：`2937.36` ms
token：`prompt=817, completion=116, reasoning=0, total=933`

66. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9205}`
耗时：`10.12` ms
返回行数：`1`

67. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9206}`
耗时：`3063.38` ms
token：`prompt=817, completion=118, reasoning=0, total=935`

68. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9206}`
耗时：`6.32` ms
返回行数：`1`

69. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9207}`
耗时：`2690.68` ms
token：`prompt=817, completion=101, reasoning=0, total=918`

70. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9207}`
耗时：`8.8` ms
返回行数：`1`

71. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9208}`
耗时：`3060.33` ms
token：`prompt=817, completion=113, reasoning=0, total=930`

72. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9208}`
耗时：`6.68` ms
返回行数：`1`

73. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9209}`
耗时：`2853.49` ms
token：`prompt=817, completion=113, reasoning=0, total=930`

74. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9209}`
耗时：`7.9` ms
返回行数：`1`

75. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9210}`
耗时：`2546.19` ms
token：`prompt=817, completion=101, reasoning=0, total=918`

76. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9210}`
耗时：`6.43` ms
返回行数：`1`

77. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9211}`
耗时：`3013.78` ms
token：`prompt=817, completion=114, reasoning=0, total=931`

78. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9211}`
耗时：`7.52` ms
返回行数：`1`

79. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9212}`
耗时：`2932.48` ms
token：`prompt=817, completion=118, reasoning=0, total=935`

80. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9212}`
耗时：`6.38` ms
返回行数：`1`

81. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9213}`
耗时：`2466.12` ms
token：`prompt=817, completion=96, reasoning=0, total=913`

82. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9213}`
耗时：`9.31` ms
返回行数：`1`

83. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9214}`
耗时：`3068.11` ms
token：`prompt=817, completion=114, reasoning=0, total=931`

84. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9214}`
耗时：`9.34` ms
返回行数：`1`

85. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9215}`
耗时：`2907.81` ms
token：`prompt=817, completion=113, reasoning=0, total=930`

86. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9215}`
耗时：`30.75` ms
返回行数：`1`

87. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9216}`
耗时：`2880.54` ms
token：`prompt=817, completion=114, reasoning=0, total=931`

88. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9216}`
耗时：`15.6` ms
返回行数：`1`

89. generated / last_order_date
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9217}`
耗时：`2559.63` ms
token：`prompt=817, completion=101, reasoning=0, total=918`

90. executed
```sql
SELECT MAX(o.order_date) AS last_order_date FROM sa_sales_order o WHERE o.product_id = :product_id AND o.status = 'COMPLETED'
```
参数：`{"product_id": 9217}`
耗时：`6.47` ms
返回行数：`1`

91. generated / refund_rates
```sql
SELECT o.rep_id, SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded, COUNT(o.id) AS total FROM sa_sales_order o LEFT JOIN sa_sales_rep s ON s.id = o.rep_id LEFT JOIN sa_sales_region r ON r.id = o.region_id LEFT JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08"}`
耗时：`4813.5` ms
token：`prompt=848, completion=204, reasoning=0, total=1052`

92. executed
```sql
SELECT o.rep_id, SUM(CASE WHEN o.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refunded, COUNT(o.id) AS total FROM sa_sales_order o LEFT JOIN sa_sales_rep s ON s.id = o.rep_id LEFT JOIN sa_sales_region r ON r.id = o.region_id LEFT JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date GROUP BY o.rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08"}`
耗时：`25.81` ms
返回行数：`16`

93. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 2}`
耗时：`4579.98` ms
token：`prompt=826, completion=186, reasoning=0, total=1012`

94. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 2}`
耗时：`14.04` ms
返回行数：`1`

95. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 2}`
耗时：`4598.88` ms
token：`prompt=826, completion=189, reasoning=0, total=1015`

96. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 2}`
耗时：`29.66` ms
返回行数：`1`

97. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 3}`
耗时：`4595.33` ms
token：`prompt=826, completion=193, reasoning=0, total=1019`

98. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 3}`
耗时：`14.12` ms
返回行数：`1`

99. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 3}`
耗时：`4581.84` ms
token：`prompt=826, completion=192, reasoning=0, total=1018`

100. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 3}`
耗时：`7.57` ms
返回行数：`1`

101. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 5}`
耗时：`4478.31` ms
token：`prompt=826, completion=187, reasoning=0, total=1013`

102. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 5}`
耗时：`10.19` ms
返回行数：`1`

103. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 5}`
耗时：`5047.56` ms
token：`prompt=826, completion=195, reasoning=0, total=1021`

104. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 5}`
耗时：`6.87` ms
返回行数：`1`

105. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 6}`
耗时：`4748.9` ms
token：`prompt=826, completion=191, reasoning=0, total=1017`

106. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 6}`
耗时：`31.06` ms
返回行数：`1`

107. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 6}`
耗时：`5096.51` ms
token：`prompt=826, completion=193, reasoning=0, total=1019`

108. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 6}`
耗时：`20.07` ms
返回行数：`1`

109. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 8}`
耗时：`4756.03` ms
token：`prompt=826, completion=193, reasoning=0, total=1019`

110. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 8}`
耗时：`7.03` ms
返回行数：`1`

111. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 8}`
耗时：`4736.83` ms
token：`prompt=826, completion=193, reasoning=0, total=1019`

112. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 8}`
耗时：`13.64` ms
返回行数：`1`

113. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9}`
耗时：`4489.58` ms
token：`prompt=826, completion=187, reasoning=0, total=1013`

114. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9}`
耗时：`29.32` ms
返回行数：`1`

115. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9}`
耗时：`4516.03` ms
token：`prompt=826, completion=190, reasoning=0, total=1016`

116. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9}`
耗时：`7.62` ms
返回行数：`1`

117. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 11}`
耗时：`4524.37` ms
token：`prompt=827, completion=188, reasoning=0, total=1015`

118. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 11}`
耗时：`6.61` ms
返回行数：`1`

119. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 11}`
耗时：`4763.62` ms
token：`prompt=827, completion=195, reasoning=0, total=1022`

120. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 11}`
耗时：`34.39` ms
返回行数：`1`

121. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 12}`
耗时：`5052.94` ms
token：`prompt=827, completion=196, reasoning=0, total=1023`

122. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 12}`
耗时：`26.0` ms
返回行数：`1`

123. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 12}`
耗时：`4774.7` ms
token：`prompt=827, completion=189, reasoning=0, total=1016`

124. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 12}`
耗时：`6.47` ms
返回行数：`1`

125. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9103}`
耗时：`4833.04` ms
token：`prompt=829, completion=192, reasoning=0, total=1021`

126. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9103}`
耗时：`6.67` ms
返回行数：`1`

127. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9103}`
耗时：`4677.17` ms
token：`prompt=829, completion=196, reasoning=0, total=1025`

128. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9103}`
耗时：`10.7` ms
返回行数：`1`

129. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9104}`
耗时：`4679.75` ms
token：`prompt=829, completion=196, reasoning=0, total=1025`

130. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9104}`
耗时：`6.17` ms
返回行数：`1`

131. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9104}`
耗时：`4513.95` ms
token：`prompt=829, completion=190, reasoning=0, total=1019`

132. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9104}`
耗时：`7.07` ms
返回行数：`1`

133. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9105}`
耗时：`4772.56` ms
token：`prompt=829, completion=197, reasoning=0, total=1026`

134. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9105}`
耗时：`6.54` ms
返回行数：`1`

135. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9105}`
耗时：`4802.7` ms
token：`prompt=829, completion=196, reasoning=0, total=1025`

136. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9105}`
耗时：`30.71` ms
返回行数：`1`

137. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9106}`
耗时：`4651.74` ms
token：`prompt=829, completion=190, reasoning=0, total=1019`

138. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9106}`
耗时：`17.4` ms
返回行数：`1`

139. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9106}`
耗时：`4601.07` ms
token：`prompt=829, completion=192, reasoning=0, total=1021`

140. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9106}`
耗时：`8.22` ms
返回行数：`1`

141. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9108}`
耗时：`4694.91` ms
token：`prompt=829, completion=197, reasoning=0, total=1026`

142. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9108}`
耗时：`30.28` ms
返回行数：`1`

143. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9108}`
耗时：`4655.71` ms
token：`prompt=829, completion=195, reasoning=0, total=1024`

144. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9108}`
耗时：`22.51` ms
返回行数：`1`

145. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9109}`
耗时：`5050.29` ms
token：`prompt=829, completion=196, reasoning=0, total=1025`

146. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9109}`
耗时：`18.43` ms
返回行数：`1`

147. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9109}`
耗时：`4600.16` ms
token：`prompt=829, completion=192, reasoning=0, total=1021`

148. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9109}`
耗时：`24.19` ms
返回行数：`1`

149. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9111}`
耗时：`4946.62` ms
token：`prompt=829, completion=191, reasoning=0, total=1020`

150. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9111}`
耗时：`17.33` ms
返回行数：`1`

151. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9111}`
耗时：`4830.73` ms
token：`prompt=829, completion=197, reasoning=0, total=1026`

152. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9111}`
耗时：`10.38` ms
返回行数：`1`

153. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9112}`
耗时：`4998.76` ms
token：`prompt=829, completion=190, reasoning=0, total=1019`

154. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9112}`
耗时：`7.28` ms
返回行数：`1`

155. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9112}`
耗时：`4831.24` ms
token：`prompt=829, completion=200, reasoning=0, total=1029`

156. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9112}`
耗时：`7.93` ms
返回行数：`1`

157. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9114}`
耗时：`5618.0` ms
token：`prompt=829, completion=196, reasoning=0, total=1025`

158. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9114}`
耗时：`12.21` ms
返回行数：`1`

159. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9114}`
耗时：`4678.45` ms
token：`prompt=829, completion=195, reasoning=0, total=1024`

160. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9114}`
耗时：`6.84` ms
返回行数：`1`

161. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9115}`
耗时：`4707.17` ms
token：`prompt=829, completion=198, reasoning=0, total=1027`

162. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-04-08", "end_date": "2026-05-08", "rep_id": 9115}`
耗时：`6.72` ms
返回行数：`1`

163. generated / rep_amount
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9115}`
耗时：`5321.67` ms
token：`prompt=829, completion=180, reasoning=0, total=1009`

164. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id
```
参数：`{"start_date": "2026-03-09", "end_date": "2026-04-07", "rep_id": 9115}`
耗时：`13.51` ms
返回行数：`1`

### 区域经理 / get_sales_summary / 区域销售额汇总

- 用户问题：我大区本月销售额
- 结果一致：是
- 静态耗时：23.53 ms
- LLM耗时：4265.41 ms
- LLM token：965（prompt 787 / completion 178 / reasoning 0）

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
耗时：`21.68` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' AND o.region_id = :region_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3}`
耗时：`4225.86` ms
token：`prompt=787, completion=178, reasoning=0, total=965`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' AND o.region_id = :region_id AND o.region_id = :scope_region_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "scope_region_id": 3}`
耗时：`36.57` ms
返回行数：`1`

### 区域经理 / query_sales_data / 区域订单明细

- 用户问题：列出我大区本月订单明细
- 结果一致：是
- 静态耗时：273.36 ms
- LLM耗时：6235.38 ms
- LLM token：1099（prompt 847 / completion 252 / reasoning 0）

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
耗时：`43.03` ms

2.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`30.42` ms

3.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`28.18` ms

4.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`27.74` ms

5.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`29.3` ms

6.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`28.27` ms

7.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9104}`
耗时：`26.81` ms

8.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9105}`
耗时：`25.24` ms

9.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9105}`
耗时：`25.93` ms

LLM SQL：

1. generated / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "limit": 20}`
耗时：`5950.13` ms
token：`prompt=847, completion=252, reasoning=0, total=1099`

2. executed
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "limit": 20, "scope_region_id": 3}`
耗时：`39.64` ms
返回行数：`12`

### 区域经理 / get_top_reps / 区域销售员排名

- 用户问题：我大区销售员排名
- 结果一致：是
- 静态耗时：102.71 ms
- LLM耗时：5642.48 ms
- LLM token：1050（prompt 809 / completion 241 / reasoning 0）

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
耗时：`33.11` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`34.1` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`32.9` ms

LLM SQL：

1. generated / rep_ranking
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5624.82` ms
token：`prompt=809, completion=241, reasoning=0, total=1050`

2. executed
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :scope_region_id GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "scope_region_id": 3}`
耗时：`15.72` ms
返回行数：`4`

### 区域经理 / get_top_products / 区域产品 Top5

- 用户问题：我大区产品 TOP5
- 结果一致：是
- 静态耗时：27.32 ms
- LLM耗时：6285.24 ms
- LLM token：1083（prompt 816 / completion 267 / reasoning 0）

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
耗时：`14.0` ms

2.
```sql
SELECT sa_sales_order.product_id, sum(sa_sales_order.amount) AS total, sum(sa_sales_order.quantity) AS qty FROM sa_sales_order WHERE sa_sales_order.status = %(status_1)s AND sa_sales_order.order_date BETWEEN %(order_date_1)s AND %(order_date_2)s AND sa_sales_order.region_id = %(region_id_1)s GROUP BY sa_sales_order.product_id ORDER BY sum(sa_sales_order.amount) DESC
```
参数：`{'status_1': 'COMPLETED', 'order_date_1': datetime.date(2026, 5, 1), 'order_date_2': datetime.date(2026, 5, 31), 'region_id_1': 3}`
耗时：`8.55` ms

LLM SQL：

1. generated / product_ranking
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' AND o.region_id = :region_id GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "top_n": 5}`
耗时：`6251.05` ms
token：`prompt=816, completion=267, reasoning=0, total=1083`

2. executed
```sql
SELECT p.id AS product_id, p.sku_code, p.name AS product_name, p.category, SUM(o.amount) AS total_amount, SUM(o.quantity) AS total_quantity FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' AND o.region_id = :region_id AND o.region_id = :scope_region_id GROUP BY p.id, p.sku_code, p.name, p.category ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "region_id": 3, "top_n": 5, "scope_region_id": 3}`
耗时：`31.73` ms
返回行数：`5`

### 区域经理 / generate_line_chart / 区域趋势折线图

- 用户问题：我大区近 6 个月趋势图
- 结果一致：是
- 静态耗时：31.63 ms
- LLM耗时：5715.8 ms
- LLM token：1028（prompt 800 / completion 228 / reasoning 0）

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
耗时：`29.3` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3}`
耗时：`5707.15` ms
token：`prompt=800, completion=228, reasoning=0, total=1028`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id AND o.region_id = :scope_region_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3, "scope_region_id": 3}`
耗时：`7.17` ms
返回行数：`7`

### 普通销售员 / get_sales_summary / 个人销售额汇总

- 用户问题：我本月销售额
- 结果一致：是
- 静态耗时：7.29 ms
- LLM耗时：4880.71 ms
- LLM token：992（prompt 791 / completion 201 / reasoning 0）

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
耗时：`6.04` ms

LLM SQL：

1. generated / sales_summary
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o INNER JOIN sa_sales_rep s ON s.id = o.rep_id INNER JOIN sa_sales_region r ON r.id = o.region_id INNER JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' AND s.id = :rep_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103}`
耗时：`4871.2` ms
token：`prompt=791, completion=201, reasoning=0, total=992`

2. executed
```sql
SELECT SUM(o.amount) AS total_amount FROM sa_sales_order o INNER JOIN sa_sales_rep s ON s.id = o.rep_id INNER JOIN sa_sales_region r ON r.id = o.region_id INNER JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' AND s.id = :rep_id AND o.rep_id = :scope_rep_id
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "scope_rep_id": 9103}`
耗时：`7.65` ms
返回行数：`1`

### 普通销售员 / query_sales_data / 个人订单明细

- 用户问题：列出我的本月订单
- 结果一致：是
- 静态耗时：30.01 ms
- LLM耗时：5871.05 ms
- LLM token：1097（prompt 851 / completion 246 / reasoning 0）

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
耗时：`7.5` ms

2.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`6.74` ms

3.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`5.7` ms

4.
```sql
SELECT sa_sales_rep.id AS sa_sales_rep_id, sa_sales_rep.name AS sa_sales_rep_name, sa_sales_rep.region_id AS sa_sales_rep_region_id, sa_sales_rep.`role` AS sa_sales_rep_role, sa_sales_rep.email AS sa_sales_rep_email, sa_sales_rep.created_at AS sa_sales_rep_created_at FROM sa_sales_rep WHERE sa_sales_rep.id = %(pk_1)s
```
参数：`{'pk_1': 9103}`
耗时：`6.46` ms

LLM SQL：

1. generated / order_detail
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "limit": 20}`
耗时：`5784.65` ms
token：`prompt=851, completion=246, reasoning=0, total=1097`

2. executed
```sql
SELECT o.id, o.order_no, o.order_date, o.rep_id, o.customer_name, o.amount, o.status FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.rep_id = :rep_id AND o.rep_id = :scope_rep_id ORDER BY o.order_date DESC, o.id DESC LIMIT :limit
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "rep_id": 9103, "limit": 20, "scope_rep_id": 9103}`
耗时：`17.24` ms
返回行数：`3`

### 普通销售员 / get_top_reps / 个人排名视角

- 用户问题：我在排名中的情况
- 结果一致：是
- 静态耗时：60.68 ms
- LLM耗时：5826.17 ms
- LLM token：1055（prompt 810 / completion 245 / reasoning 0）

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
耗时：`20.03` ms

2.
```sql
SELECT sa_sales_rep.id, sa_sales_rep.name, sa_sales_rep.region_id, sa_sales_rep.`role`, sa_sales_rep.email, sa_sales_rep.created_at FROM sa_sales_rep
```
参数：`{}`
耗时：`20.55` ms

3.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`17.73` ms

LLM SQL：

1. generated / rep_ranking
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5}`
耗时：`5816.5` ms
token：`prompt=810, completion=245, reasoning=0, total=1055`

2. executed
```sql
SELECT s.id AS rep_id, s.name AS rep_name, r.id AS region_id, r.name AS region_name, SUM(o.amount) AS total_amount FROM sa_sales_order o JOIN sa_sales_rep s ON s.id = o.rep_id JOIN sa_sales_region r ON r.id = o.region_id JOIN sa_product p ON p.id = o.product_id WHERE o.order_date BETWEEN :start_date AND :end_date AND o.status = 'COMPLETED' AND o.rep_id = :scope_rep_id GROUP BY s.id, s.name, r.id, r.name ORDER BY total_amount DESC LIMIT :top_n
```
参数：`{"start_date": "2026-05-01", "end_date": "2026-05-31", "top_n": 5, "scope_rep_id": 9103}`
耗时：`8.07` ms
返回行数：`1`

### 普通销售员 / get_region_ranking / 大区排名权限

- 用户问题：我能看大区排名吗
- 结果一致：是
- 静态耗时：14.04 ms
- LLM耗时：15.61 ms
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
耗时：`7.08` ms

2.
```sql
SELECT sa_sales_region.id, sa_sales_region.name, sa_sales_region.parent_region_id, sa_sales_region.created_at FROM sa_sales_region
```
参数：`{}`
耗时：`5.55` ms

LLM SQL：
无。

### 普通销售员 / get_monthly_trend / 个人趋势

- 用户问题：看我近 6 个月趋势
- 结果一致：否
- 静态耗时：7.74 ms
- LLM耗时：5537.86 ms
- LLM token：1033（prompt 801 / completion 232 / reasoning 0）

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
耗时：`6.34` ms

LLM SQL：

1. generated / monthly_trend
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o INNER JOIN sa_sales_rep s ON s.id = o.rep_id INNER JOIN sa_sales_region r ON r.id = o.region_id INNER JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3}`
耗时：`5513.59` ms
token：`prompt=801, completion=232, reasoning=0, total=1033`

2. executed
```sql
SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month, SUM(o.amount) AS total_amount, COUNT(*) AS order_count FROM sa_sales_order o INNER JOIN sa_sales_rep s ON s.id = o.rep_id INNER JOIN sa_sales_region r ON r.id = o.region_id INNER JOIN sa_product p ON p.id = o.product_id WHERE o.status = 'COMPLETED' AND o.order_date BETWEEN :start_date AND :end_date AND o.region_id = :region_id AND o.rep_id = :scope_rep_id GROUP BY DATE_FORMAT(o.order_date, '%Y-%m') ORDER BY month
```
参数：`{"start_date": "2025-11-01", "end_date": "2026-05-08", "region_id": 3, "scope_rep_id": 9103}`
耗时：`22.42` ms
返回行数：`3`
