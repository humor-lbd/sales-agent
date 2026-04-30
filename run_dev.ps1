<#
文件作用：
- 在 Windows 开发环境中启动 FastAPI 服务，便于本地联调。
- 阅读这个脚本时，建议先看参数，再看它按什么顺序执行主流程。
#>

$python = "E:\develop\mini_anaconda\envs\dev\python.exe"

if (-not (Test-Path $python)) {
    throw "未找到指定 Python 环境：$python"
}

& $python -m uvicorn app.main:app --reload --port 8088
