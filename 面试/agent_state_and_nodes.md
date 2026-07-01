# Sales Agent 面试梳理：State 设计与节点职责

## 1. 项目 Agent 架构概览

这个项目是一个基于 **LangGraph + ReAct + Tool Calling** 的销售数据分析 Agent。

核心入口和文件：

- `app/logic/agent.py`：对外 Agent 入口，提供同步和流式聊天能力。
- `app/graph/builder.py`：组装 LangGraph 工作流。
- `app/graph/state.py`：定义 Agent 执行过程中的状态结构。
- `app/graph/router.py`：定义节点之间的路由逻辑。
- `app/graph/nodes/*.py`：每个图节点的具体实现。

整体执行流程：

```text
START
  ↓
bootstrap
  ↓
load_memory
  ↓
guardrails
  ↓
react_agent  ←→  react_tool_executor
  ↓
persist_memory
  ↓
END
```

流程说明：

1. 初始化状态。
2. 加载历史会话和摘要上下文。
3. 做业务边界检查。
4. 调用 ReAct Agent 判断是否需要工具。
5. 如需工具，执行工具并把结果交回模型。
6. 生成最终回答后保存记忆并结束。

---

## 2. GraphState 是怎么设计的？

状态定义在 `app/graph/state.py`。

```python
class GraphState(TypedDict, total=False):
    session_id: str
    request_text: str
    messages: list[dict[str, Any]]
    react_messages: list[Any]
    summary_context: str | None
    tool_results: dict[str, Any]
    artifacts: list[dict[str, Any]]
    final_answer: str | None
    streamed_final_answer: bool
    error: str | None
    rejected: bool
    tool_call_count: int
    react_round_count: int
```

面试表达：

> 这个项目把 Agent 一轮执行过程中的所有中间信息都放在 `GraphState` 里。每个节点只读取自己关心的字段，然后返回局部状态更新，由 LangGraph 负责合并。这样节点之间是松耦合的，也方便调试、扩展和流式输出。

字段说明：

| 字段 | 作用 |
|---|---|
| `session_id` | 当前会话 ID，用来读取和保存历史消息。 |
| `request_text` | 用户当前输入。 |
| `messages` | 持久化的历史消息，通常是简单 dict 格式。 |
| `react_messages` | 给 LLM / ReAct 循环使用的 LangChain Message 列表。 |
| `summary_context` | 长历史压缩后的摘要，放入系统提示词。 |
| `tool_results` | 工具调用返回的文本结果。 |
| `artifacts` | 图表等结构化结果，供前端展示。 |
| `final_answer` | 最终回复，有值时说明本轮可以结束。 |
| `streamed_final_answer` | 标记最终答案是否已经流式输出过。 |
| `error` | 异常信息。 |
| `rejected` | 是否被 guardrails 拒绝。 |
| `tool_call_count` | 当前轮工具调用次数，用于防循环。 |
| `react_round_count` | 当前轮 ReAct 推理轮数。 |

---

## 3. 为什么分 messages 和 react_messages？

### messages

`messages` 是持久化历史，来自 `memory_service.get_messages()`，一般是这种结构：

```python
{"role": "user", "content": "..."}
{"role": "assistant", "content": "..."}
```

它适合保存到数据库或本地存储。

### react_messages

`react_messages` 是模型执行时真正使用的上下文，是 LangChain Message 对象列表，例如：

- `HumanMessage`
- `AIMessage`
- `ToolMessage`
- `SystemMessage`

它不只是普通聊天记录，还会记录 ReAct 执行轨迹：

```text
HumanMessage
AIMessage(tool_calls)
ToolMessage
AIMessage(final_answer)
```

面试表达：

> `messages` 面向持久化，`react_messages` 面向模型执行。这样既避免把 LangChain 内部对象直接持久化，也方便在 ReAct 循环里不断追加模型回复和工具结果。

---

## 4. 各节点职责

## 4.1 bootstrap_node

位置：`app/graph/nodes/bootstrap.py`

职责：初始化一轮 Agent 执行的默认状态。

它初始化：

```python
messages = []
react_messages = []
summary_context = None
tool_results = {}
artifacts = []
final_answer = None
streamed_final_answer = False
error = None
rejected = False
tool_call_count = 0
react_round_count = 0
```

面试表达：

> `bootstrap_node` 是状态初始化节点，保证后续节点拿到的字段都有默认值，减少空值判断。

---

## 4.2 load_memory_node

位置：`app/graph/nodes/memory.py`

职责：加载会话历史，并构造当前轮 ReAct 的上下文。

主要逻辑：

1. 根据 `session_id` 从 `memory_service` 读取历史消息。
2. 判断当前问题是否是追问。
3. 如果不是追问，只把当前问题放进 `react_messages`。
4. 如果是追问，带上最近若干轮历史。
5. 如果历史太长，把更早历史压缩成 `summary_context`。
6. 返回 `messages`、`react_messages` 和 `summary_context`。

返回示例：

```python
{
    "messages": messages,
    "react_messages": react_messages,
    "summary_context": summary_context,
}
```

面试表达：

> `load_memory_node` 没有简单粗暴地把所有历史都塞进模型，而是做了追问识别、窗口裁剪和历史摘要。普通问题只使用当前输入，追问才带最近上下文，这样可以降低 token 成本，也减少历史噪声。

---

## 4.3 guardrails_node

位置：`app/graph/nodes/guardrails.py`

职责：做业务边界控制。

它拒绝两类请求：

1. 写操作：
   - 修改
   - 删除
   - 新增
   - 插入
   - 更新
   - 写入

2. 预测类请求：
   - 预测
   - 预估
   - 明年销售
   - 未来销售

被拒绝时返回：

```python
{
    "rejected": True,
    "final_answer": "我只能帮助查询和分析销售数据，不能修改、删除或新增业务数据。",
    "streamed_final_answer": False,
}
```

面试表达：

> `guardrails_node` 是业务安全边界。这个 Agent 的定位是销售数据查询和分析，所以它会拒绝数据写入和未来预测，避免 Agent 越权或给出无法保证准确性的预测结果。

---

## 4.4 react_agent_node

位置：`app/graph/nodes/react_agent.py`

职责：调用绑定工具的 LLM，让模型决定下一步是直接回答还是调用工具。

核心逻辑：

```python
llm_with_tools = _get_llm_with_tools(runtime)
messages = _ensure_react_messages(state)
response = llm_with_tools.invoke([
    _build_system_message(runtime, state),
    *messages,
])
return _finalize_react_turn(...)
```

系统提示词里会注入：

- 当前日期。
- 当前用户权限信息。
- 当前用户请求。
- 历史摘要。

面试表达：

> `react_agent_node` 是大脑节点。它把系统提示词、历史上下文和工具 schema 一起交给模型，由模型决定是直接生成最终回答，还是发起某个工具调用。

---

## 4.5 _finalize_react_turn

位置：`app/graph/nodes/react_agent.py`

职责：统一处理一次 LLM 回复后的收尾逻辑。

它做几件事：

1. 把 LLM 回复追加到 `react_messages`。
2. 检查回复里是否有 `tool_calls`。
3. 如果有工具调用但达到工具调用上限，就停止。
4. 如果有工具调用，返回 `final_answer = None`，让图路由到工具执行节点。
5. 如果没有工具调用，则提取最终回答。
6. 如果生成了图表 artifact，会补充“已生成图表”。
7. 如果没有 artifact，但模型声称图表已生成，会清理这种误导性表达。

面试表达：

> `_finalize_react_turn` 是 ReAct 单轮的统一收口。它既处理工具分支，也处理最终回答，还做了防循环和图表一致性校验。例如没有图表 artifact 时，会去掉“图表已生成”这类可能的幻觉描述。

---

## 4.6 react_tool_executor_node

位置：`app/graph/nodes/react_tool_executor.py`

职责：执行模型发起的工具调用，并把结果写回上下文。

执行流程：

1. 从 `react_messages` 里找到最后一个 `AIMessage`。
2. 读取里面的 `tool_calls`。
3. 根据工具名找到真实工具。
4. 执行工具。
5. 把结果包装成 `ToolMessage`。
6. 追加回 `react_messages`。
7. 如果工具返回图表，则加入 `artifacts`。
8. 更新 `tool_results`。
9. 更新 `tool_call_count`。

返回示例：

```python
{
    "react_messages": messages,
    "artifacts": artifacts,
    "tool_results": {"text": merged_text},
    "tool_call_count": executed_count,
}
```

面试表达：

> `react_tool_executor_node` 是执行器节点。它不负责思考，只负责把模型生成的 tool call 转成真实函数调用，并把工具结果以 `ToolMessage` 的形式交还给模型，让下一轮 LLM 基于工具结果继续推理。

---

## 4.7 persist_memory_node

位置：`app/graph/nodes/memory.py`

职责：把当前用户输入和最终回答保存进会话历史。

保存结构：

```python
history + [
    {"role": "user", "content": request_text},
    {"role": "assistant", "content": final_answer, "artifacts": artifacts},
]
```

面试表达：

> `persist_memory_node` 是收尾节点，只在最终回答产生后执行，把本轮对话写回 memory service，保证下一轮用户追问时可以基于历史继续分析。

---

## 4.8 error_handler

位置：`app/graph/nodes/error_handler.py`

职责：异常兜底。

异常时返回：

```python
{
    "error": str(exc),
    "artifacts": [],
    "final_answer": "服务暂时不可用，请稍后重试。",
    "streamed_final_answer": False,
    "rejected": False,
}
```

面试表达：

> 错误处理没有让异常直接暴露给用户，而是转成稳定的 `GraphState` 和兜底回复，保证前端协议稳定。

---

## 5. 路由逻辑

位置：`app/graph/router.py`

### guardrails 后路由

```python
def route_after_guardrails(state: GraphState) -> str:
    return "persist_memory" if state.get("rejected") else "react_agent"
```

说明：

- 如果被拒绝，直接保存拒绝回答并结束。
- 如果未被拒绝，进入 ReAct Agent。

### react_agent 后路由

```python
def route_after_react_agent(state: GraphState) -> str:
    if state.get("final_answer"):
        return "persist_memory"

    messages = state.get("react_messages") or []
    if not messages:
        return "persist_memory"

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []
    return "react_tool_executor" if tool_calls else "persist_memory"
```

说明：

- 如果已经有最终回答，进入保存记忆节点。
- 如果最后一条 AIMessage 有工具调用，进入工具执行节点。
- 如果没有工具调用，也进入保存记忆节点。

---

## 6. ReAct 循环怎么跑？

核心循环：

```text
react_agent
  ↓ 如果有 tool_calls
react_tool_executor
  ↓ 把 ToolMessage 写回 react_messages
react_agent
  ↓ 模型基于工具结果继续判断
...
  ↓ 直到 final_answer 不为空
persist_memory
```

面试表达：

> 这是典型 ReAct 模式。LLM 不是一次性回答，而是可以多轮“思考、调用工具、观察结果、再思考”。`react_messages` 保存完整执行轨迹，直到模型不再调用工具，而是输出最终回答。

---

## 7. 同步和流式调用

### 同步入口

位置：`app/logic/agent.py`

```python
def chat(self, session_id: str, message: str) -> dict[str, Any]:
    context = self._build_context()
    result = self._run_graph(self.graph, session_id, message, context, "graph_total")
    return {
        "reply": result.get("final_answer", ""),
        "artifacts": result.get("artifacts") or [],
    }
```

同步模式直接执行：

```python
graph.invoke(initial_state, context=context)
```

### 流式入口

位置：`app/logic/agent.py`

```python
def chat_stream(self, session_id: str, message: str):
    ...
```

流式模式会输出：

- `status`：当前进度。
- `token`：模型生成的文本片段。
- `artifacts`：图表等结构化结果。
- `done`：结束标记。

流式模式为了更细粒度控制前端体验，会手动串起部分节点：

```text
bootstrap_node
load_memory_node
guardrails_node
stream_react_agent_node
react_tool_executor_node
```

面试表达：

> 同步模式直接跑 LangGraph；流式模式为了更好地控制 token 输出和状态事件，手动串起核心节点。这样前端可以实时看到“正在读取上下文”“正在调用工具”“正在输出回答”等状态。

---

## 8. 这个 State 设计的优点

### 1. 节点解耦

每个节点只关心自己的字段：

- memory 节点关心 `session_id`、`messages`、`summary_context`。
- guardrails 节点关心 `request_text`、`rejected`、`final_answer`。
- tool executor 关心 `react_messages`、`tool_results`、`artifacts`。

### 2. 路由清晰

路由只依赖少量关键状态：

- `rejected`
- `final_answer`
- `tool_calls`

### 3. 支持 ReAct 多轮工具调用

`react_messages` 可以持续追加：

```text
HumanMessage
AIMessage(tool_calls)
ToolMessage
AIMessage(final_answer)
```

### 4. 支持结构化前端展示

`artifacts` 单独存图表结果，避免和自然语言回答混在一起。

### 5. 支持长对话

`summary_context` 用于保存历史摘要，避免上下文过长。

### 6. 支持防循环

`tool_call_count` 和 `react_round_count` 可以限制工具调用次数和推理轮数。

---

## 9. 面试可直接背的完整回答

> 我这个项目的 Agent 是基于 LangGraph 实现的，是一个 ReAct 风格的销售数据分析 Agent。核心状态是 `GraphState`，里面保存了一轮请求从输入到最终回答的所有中间数据，比如 `session_id`、当前问题 `request_text`、历史消息 `messages`、模型执行用的 `react_messages`、历史摘要 `summary_context`、工具结果 `tool_results`、图表类结构化结果 `artifacts`、最终回答 `final_answer`，以及防循环用的 `tool_call_count` 和 `react_round_count`。
>
> 整体图流程是 `bootstrap -> load_memory -> guardrails -> react_agent -> react_tool_executor -> react_agent -> persist_memory`。其中 `bootstrap` 负责初始化状态，`load_memory` 负责加载历史和压缩长上下文，`guardrails` 负责拦截写操作和预测类请求，`react_agent` 是大脑节点，会调用绑定工具的 LLM，让模型决定是否需要调用工具，`react_tool_executor` 负责执行工具并把结果作为 `ToolMessage` 写回上下文，最后 `persist_memory` 把本轮用户问题和助手回答保存起来。
>
> 这里我把 `messages` 和 `react_messages` 分开设计。`messages` 是数据库持久化格式，比较简单；`react_messages` 是 LangChain Message 对象，用来承载 ReAct 执行轨迹，包括 AIMessage、ToolMessage 和工具调用结果。这样既方便存储，也方便模型多轮工具调用。
>
> 路由逻辑也比较清晰：如果 guardrails 拒绝，就直接进入 memory 持久化；如果 react_agent 产生了 `final_answer`，就结束；如果 AIMessage 里有 tool_calls，就进入工具执行节点，然后再回到 react_agent。这样形成一个可控的 ReAct 循环。
>
> 这个设计的优点是状态集中、节点职责清晰、方便调试，也支持同步和流式两种调用方式。流式模式下会额外输出 status、token、artifacts 和 done 事件，前端体验更好。

---

## 10. 面试官可能追问

### Q1：为什么不用一个大函数直接写完整流程？

答：

> 因为 Agent 流程天然有分支和循环，用 LangGraph 可以把每一步拆成节点，状态通过 `GraphState` 传递。这样每个节点职责单一，也方便加 guardrails、memory、tool executor、error handler 等逻辑。

### Q2：怎么避免 Agent 无限调用工具？

答：

> 用 `tool_call_count` 统计当前轮工具调用次数，在 `react_agent_node` 和 `react_tool_executor_node` 都会检查 `agent_max_tool_calls`，达到上限后返回兜底回答，停止 ReAct 循环。

### Q3：历史上下文太长怎么办？

答：

> `load_memory_node` 会保留最近窗口，并把更早历史压缩成 `summary_context`。优先用 LLM 摘要，如果失败就回退到规则摘要。最终摘要会放进系统提示词，而不是把所有历史完整塞给模型。

### Q4：工具调用结果怎么给模型看？怎么给前端看？

答：

> 工具返回结果会拆成两部分：文本内容放进 `ToolMessage`，让模型继续推理；图表等结构化内容放进 `artifacts`，给前端渲染。这样实现了模型上下文和 UI 展示的分离。

### Q5：权限控制在哪里做？

答：

> 有两层。一层是 `guardrails_node` 做业务边界，比如拒绝写操作和预测类请求；另一层是在系统提示词里注入当前用户信息，同时真正的数据权限由 Service 层强制过滤，避免只依赖提示词约束模型。

### Q6：同步和流式为什么分开？

答：

> 同步模式可以直接 `graph.invoke`。流式模式为了向前端实时输出 token 和状态，所以手动串起节点，尤其是 `stream_react_agent_node` 会在没有工具调用时直接流式吐 token；如果出现工具调用，则先暂停文本输出，执行工具后再继续。
