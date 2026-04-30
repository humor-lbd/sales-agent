<!--
文件作用：
- 说明后端接口契约、请求参数、返回格式和状态码约定。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

# API 文档

`sales-agent` 默认运行在 `http://127.0.0.1:8088`，同时保留 FastAPI 自动生成的交互文档：

- `GET /docs`
- `GET /openapi.json`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 通用约定

- 所有接口默认返回 `application/json`
- 流式接口 `POST /agent/chat/stream` 返回 `text/event-stream`
- 当 `AUTH_ENABLED=true` 时，除 `/health` 和 `/auth/login` 之外的接口需要携带：

```http
Authorization: Bearer <token>
```

- 统一错误格式：

```json
{
  "error": "错误说明"
}
```

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 1. 健康检查

### `GET /health`

返回：

```json
{
  "status": "ok"
}
```

### `GET /ops/metrics`

返回运行时指标快照，便于对照 `liucheng.md` 中的性能与稳定性关注项。其中 `llm.avgFirstTokenMs` 表示流式接口从收到请求到首个 token 输出的端到端耗时均值。

返回示例：

```json
{
  "uptimeSeconds": 42.13,
  "requests": {
    "total": 12,
    "byPath": {
      "GET /health": {
        "count": 3,
        "avgMs": 1.33,
        "maxMs": 3.0,
        "statuses": {
          "200": 3
        }
      }
    }
  },
  "database": {
    "queryCount": 21,
    "avgMs": 2.17,
    "maxMs": 8.41
  },
  "cache": {
    "hits": 4,
    "misses": 2,
    "sets": 2,
    "hitRate": 0.6667,
    "avgGetMs": 0.54,
    "avgSetMs": 0.73,
    "maxGetMs": 0.91,
    "maxSetMs": 1.12
  },
  "llm": {
    "syncCalls": 3,
    "streamCalls": 1,
    "toolLoopCalls": 2,
    "avgMs": 1187.24,
    "maxMs": 2410.44,
    "avgFirstTokenMs": 935.11,
    "maxFirstTokenMs": 935.11
  },
  "tools": {
    "get_monthly_trend": {
      "count": 1,
      "avgMs": 6.21,
      "maxMs": 6.21
    }
  }
}
```

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 2. 登录与退出

### `POST /auth/login`

请求：

```json
{
  "repId": 1
}
```

返回：

```json
{
  "token": "jwt-token",
  "username": "张伟",
  "role": "SALES_REP"
}
```

### `POST /auth/logout`

返回：

```json
{
  "message": "已退出登录"
}
```

说明：

- 当前版本未实现服务端 token 黑名单
- 调用方退出后应主动丢弃本地 token

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 3. 对话接口

### `POST /agent/chat`

请求：

```json
{
  "sessionId": "demo-001",
  "message": "本月华东区销售额是多少？"
}
```

返回：

```json
{
  "sessionId": "demo-001",
  "reply": "本月至今华东区销售额为 ¥20,997。",
  "durationMs": 1488
}
```

### `POST /agent/chat/stream`

请求体与同步聊天一致。

SSE 事件：

- `status`：阶段性状态，例如“正在读取会话上下文...”或“工具结果已返回，继续分析...”
- `token`：模型增量输出
- `artifacts`：图表 artifact 的 JSON 字符串
- `done`：本次流式输出结束
- `error`：流式过程中的错误信息

当前实现说明：

- 如果问题需要先走 `tool-loop`，前端会先收到若干 `status` 事件，再进入最终回答的实时 `token`
- 带图表 artifact 的分析型最终收尾也会优先走真实流式输出，而不是统一等全文完成后再本地切片
- `artifacts` 事件通常出现在文本输出结束之后、`done` 之前

示例：

```text
event: status
data: 正在读取会话上下文...

event: status
data: 工具结果已返回，继续分析...

event: token
data: 近6个月销售趋势整体先升后降，

event: token
data: 已生成折线图，请查看下方。

event: artifacts
data: [{"kind":"echarts","slot":"main_chart","title":"近6个月销售趋势"}]

event: done
data: [DONE]
```

### `DELETE /agent/session/{sessionId}`

返回：

```json
{
  "message": "会话记忆已清除",
  "sessionId": "demo-001"
}
```

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 4. 工具测试接口

这些接口用于跳过 LLM，直接验证 Service / Tool 的确定性输出。

### `POST /test/tool/query-orders`

请求：

```json
{
  "startDate": "2026-04-01",
  "endDate": "2026-04-30",
  "regionName": "华东区",
  "repName": "张伟",
  "limit": 10
}
```

### `POST /test/tool/top-reps`

请求：

```json
{
  "startDate": "2026-04-01",
  "endDate": "2026-04-30",
  "regionName": "华东区",
  "topN": 5
}
```

### `POST /test/tool/region-ranking`

请求：

```json
{
  "startDate": "2026-04-01",
  "endDate": "2026-04-30"
}
```

### `POST /test/tool/top-products`

请求：

```json
{
  "startDate": "2026-04-01",
  "endDate": "2026-04-30",
  "topN": 5
}
```

### `POST /test/tool/month-over-month`

请求：

```json
{
  "currentStart": "2026-04-01",
  "currentEnd": "2026-04-30",
  "prevStart": "2026-03-01",
  "prevEnd": "2026-03-31",
  "regionName": "华东区"
}
```

### `POST /test/tool/year-over-year`

请求：

```json
{
  "startDate": "2026-04-01",
  "endDate": "2026-04-30",
  "regionName": "华东区"
}
```

### `POST /test/tool/monthly-trend`

请求：

```json
{
  "months": 6,
  "regionName": "华东区"
}
```

### `POST /test/tool/line-chart`

请求：

```json
{
  "months": 6,
  "regionName": "华东区",
  "title": "近6个月销售趋势"
}
```

返回值带 `CHART_JSON:` 前缀，后面是 ECharts option JSON。

### `POST /test/tool/bar-chart`

请求：

```json
{
  "dimension": "region",
  "startDate": "2026-04-01",
  "endDate": "2026-04-30",
  "title": "区域销售对比"
}
```

### `POST /test/tool/pie-chart`

请求：

```json
{
  "dimension": "category",
  "startDate": "2026-04-01",
  "endDate": "2026-04-30",
  "title": "品类销售占比"
}
```

### `POST /test/tool/detect-anomalies`

请求体为空。

返回值为格式化后的异常检测文本。

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 5. 状态码

- `200`：成功
- `400`：参数错误或业务校验失败
- `401`：鉴权失败或缺少 token
- `500`：服务内部错误
- `502`：模型网关或模型鉴权失败
- `503`：模型额度不足、限流或暂时不可用
