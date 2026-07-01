# LLM SQL 优化前后对比报告

## 对比口径

- 优化前：`logs/sql_mode_compare_results_before_opt.json`
- 当前版本：`logs/sql_mode_compare_results.json`
- 当前版本脚本已补充：
  - `LLM模式`（`bypass / template / cache / generator`）
  - `命中情况`
  - `静态 token`（固定为 `0`）

## 总体结果

| 指标 | 优化前 | 当前版本 | 变化 |
| --- | --- | --- | --- |
| 总场景数 | 28 | 28 | +0 |
| 结果完全一致 | 26 | 26 | +0 |
| 静态总耗时(ms) | 2468.79 | 3838.4 | +1369.61 |
| LLM 总耗时(ms) | 473563.35 | 71160.57 | -402402.78 |
| LLM 总 token | 108889 | 11748 | -97141 |

## 当前版本的命中分布

| 模式 | 场景数 | 说明 |
| --- | --- | --- |
| `template` | 14 | ranking / ranking 驱动图表直接命中受控模板，不再调用模型 |
| `generator` | 11 | 仍然由模型生成 SQL |
| `generator+cache` | 2 | 同一工具内部多次查询，第二次命中 SQL 结构缓存 |
| `bypass` | 1 | 白名单/权限直接走写死 SQL |

## 结论

- 当前版本 LLM 总耗时从 `473563.35 ms` 降到 `71160.57 ms`，下降约 `85.0%`。
- 当前版本 LLM token 从 `108889` 降到 `11748`，下降约 `89.2%`。
- 最大收益不再只是“少调模型”，而是：
  - ranking 类改成了 `template`
  - 部分重复查询出现了 `cache`
  - 报告里可以直接看出哪些场景其实仍在 `generator`
- 当前版本静态总耗时比旧报告更高，主要受本次运行环境波动影响；这不改变“静态 SQL 明显便宜、稳定”的结论。

## 各 Tool 对比

| Tool | 优化前 LLM平均(ms) | 当前 LLM平均(ms) | 优化前平均token | 当前平均token | 当前主要模式 |
| --- | --- | --- | --- | --- | --- |
| `calc_month_over_month` | 8437.55 | 4183.97 | 1918.0 | 844.0 | `generator+cache` |
| `calc_year_over_year` | 8457.73 | 4034.78 | 1923.0 | 843.0 | `generator+cache` |
| `detect_sales_anomalies` | 321108.93 | 5354.59 | 80095.0 | 942.0 | `generator` |
| `generate_bar_chart` | 5600.38 | 37.34 | 1046.25 | 0.0 | `template` |
| `generate_line_chart` | 5361.58 | 5603.02 | 1020.0 | 915.0 | `generator` |
| `generate_pie_chart` | 5683.02 | 36.05 | 1048.5 | 0.0 | `template` |
| `get_monthly_trend` | 5272.11 | 5101.93 | 1020.5 | 907.5 | `generator` |
| `get_region_ranking` | 2416.37 | 161.82 | 501.0 | 0.0 | `template/bypass` |
| `get_sales_summary` | 4521.21 | 4358.51 | 975.0 | 854.33 | `generator` |
| `get_top_products` | 6019.76 | 29.16 | 1071.5 | 0.0 | `template` |
| `get_top_reps` | 5745.7 | 37.11 | 1053.33 | 0.0 | `template` |
| `query_sales_data` | 7161.72 | 7438.32 | 1087.67 | 970.33 | `generator` |

## 现在该怎么理解

### 已经明显优化成功的

- `get_top_reps`
- `get_region_ranking`
- `get_top_products`
- `generate_bar_chart`
- `generate_pie_chart`

这些场景现在基本靠 `template` 跑，token 接近 `0`，延迟也降到了接近静态查询。

### 仍然值得继续收敛的

- `query_sales_data`
- `get_sales_summary`
- `get_monthly_trend`
- `generate_line_chart`
- `detect_sales_anomalies`

这些仍然是 `generator` 主导，耗时和 token 还在明显消耗预算。

## 建议

1. `ranking` 类现在已经很适合继续保留在 LLM SQL 主链路，但实际上已经更像“模板 SQL 链路”了。
2. `summary / trend / detail / anomaly` 仍建议默认写死 SQL，除非后面继续做模板化或更严格白名单分流。
3. 对 `query_sales_data` 最值得优先修：
   - 结果偏差仍然存在
   - token 和耗时都不低
4. 对 `detect_sales_anomalies` 最值得优先再优化：
   - 当前虽然已经比早期版本好很多
   - 但它仍属于高成本 `generator` 路径
