<#
文件作用：
- 串联烟雾测试、性能探针和回归对比，作为切流前检查脚本。
- 阅读这个脚本时，建议先看参数，再看它按什么顺序执行主流程。
#>

param(
    [string]$PythonBaseUrl = "http://127.0.0.1:8088",
    [string]$JavaBaseUrl = "http://127.0.0.1:8080",
    [string]$Token = "",
    [string]$DatabaseUrl = ""
)

# 下面进入脚本主流程：先校验参数，再按顺序执行检查或启动动作。
$ErrorActionPreference = "Stop"

$tokenArgs = @()
if ($Token) {
    $tokenArgs += @("--token", $Token)
}

Write-Host "== Smoke test =="
python scripts/smoke_test.py --base-url $PythonBaseUrl @tokenArgs

Write-Host "`n== Performance probe =="
python scripts/perf_probe.py --base-url $PythonBaseUrl @tokenArgs

if ($DatabaseUrl) {
    Write-Host "`n== Stability probe =="
    python scripts/stability_probe.py --base-url $PythonBaseUrl --database-url $DatabaseUrl @tokenArgs
}

Write-Host "`n== Java/Python regression =="
python scripts/regression_compare.py --java-base-url $JavaBaseUrl --python-base-url $PythonBaseUrl @tokenArgs

Write-Host "`n预切换检查全部通过"
