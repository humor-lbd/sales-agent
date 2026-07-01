"""
文件作用：
- 对比 Java 与 Python 工具接口结果，验证迁移后行为是否一致。
- 阅读这个文件时，建议先看文件头说明，再顺着主要函数或类往下追踪。
"""

import argparse
import difflib
import json
import sys
from dataclasses import dataclass

import httpx

from _common import build_headers


@dataclass
# 定义类 Case，把当前文件相关的状态或能力封装起来，便于在其他模块中复用。
class Case:
    name: str
    path: str
    payload: dict | None
    compare_mode: str


CASES = [
    Case(
        name="query-orders",
        path="/test/tool/query-orders",
        payload={"startDate": "2026-04-01", "endDate": "2026-04-30", "regionName": "华东区", "limit": 10},
        compare_mode="text",
    ),
    Case(
        name="region-ranking",
        path="/test/tool/region-ranking",
        payload={"startDate": "2026-04-01", "endDate": "2026-04-30"},
        compare_mode="text",
    ),
    Case(
        name="top-products",
        path="/test/tool/top-products",
        payload={"startDate": "2026-04-01", "endDate": "2026-04-30", "topN": 5},
        compare_mode="text",
    ),
    Case(
        name="monthly-trend",
        path="/test/tool/monthly-trend",
        payload={"months": 6, "regionName": "华东区"},
        compare_mode="text",
    ),
    Case(
        name="line-chart",
        path="/test/tool/line-chart",
        payload={"months": 6, "regionName": "华东区", "title": "近6个月销售趋势"},
        compare_mode="chart",
    ),
]


# 定义函数 normalize_text，负责把输入整理成统一格式，方便后续处理。
def normalize_text(value: str) -> str:
    """
    作用：执行normalize_text对应的业务逻辑。
    参数：value。
    返回：函数执行后的结果。
    """
    return "\n".join(line.rstrip() for line in value.strip().splitlines())


# 定义函数 normalize_chart，负责把输入整理成统一格式，方便后续处理。
def normalize_chart(value: str) -> str:
    """
    作用：执行normalize_chart对应的业务逻辑。
    参数：value。
    返回：函数执行后的结果。
    """
    payload = value.removeprefix("CHART_JSON:")
    return json.dumps(json.loads(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# 定义函数 fetch_case，负责从外部依赖中抓取或查询数据。
def fetch_case(client: httpx.Client, case: Case) -> str:
    """
    作用：执行fetch_case对应的业务逻辑。
    参数：client、case。
    返回：函数执行后的结果。
    """
    response = client.post(case.path, json=case.payload or {})
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return response.text
        if isinstance(payload, str):
            return payload
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return response.text


# 定义函数 compare_case，负责当前文件中的一个关键步骤或对外能力。
def compare_case(case: Case, java_value: str, python_value: str) -> tuple[bool, str]:
    """
    作用：执行compare_case对应的业务逻辑。
    参数：case、java_value、python_value。
    返回：函数执行后的结果。
    """
    if case.compare_mode == "chart":
        java_norm = normalize_chart(java_value)
        python_norm = normalize_chart(python_value)
    else:
        java_norm = normalize_text(java_value)
        python_norm = normalize_text(python_value)

    if java_norm == python_norm:
        return True, ""

    diff = "\n".join(
        difflib.unified_diff(
            java_norm.splitlines(),
            python_norm.splitlines(),
            fromfile="java",
            tofile="python",
            lineterm="",
        )
    )
    return False, diff


# 定义函数 main，作为脚本入口，串起当前文件的整体执行流程。
def main() -> int:
    """
    作用：作为脚本入口，串联整体执行流程。
    参数：无。
    返回：函数执行后的结果。
    """
    parser = argparse.ArgumentParser(description="对比 Java / Python 工具接口输出")
    parser.add_argument("--java-base-url", required=True, help="Java 服务地址")
    parser.add_argument("--python-base-url", required=True, help="Python 服务地址")
    parser.add_argument("--java-token", default=None, help="Java Bearer Token")
    parser.add_argument("--python-token", default=None, help="Python Bearer Token")
    parser.add_argument("--timeout", type=float, default=60.0, help="请求超时")
    args = parser.parse_args()

    failures = []
    with httpx.Client(base_url=args.java_base_url, headers=build_headers(args.java_token), timeout=args.timeout) as java_client:
        with httpx.Client(base_url=args.python_base_url, headers=build_headers(args.python_token), timeout=args.timeout) as python_client:
            for case in CASES:
                java_value = fetch_case(java_client, case)
                python_value = fetch_case(python_client, case)
                ok, diff = compare_case(case, java_value, python_value)
                print(f"[{'PASS' if ok else 'FAIL'}] {case.name}")
                if not ok:
                    failures.append((case.name, diff))

    if failures:
        print("\n以下用例存在差异：", file=sys.stderr)
        for name, diff in failures:
            print(f"\n--- {name} ---\n{diff}", file=sys.stderr)
        return 1

    print("\nJava / Python 确定性接口回归通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
