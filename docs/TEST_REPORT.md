<!--
文件作用：
- 记录本地验证结论，帮助读者了解当前版本的通过情况。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

# 本地验证报告

验证日期：`2026-04-13`

验证环境：

- Python 环境：`E:\develop\mini_anaconda\envs\dev`
- Python 服务地址：`http://127.0.0.1:8088`
- 数据源：复用现有 MySQL / Redis 测试实例

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 1. 静态检查

- `python -m compileall app scripts tests`：通过
- `pytest -q`：`15 passed`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 2. 烟雾测试

执行脚本：

```powershell
python scripts/smoke_test.py --base-url http://127.0.0.1:8088 --timeout 180
```

结果：

- `health`：通过
- `chat-intro`：通过
- `chat-trend`：通过
- `chat-summary`：通过
- `chat-chart`：通过
- `chat-anomaly`：通过
- `stream-trend`：通过

结论：

- 典型问句链路可用
- SSE 流式返回可用

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 3. 性能探针

执行脚本：

```powershell
python scripts/perf_probe.py --base-url http://127.0.0.1:8088 --iterations 1 --timeout 180
```

结果：

- `/agent/chat`：`13096ms`
- `/agent/chat/stream first token`：`12073ms`

说明：

- 当前为本地开发联调基线
- 首 token 指标已修正为“收到请求到输出首个 token”的端到端口径

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 4. 稳定性探针

执行脚本：

```powershell
python scripts/stability_probe.py --base-url http://127.0.0.1:8088 --database-url <mysql-url> --concurrency 1 --timeout 180
```

结果：

- 并发聊天成功率：`1/1`
- 并发平均耗时：`10909ms`
- 会话记忆落库：通过
- `sa_chat_memory` 消息条数：`4`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 5. 指标快照

验证时抓取 `GET /ops/metrics`，关键指标如下：

- 请求总数：`8`
- MySQL 查询数：`17`
- MySQL 平均耗时：`6.48ms`
- Redis 命中率：`66.67%`
- 端到端首 token 平均耗时：`10376.78ms`

结论：

- 新增运行时指标接口可用
- MySQL / Redis / LLM / Tool 指标可观测
- 稳定性脚本与指标口径能对上

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 6. Java / Python 回归

已在本地完成一次真实确定性接口回归，对比如下：

- `query-orders`
- `region-ranking`
- `top-products`
- `monthly-trend`
- `line-chart`

结果：

- 上述接口均通过

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 7. 当前剩余项

仓库内可落地的迁移、验证、脚本和文档已补齐。

当前剩余工作只涉及外部环境执行：

- 在测试环境接入真实网关做小流量灰度
- 按 `docs/ROLLBACK.md` 演练真实回滚
- 在灰度窗口内持续观察线上指标
