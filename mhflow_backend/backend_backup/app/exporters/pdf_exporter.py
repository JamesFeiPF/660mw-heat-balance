"""MHFlow PDF报告导出器

将热平衡计算结果导出为PDF格式的报告。
"""
import os
import io
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab 库不可用，PDF导出功能将不可用")


class PDFExporter:
    """
    PDF报告导出器

    将热平衡计算结果生成专业的PDF报告，
    包含系统概况、各节点参数、系统性能指标等。
    """

    def __init__(self, results: Dict[str, Any], model_data: Optional[Dict[str, Any]] = None):
        """
        初始化PDF导出器

        参数:
            results: 求解结果
            model_data: 模型数据
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab 库不可用，请安装: pip install reportlab")

        self.results = results
        self.model_data = model_data or {}
        self.styles = self._create_styles()

    def _create_styles(self):
        """创建文档样式"""
        styles = getSampleStyleSheet()

        # 标题样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.darkblue,
        ))

        # 副标题
        styles.add(ParagraphStyle(
            name='ChineseSubtitle',
            fontName='Helvetica',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=10,
            textColor=colors.grey,
        ))

        # 章节标题
        styles.add(ParagraphStyle(
            name='SectionTitle',
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.darkblue,
        ))

        # 小节标题
        styles.add(ParagraphStyle(
            name='SubSectionTitle',
            fontName='Helvetica-Bold',
            fontSize=11,
            spaceBefore=10,
            spaceAfter=5,
        ))

        # 正文
        styles.add(ParagraphStyle(
            name='BodyText2',
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=5,
            leading=14,
        ))

        return styles

    def export(self, output_path: Optional[str] = None) -> bytes:
        """
        导出PDF报告

        参数:
            output_path: 输出文件路径 (为空则返回字节流)

        返回:
            PDF字节数据
        """
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        elements = []

        # ===== 封面 =====
        elements.append(Spacer(1, 80))
        elements.append(Paragraph(
            "MHFlow Heat Balance Report",
            self.styles['ChineseTitle']
        ))
        model_name = self.model_data.get("name", "Unknown Model")
        elements.append(Paragraph(
            f"Model: {model_name}",
            self.styles['ChineseSubtitle']
        ))
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="80%", thickness=1, color=colors.grey))
        elements.append(Spacer(1, 20))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(
            f"Generated: {now}",
            self.styles['ChineseSubtitle']
        ))

        converged = self.results.get("converged", False)
        iterations = self.results.get("iteration_count", 0)
        elements.append(Paragraph(
            f"Converged: {'Yes' if converged else 'No'} (Iterations: {iterations})",
            self.styles['ChineseSubtitle']
        ))

        elements.append(PageBreak())

        # ===== 系统性能指标 =====
        performance = self.results.get("system_performance", {})
        if performance:
            elements.append(Paragraph(
                "System Performance Summary",
                self.styles['SectionTitle']
            ))

            perf_data = [
                ["Parameter", "Value", "Unit"],
                ["Electrical Power", f"{performance.get('w_electrical_mw', 0):.2f}", "MW"],
                ["Turbine Internal Power", f"{performance.get('w_turbine_internal_mw', 0):.2f}", "MW"],
                ["Boiler Heat Input", f"{performance.get('q_boiler_mw', 0):.2f}", "MW"],
                ["Heat Rate", f"{performance.get('heat_rate_kj_kwh', 0):.2f}", "kJ/kWh"],
                ["Boiler Efficiency", f"{performance.get('eta_boiler', 0) * 100:.2f}", "%"],
                ["Plant Efficiency", f"{performance.get('eta_plant', 0) * 100:.2f}", "%"],
                ["Coal Consumption Rate", f"{performance.get('coal_consumption_rate_g_kwh', 0):.2f}", "g/kWh"],
                ["Steam Rate", f"{performance.get('steam_rate_kg_kwh', 0):.4f}", "kg/kWh"],
                ["Main Steam Flow", f"{performance.get('main_steam_flow_t_h', 0):.2f}", "t/h"],
                ["Annual Generation", f"{performance.get('annual_generation_mwh', 0):.0f}", "MWh"],
                ["Annual Coal Consumption", f"{performance.get('annual_coal_tons', 0):.0f}", "tons"],
            ]

            table = Table(perf_data, colWidths=[180, 120, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))

        # ===== 元件计算结果 =====
        components = self.results.get("components", {})
        if components:
            elements.append(Paragraph(
                "Component Results",
                self.styles['SectionTitle']
            ))

            for comp_name, comp_data in components.items():
                comp_type = comp_data.get("component_type", "")
                results_data = comp_data.get("results", {})

                if not results_data:
                    continue

                elements.append(Paragraph(
                    f"{comp_name} ({comp_type})",
                    self.styles['SubSectionTitle']
                ))

                # 构建结果表格
                table_data = [["Parameter", "Value"]]
                for key, value in results_data.items():
                    if isinstance(value, float):
                        table_data.append([key, f"{value:.4f}"])
                    elif isinstance(value, list):
                        table_data.append([key, f"[{len(value)} items]"])
                    else:
                        table_data.append([key, str(value)])

                if len(table_data) > 1:
                    table = Table(table_data, colWidths=[200, 200])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.steelblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 10))

        # ===== 出口端口参数 =====
        elements.append(PageBreak())
        elements.append(Paragraph(
            "Node Parameters",
            self.styles['SectionTitle']
        ))

        node_table_data = [["Node", "P (MPa)", "T (C)", "H (kJ/kg)", "S (kJ/kg/K)", "M (kg/s)"]]

        for comp_name, comp_data in components.items():
            for port in comp_data.get("outlet_ports", []):
                port_name = port.get("name", "")
                node_table_data.append([
                    f"{comp_name}.{port_name}",
                    f"{port.get('p', 0):.4f}",
                    f"{port.get('t', 0):.2f}",
                    f"{port.get('h', 0):.2f}",
                    f"{port.get('s', 0):.4f}",
                    f"{port.get('m', 0):.4f}",
                ])

        if len(node_table_data) > 1:
            table = Table(node_table_data, colWidths=[100, 60, 60, 70, 80, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(table)

        # 生成PDF
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        # 如果指定了输出路径，保存文件
        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(pdf_data)
            logger.info(f"PDF报告已保存: {output_path}")

        return pdf_data
