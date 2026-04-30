"""
文件作用：
- 用典型问句做烟雾测试，确认主链路可用。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

import argparse
import sys
import time

import httpx


# 定义函数 build_headers，负责组装当前步骤需要的对象或参数。
def build_headers(token: str | None) -> dict[str, str]:
    """
    作用：构建headers对象或结构。
    参数：token。
    返回：函数执行后的结果。
    """
    return {"Authorization": f"Bearer {token}"} if token else {}


# 定义函数 run_health_check，负责执行当前场景下的一段主流程。
def run_health_check(client: httpx.Client) -> tuple[bool, str]:
    """
    作用：执行run_health_check对应的业务逻辑。
    参数：client。
    返回：函数执行后的结果。
    """
    response = client.get("/health")
    ok = response.status_code == 200 and response.json().get("status") == "ok"
    return ok, response.text


# 定义函数 run_chat_case，负责执行当前场景下的一段主流程。
def run_chat_case(client: httpx.Client, session_id: str, message: str) -> tuple[bool, str]:
    """
    作用：执行run_chat_case对应的业务逻辑。
    参数：client、session_id、message。
    返回：函数执行后的结果。
    """
    response = client.post("/agent/chat", json={"sessionId": session_id, "message": message})
    ok = response.status_code == 200 and bool(response.json().get("reply"))
    return ok, response.text


# 定义函数 run_stream_case，负责执行当前场景下的一段主流程。
def run_stream_case(client: httpx.Client, session_id: str, message: str) -> tuple[bool, str]:
    """
    作用：执行run_stream_case对应的业务逻辑。
    参数：client、session_id、message。
    返回：函数执行后的结果。
    """
    with client.stream("POST", "/agent/chat/stream", json={"sessionId": session_id, "message": message}) as response:
        body_lines = []
        saw_token = False
        saw_done = False
        for line in response.iter_lines():
            if not line:
                continue
            body_lines.append(line)
            if line == "event: token":
                saw_token = True
            if line == "event: done":
                saw_done = True
                break
        ok = response.status_code == 200 and saw_token and saw_done
        return ok, "\n".join(body_lines)


# 定义函数 main，作为脚本入口，串起当前文件的整体执行流程。
def main() -> int:
    """
    作用：作为脚本入口，串联整体执行流程。
    参数：无。
    返回：函数执行后的结果。
    """
    parser = argparse.ArgumentParser(description="运行 sales-agent 烟雾测试")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088", help="服务地址")
    parser.add_argument("--token", default=None, help="可选 Bearer Token")
    parser.add_argument("--timeout", type=float, default=120.0, help="单请求超时时间")
    args = parser.parse_args()

    headers = build_headers(args.token)
    cases = [
        ("health", lambda client: run_health_check(client)),
        ("chat-intro", lambda client: run_chat_case(client, "smoke-intro", "你好，你能做什么？")),
        ("chat-trend", lambda client: run_chat_case(client, "smoke-trend", "近6个月的月度销售趋势是什么？")),
        ("chat-summary", lambda client: run_chat_case(client, "smoke-summary", "本月华东区销售额是多少？")),
        ("chat-chart", lambda client: run_chat_case(client, "smoke-chart", "帮我生成近6个月销售趋势图")),
        ("chat-anomaly", lambda client: run_chat_case(client, "smoke-anomaly", "最近有没有销售异常？")),
        ("stream-trend", lambda client: run_stream_case(client, "smoke-stream", "近6个月的月度销售趋势是什么？")),
    ]

    failures = []
    with httpx.Client(base_url=args.base_url, headers=headers, timeout=args.timeout) as client:
        for name, case in cases:
            started = time.perf_counter()
            ok, detail = case(client)
            duration_ms = int((time.perf_counter() - started) * 1000)
            print(f"[{'PASS' if ok else 'FAIL'}] {name} ({duration_ms}ms)")
            if not ok:
                failures.append((name, detail))

    if failures:
        print("\n以下用例失败：", file=sys.stderr)
        for name, detail in failures:
            print(f"\n--- {name} ---\n{detail}", file=sys.stderr)
        return 1

    print("\n烟雾测试全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
