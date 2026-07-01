"""
文件作用：
- 压测同步和流式接口，帮助快速观察平均耗时与首 token 延迟。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

import argparse
import statistics
import time

import httpx

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


# 定义函数 probe_chat，负责当前文件中的一个关键步骤或对外能力。
def probe_chat(client: httpx.Client, iterations: int, payload: dict) -> list[float]:
    """
    作用：执行probe_chat对应的业务逻辑。
    参数：client、iterations、payload。
    返回：函数执行后的结果。
    """
    latencies = []
    for index in range(iterations):
        payload["sessionId"] = f"perf-chat-{index}"
        started = time.perf_counter()
        response = client.post("/agent/chat", json=payload)
        response.raise_for_status()
        latencies.append((time.perf_counter() - started) * 1000)
    return latencies


# 定义函数 probe_stream_first_token，负责当前文件中的一个关键步骤或对外能力。
def probe_stream_first_token(client: httpx.Client, iterations: int, payload: dict) -> list[float]:
    """
    作用：执行probe_stream_first_token对应的业务逻辑。
    参数：client、iterations、payload。
    返回：函数执行后的结果。
    """
    latencies = []
    for index in range(iterations):
        payload["sessionId"] = f"perf-stream-{index}"
        started = time.perf_counter()
        with client.stream("POST", "/agent/chat/stream", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line == "event: token":
                    latencies.append((time.perf_counter() - started) * 1000)
                    break
    return latencies


# 定义函数 print_stats，负责当前文件中的一个关键步骤或对外能力。
def print_stats(label: str, values: list[float]) -> None:
    """
    作用：执行print_stats对应的业务逻辑。
    参数：label、values。
    返回：函数执行后的结果。
    """
    avg = statistics.mean(values)
    p95 = percentile_95(values)
    print(f"{label}: avg={avg:.0f}ms min={min(values):.0f}ms max={max(values):.0f}ms p95={p95:.0f}ms")


# 定义函数 main，作为脚本入口，串起当前文件的整体执行流程。
def main() -> int:
    """
    作用：作为脚本入口，串联整体执行流程。
    参数：无。
    返回：函数执行后的结果。
    """
    parser = argparse.ArgumentParser(description="测 sales-agent 同步与流式接口性能")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088", help="服务地址")
    parser.add_argument("--token", default=None, help="可选 Bearer Token")
    parser.add_argument("--iterations", type=int, default=3, help="每类探针执行次数")
    parser.add_argument("--message", default="本月华东区销售额是多少？", help="探针问题")
    parser.add_argument("--timeout", type=float, default=120.0, help="请求超时")
    args = parser.parse_args()

    payload = {"sessionId": "perf-default", "message": args.message}
    headers = build_headers(args.token)
    with httpx.Client(base_url=args.base_url, headers=headers, timeout=args.timeout) as client:
        chat_latencies = probe_chat(client, args.iterations, payload.copy())
        stream_latencies = probe_stream_first_token(client, args.iterations, payload.copy())

    print_stats("/agent/chat", chat_latencies)
    print_stats("/agent/chat/stream first token", stream_latencies)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
