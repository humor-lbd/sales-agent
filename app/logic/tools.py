"""
销售工具模块

该模块把业务能力包装成确定性工具，供Graph执行节点直接调用。
主要功能包括：
- 销售数据查询和分析
- 图表生成（折线图、柱状图、饼图）
- 异常检测
- 数据验证和格式化
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.core.config import get_settings
from app.logic.schemas import AnomalyDTO
from app.logic.services import SalesQueryService
from app.logic.validators import clamp_months, parse_date, validate_dimension, validate_region_name, validate_top_n


def money(value: Decimal) -> str:
    """
    格式化金额为人民币格式
    
    Args:
        value: 金额
    
    Returns:
        格式化后的金额字符串（如¥1,000）
    """
    return f"¥{value:,.0f}"


class SalesTools:
    """
    销售工具类
    
    提供各种销售数据查询、分析和图表生成功能。
    """
    def __init__(self, service: SalesQueryService) -> None:
        """
        初始化销售工具
        
        Args:
            service: 销售查询服务实例
        """
        self.service = service
        self.settings = get_settings()

    def _resolve_region_id(self, region_name: str | None, *, detail: bool = False) -> tuple[int | None, str | None]:
        """
        作用：统一完成大区名称校验和 ID 解析。
        参数：region_name、detail。
        返回：region_id、错误提示。
        """
        try:
            validate_region_name(region_name)
        except ValueError as exc:
            return None, str(exc)
        region_id = self.service.get_region_id_by_name(region_name)
        if region_name and region_id is None:
            message = f"未找到大区：{region_name}"
            if detail:
                message += "，请确认大区名称是否正确（华东区/华南区/华北区/西南区）"
            return None, message
        return region_id, None

    @staticmethod
    def _normalize_months(months: int) -> int:
        """
        作用：统一限制趋势查询月份范围。
        参数：months。
        返回：归一化后的月份数。
        """
        return clamp_months(months, minimum=1, maximum=24)

    @staticmethod
    def _chart_response(message: str, option: dict | None = None, title: str | None = None) -> dict:
        """
        构建图表响应
        
        Args:
            message: 响应消息
            option: ECharts配置选项
            title: 图表标题
        
        Returns:
            包含消息和附件的响应字典
        """
        artifact = None
        if option is not None:
            artifact = {
                "kind": "echarts",
                "slot": "main_chart",
                "title": title,
                "option": option,
            }
        return {"message": message, "artifact": artifact}

    @staticmethod
    def _infer_chart_dimension(dimension: str, title: str | None = None) -> str:
        """
        根据标题修正图表维度
        
        Args:
            dimension: 维度名称
            title: 图表标题
        
        Returns:
            修正后的维度
        """
        resolved = validate_dimension(dimension)
        if not title:
            return resolved

        text = title.lower()
        if ("top" in text and "产品" in title) or "畅销产品" in title or "sku" in text:
            return "product"
        if "销售员" in title or "业务员" in title:
            return "rep"
        if "品类" in title or "类别" in title or "类目" in title:
            return "category"
        if "大区" in title or "区域" in title:
            return "region"
        return resolved

    @staticmethod
    def _category_pie_data(products) -> list[dict]:
        """
        把产品销售数据聚合为品类占比数据
        
        Args:
            products: 产品销售数据列表
        
        Returns:
            ECharts饼图数据
        """
        category_total: dict[str, Decimal] = {}
        for product in products:
            category_total[product.category] = category_total.get(product.category, Decimal("0")) + product.total_amount
        return [{"name": name, "value": int(total)} for name, total in category_total.items()]

    @staticmethod
    def _pie_message(data: list[dict]) -> str:
        """
        生成饼图数据的文本说明
        
        Args:
            data: 饼图数据
        
        Returns:
            包含饼图数据说明的文本
        """
        total = sum(Decimal(str(item.get("value", 0))) for item in data)
        lines = ["已生成饼图。", "图表数据："]
        for item in data:
            value = Decimal(str(item.get("value", 0)))
            ratio = (value / total * Decimal("100")) if total else Decimal("0")
            sku = f" [{item['sku']}]" if item.get("sku") else ""
            lines.append(f"- {item['name']}{sku}：{money(value)}，占比 {ratio:.1f}%")
        return "\n".join(lines)

    def query_orders(self, start_date: str, end_date: str, region_name: str | None = None, rep_name: str | None = None, limit: int = 20) -> str:
        """
        查询销售订单
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            region_name: 区域名称（可选）
            rep_name: 销售代表名称（可选）
            limit: 返回记录数限制
        
        Returns:
            订单查询结果文本
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        region_id, region_error = self._resolve_region_id(region_name, detail=True)
        rep_id = self.service.get_rep_id_by_name(rep_name)
        if region_error:
            return region_error
        if rep_name and rep_id is None:
            return f"未找到销售员：{rep_name}，请确认姓名是否正确"

        orders = self.service.query_orders(rep_id, region_id, start, end)
        if not orders:
            target = f"{region_name} " if region_name else ""
            return f"在 {start_date} 至 {end_date} 期间，{target}暂无订单数据"

        show_count = min(limit, 50, len(orders))
        lines = [
            f"订单查询结果（{start_date} 至 {end_date}{'，' + region_name if region_name else ''}）：",
            f"共找到 {len(orders)} 条订单" + (f"，以下显示前 {show_count} 条" if show_count < len(orders) else ""),
            "",
        ]
        for order in orders[:show_count]:
            lines.append(
                f"- 订单号：{order.order_no} | 日期：{order.order_date} | 销售员：{self.service.get_rep_name(order.rep_id)} | "
                f"客户：{order.customer_name} | 金额：{money(order.amount)} | 状态：{self.translate_status(order.status)}"
            )
        completed = [order for order in orders[:show_count] if order.status == "COMPLETED"]
        completed_total = sum((order.amount for order in completed), Decimal("0"))
        lines.append("")
        lines.append(f"小计：完成订单 {len(completed)} 笔，金额合计 {money(completed_total)}")
        return "\n".join(lines)

    def get_top_reps(self, start_date: str, end_date: str, region_name: str | None = None, top_n: int = 5) -> str:
        """
        获取销售代表排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            region_name: 区域名称（可选）
            top_n: 返回前N名
        
        Returns:
            销售代表排名文本
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        reps = self.service.query_rep_ranking(start, end, validate_top_n(top_n))
        if region_name:
            region_id, region_error = self._resolve_region_id(region_name)
            if region_error:
                return region_error
            reps = [rep for rep in reps if rep.region_id == region_id]
        if not reps:
            return "该时段内暂无销售数据"
        lines = [f"销售员业绩排名（{start_date} 至 {end_date}{'，' + region_name if region_name else '，全公司'}）：", ""]
        for idx, rep in enumerate(reps, start=1):
            lines.append(f"第 {idx} 名：{rep.rep_name}（{rep.region_name}）  销售额：{money(rep.total_amount)}")
        return "\n".join(lines)

    def get_region_ranking(self, start_date: str, end_date: str) -> str:
        """
        获取区域销售排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            区域销售排名文本
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        regions = self.service.query_region_ranking(start, end)
        if not regions:
            return "该时段内暂无数据"
        grand_total = sum((region.total_amount for region in regions), Decimal("0"))
        lines = [f"大区业绩排名（{start_date} 至 {end_date}）：", ""]
        for idx, region in enumerate(regions, start=1):
            ratio = (region.total_amount / grand_total * Decimal("100")) if grand_total else Decimal("0")
            lines.append(f"第 {idx} 名：{region.region_name}  销售额：{money(region.total_amount)}  占比：{ratio:.1f}%")
        lines.append("")
        lines.append(f"全公司合计：{money(grand_total)}")
        return "\n".join(lines)

    def get_top_products(self, start_date: str, end_date: str, top_n: int = 10, region_name: str | None = None) -> str:
        """
        获取产品销售排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            top_n: 返回前N名（负数表示最差）
            region_name: 区域名称（可选）
        
        Returns:
            产品销售排名文本
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        is_worst = top_n < 0
        n = validate_top_n(top_n)
        region_id, region_error = self._resolve_region_id(region_name)
        if region_error:
            return region_error
        products = self.service.query_product_ranking(start, end, 999 if is_worst else n, region_id)
        if not products:
            scope = f"{region_name}" if region_name else "该时段"
            return f"{scope}暂无产品销售数据"
        products = list(reversed(products[-n:])) if is_worst else products[:n]
        scope = f"{region_name}" if region_name else "全公司"
        lines = [f"产品销售排名{'（最差）' if is_worst else '（最佳）'}（{start_date} 至 {end_date}，{scope}）：", ""]
        for idx, product in enumerate(products, start=1):
            lines.append(
                f"第 {idx} 名：{product.product_name} [{product.sku_code}]  品类：{product.category}  "
                f"销售额：{money(product.total_amount)}  数量：{product.total_quantity} 件"
            )
        return "\n".join(lines)

    def get_sales_summary(self, start_date: str, end_date: str, region_name: str | None = None) -> str:
        """
        获取销售额汇总
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            region_name: 区域名称（可选）
        
        Returns:
            销售额汇总文本
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        region_id, region_error = self._resolve_region_id(region_name)
        if region_error:
            return region_error
        total = self.service.query_total_amount(region_id, start, end)
        scope = f"，{region_name}" if region_name else "，全公司"
        return f"销售额汇总（{start_date} 至 {end_date}{scope}）：\n总销售额：{money(total)}"

    def calc_month_over_month(self, current_start: str, current_end: str, prev_start: str | None = None, prev_end: str | None = None, region_name: str | None = None) -> str:
        """
        计算环比
        
        Args:
            current_start: 当前周期开始日期
            current_end: 当前周期结束日期
            prev_start: 对比周期开始日期（可选）
            prev_end: 对比周期结束日期（可选）
            region_name: 区域名称（可选）
        
        Returns:
            环比分析文本
        """
        c_start = parse_date(current_start)
        c_end = parse_date(current_end)
        if not prev_start:
            days = (c_end - c_start).days + 1
            p_end = c_start - timedelta(days=1)
            p_start = p_end - timedelta(days=days - 1)
        else:
            p_start = parse_date(prev_start)
            p_end = parse_date(prev_end or prev_start)
        region_id, region_error = self._resolve_region_id(region_name)
        if region_error:
            return region_error
        current = self.service.query_total_amount(region_id, c_start, c_end)
        previous = self.service.query_total_amount(region_id, p_start, p_end)
        growth = self.service.calc_growth_rate(current, previous)
        lines = [f"环比分析（{region_name if region_name else '全公司'}）：", ""]
        lines.append(f"当前周期（{c_start} 至 {c_end}）：{money(current)}")
        lines.append(f"对比周期（{p_start} 至 {p_end}）：{money(previous)}")
        if growth is None:
            lines.append("对比周期无数据，无法计算增长率")
        else:
            direction = "↑ 增长" if growth >= 0 else "↓ 下降"
            diff = abs(current - previous)
            lines.append(f"环比变化：{direction} {abs(growth):.1f}%（{'增加' if growth >= 0 else '减少'} {money(diff)}）")
        return "\n".join(lines)

    def calc_year_over_year(self, start_date: str, end_date: str, region_name: str | None = None) -> str:
        """
        计算同比
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            region_name: 区域名称（可选）
        
        Returns:
            同比分析文本
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        prev_start = start.replace(year=start.year - 1)
        prev_end = end.replace(year=end.year - 1)
        region_id, region_error = self._resolve_region_id(region_name)
        if region_error:
            return region_error
        current = self.service.query_total_amount(region_id, start, end)
        previous = self.service.query_total_amount(region_id, prev_start, prev_end)
        growth = self.service.calc_growth_rate(current, previous)
        lines = [f"同比分析（{region_name if region_name else '全公司'}）：", ""]
        lines.append(f"今年（{start} 至 {end}）：{money(current)}")
        lines.append(f"去年（{prev_start} 至 {prev_end}）：{money(previous)}")
        if growth is None:
            lines.append("去年同期无数据，无法计算同比增长率")
        else:
            lines.append(f"同比变化：{'↑ 同比增长' if growth >= 0 else '↓ 同比下降'} {abs(growth):.1f}%")
        return "\n".join(lines)

    def get_monthly_trend(self, months: int, region_name: str | None = None) -> str:
        """
        获取月度销售趋势
        
        Args:
            months: 查询月数
            region_name: 区域名称（可选）
        
        Returns:
            月度销售趋势文本
        """
        normalized_months = self._normalize_months(months)
        region_id, region_error = self._resolve_region_id(region_name)
        if region_error:
            return region_error
        trend = self.service.query_monthly_trend(region_id, normalized_months)
        if not trend:
            return "暂无趋势数据"
        lines = [f"月度销售趋势（近 {normalized_months} 个月{'，' + region_name if region_name else '，全公司'}）：", ""]
        for idx, item in enumerate(trend):
            change = ""
            if idx > 0:
                rate = self.service.calc_growth_rate(item.total_amount, trend[idx - 1].total_amount)
                if rate is not None:
                    change = f" ({'↑' if rate >= 0 else '↓'}{abs(rate):.1f}%)"
            lines.append(f"{item.month}：{money(item.total_amount)}  订单数：{item.order_count}{change}")
        if len(trend) >= 2:
            overall = self.service.calc_growth_rate(trend[-1].total_amount, trend[0].total_amount)
            if overall is not None:
                lines.append("")
                lines.append(f"整体趋势：{'上升' if overall >= 0 else '下降'} {abs(overall):.1f}%（{trend[0].month} 至 {trend[-1].month}）")
        return "\n".join(lines)

    def generate_line_chart(self, months: int, region_name: str | None = None, title: str | None = None) -> dict:
        """
        生成折线图
        
        Args:
            months: 查询月数
            region_name: 区域名称（可选）
            title: 图表标题（可选）
        
        Returns:
            包含图表配置的响应字典
        """
        normalized_months = self._normalize_months(months)
        region_id, region_error = self._resolve_region_id(region_name)
        if region_error:
            return self._chart_response(region_error)
        data = self.service.query_monthly_trend(region_id, normalized_months)
        if not data:
            return self._chart_response("暂无数据，无法生成图表")
        chart_title = title or "销售趋势"
        option = {
            "title": {"text": chart_title},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": [item.month for item in data]},
            "yAxis": {"type": "value", "name": "销售额（元）"},
            "series": [
                {
                    "type": "line",
                    "data": [int(item.total_amount) for item in data],
                    "smooth": True,
                    "name": "销售额",
                    "itemStyle": {"color": "#5470c6"},
                }
            ],
        }
        return self._chart_response("已生成折线图。", option, chart_title)

    def generate_bar_chart(self, dimension: str, start_date: str, end_date: str, title: str | None = None, top_n: int = 10) -> dict:
        """
        生成柱状图
        
        Args:
            dimension: 维度（region/rep/category/product）
            start_date: 开始日期
            end_date: 结束日期
            title: 图表标题（可选）
            top_n: 返回前N名
        
        Returns:
            包含图表配置的响应字典
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        try:
            dimension = self._infer_chart_dimension(dimension, title)
        except ValueError as exc:
            return self._chart_response(str(exc))
        if dimension == "region":
            rows = self.service.query_region_ranking(start, end)
            names = [row.region_name for row in rows]
            values = [int(row.total_amount) for row in rows]
        elif dimension == "rep":
            rows = self.service.query_rep_ranking(start, end, validate_top_n(top_n))
            names = [row.rep_name for row in rows]
            values = [int(row.total_amount) for row in rows]
        elif dimension == "product":
            products = self.service.query_product_ranking(start, end, validate_top_n(top_n))
            names = [product.product_name for product in products]
            values = [int(product.total_amount) for product in products]
        else:
            products = self.service.query_product_ranking(start, end, 100)
            category_data = self._category_pie_data(products)
            names = [item["name"] for item in category_data]
            values = [item["value"] for item in category_data]
        if not names:
            return self._chart_response("暂无数据，无法生成图表")
        chart_title = title or "销售对比"
        option = {
            "title": {"text": chart_title},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": names, "axisLabel": {"rotate": 30}},
            "yAxis": {"type": "value", "name": "销售额（元）"},
            "series": [{"type": "bar", "data": values, "itemStyle": {"color": "#91cc75"}}],
        }
        return self._chart_response("已生成柱状图。", option, chart_title)

    def generate_pie_chart(self, dimension: str, start_date: str, end_date: str, title: str | None = None, top_n: int = 10) -> dict:
        """
        生成饼图
        
        Args:
            dimension: 维度（region/rep/category/product）
            start_date: 开始日期
            end_date: 结束日期
            title: 图表标题（可选）
            top_n: 返回前N名
        
        Returns:
            包含图表配置的响应字典
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        try:
            dimension = self._infer_chart_dimension(dimension, title)
        except ValueError as exc:
            return self._chart_response(str(exc))
        if dimension == "region":
            rows = self.service.query_region_ranking(start, end)
            data = [{"name": row.region_name, "value": int(row.total_amount)} for row in rows]
        elif dimension == "rep":
            rows = self.service.query_rep_ranking(start, end, validate_top_n(top_n))
            data = [{"name": row.rep_name, "value": int(row.total_amount)} for row in rows]
        elif dimension == "product":
            products = self.service.query_product_ranking(start, end, validate_top_n(top_n))
            data = [
                {
                    "name": product.product_name,
                    "value": int(product.total_amount),
                    "sku": product.sku_code,
                    "category": product.category,
                    "quantity": product.total_quantity,
                }
                for product in products
            ]
        else:
            products = self.service.query_product_ranking(start, end, 100)
            data = self._category_pie_data(products)
        if not data:
            return self._chart_response("暂无数据，无法生成图表")
        default_titles = {
            "region": "大区销售额占比",
            "rep": "销售员销售额占比",
            "category": "品类销售额占比",
            "product": f"最畅销产品Top{validate_top_n(top_n)}销售额占比",
        }
        chart_title = title or default_titles.get(dimension, "销售占比")
        option = {
            "title": {"text": chart_title, "left": "center"},
            "tooltip": {"trigger": "item", "formatter": "{b}: ¥{c} ({d}%)"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [
                {
                    "type": "pie",
                    "radius": "55%",
                    "data": data,
                    "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0,0,0,0.5)"}},
                }
            ],
        }
        return self._chart_response(self._pie_message(data), option, chart_title)

    def detect_all_anomalies(self) -> str:
        """
        检测所有异常
        
        Returns:
            异常检测结果文本
        """
        anomalies: list[AnomalyDTO] = []
        anomalies.extend(self._detect_region_drop())
        anomalies.extend(self._detect_zero_sale_products())
        anomalies.extend(self._detect_high_refund_reps())
        anomalies.extend(self._detect_rep_performance_drop())
        if not anomalies:
            return "当前数据未检测到明显异常，销售数据运行正常。"
        severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        anomalies.sort(key=lambda item: severity_rank.get(item.severity, 9))
        lines = [f"异常检测结果：共发现 {len(anomalies)} 个异常", ""]
        labels = {"HIGH": "高优先级", "MEDIUM": "中优先级", "LOW": "低优先级"}
        for anomaly in anomalies:
            lines.append(f"{labels.get(anomaly.severity, '低优先级')}｜{anomaly.type}")
            lines.append(f"  对象：{anomaly.subject}")
            lines.append(f"  描述：{anomaly.description}")
            lines.append(f"  建议：{anomaly.suggestion}")
            lines.append("")
        return "\n".join(lines).strip()

    def _detect_region_drop(self) -> list[AnomalyDTO]:
        """
        检测大区订单量骤降
        
        Returns:
            异常列表
        """
        today = date.today()
        recent_start = today - timedelta(weeks=2)
        base_start = today - timedelta(weeks=6)
        base_end = today - timedelta(weeks=2, days=1)
        result = []
        for region in self.service.regions():
            recent_count = self.service.query_order_count(region.id, recent_start, today)
            base_count = self.service.query_order_count(region.id, base_start, base_end)
            base_avg = base_count / 2.0
            if base_avg < 2:
                continue
            drop_rate = (base_avg - recent_count) / base_avg
            if drop_rate > self.settings.trend_drop_threshold:
                result.append(
                    AnomalyDTO(
                        type="大区订单量骤降",
                        severity="HIGH" if drop_rate > 0.6 else "MEDIUM",
                        subject=region.name,
                        description=f"近 2 周订单量 {recent_count} 笔，过去 4 周均值 {base_avg:.1f} 笔/两周，下降 {drop_rate * 100:.0f}%",
                        suggestion="建议联系大区负责人确认原因，检查是否有系统问题或市场变化",
                    )
                )
        return result

    def _detect_zero_sale_products(self) -> list[AnomalyDTO]:
        """
        检测连续零销售产品
        
        Returns:
            异常列表
        """
        today = date.today()
        result = []
        for product in self.service.active_products():
            last_sale = self.service.query_last_order_date(product.id)
            if last_sale is None:
                continue
            days_without_sale = (today - last_sale).days
            if days_without_sale >= self.settings.anomaly_threshold_days:
                severity = "HIGH" if days_without_sale >= 14 else "MEDIUM" if days_without_sale >= 7 else "LOW"
                result.append(
                    AnomalyDTO(
                        type="产品连续零销售",
                        severity=severity,
                        subject=f"{product.name}（{product.sku_code}）",
                        description=f"已连续 {days_without_sale} 天无销售订单，上次出单日期：{last_sale}",
                        suggestion="检查产品是否下架、库存是否充足、价格是否有竞争力",
                    )
                )
        return result

    def _detect_high_refund_reps(self) -> list[AnomalyDTO]:
        """
        检测高退单率销售代表
        
        Returns:
            异常列表
        """
        end = date.today()
        start = end - timedelta(days=30)
        result = []
        for rep_id, refunded, total in self.service.query_refund_rates(start, end):
            if total < 3:
                continue
            refund_rate = refunded / total
            if refund_rate > 0.15:
                result.append(
                    AnomalyDTO(
                        type="销售员退单率异常",
                        severity="HIGH" if refund_rate > 0.3 else "MEDIUM",
                        subject=self.service.get_rep_name(rep_id),
                        description=f"近 30 天退单率 {refund_rate * 100:.0f}%（{refunded}/{total} 单），明显高于团队平均水平",
                        suggestion="建议与该销售员沟通了解原因，排查是否存在虚报订单或客户不满意的情况",
                    )
                )
        return result

    def _detect_rep_performance_drop(self) -> list[AnomalyDTO]:
        """
        检测销售代表业绩骤降
        
        Returns:
            异常列表
        """
        today = date.today()
        current_start = today - timedelta(days=30)
        previous_start = today - timedelta(days=60)
        previous_end = today - timedelta(days=31)
        result = []
        for rep in self.service.sales_reps():
            current = self.service.sum_amount_by_rep(rep.id, current_start, today)
            previous = self.service.sum_amount_by_rep(rep.id, previous_start, previous_end)
            growth = self.service.calc_growth_rate(current, previous)
            if growth is None:
                continue
            if growth <= Decimal("-50"):
                result.append(
                    AnomalyDTO(
                        type="销售员业绩骤降",
                        severity="HIGH" if growth <= Decimal("-80") else "MEDIUM",
                        subject=rep.name,
                        description=f"近 30 天销售额 {money(current)}，较前 30 天下滑 {abs(growth):.1f}%",
                        suggestion="建议复盘客户跟进情况、商机储备和区域支持情况",
                    )
                )
        return result

    @staticmethod
    def translate_status(status: str) -> str:
        """
        翻译订单状态
        
        Args:
            status: 订单状态
        
        Returns:
            翻译后的状态文本
        """
        return {"COMPLETED": "已完成", "REFUNDED": "已退款", "CANCELLED": "已取消"}.get(status, status)
