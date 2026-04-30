<!--
文件作用：
- 说明前端子项目的安装、启动和构建方式。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

# frontend

这是 `sales-agent` 的 Python 版前端，基于 `jc-agent-front` 的 Vue 3 页面结构重建，并对接 Python 后端：

- 登录页
- 聊天页
- 流式回答
- 图表渲染
- 本地会话管理
- Python 后端运行时指标抽屉

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 启动

1. 安装依赖

```powershell
npm install
```

2. 复制环境变量

```powershell
Copy-Item .env.example .env
```

3. 启动开发服务器

```powershell
npm run dev
```

默认前端地址：

- `http://127.0.0.1:5174`

默认代理到 Python 后端：

- `http://127.0.0.1:8088`
