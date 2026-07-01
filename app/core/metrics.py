"""
运行时指标管理模块

该模块负责维护应用运行期的各项指标，支撑健康观测和性能分析。
主要功能包括：
- 记录HTTP请求的处理时间和状态码
- 跟踪数据库查询性能
- 监控缓存操作（命中、未命中、设置）
- 统计LLM调用情况
- 记录工具调用性能
- 生成指标快照用于监控和分析

设计定位（为什么不直接上 Prometheus/OTel）：
- 这是一个轻量的“进程内指标聚合器”，不依赖外部组件，启动即用，适合 demo/中小项目。
- 指标以 Python 内存结构维护，通过 snapshot() 生成结构化字典，便于被接口直接返回。
- 该实现关注“聚合后的统计结果”（count/avg/max），而非高精度时序数据。

重要限制与取舍：
- 进程重启后指标会清零；多进程部署时每个进程各自一份，需要在更上层做聚合。
- 为避免高基数标签（high cardinality），不会按 SQL 文本、用户 ID 等维度细分指标桶。
- 通过 threading.Lock 实现线程安全，锁粒度较粗但实现简单可靠，适合该项目的负载规模。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict


class RuntimeMetrics:
    """
    运行时指标收集器
    
    线程安全的运行时指标收集器，用于跟踪应用的各项性能指标。

    使用方式（典型调用点）：
    - HTTP 中间件：record_request（统计请求耗时、状态码）
    - DB 层 event hook 或仓库层：record_db_query（统计查询耗时）
    - Redis 客户端封装：record_cache_get / record_cache_set（统计命中率与耗时）
    - Agent/Graph：record_llm_call（统计模型调用与首 token）
    - 工具执行器：record_tool_call（统计各工具耗时）

    注意：该类不负责“指标暴露协议”（如 Prometheus exposition format），只负责聚合与快照。
    """
    def __init__(self) -> None:
        """
        初始化运行时指标收集器
        
        创建线程锁并重置所有指标。
        """
        # 由于 FastAPI 可能存在线程池 + 异步协程并发更新指标，使用线程锁保护共享状态。
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        """
        重置所有运行时指标
        
        将所有指标重置为初始状态，包括：
        - 启动时间
        - HTTP请求统计
        - 数据库查询统计
        - 缓存操作统计
        - LLM调用统计
        - 工具调用统计
        """
        with self._lock:
            # 运行起点（秒级时间戳），用于计算 uptime。
            self.started_at = time.time()

            # HTTP 请求总数（全路径聚合）。
            self.request_total = 0

            # HTTP 请求分桶统计：key = "{METHOD} {PATH}"
            # 例如： "POST /agent/chat"、"GET /health"
            # 每个桶维护 count/total/max 以及状态码分布。
            self.request_paths: dict[str, dict] = defaultdict(
                lambda: {
                    "count": 0,
                    "total_ms": 0.0,
                    "max_ms": 0.0,
                    "statuses": defaultdict(int),
                }
            )

            # DB 查询聚合统计（不按 SQL 文本分桶，避免高基数与敏感信息泄露风险）。
            self.db_queries = {"count": 0, "total_ms": 0.0, "max_ms": 0.0}

            # 缓存统计：命中/未命中/写入次数，以及 get/set 的耗时聚合。
            self.cache = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "get_total_ms": 0.0,
                "set_total_ms": 0.0,
                "max_get_ms": 0.0,
                "max_set_ms": 0.0,
            }

            # LLM 统计：按调用类型计数，并维护整体耗时与首 token 统计。
            # - sync_calls：同步调用（或非 stream/tool_loop 的调用）
            # - stream_calls：流式链路整体调用
            # - tool_loop_calls：工具循环阶段（ReAct loop）的调用
            self.llm = {
                "sync_calls": 0,
                "stream_calls": 0,
                "tool_loop_calls": 0,
                "total_ms": 0.0,
                "max_ms": 0.0,
                "first_token_total_ms": 0.0,
                "first_token_count": 0,
                "max_first_token_ms": 0.0,
            }

            # 工具调用分桶统计：key = tool_name，例如 "query_orders"、"get_sales_summary"
            self.tool_calls: dict[str, dict] = defaultdict(
                lambda: {"count": 0, "total_ms": 0.0, "max_ms": 0.0}
            )

            # LLM SQL统计：校验、执行与回退情况。
            self.llm_sql = {
                "validation_success": 0,
                "validation_failed": 0,
                "execution_success": 0,
                "execution_failed": 0,
                "fallbacks": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "generated_prompt_tokens": 0,
                "generated_completion_tokens": 0,
                "generated_total_tokens": 0,
                "template_hits": 0,
                "execution_total_ms": 0.0,
                "max_execution_ms": 0.0,
            }

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        """
        记录HTTP请求指标
        
        Args:
            method: HTTP请求方法
            path: 请求路径
            status_code: 响应状态码
            duration_ms: 处理时间（毫秒）
        """
        # 分桶 key 使用 method+path，避免不同方法混在一起（GET/POST 语义不同）。
        key = f"{method} {path}"
        with self._lock:
            self.request_total += 1
            bucket = self.request_paths[key]
            bucket["count"] += 1
            bucket["total_ms"] += duration_ms
            bucket["max_ms"] = max(bucket["max_ms"], duration_ms)
            bucket["statuses"][str(status_code)] += 1

    def record_db_query(self, duration_ms: float) -> None:
        """
        记录数据库查询指标
        
        Args:
            duration_ms: 查询执行时间（毫秒）
        """
        with self._lock:
            self.db_queries["count"] += 1
            self.db_queries["total_ms"] += duration_ms
            self.db_queries["max_ms"] = max(self.db_queries["max_ms"], duration_ms)

    def record_cache_get(self, hit: bool, duration_ms: float) -> None:
        """
        记录缓存获取操作指标
        
        Args:
            hit: 是否命中缓存
            duration_ms: 操作执行时间（毫秒）
        """
        with self._lock:
            if hit:
                self.cache["hits"] += 1
            else:
                self.cache["misses"] += 1
            self.cache["get_total_ms"] += duration_ms
            self.cache["max_get_ms"] = max(self.cache["max_get_ms"], duration_ms)

    def record_cache_set(self, duration_ms: float) -> None:
        """
        记录缓存设置操作指标
        
        Args:
            duration_ms: 操作执行时间（毫秒）
        """
        with self._lock:
            self.cache["sets"] += 1
            self.cache["set_total_ms"] += duration_ms
            self.cache["max_set_ms"] = max(self.cache["max_set_ms"], duration_ms)

    def record_llm_call(self, call_type: str, duration_ms: float, first_token_ms: float | None = None) -> None:
        """
        记录LLM调用指标
        
        Args:
            call_type: 调用类型（stream、tool_loop或其他）
            duration_ms: 调用执行时间（毫秒）
            first_token_ms: 首token响应时间（毫秒，可选）
        """
        with self._lock:
            # 用 call_type 把不同链路区分开，便于分析“流式”与“工具循环”的耗时差异。
            if call_type == "stream":
                self.llm["stream_calls"] += 1
            elif call_type == "tool_loop":
                self.llm["tool_loop_calls"] += 1
            else:
                self.llm["sync_calls"] += 1
            self.llm["total_ms"] += duration_ms
            self.llm["max_ms"] = max(self.llm["max_ms"], duration_ms)
            if first_token_ms is not None:
                self.llm["first_token_total_ms"] += first_token_ms
                self.llm["first_token_count"] += 1
                self.llm["max_first_token_ms"] = max(self.llm["max_first_token_ms"], first_token_ms)

    def record_tool_call(self, tool_name: str, duration_ms: float) -> None:
        """
        记录工具调用指标
        
        Args:
            tool_name: 工具名称
            duration_ms: 调用执行时间（毫秒）
        """
        with self._lock:
            bucket = self.tool_calls[tool_name]
            bucket["count"] += 1
            bucket["total_ms"] += duration_ms
            bucket["max_ms"] = max(bucket["max_ms"], duration_ms)

    def record_llm_sql_validation(self, ok: bool) -> None:
        """
        记录LLM SQL校验结果。
        
        Args:
            ok: 校验是否通过
        """
        with self._lock:
            if ok:
                self.llm_sql["validation_success"] += 1
            else:
                self.llm_sql["validation_failed"] += 1

    def record_llm_sql_execution(self, ok: bool, duration_ms: float) -> None:
        """
        记录LLM SQL执行结果。
        
        Args:
            ok: 执行是否成功
            duration_ms: 执行耗时
        """
        with self._lock:
            if ok:
                self.llm_sql["execution_success"] += 1
            else:
                self.llm_sql["execution_failed"] += 1
            self.llm_sql["execution_total_ms"] += duration_ms
            self.llm_sql["max_execution_ms"] = max(self.llm_sql["max_execution_ms"], duration_ms)

    def record_llm_sql_fallback(self) -> None:
        """
        记录LLM SQL回退到确定性查询。
        """
        with self._lock:
            self.llm_sql["fallbacks"] += 1

    def record_llm_sql_cache(self, hit: bool) -> None:
        """
        记录 LLM SQL 模板缓存命中情况。
        """
        with self._lock:
            if hit:
                self.llm_sql["cache_hits"] += 1
            else:
                self.llm_sql["cache_misses"] += 1

    def record_llm_sql_tokens(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
        """
        记录 LLM SQL token 消耗。
        """
        with self._lock:
            self.llm_sql["generated_prompt_tokens"] += int(prompt_tokens)
            self.llm_sql["generated_completion_tokens"] += int(completion_tokens)
            self.llm_sql["generated_total_tokens"] += int(total_tokens)

    def record_llm_sql_template_hit(self) -> None:
        """
        记录 SQL 模板命中次数。
        """
        with self._lock:
            self.llm_sql["template_hits"] += 1

    @staticmethod
    def _avg(total_ms: float, count: int) -> float:
        """
        计算平均值
        
        Args:
            total_ms: 总时间（毫秒）
            count: 次数
        
        Returns:
            平均值（保留两位小数）
        """
        # 平均值在 snapshot 阶段统一计算，避免在每次 record_* 时增加锁内开销。
        return round(total_ms / count, 2) if count else 0.0

    def snapshot(self) -> dict:
        """
        生成运行时指标快照
        
        Returns:
            包含所有指标的字典，包括：
            - 运行时间
            - HTTP请求统计
            - 数据库查询统计
            - 缓存操作统计
            - LLM调用统计
            - 工具调用统计
        """
        with self._lock:
            # 将 defaultdict 等内部结构转换为普通 dict，保证可 JSON 序列化且输出稳定。
            request_paths = {
                key: {
                    "count": value["count"],
                    "avgMs": self._avg(value["total_ms"], value["count"]),
                    "maxMs": round(value["max_ms"], 2),
                    "statuses": dict(value["statuses"]),
                }
                for key, value in sorted(self.request_paths.items())
            }
            tool_calls = {
                key: {
                    "count": value["count"],
                    "avgMs": self._avg(value["total_ms"], value["count"]),
                    "maxMs": round(value["max_ms"], 2),
                }
                for key, value in sorted(self.tool_calls.items())
            }

            # 预先计算一些常用分母，避免重复计算与除零。
            db_count = int(self.db_queries["count"])
            cache_get_count = int(self.cache["hits"] + self.cache["misses"])
            llm_call_count = int(self.llm["sync_calls"] + self.llm["stream_calls"] + self.llm["tool_loop_calls"])
            llm_sql_execution_count = int(self.llm_sql["execution_success"] + self.llm_sql["execution_failed"])
            uptime_seconds = round(time.time() - self.started_at, 2)

            return {
                "uptimeSeconds": uptime_seconds,
                "requests": {
                    "total": int(self.request_total),
                    "byPath": request_paths,
                },
                "database": {
                    "queryCount": db_count,
                    "avgMs": self._avg(self.db_queries["total_ms"], db_count),
                    "maxMs": round(self.db_queries["max_ms"], 2),
                },
                "cache": {
                    "hits": int(self.cache["hits"]),
                    "misses": int(self.cache["misses"]),
                    "sets": int(self.cache["sets"]),
                    "hitRate": round(self.cache["hits"] / cache_get_count, 4) if cache_get_count else 0.0,
                    "avgGetMs": self._avg(self.cache["get_total_ms"], cache_get_count),
                    "avgSetMs": self._avg(self.cache["set_total_ms"], int(self.cache["sets"])),
                    "maxGetMs": round(self.cache["max_get_ms"], 2),
                    "maxSetMs": round(self.cache["max_set_ms"], 2),
                },
                "llm": {
                    "syncCalls": int(self.llm["sync_calls"]),
                    "streamCalls": int(self.llm["stream_calls"]),
                    "toolLoopCalls": int(self.llm["tool_loop_calls"]),
                    "avgMs": self._avg(self.llm["total_ms"], llm_call_count),
                    "maxMs": round(self.llm["max_ms"], 2),
                    "avgFirstTokenMs": self._avg(self.llm["first_token_total_ms"], int(self.llm["first_token_count"])),
                    "maxFirstTokenMs": round(self.llm["max_first_token_ms"], 2),
                },
                "tools": tool_calls,
                "llmSql": {
                    "validationSuccess": int(self.llm_sql["validation_success"]),
                    "validationFailed": int(self.llm_sql["validation_failed"]),
                    "executionSuccess": int(self.llm_sql["execution_success"]),
                    "executionFailed": int(self.llm_sql["execution_failed"]),
                    "fallbacks": int(self.llm_sql["fallbacks"]),
                    "cacheHits": int(self.llm_sql["cache_hits"]),
                    "cacheMisses": int(self.llm_sql["cache_misses"]),
                    "templateHits": int(self.llm_sql["template_hits"]),
                    "generatedPromptTokens": int(self.llm_sql["generated_prompt_tokens"]),
                    "generatedCompletionTokens": int(self.llm_sql["generated_completion_tokens"]),
                    "generatedTotalTokens": int(self.llm_sql["generated_total_tokens"]),
                    "avgExecutionMs": self._avg(self.llm_sql["execution_total_ms"], llm_sql_execution_count),
                    "maxExecutionMs": round(self.llm_sql["max_execution_ms"], 2),
                },
            }


# 运行时指标实例
runtime_metrics = RuntimeMetrics()
