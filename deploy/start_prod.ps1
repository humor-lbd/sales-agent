<#
文件作用：
- 在 Windows 环境中用生产参数启动 Python 服务。
- 阅读这个脚本时，建议先看参数，再看它按什么顺序执行主流程。
#>

param(
    [string]$PythonPath = "E:\develop\mini_anaconda\envs\dev\python.exe",
    [string]$Host = "0.0.0.0",
    [int]$Port = 8088,
    [int]$Workers = 2
)

# 下面进入脚本主流程：先校验参数，再按顺序执行检查或启动动作。
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path $PythonPath)) {
    throw "未找到 Python 可执行文件：$PythonPath"
}

if (-not (Test-Path (Join-Path $projectRoot ".env"))) {
    throw "未找到 .env，请先根据 .env.example 补齐环境变量"
}

Push-Location $projectRoot
try {
    & $PythonPath -m uvicorn app.main:app --host $Host --port $Port --workers $Workers
}
finally {
    Pop-Location
}
