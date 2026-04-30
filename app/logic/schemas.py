"""
数据模型定义模块

该模块集中定义了应用中使用的各种数据模型，包括：
- 接口请求和响应模型
- 内部数据传输对象 (DTO)
- 用户信息模型
- 图表相关模型

所有模型均使用 Pydantic V2 语法定义，提供类型提示和数据验证功能。
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """
    用户信息模型
    
    用于表示系统用户的基本信息，包括用户ID、用户名、角色等。
    """
    user_id: int
    """用户ID"""
    username: str
    """用户名"""
    role: str
    """用户角色"""
    region_id: int | None = None
    """区域ID（可选）"""
    rep_id: int | None = None
    """销售代表ID（可选）"""


class ChatRequest(BaseModel):
    """
    聊天请求模型
    
    用于接收前端发送的聊天请求，包含会话ID和消息内容。
    """
    session_id: str = Field(alias="sessionId", min_length=1, max_length=100)
    """会话ID"""
    message: str = Field(min_length=1, max_length=2000)
    """消息内容"""

    model_config = {"populate_by_name": True}


class ChatArtifact(BaseModel):
    """
    聊天附件模型
    
    用于表示聊天响应中的附件，如图表、文件等。
    """
    kind: str
    """附件类型"""
    slot: str = "main_chart"
    """附件插槽"""
    title: str | None = None
    """附件标题"""
    option: dict | None = None
    """附件选项（如ECharts配置）"""


class ChartToolResponse(BaseModel):
    """
    图表工具响应模型
    
    用于表示图表工具执行后的响应结果。
    """
    message: str
    """响应消息"""
    artifact: ChatArtifact | None = None
    """图表附件"""


class ChatResponse(BaseModel):
    """
    聊天响应模型
    
    用于返回聊天请求的处理结果，包含回复内容和附件。
    """
    session_id: str = Field(alias="sessionId")
    """会话ID"""
    reply: str
    """回复内容"""
    artifacts: list[ChatArtifact] = Field(default_factory=list)
    """附件列表"""
    duration_ms: int = Field(alias="durationMs")
    """处理时间（毫秒）"""

    model_config = {"populate_by_name": True}


class LoginRequest(BaseModel):
    """
    登录请求模型
    
    用于接收用户登录请求，包含销售代表ID。
    """
    rep_id: int = Field(alias="repId")
    """销售代表ID"""

    model_config = {"populate_by_name": True}


class QueryRequest(BaseModel):
    """
    查询请求模型
    
    用于接收销售数据查询请求，包含时间范围、区域、销售代表等筛选条件。
    """
    start_date: str = Field(alias="startDate")
    """开始日期"""
    end_date: str = Field(alias="endDate")
    """结束日期"""
    region_name: str | None = Field(default=None, alias="regionName")
    """区域名称（可选）"""
    rep_name: str | None = Field(default=None, alias="repName")
    """销售代表名称（可选）"""
    limit: int = 12
    """返回记录数限制"""

    model_config = {"populate_by_name": True}


class RankRequest(BaseModel):
    """
    排名请求模型
    
    用于接收销售排名查询请求，包含时间范围、区域等筛选条件。
    """
    start_date: str = Field(alias="startDate")
    """开始日期"""
    end_date: str = Field(alias="endDate")
    """结束日期"""
    region_name: str | None = Field(default=None, alias="regionName")
    """区域名称（可选）"""
    top_n: int = Field(alias="topN")
    """返回前N名"""

    model_config = {"populate_by_name": True}


class RangeRequest(BaseModel):
    """
    范围请求模型
    
    用于接收时间范围请求，包含开始日期和结束日期。
    """
    start_date: str = Field(alias="startDate")
    """开始日期"""
    end_date: str = Field(alias="endDate")
    """结束日期"""

    model_config = {"populate_by_name": True}


class ProductRankRequest(BaseModel):
    """
    产品排名请求模型
    
    用于接收产品销售排名查询请求，包含时间范围等筛选条件。
    """
    start_date: str = Field(alias="startDate")
    """开始日期"""
    end_date: str = Field(alias="endDate")
    """结束日期"""
    top_n: int = Field(alias="topN")
    """返回前N名"""

    model_config = {"populate_by_name": True}


class MomRequest(BaseModel):
    """
    环比请求模型
    
    用于接收环比分析请求，包含当前和 previous 时间范围。
    """
    current_start: str = Field(alias="currentStart")
    """当前开始日期"""
    current_end: str = Field(alias="currentEnd")
    """当前结束日期"""
    prev_start: str | None = Field(default=None, alias="prevStart")
    """Previous开始日期（可选）"""
    prev_end: str | None = Field(default=None, alias="prevEnd")
    """Previous结束日期（可选）"""
    region_name: str | None = Field(default=None, alias="regionName")
    """区域名称（可选）"""

    model_config = {"populate_by_name": True}


class YoyRequest(BaseModel):
    """
    同比请求模型
    
    用于接收同比分析请求，包含时间范围和区域等筛选条件。
    """
    start_date: str = Field(alias="startDate")
    """开始日期"""
    end_date: str = Field(alias="endDate")
    """结束日期"""
    region_name: str | None = Field(default=None, alias="regionName")
    """区域名称（可选）"""

    model_config = {"populate_by_name": True}


class TrendRequest(BaseModel):
    """
    趋势请求模型
    
    用于接收趋势分析请求，包含月份数和区域等筛选条件。
    """
    months: int
    """月份数"""
    region_name: str | None = Field(default=None, alias="regionName")
    """区域名称（可选）"""

    model_config = {"populate_by_name": True}


class LineChartRequest(TrendRequest):
    """
    折线图请求模型
    
    用于接收折线图生成请求，继承自趋势请求模型。
    """
    title: str | None = None
    """图表标题"""


class BarPieChartRequest(BaseModel):
    """
    柱状图/饼图请求模型
    
    用于接收柱状图或饼图生成请求，包含维度、时间范围等参数。
    """
    dimension: str
    """维度（如region、product等）"""
    start_date: str = Field(alias="startDate")
    """开始日期"""
    end_date: str = Field(alias="endDate")
    """结束日期"""
    title: str | None = None
    """图表标题"""
    top_n: int = Field(default=10, alias="topN")
    """返回前N名"""

    model_config = {"populate_by_name": True}


class MonthlyTrendDTO(BaseModel):
    """
    月度趋势数据传输对象
    
    用于表示月度销售趋势数据。
    """
    month: str
    """月份"""
    total_amount: Decimal
    """总销售额"""
    order_count: int
    """订单数量"""


class RepSalesDTO(BaseModel):
    """
    销售代表销售数据传输对象
    
    用于表示销售代表的销售数据。
    """
    rep_id: int
    """销售代表ID"""
    rep_name: str
    """销售代表名称"""
    region_id: int
    """区域ID"""
    region_name: str
    """区域名称"""
    total_amount: Decimal
    """总销售额"""
    order_count: int = 0
    """订单数量"""


class RegionSalesDTO(BaseModel):
    """
    区域销售数据传输对象
    
    用于表示区域的销售数据。
    """
    region_id: int
    """区域ID"""
    region_name: str
    """区域名称"""
    total_amount: Decimal
    """总销售额"""
    order_count: int = 0
    """订单数量"""
    total_profit: Decimal = Decimal("0")
    """总利润"""


class ProductSalesDTO(BaseModel):
    """
    产品销售数据传输对象
    
    用于表示产品的销售数据。
    """
    product_id: int
    """产品ID"""
    sku_code: str
    """SKU编码"""
    product_name: str
    """产品名称"""
    category: str
    """产品类别"""
    total_amount: Decimal
    """总销售额"""
    total_quantity: int
    """总数量"""


class AnomalyDTO(BaseModel):
    """
    异常数据传输对象
    
    用于表示销售数据中的异常情况。
    """
    type: str
    """异常类型"""
    severity: str
    """严重程度"""
    subject: str
    """异常主题"""
    description: str
    """异常描述"""
    suggestion: str
    """建议措施"""
