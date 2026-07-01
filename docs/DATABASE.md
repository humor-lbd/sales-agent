<!--
文件作用：
- 解释数据库表结构、字段用途和数据访问边界。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

# 数据库说明

Python 版默认复用 Java 项目的 MySQL 表结构，不额外引入不兼容字段。当前 ORM 与数据库表的映射如下。

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 表清单

### `sa_sales_region`

用途：

- 保存销售大区
- 支持大区排行、订单过滤、权限限制

关键字段：

- `id`
- `name`
- `parent_region_id`
- `created_at`

### `sa_sales_rep`

用途：

- 保存销售员与管理角色信息
- 支持登录、权限判断、销售员排行

关键字段：

- `id`
- `name`
- `region_id`
- `role`
- `email`
- `created_at`

角色约定：

- `SALES_REP`
- `SALES_MANAGER`
- `SALES_DIRECTOR`

### `sa_product`

用途：

- 保存产品信息
- 支持产品排行、品类图表、异常检测

关键字段：

- `id`
- `sku_code`
- `name`
- `category`
- `unit_price`
- `cost`
- `status`
- `created_at`

### `sa_sales_order`

用途：

- 保存订单明细
- 是所有汇总、趋势、异常检测的主数据表

关键字段：

- `id`
- `order_no`
- `rep_id`
- `product_id`
- `region_id`
- `customer_name`
- `quantity`
- `unit_price`
- `amount`
- `cost`
- `profit`
- `status`
- `order_date`
- `created_at`

状态约定：

- `COMPLETED`
- `REFUNDED`
- `CANCELLED`

### `sa_chat_memory`

用途：

- 按 `session_id` 保存 Agent 会话消息
- 支持同步聊天和流式聊天共用上下文

关键字段：

- `id`
- `session_id`
- `messages`
- `updated_at`

兼容策略：

- Python 版继续把整轮消息存为 JSON 字符串
- 优先保证 Python 自身稳定读写
- 如需和 Java 共用同一 `sessionId`，应先确认消息 JSON 格式兼容

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## ORM 与字段类型

当前 ORM 设计约束：

- 金额统一使用 `Decimal`
- 日期字段使用 `date`
- 时间字段使用 `datetime`
- 主键沿用原表 `BigInteger`

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 初始化策略

推荐继续复用仓库原有的：

- `src/main/resources/db/schema.sql`
- `src/main/resources/db/data.sql`

这样做的好处：

- Java / Python 使用同一批演示数据
- 回归测试时更容易做结果比对
- 不必在迁移首版就引入 Alembic

补充业务场景数据：

- `app/db/sql/scenario_coverage.sql`：在已有 seed 基础上追加 `ORD-SC-*` 订单，覆盖本月汇总、排行、趋势、同比、环比、图表、异常检测和权限范围。
- `scripts/load_scenario_data.py`：加载并校验补充数据，适合演示、联调和回归前执行。
- `docs/SCENARIO_DATA.md`：说明每类业务场景对应的数据来源和验证问句。
- `app/db/sql/jiusen_scenario_coverage.sql`：基于山西玖森百立科技服务有限公司“咪婴伴侣”业务追加 `ORD-JS-*` 订单、`SKU-JS-*` 产品和 9100 段销售/服务人员。
- `scripts/load_jiusen_scenario_data.py`：加载并校验玖森百立业务场景数据。
- `docs/JIUSEN_SCENARIO_DATA.md`：说明母婴 O2O、产后修复、陪诊、母婴商城、直播电商等场景如何覆盖项目工具。

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 数据使用边界

迁移后的 Python 版仍然遵循：

- 只查询，不直接修改业务数据
- LLM 不直接接触数据库
- 统一通过 Tool -> Service -> Repository 访问数据

<!-- 下方章节继续展开当前文档的一个核心主题，阅读时建议结合实际代码一起看。 -->
## 建议索引检查

为了保证测试和灰度期间查询稳定，建议确认这些字段上存在索引或可接受的查询计划：

- `sa_sales_order.order_date`
- `sa_sales_order.rep_id`
- `sa_sales_order.region_id`
- `sa_sales_order.product_id`
- `sa_sales_order.status`
- `sa_chat_memory.session_id`
