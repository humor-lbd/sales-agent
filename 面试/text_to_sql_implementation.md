# Sales Agent 面试梳理：Text-to-SQL 实现、校验与安全防护

## 1. Text-to-SQL 在项目里的定位

这个项目的 Text-to-SQL 不是让大模型直接面对用户自然语言生成 SQL，而是采用了更安全的 **结构化任务 -> SQL 生成/模板匹配 -> 校验 -> 权限注入 -> 执行 -> 结果映射** 的链路。

核心代码位置：

- `app/logic/sql_agent/service.py`：Text-to-SQL 主服务，负责整体编排。
- `app/logic/sql_agent/generator.py`：调用 LLM 生成 SQL JSON。
- `app/logic/sql_agent/validator.py`：SQL 安全校验和业务口径校验。
- `app/logic/sql_agent/policy.py`：权限过滤注入。
- `app/logic/sql_agent/executor.py`：参数化执行 SQL。
- `app/logic/sql_agent/schema_registry.py`：允许访问的表、字段、join 和指标口径白名单。
- `app/logic/sql_agent/template_registry.py`：高频任务 SQL 模板。
- `app/logic/sql_agent/cache.py`：SQL 结构缓存。
- `app/logic/sql_agent/result_mapper.py`：SQL 查询结果转 DTO。
- `app/logic/services.py`：业务服务层，根据配置决定是否使用 LLM SQL，以及失败时回退确定性查询。

整体流程：

```text
用户问题
  ↓
Agent 选择销售工具
  ↓
SalesTools 参数校验、日期解析、区域/销售员名称解析
  ↓
SalesQueryService
  ↓
_maybe_llm_sql 判断是否启用 LLM SQL
  ↓
LlmSqlQueryService 构造 SqlTaskSpec
  ↓
优先匹配 SQL 模板
  ↓ 未命中
读取 SQL 结构缓存
  ↓ 未命中
LLM 生成 SQL JSON
  ↓
SQL Validator 校验
  ↓
PermissionPolicyInjector 注入权限条件
  ↓
再次校验
  ↓
SqlExecutor 参数化执行
  ↓
ResultMapper 转业务 DTO
  ↓
SalesTools 格式化成自然语言或图表 artifact
```

---

## 2. 面试一句话概括

> 这个项目的 Text-to-SQL 不是直接把用户原始问题交给模型生成 SQL，而是先由 Agent 选择具体业务工具，工具层把自然语言请求转成结构化的 `SqlTaskSpec`，再由模板、缓存或 LLM 生成候选 SQL。生成后的 SQL 会经过白名单、只读、参数化、业务口径、返回列契约、权限注入、执行超时和行数限制等多层校验，失败时还可以自动修复或回退到确定性 Repository 查询。

---

## 3. 入口：从工具调用进入 Text-to-SQL

LLM 在 ReAct 节点中选择工具，比如：

- `get_sales_summary`
- `get_top_reps`
- `get_region_ranking`
- `get_top_products`
- `get_monthly_trend`
- `query_sales_data`
- `detect_sales_anomalies`

这些工具实现在 `app/logic/tools.py`。

以销售汇总为例：

```python
def get_sales_summary(self, start_date: str, end_date: str, region_name: str | None = None) -> str:
    start = parse_date(start_date)
    end = parse_date(end_date)
    region_id, region_error = self._resolve_region_id(region_name)
    total = self.service.query_total_amount(region_id, start, end)
    return f"销售额汇总...总销售额：{money(total)}"
```

这一层做了：

1. 日期解析：`parse_date`。
2. 区域名称校验：`validate_region_name`。
3. 区域名转 `region_id`。
4. 调用业务服务 `SalesQueryService`。

面试表达：

> 用户自然语言不会直接进入 SQL 生成器，而是先被 Agent 解析成某个确定性工具调用。工具入参经过日期、区域、top_n、维度等校验后，才进入 Text-to-SQL 层。这样可以把自由文本问题收敛成有限的业务查询任务。

---

## 4. SalesQueryService：是否启用 LLM SQL

位置：`app/logic/services.py`

`SalesQueryService` 中有一个关键方法：

```python
def _maybe_llm_sql(self, operation_name, operation, fallback):
    settings = self._runtime_settings()
    llm_sql = getattr(self, "llm_sql", None)
    if not getattr(settings, "llm_sql_enabled", False) or llm_sql is None:
        return fallback()
    if not self._llm_sql_allowed_for(operation_name):
        return fallback()

    if getattr(settings, "llm_sql_shadow_mode", True):
        result = fallback()
        try:
            operation(llm_sql)
        except Exception:
            runtime_metrics.record_llm_sql_fallback()
        return result

    try:
        return operation(llm_sql)
    except Exception:
        runtime_metrics.record_llm_sql_fallback()
        if getattr(settings, "llm_sql_use_fallback", True):
            return fallback()
        raise
```

这里有几个关键设计：

| 机制 | 作用 |
|---|---|
| `llm_sql_enabled` | 总开关，决定是否启用 LLM SQL。 |
| `llm_sql_allowed_operations` | 操作白名单，只允许部分查询走 LLM SQL。 |
| `llm_sql_shadow_mode` | 影子模式：真实结果仍用确定性查询，LLM SQL 只做旁路验证。 |
| `llm_sql_use_fallback` | LLM SQL 失败时是否回退到传统 Repository 查询。 |

面试表达：

> 我没有一上来就完全依赖 LLM SQL，而是在业务服务层做了灰度控制。可以通过配置决定哪些操作允许使用 LLM SQL，也支持 shadow mode，先让 LLM SQL 在旁路跑，主链路仍返回确定性查询结果。这样上线风险更低。

---

## 5. SqlTaskSpec：把自然语言收敛成结构化任务

位置：`app/logic/sql_agent/models.py`

```python
class SqlTaskSpec(BaseModel):
    tool_name: str
    task_type: str
    start_date: date | None = None
    end_date: date | None = None
    region_id: int | None = None
    rep_id: int | None = None
    product_id: int | None = None
    category: str | None = None
    top_n: int | None = None
    months: int | None = None
    dimension: str | None = None
    order_by: str | None = None
    limit: int | None = None
    scope: QueryScope = Field(default_factory=QueryScope)
    result_contract: list[str] = Field(default_factory=list)
```

`SqlTaskSpec` 包含：

- 当前工具名。
- 查询任务类型。
- 日期范围。
- 区域、销售员、产品等过滤条件。
- top_n、limit 等分页/排序参数。
- 当前用户权限范围 `scope`。
- 期望返回字段 `result_contract`。

示例：查询销售额汇总时构造：

```python
task = SqlTaskSpec(
    tool_name="get_sales_summary",
    task_type="sales_summary",
    start_date=start,
    end_date=end,
    region_id=region_id,
    rep_id=scope.rep_id if scope.role == "SALES_REP" else None,
    result_contract=["total_amount"],
)
```

面试表达：

> `SqlTaskSpec` 是 Text-to-SQL 的中间表示层。LLM 不直接理解完整业务系统，而是基于这个结构化任务生成 SQL。这能减少 prompt 不确定性，也方便后续做 result contract 校验。

---

## 6. Schema Registry：表、字段、Join 和指标口径白名单

位置：`app/logic/sql_agent/schema_registry.py`

允许访问的表只有：

```python
allowed_tables = {
    "sa_sales_order",
    "sa_sales_rep",
    "sa_sales_region",
    "sa_product",
}
```

表别名固定：

```python
table_aliases = {
    "o": "sa_sales_order",
    "s": "sa_sales_rep",
    "r": "sa_sales_region",
    "p": "sa_product",
}
```

字段也有白名单，例如订单表只允许：

```python
id, order_no, rep_id, product_id, region_id,
customer_name, quantity, unit_price, amount,
cost, profit, status, order_date, created_at
```

Schema Registry 还会提供给模型：

1. 允许访问的表。
2. 允许字段。
3. 固定 join 关系。
4. 业务指标口径。

业务口径包括：

- 销售额使用 `SUM(o.amount)`。
- 销售数量使用 `SUM(o.quantity)`。
- 销售额、排名、趋势默认只统计 `o.status = 'COMPLETED'`。
- 月份趋势使用 `DATE_FORMAT(o.order_date, '%Y-%m') AS month`。
- 日期范围必须使用 `o.order_date BETWEEN :start_date AND :end_date`。
- 明细查询必须带 `LIMIT`。

面试表达：

> Schema Registry 是安全和业务口径的第一道约束。模型只知道白名单表、白名单字段和固定 join 关系，不会暴露整个数据库 schema。同时它也告诉模型销售额、趋势、排名这些指标应该怎么计算。

---

## 7. SQL 模板优先：高频任务不用 LLM 生成

位置：`app/logic/sql_agent/template_registry.py`

项目内置了高频稳定任务模板，例如：

- `sales_summary`
- `monthly_trend`
- `refund_rates`
- `rep_ranking`
- `region_ranking`
- `product_ranking`

以销售汇总模板为例：

```sql
SELECT COALESCE(SUM(o.amount), 0) AS total_amount
FROM sa_sales_order o
WHERE o.status = 'COMPLETED'
AND o.order_date BETWEEN :start_date AND :end_date
AND (:region_id IS NULL OR o.region_id = :region_id)
```

在 `LlmSqlQueryService._generate_valid_sql()` 里，优先流程是：

```text
模板匹配
  ↓ 命中
参数合并
  ↓
权限注入
  ↓
SQL 校验
  ↓
执行
```

面试表达：

> 高频、稳定、风险高的查询优先走受控 SQL 模板，LLM 只作为补充能力。这样既保留了 Text-to-SQL 的灵活性，也避免把所有查询都交给模型自由生成。

---

## 8. SQL 结构缓存

位置：`app/logic/sql_agent/cache.py`

项目支持把已经通过校验的 SQL 结构缓存起来。

缓存 key 不是用原始用户问题，而是基于结构化任务签名：

```python
payload = {
    "tool_name": task.tool_name,
    "task_type": task.task_type,
    "scope_role": task.scope.role,
    "scope_has_region": task.scope.region_id is not None,
    "scope_has_rep": task.scope.rep_id is not None,
    "has_region": task.region_id is not None,
    "has_rep": task.rep_id is not None,
    "has_product": task.product_id is not None,
    "has_category": task.category is not None,
    "has_months": task.months is not None,
    "has_top_n": task.top_n is not None,
    "has_limit": task.limit is not None,
    "dimension": task.dimension,
    "order_by": task.order_by,
    "result_contract": task.result_contract,
}
```

然后做 SHA256。

缓存内容包括：

- SQL 结构。
- 返回字段。
- task_type。
- tool_name。
- created_at。

支持两种后端：

- memory
- redis

面试表达：

> 缓存的是 SQL 结构，不缓存具体参数值。日期、region_id、top_n 等参数仍然由应用侧重新合并进去。这样既能减少 LLM 调用，又不会把某一次请求的参数污染到下一次请求。

---

## 9. LLM SQL 生成器

位置：`app/logic/sql_agent/generator.py`

生成器负责调用 LLM，要求模型只返回 JSON：

```json
{
  "sql": "SELECT ...",
  "params": {"start_date": "YYYY-MM-DD"},
  "result_columns": ["column_a", "column_b"],
  "reason": "一句话说明选择该 SQL 的原因",
  "confidence": 0.0
}
```

系统提示词要求：

- 只能生成只读 SELECT SQL。
- 不能生成 INSERT、UPDATE、DELETE、DROP 等危险语句。
- 只能使用给定 schema 中的表和字段。
- 必须使用命名参数，例如 `:start_date`。
- 不要把参数值直接拼进 SQL。
- 除 JSON 外不要输出解释、Markdown 或代码块。

生成器做了几件事：

1. 构造 SystemMessage 和 HumanMessage。
2. 调用 LLM。
3. 提取 JSON。
4. `json.loads` 解析。
5. 使用 Pydantic 校验是否符合 `GeneratedSql` 结构。
6. 记录耗时和 token 指标。

面试表达：

> LLM 生成器只负责产出候选 SQL，不直接执行。它返回的是结构化 JSON，并用 Pydantic 校验格式。真正能不能执行，要交给后面的 Validator 和权限注入器决定。

---

## 10. 参数安全：应用侧合并参数，不信任 LLM params

位置：`app/logic/sql_agent/service.py`

关键方法：

```python
def _merge_app_params(generated: GeneratedSql, task: SqlTaskSpec) -> dict[str, Any]:
    # 参数值必须由应用侧从工具入参生成，不能信任 LLM 自带的 params。
```

这里非常重要：

> 项目不信任 LLM 返回的 `params`，而是从 `SqlTaskSpec` 重新生成参数。

例如：

```python
if task.start_date is not None:
    params["start_date"] = task.start_date
if task.end_date is not None:
    params["end_date"] = task.end_date
if task.region_id is not None:
    params["region_id"] = task.region_id
if task.top_n is not None:
    params["top_n"] = max(abs(int(task.top_n)), 1)
if task.limit is not None:
    params["limit"] = min(max(int(task.limit), 1), 50)
```

安全点：

1. 参数值来自工具层校验后的结构化参数。
2. 不使用 LLM 自带 params。
3. `top_n` 做绝对值和最小值处理。
4. `limit` 限制在 1 到 50。
5. SQL 执行时使用 SQLAlchemy 参数绑定。

面试表达：

> 这是防 SQL 注入的关键设计。LLM 只负责生成带占位符的 SQL 结构，参数值必须由应用侧从已校验的工具入参生成，执行时再走 SQLAlchemy 参数化绑定，避免把用户输入直接拼进 SQL。

---

## 11. SQL Validator：多层安全校验

位置：`app/logic/sql_agent/validator.py`

`SqlValidator.validate()` 是安全核心。

### 11.1 只允许单条只读查询

校验项：

```python
if not re.match(r"^\s*(select|with)\b", sql, re.IGNORECASE):
    errors.append("只允许 SELECT 或 WITH ... SELECT 查询")
```

只允许：

- `SELECT`
- `WITH ... SELECT`

不允许：

- `INSERT`
- `UPDATE`
- `DELETE`
- `DROP`
- `ALTER`
- `TRUNCATE`
- `CREATE`
- 等写操作或危险操作。

### 11.2 禁止分号

```python
if ";" in sql:
    errors.append("SQL 不允许包含分号")
```

目的：防止多语句注入，例如：

```sql
SELECT ...; DROP TABLE ...
```

### 11.3 禁止注释

```python
if "--" in sql or "/*" in sql or "*/" in sql or re.search(r"(^|\s)#", sql):
    errors.append("SQL 不允许包含注释")
```

目的：防止通过注释绕过后续条件，例如：

```sql
WHERE id = :id -- AND role = 'xxx'
```

### 11.4 禁止 SELECT *

```python
if re.search(r"\bselect\s+\*", sql, re.IGNORECASE) or re.search(r",\s*\*", sql):
    errors.append("不允许 SELECT *")
```

目的：

- 避免泄露多余字段。
- 强制返回列契约明确。
- 降低无意暴露敏感字段的风险。

### 11.5 禁止系统库

```python
_system_schemas = ("mysql.", "information_schema.", "performance_schema.", "sys.")
```

不允许查询：

- `mysql`
- `information_schema`
- `performance_schema`
- `sys`

目的：防止探测数据库元数据。

### 11.6 危险关键词黑名单

```python
_dangerous_keywords = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "REPLACE", "GRANT", "REVOKE", "CALL", "EXEC",
    "LOAD", "OUTFILE", "INFILE", "LOCK", "UNLOCK", "SET",
    "SHOW", "DESCRIBE",
)
```

这些关键词出现在 SQL 中都会失败。

### 11.7 表白名单

Validator 会从 `FROM` 和 `JOIN` 提取表名：

```python
tables = self._extract_tables(sql)
unauthorized = sorted(tables - self.schema.allowed_tables)
if unauthorized:
    errors.append("SQL 使用了未授权表：" + ", ".join(unauthorized))
```

只允许查询：

- `sa_sales_order`
- `sa_sales_rep`
- `sa_sales_region`
- `sa_product`

比如 `sa_chat_memory` 不允许查询。

### 11.8 字段白名单

Validator 会检查别名字段：

```python
for alias, column in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b", sql):
    if alias in self.schema.table_aliases and not self.schema.allows_column(alias, column):
        errors.append(f"未授权字段：{alias}.{column}")
```

也就是说：

- `o.amount` 必须在订单表字段白名单里。
- `s.name` 必须在销售员表字段白名单里。
- 非白名单字段直接拒绝。

### 11.9 业务口径校验

销售指标类查询必须过滤完成订单：

```python
if task.task_type in self.schema.sales_metric_tasks:
    has_completed_filter = bool(re.search(
        r"o\.status\s*=\s*['\"]?completed['\"]?", sql, re.IGNORECASE,
    ))
    if not has_completed_filter:
        errors.append("销售指标查询必须过滤 o.status = 'COMPLETED'")
```

订单明细查询则不能默认过滤 COMPLETED：

```python
if task.task_type in self.schema.detail_tasks:
    if re.search(r"o\.status\s*=\s*['\"]?completed['\"]?", lower, re.IGNORECASE):
        errors.append("订单明细查询不允许默认过滤 COMPLETED，必须保留 REFUNDED/CANCELLED 等状态")
```

面试表达：

> Validator 不只做 SQL 安全校验，还做业务口径校验。比如销售额、排名、趋势必须只统计已完成订单；但订单明细不能默认过滤已完成，因为明细查询需要保留退款、取消等状态。

### 11.10 日期范围校验

如果任务有开始和结束日期，SQL 必须使用：

```sql
o.order_date BETWEEN :start_date AND :end_date
```

代码校验：

```python
if task.start_date and task.end_date:
    if "o.order_date" not in lower or ":start_date" not in lower or ":end_date" not in lower:
        errors.append("销售查询必须使用 o.order_date 和 :start_date/:end_date")
```

### 11.11 参数过滤一致性校验

如果任务没有提供 `region_id`，SQL 不允许强制过滤 `:region_id`。

```python
if task.region_id is None:
    strict_region_filter = re.search(r"\b(?:o\.region_id|r\.id)\s*=\s*:region_id\b", lower)
    optional_region_filter = ":region_id is null" in lower or ":region_id) is null" in lower
    if strict_region_filter and not optional_region_filter:
        errors.append("任务未提供 region_id，SQL 不允许强制过滤 :region_id")
```

类似地还检查：

- `rep_id`
- `product_id`

目的：防止模型凭空加过滤条件，导致结果错误。

### 11.12 返回列契约校验

`SqlTaskSpec` 会声明 `result_contract`，比如销售汇总必须返回：

```python
["total_amount"]
```

Validator 会检查生成 SQL 的 `result_columns` 或 SQL alias 是否满足要求：

```python
missing_contract = self._has_result_contract(generated, task, sql)
if missing_contract:
    errors.append("SQL 返回列不满足 result_contract：" + ", ".join(missing_contract))
```

目的：保证后续 `result_mapper` 能稳定映射结果。

### 11.13 明细查询自动补 LIMIT

如果是订单明细查询且没有 LIMIT，会自动补：

```python
limit = min(max(int(task.limit or 20), 1), 50)
return f"{sql.rstrip()} LIMIT {limit}"
```

目的：避免明细查询一次返回过多数据。

---

## 12. 权限注入：PermissionPolicyInjector

位置：`app/logic/sql_agent/policy.py`

权限由 `QueryScope` 表示：

```python
class QueryScope(BaseModel):
    role: Literal["SALES_REP", "SALES_MANAGER", "SALES_DIRECTOR", "ANONYMOUS"]
    user_id: int | str | None = None
    region_id: int | None = None
    rep_id: int | None = None
```

当前用户转换成 scope：

```python
if current_user.role == "SALES_REP":
    scope.rep_id = current_user.rep_id
if current_user.role == "SALES_MANAGER":
    scope.region_id = current_user.region_id
```

权限注入逻辑：

### 销售员 SALES_REP

必须注入：

```sql
o.rep_id = :scope_rep_id
```

代码：

```python
if scope.role == "SALES_REP":
    scoped_params["scope_rep_id"] = scope.rep_id
    return self._append_condition(sql, "o.rep_id = :scope_rep_id"), scoped_params
```

### 销售经理 SALES_MANAGER

必须注入：

```sql
o.region_id = :scope_region_id
```

代码：

```python
if scope.role == "SALES_MANAGER":
    scoped_params["scope_region_id"] = scope.region_id
    return self._append_condition(sql, "o.region_id = :scope_region_id"), scoped_params
```

### 其他角色

例如总监或匿名，不额外注入，取决于业务定义。

重要点：

- 权限条件由应用层强制追加，不依赖模型自觉生成。
- 如果销售员或销售经理查询中没有订单表，会直接报错。
- 注入后还会再次调用 Validator 校验。

面试表达：

> 权限控制不是靠 prompt 提醒模型，而是在 SQL 生成后由 `PermissionPolicyInjector` 强制注入。销售员只能看自己的 `rep_id`，销售经理只能看自己的 `region_id`。注入之后还会再跑一次 SQL 校验，保证最终执行的是带权限边界的 SQL。

---

## 13. 生成失败后的修复机制

位置：`app/logic/sql_agent/service.py`

主流程：

```python
attempts = max(int(settings.llm_sql_repair_attempts), 0) + 1
for _ in range(attempts):
    generated = self.generator.generate(task, self.schema, errors)
    validation = self.validator.validate(generated, task)
    if not validation.ok:
        if not self._is_repairable(validation.errors):
            raise RuntimeError(...)
        errors = validation.errors
        continue
```

如果校验失败：

1. 判断是否可修复。
2. 可修复错误会把错误信息放回 prompt，让模型重新生成。
3. 不可修复错误直接失败。

不可修复错误包括：

```python
_UNREPAIRABLE_PATTERNS = (
    "危险关键词",
    "未授权表",
    "不允许查询系统库",
    "SQL 不能为空",
    "不允许包含分号",
)
```

面试表达：

> 对于业务口径或返回列不满足这类错误，可以把错误反馈给模型让它修复。但如果出现危险关键词、未授权表、系统库、分号等明显安全问题，就直接认为不可修复，不再继续让模型尝试，避免风险扩大。

---

## 14. 执行层安全：SqlExecutor

位置：`app/logic/sql_agent/executor.py`

执行器使用 SQLAlchemy 参数化执行：

```python
rows = self.db.execute(text(sql), params).mappings().all()
```

执行前设置 MySQL 查询超时：

```python
self.db.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {self.timeout_seconds * 1000}"))
```

返回时限制最大行数：

```python
return [dict(row) for row in rows[: self.max_rows]]
```

配置项：

- `llm_sql_max_rows`：最大返回行数，默认 200。
- `llm_sql_timeout_seconds`：SQL 执行超时，默认 5 秒。

面试表达：

> 执行层还有最后一道保护：SQLAlchemy 参数化执行、防注入；MySQL 设置最大执行时间、防慢查询；返回结果做最大行数限制，防止一次拉取过多数据。

---

## 15. 结果映射：Result Mapper

位置：`app/logic/sql_agent/result_mapper.py`

SQL 执行后返回的是 `list[dict]`，项目会映射成业务 DTO：

- `map_order_rows`
- `map_region_rows`
- `map_rep_rows`
- `map_product_rows`
- `map_monthly_trend_rows`

例如产品排行映射：

```python
ProductSalesDTO(
    product_id=to_int(row.get("product_id")),
    sku_code=str(row.get("sku_code") or ""),
    product_name=str(row.get("product_name") or "未知产品"),
    category=str(row.get("category") or "未知"),
    total_amount=to_decimal(row.get("total_amount")),
    total_quantity=to_int(row.get("total_quantity")),
)
```

面试表达：

> SQL 层不会直接把数据库行返回给 Agent，而是先映射成业务 DTO。这样上层工具可以复用原有格式化逻辑，LLM SQL 和传统 Repository 查询对外表现一致。

---

## 16. 审计日志与指标

位置：`app/logic/sql_agent/service.py`

项目会记录结构化审计日志：

```python
payload = {
    "event": "llm_sql_audit",
    "tool_name": task.tool_name,
    "task_type": task.task_type,
    "source": audit.source,
    "cache_hit": audit.cache_hit,
    "template_id": audit.template_id,
    "task_signature": audit.task_signature,
    "scope_role": task.scope.role,
    "scope_user_id": task.scope.user_id,
    "scope_region_id": task.scope.region_id,
    "scope_rep_id": task.scope.rep_id,
    "generation_ms": round(audit.generation_ms, 2),
    "execution_ms": round(execution_ms, 2),
    "prompt_tokens": audit.prompt_tokens,
    "completion_tokens": audit.completion_tokens,
    "total_tokens": audit.total_tokens,
    "row_count": row_count,
    "sql": sql,
    "params": params,
}
```

记录内容包括：

- 工具名。
- 任务类型。
- SQL 来源：template / cache / generator。
- 是否命中缓存。
- 权限 scope。
- 生成耗时。
- 执行耗时。
- token 数。
- 返回行数。
- 最终 SQL 和参数。

面试表达：

> LLM SQL 的可观测性很重要，所以这里有结构化审计日志和 metrics。可以追踪 SQL 是模板来的、缓存来的还是模型生成的，也能看到权限范围、执行耗时、token 成本和返回行数，方便上线后排查问题。

---

## 17. 配置项

位置：`app/core/config.py`

相关配置：

| 配置 | 作用 |
|---|---|
| `LLM_SQL_ENABLED` | 是否启用 LLM SQL。 |
| `LLM_SQL_SHADOW_MODE` | 是否开启影子模式。 |
| `LLM_SQL_MODEL` | SQL 生成模型。 |
| `LLM_SQL_TEMPERATURE` | SQL 生成温度，默认 0。 |
| `LLM_SQL_REPAIR_ATTEMPTS` | SQL 失败后的修复次数。 |
| `LLM_SQL_MAX_ROWS` | 最大返回行数。 |
| `LLM_SQL_TIMEOUT_SECONDS` | SQL 执行超时时间。 |
| `LLM_SQL_USE_FALLBACK` | 失败时是否回退确定性查询。 |
| `LLM_SQL_ALLOWED_OPERATIONS` | 允许走 LLM SQL 的操作名白名单。 |
| `LLM_SQL_CACHE_ENABLED` | 是否启用 SQL 结构缓存。 |
| `LLM_SQL_CACHE_TTL_SECONDS` | SQL 结构缓存 TTL。 |
| `LLM_SQL_CACHE_BACKEND` | 缓存后端，memory 或 redis。 |
| `LLM_SQL_PROMPT_PROFILE` | prompt 风格，compact 或 full。 |
| `LLM_SQL_TEMPLATE_MODE` | 是否优先使用受控 SQL 模板。 |
| `LLM_SQL_AUDIT_LOG_ENABLED` | 是否启用审计日志。 |

面试表达：

> 这套 Text-to-SQL 是可以灰度和回滚的。通过配置可以关闭、开启影子模式、限制操作范围、控制缓存、限制行数和超时，也可以决定失败后是否回退到确定性查询。

---

## 18. 安全防护总结

这个项目的 Text-to-SQL 安全不是单点防护，而是多层防线。

### 第一层：入口收敛

用户问题先变成工具调用，再变成结构化 `SqlTaskSpec`，不是直接把原始自然语言交给 SQL 生成器。

### 第二层：Schema 白名单

只暴露允许的表、字段和 join 关系，不暴露全库 schema。

### 第三层：模板优先

高频稳定查询优先使用受控 SQL 模板，减少 LLM 自由生成。

### 第四层：参数不信任 LLM

LLM 只生成 SQL 结构，参数值由应用侧从工具入参生成。

### 第五层：参数化执行

使用 SQLAlchemy `text(sql), params` 执行，避免字符串拼接注入。

### 第六层：SQL Validator

校验：

- 只允许 SELECT / WITH。
- 禁止分号。
- 禁止注释。
- 禁止危险关键词。
- 禁止系统库。
- 禁止 SELECT *。
- 表白名单。
- 字段白名单。
- 日期范围必须正确。
- 业务口径必须正确。
- 返回列必须满足契约。
- 明细查询必须 LIMIT。

### 第七层：权限强制注入

销售员追加 `o.rep_id = :scope_rep_id`。

销售经理追加 `o.region_id = :scope_region_id`。

权限注入后再次校验。

### 第八层：执行限制

- SQL 执行超时。
- 最大返回行数。
- 查询失败回退传统查询。

### 第九层：审计与监控

记录最终 SQL、参数、权限范围、耗时、token、行数和 SQL 来源。

---

## 19. 面试可直接背的完整回答

> 这个项目的 Text-to-SQL 不是直接把用户问题交给大模型生成 SQL，而是做了分层设计。用户自然语言先由 Agent 转成具体工具调用，比如销售额汇总、产品排行、月度趋势等。工具层会先解析日期、区域、销售员、top_n 等参数，然后业务服务层把这些参数封装成结构化的 `SqlTaskSpec`。
>
> SQL 生成时会优先匹配受控 SQL 模板，比如销售汇总、月度趋势、销售员排行这些高频任务都有模板。如果模板没命中，再看 SQL 结构缓存。如果缓存也没有，才调用 LLM 生成 SQL JSON。LLM 返回的是 `GeneratedSql`，包括 SQL、result_columns、reason 和 confidence，但它只是候选 SQL，不能直接执行。
>
> 安全上做了多层防护。第一，Schema Registry 只暴露允许访问的四张销售业务表和字段，不暴露全库结构。第二，LLM 必须生成命名参数 SQL，不能把参数值拼进去。第三，应用侧完全不信任 LLM 返回的 params，而是从 `SqlTaskSpec` 重新合并参数。第四，Validator 会检查 SQL 只能是 SELECT 或 WITH，不能有分号、注释、危险关键词、系统库、SELECT *，表和字段必须在白名单内。第五，还会校验业务口径，比如销售额、排名、趋势必须过滤 `o.status = 'COMPLETED'`，订单明细不能默认过滤 completed，并且返回列必须满足 result_contract。第六，权限不是靠 prompt，而是由 `PermissionPolicyInjector` 强制注入，比如销售员只能看自己的 `rep_id`，销售经理只能看自己的 `region_id`，注入后还会再次校验。
>
> 执行层使用 SQLAlchemy 参数化执行，并设置最大执行时间和最大返回行数。如果 LLM SQL 失败，业务层可以回退到确定性 Repository 查询。上线时还支持 shadow mode，主链路仍然用传统查询，LLM SQL 只旁路运行并记录审计日志。整体上，这套方案兼顾了 Text-to-SQL 的灵活性和生产环境的安全性、可控性。

---

## 20. 面试官可能追问

### Q1：为什么不直接让 LLM 根据用户问题生成 SQL？

答：

> 因为直接从自然语言到 SQL 风险比较高，用户输入太自由，模型可能生成越权 SQL 或错误口径。这个项目先把用户问题收敛成有限的业务工具，再构造成结构化 `SqlTaskSpec`，这样 SQL 生成的空间更小，后续也更容易校验。

### Q2：怎么防 SQL 注入？

答：

> 主要有三点。第一，LLM 只能生成带命名占位符的 SQL，不能拼参数值。第二，项目不信任 LLM 返回的 params，而是由应用侧根据工具入参重新合并参数。第三，执行时使用 SQLAlchemy 参数化绑定。另外 Validator 还禁止分号和注释，防止多语句或注释绕过。

### Q3：怎么防止模型查敏感表？

答：

> Schema Registry 只暴露四张允许表，Validator 会从 FROM 和 JOIN 中提取表名，检查是否在 allowed_tables 内。像 `sa_chat_memory`、系统库 `information_schema`、`mysql` 等都不允许查询。

### Q4：怎么保证业务口径正确？

答：

> 一方面 prompt 里给了业务指标口径，比如销售额用 `SUM(o.amount)`，趋势按月份分组；另一方面 Validator 做硬校验，比如销售额、排名、趋势必须过滤 `o.status = 'COMPLETED'`，日期范围必须使用 `o.order_date BETWEEN :start_date AND :end_date`，返回列必须满足 `result_contract`。

### Q5：权限控制靠什么？

答：

> 权限不依赖 prompt，而是在 SQL 生成后由 `PermissionPolicyInjector` 强制注入。销售员追加 `o.rep_id = :scope_rep_id`，销售经理追加 `o.region_id = :scope_region_id`。注入后再次 Validator 校验，最终执行的是带权限条件的 SQL。

### Q6：LLM 生成错了怎么办？

答：

> 如果是可修复错误，比如返回列不满足、业务口径遗漏，会把错误反馈给 LLM 重新生成，重试次数由 `LLM_SQL_REPAIR_ATTEMPTS` 控制。如果是危险关键词、未授权表、系统库、分号等不可修复安全错误，就直接失败。业务层还可以根据配置回退到传统 Repository 查询。

### Q7：为什么要有 SQL 模板和缓存？

答：

> 高频稳定查询优先使用模板，可以减少 LLM 不确定性和成本。缓存则保存已经校验通过的 SQL 结构，后续相同类型任务不用再调模型。缓存的是 SQL 结构，不缓存参数值，参数每次由应用侧重新合并。

### Q8：如何上线降低风险？

答：

> 有 shadow mode。开启后，主链路仍返回传统 Repository 查询结果，LLM SQL 只在旁路执行并记录日志。等稳定后再关闭 shadow mode 使用 LLM SQL 结果。并且可以通过 allowed operations 控制只让部分查询走 LLM SQL。

### Q9：怎么避免慢查询或大结果集？

答：

> 执行层会设置 MySQL `MAX_EXECUTION_TIME`，并用 `llm_sql_max_rows` 限制最大返回行数。明细查询如果没有 LIMIT，Validator 会自动补 LIMIT，且 limit 最大限制在 50。

### Q10：SQL 结果怎么和原系统兼容？

答：

> SQL 执行返回的是 dict 行数据，之后会经过 `result_mapper` 转成和传统 Repository 一样的 DTO，比如 `ProductSalesDTO`、`RegionSalesDTO`、`MonthlyTrendDTO`。所以上层工具不关心数据来自 LLM SQL 还是传统查询。
