# Agent 节点输出报告

## 1. 说明

本文档针对前端一次真实复杂问题请求，整理该请求在 `sales-agent` 项目中的 Agent 节点执行过程、每个节点的主要输入输出、工具调用参数、超时位置和最终返回结果。

本次分析对应请求：

- 前端页面：`http://127.0.0.1:5173/`
- 后端接口：`POST /agent/chat/stream`
- 请求 ID：`4a8944980b1b4fa8bc8f86fb747eee93`

用户问题：

> 分析6个月的销售趋势、本月销售额、订单明细前5条、和上月相比的环比变化，并生成一张趋势图，最后告诉我有没有明显异常风险。

相关源码：

- `app/graph/builder.py`
- `app/graph/nodes/bootstrap.py`
- `app/graph/nodes/memory.py`
- `app/graph/nodes/guardrails.py`
- `app/graph/nodes/react_agent.py`
- `app/graph/nodes/react_tool_executor.py`
- `app/logic/tools.py`
- `app/logic/services.py`
- `app/logic/sql_agent/service.py`

相关日志：

- `logs/uvicorn.llm_sql.stdout.log`
- `logs/uvicorn.llm_sql.stderr.log`

## 2. 整体执行链路

本次请求在 LangGraph 中实际经过的节点链路如下：

1. `bootstrap`
2. `load_memory`
3. `guardrails`
4. `react_agent`
5. `react_tool_executor`
6. `react_agent`
7. `react_tool_executor`
8. `react_agent`
9. `react_tool_executor`
10. `react_agent`
11. `react_tool_executor`
12. `react_agent`
13. `react_tool_executor`
14. `react_agent`
15. `react_tool_executor`
16. `react_agent`
17. `persist_memory`

其中：

- `react_agent` 负责思考、决定要不要继续调用工具
- `react_tool_executor` 负责真正执行工具
- 执行模式是典型的 `ReAct` 循环：  
  `react_agent -> react_tool_executor -> react_agent -> ... -> final_answer`

## 3. 节点级输出

### 3.1 bootstrap

作用：

- 初始化本轮状态
- 放入后续节点要使用的默认字段

主要输入：

```json
{
  "session_id": "前端会话ID",
  "request_text": "分析6个月的销售趋势、本月销售额、订单明细前5条、和上月相比的环比变化，并生成一张趋势图，最后告诉我有没有明显异常风险。"
}
```

主要输出：

```json
{
  "session_id": "前端会话ID",
  "request_text": "分析6个月的销售趋势、本月销售额、订单明细前5条、和上月相比的环比变化，并生成一张趋势图，最后告诉我有没有明显异常风险。",
  "messages": [],
  "react_messages": [],
  "summary_context": null,
  "tool_results": {},
  "artifacts": [],
  "final_answer": null,
  "streamed_final_answer": false,
  "error": null,
  "rejected": false,
  "tool_call_count": 0,
  "react_round_count": 0
}
```

### 3.2 load_memory

作用：

- 从数据库读取会话历史
- 把历史消息组装成 `react_messages`
- 如有必要，生成摘要 `summary_context`

本次请求表现：

- 这是一个独立分析问题，不是“继续”“接着”“图呢”这类明显追问
- 因此本轮核心是将用户问题本身放入 `react_messages`

主要输出可以理解为：

```json
{
  "messages": [],
  "react_messages": [
    {
      "type": "HumanMessage",
      "content": "分析6个月的销售趋势、本月销售额、订单明细前5条、和上月相比的环比变化，并生成一张趋势图，最后告诉我有没有明显异常风险。"
    }
  ],
  "summary_context": null
}
```

### 3.3 guardrails

作用：

- 拦截越界请求
- 禁止修改数据、删除数据、新增数据
- 禁止未来预测类请求

本次请求判断结果：

- 用户是在做销售分析
- 不涉及写数据
- 不涉及未来预测

输出：

```json
{
  "rejected": false
}
```

说明：

- 因为 `rejected=false`，流程继续进入 `react_agent`

## 4. ReAct 轮次与工具执行

### 4.1 第 1 轮 react_agent

Agent 输出含义：

- 先获取近 6 个月销售趋势

工具调用：

```json
[
  {
    "name": "get_monthly_trend",
    "args": {
      "months": 6
    }
  }
]
```

### 4.2 第 1 次 react_tool_executor

执行工具：

- `get_monthly_trend`

工具入参：

```json
{
  "months": 6
}
```

工具结果摘要：

- 成功
- 返回近 6 个月月度销售趋势

返回给 `react_agent` 的文本结果大意：

```text
月度销售趋势（近 6 个月，全公司）：
2025-11：¥313,379
2025-12：¥499,868
2026-01：¥308,687
2026-02：¥217,707
2026-03：¥576,626
2026-04：¥520,442
2026-05：¥648,720
整体趋势：上升 107.0%
```

附加说明：

- 此工具底层使用了 LLM 生成 SQL
- 后端日志中出现 `LLM SQL executed`

### 4.3 第 2 轮 react_agent

Agent 输出含义：

- 接着查询本月销售额

工具调用：

```json
[
  {
    "name": "get_sales_summary",
    "args": {
      "start_date": "2026-05-01",
      "end_date": "2026-05-07"
    }
  }
]
```

### 4.4 第 2 次 react_tool_executor

执行工具：

- `get_sales_summary`

工具入参：

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-07"
}
```

工具结果：

- 失败

错误日志：

```text
Timeout reading from socket
```

返回给 `react_agent` 的内容：

```text
工具执行失败：Timeout reading from socket
```

这一步是本次请求中明确的超时点。

### 4.5 第 3 轮 react_agent

Agent 输出含义：

- 发现“本月销售额汇总”超时
- 不停止流程
- 改走替代路径
- 改查 `2026-05-01 ~ 2026-05-07` 的订单明细前 5 条
- 顺便利用明细补齐本月销售情况

工具调用：

```json
[
  {
    "name": "query_sales_data",
    "args": {
      "start_date": "2026-05-01",
      "end_date": "2026-05-07",
      "limit": 5
    }
  }
]
```

### 4.6 第 3 次 react_tool_executor

执行工具：

- `query_sales_data`

工具入参：

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-07",
  "limit": 5
}
```

工具结果摘要：

- 成功
- 找到 20 条订单
- 返回前 5 条
- 前 5 条小计：`¥194,097`

返回给 `react_agent` 的结果大意：

```text
订单查询结果（2026-05-01 至 2026-05-07）：
共找到 20 条订单，以下显示前 5 条
...
小计：完成订单 5 笔，金额合计 ¥194,097
```

### 4.7 第 4 轮 react_agent

Agent 输出含义：

- 继续计算环比
- 采用已结束自然月口径
- 用 `2026-04` 对比 `2026-03`

工具调用：

```json
[
  {
    "name": "calc_month_over_month",
    "args": {
      "current_start": "2026-04-01",
      "current_end": "2026-04-30",
      "prev_start": "2026-03-01",
      "prev_end": "2026-03-31"
    }
  }
]
```

### 4.8 第 4 次 react_tool_executor

执行工具：

- `calc_month_over_month`

工具入参：

```json
{
  "current_start": "2026-04-01",
  "current_end": "2026-04-30",
  "prev_start": "2026-03-01",
  "prev_end": "2026-03-31"
}
```

工具结果摘要：

- 成功
- 当前周期：`2026-04-01 ~ 2026-04-30`
- 对比周期：`2026-03-01 ~ 2026-03-31`
- 当前销售额：`¥520,442`
- 对比销售额：`¥576,626`
- 环比：`下降 9.7%`

返回文本大意：

```text
环比分析（全公司）：
当前周期：¥520,442
对比周期：¥576,626
环比变化：下降 9.7%
```

### 4.9 第 5 轮 react_agent

Agent 输出含义：

- 生成近 6 个月趋势图

工具调用：

```json
[
  {
    "name": "generate_line_chart",
    "args": {
      "months": 6,
      "title": "近6个月销售额趋势（2025-11 至 2026-05）"
    }
  }
]
```

### 4.10 第 5 次 react_tool_executor

执行工具：

- `generate_line_chart`

工具入参：

```json
{
  "months": 6,
  "title": "近6个月销售额趋势（2025-11 至 2026-05）"
}
```

工具结果摘要：

- 成功
- 返回图表 artifact

结果文本：

```text
已生成折线图。
```

附带产物：

```json
{
  "kind": "echarts",
  "slot": "main_chart",
  "title": "近6个月销售额趋势（2025-11 至 2026-05）",
  "option": {
    "title": { "text": "近6个月销售额趋势（2025-11 至 2026-05）" },
    "xAxis": { "type": "category" },
    "yAxis": { "type": "value", "name": "销售额（元）" },
    "series": [
      {
        "type": "line",
        "name": "销售额",
        "smooth": true
      }
    ]
  }
}
```

### 4.11 第 6 轮 react_agent

Agent 输出含义：

- 最后检测异常与风险

工具调用：

```json
[
  {
    "name": "detect_sales_anomalies",
    "args": {}
  }
]
```

### 4.12 第 6 次 react_tool_executor

执行工具：

- `detect_sales_anomalies`

工具入参：

```json
{}
```

工具结果摘要：

- 成功
- 检出 `19` 个异常

返回文本的主要内容包括：

- 多个产品连续多天无销售
- 部分销售员退单率偏高
- 部分销售员近 30 天业绩明显下滑

### 4.13 第 7 轮 react_agent

Agent 行为：

- 不再继续调用工具
- 汇总趋势、本月订单、环比、图表、异常检测结果
- 生成最终回答

这一轮输出的是最终答案，不再有 `tool_calls`

关键状态变化：

```json
{
  "final_answer": "最终分析报告全文",
  "react_round_count": 7
}
```

## 5. persist_memory 节点输出

### 5.1 persist_memory

作用：

- 将本轮用户问题写回聊天记忆
- 将本轮最终回答写回聊天记忆
- 如有图表 artifact，一并写入

返回值：

```json
{}
```

说明：

- 这个节点看起来“没输出内容”
- 但它完成了本轮会话的持久化

## 6. 哪一步超时

本次请求超时位置如下：

- 节点：`react_tool_executor`
- 工具：`get_sales_summary`
- 参数：

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-07"
}
```

错误：

```text
Timeout reading from socket
```

说明：

- 超时的是“本月销售额汇总”
- 不是整个 Agent 崩溃
- Agent 在拿到失败结果后，自动改用订单明细继续完成分析

## 7. 最终返回了什么

最终返回是一段综合分析文本，核心结论包括：

1. 近 6 个月销售整体呈上升趋势
2. 本月前 7 天可从订单明细口径得到销售额 `¥194,097`
3. 2026 年 4 月相对 2026 年 3 月环比下降 `9.7%`
4. 已生成近 6 个月趋势图
5. 异常检测共发现 `19` 个异常
6. 风险主要集中在：
   - 多个产品长时间无销售
   - 部分销售员退单率偏高
   - 部分销售员业绩明显下滑

## 8. 本次请求的 ReAct 特征总结

这次真实请求比较典型地体现了本项目的 ReAct 架构特点：

1. `react_agent` 先做任务拆解，不一次性直接回答
2. 每一轮只决定“下一步调用哪个工具”
3. `react_tool_executor` 执行完工具后，把结果再交回 `react_agent`
4. `react_agent` 根据工具结果继续判断：
   - 是否已经足够回答
   - 是否还要继续调工具
   - 如果某一步失败，是否改走替代路径
5. 最后由 `react_agent` 汇总所有工具结果，生成最终自然语言回答

本次请求中的典型体现就是：

- 本月销售汇总超时
- Agent 没有直接失败
- 而是自动改用订单明细补齐分析
- 最终仍返回了完整结论

## 9. 补充说明

本报告基于如下信息整理：

1. 项目图结构源码
2. 当前后端运行日志
3. 本次前端真实请求对应的 `request_id`
4. 已核对的工具实现和服务层逻辑

由于当前项目默认日志没有把完整 GraphState 结构逐节点序列化到磁盘，因此本文档中的节点输出，采用“源码结构 + 实际日志 + 本次请求工具执行结果”综合还原，能够准确反映本次请求的执行过程。
