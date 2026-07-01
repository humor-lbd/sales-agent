"""
文件作用：
- 检查并发稳定性和会话记忆落库是否正常。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

import argparse
import asyncio
import json
import statistics
import time
import uuid

import httpx
from sqlalchemy import create_engine, text

from _common import build_headers


# 定义函数 percentile_95，负责当前文件中的一个关键步骤或对外能力。
def percentile_95(values: list[float]) -> float:
    """
    作用：执行percentile_95对应的业务逻辑。
    参数：values。
    返回：函数执行后的结果。
    """
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=20, method="inclusive")[18]


# 定义函数 run_parallel_chats，负责执行当前场景下的一段主流程。
async def run_parallel_chats(base_url: str, headers: dict[str, str], message: str, concurrency: int, timeout: float) -> tuple[int, list[float]]:
    """
    作用：执行run_parallel_chats对应的业务逻辑。
    参数：base_url、headers、message、concurrency、timeout。
    返回：函数执行后的结果。
    """
    latencies: list[float] = []
    successes = 0

    async def worker(index: int, client: httpx.AsyncClient) -> None:
        """
        作用：执行worker对应的业务逻辑。
        参数：index、client。
        返回：函数执行后的结果。
        """
        nonlocal successes
        session_id = f"stability-{uuid.uuid4().hex[:12]}-{index}"
        started = time.perf_counter()
        response = await client.post("/agent/chat", json={"sessionId": session_id, "message": message})
        duration_ms = (time.perf_counter() - started) * 1000
        latencies.append(duration_ms)
        if response.status_code == 200 and response.json().get("reply"):
            successes += 1

    async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout) as client:
        await asyncio.gather(*(worker(index, client) for index in range(concurrency)))
    return successes, latencies


# 定义函数 verify_memory_row，负责当前文件中的一个关键步骤或对外能力。
def verify_memory_row(base_url: str, headers: dict[str, str], timeout: float, database_url: str) -> tuple[bool, str]:
    """
    作用：执行verify_memory_row对应的业务逻辑。
    参数：base_url、headers、timeout、database_url。
    返回：函数执行后的结果。
    """
    session_id = f"memory-{uuid.uuid4().hex[:10]}"
    with httpx.Client(base_url=base_url, headers=headers, timeout=timeout) as client:
        first = client.post("/agent/chat", json={"sessionId": session_id, "message": "你好，你能做什么？"})
        second = client.post("/agent/chat", json={"sessionId": session_id, "message": "请继续上一个问题，简短总结一次。"})
        if first.status_code != 200 or second.status_code != 200:
            return False, f"chat failed: first={first.status_code} second={second.status_code}"

    engine = create_engine(database_url)
    with engine.connect() as connection:
        row = connection.execute(
            text("select messages from sa_chat_memory where session_id = :session_id"),
            {"session_id": session_id},
        ).fetchone()
    if not row:
        return False, "sa_chat_memory 中未找到会话记录"
    messages = json.loads(row[0])
    with httpx.Client(base_url=base_url, headers=headers, timeout=timeout) as client:
        client.delete(f"/agent/session/{session_id}")
    if len(messages) < 4:
        return False, f"会话消息数量不足，实际为 {len(messages)}"
    return True, f"消息条数 {len(messages)}"


# 定义函数 fetch_metrics，负责从外部依赖中抓取或查询数据。
def fetch_metrics(base_url: str, headers: dict[str, str], timeout: float) -> dict:
    """
    作用：执行fetch_metrics对应的业务逻辑。
    参数：base_url、headers、timeout。
    返回：函数执行后的结果。
    """
    with httpx.Client(base_url=base_url, headers=headers, timeout=timeout) as client:
        response = client.get("/ops/metrics")
        response.raise_for_status()
        return response.json()


# 定义函数 main，作为脚本入口，串起当前文件的整体执行流程。
def main() -> int:
    """
    作用：作为脚本入口，串联整体执行流程。
    参数：无。
    返回：函数执行后的结果。
    """
    parser = argparse.ArgumentParser(description="测 sales-agent 并发稳定性与会话记忆一致性")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088", help="服务地址")
    parser.add_argument("--token", default=None, help="可选 Bearer Token")
    parser.add_argument("--database-url", required=True, help="用于校验 sa_chat_memory 的数据库连接串")
    parser.add_argument("--concurrency", type=int, default=4, help="并发请求数")
    parser.add_argument("--timeout", type=float, default=120.0, help="请求超时")
    parser.add_argument("--message", default="本月华东区销售额是多少？", help="并发探针问题")
    args = parser.parse_args()

    headers = build_headers(args.token)
    successes, latencies = asyncio.run(
        run_parallel_chats(args.base_url, headers, args.message, args.concurrency, args.timeout)
    )
    avg_ms = statistics.mean(latencies)
    p95_ms = percentile_95(latencies)
    print(
        f"parallel-chat: success={successes}/{args.concurrency} avg={avg_ms:.0f}ms max={max(latencies):.0f}ms p95={p95_ms:.0f}ms"
    )

    memory_ok, memory_detail = verify_memory_row(args.base_url, headers, args.timeout, args.database_url)
    print(f"memory-roundtrip: {'PASS' if memory_ok else 'FAIL'} {memory_detail}")
    if not memory_ok:
        return 1

    metrics = fetch_metrics(args.base_url, headers, args.timeout)
    print(
        "metrics-snapshot: "
        f"requests={metrics['requests']['total']} "
        f"dbQueries={metrics['database']['queryCount']} "
        f"cacheHitRate={metrics['cache']['hitRate']:.2%} "
        f"avgFirstTokenMs={metrics['llm']['avgFirstTokenMs']:.0f}"
    )
    return 0 if successes == args.concurrency else 1


if __name__ == "__main__":
    raise SystemExit(main())
