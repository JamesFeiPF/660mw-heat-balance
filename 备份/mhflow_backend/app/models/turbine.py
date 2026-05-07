"""MHFlow 汽轮机模型"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t, ph_to_s


class Turbine(BaseComponent):
    """
    汽轮机模型

    支持高压缸、中压缸、低压缸。
    可包含多级抽汽。

    入口端口:
        - steam_in: 蒸汽入口 (p, t, h, m)
    出口端口:
        - steam_out: 蒸汽出口 (p, h, m)
        - extraction_1..N: 抽汽出口 (p, h, m, t)

    参数:
        - eta_isen: 等熵效率 (0~1)
        - p_out: 排汽压力 (MPa)
        - stage: 汽缸类型 (HP/IP/LP)
        - extractions: 抽汽参数列表
            [{"name": "ext1", "p": MPa, "m_frac": 质量分数}]
    """

    def __init__(
        self,
        name: str = "Turbine",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "steam_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_outlets = [
            {"name": "steam_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_params = {
            "eta_isen": 0.88,
            "p_out": 0.0049,  # MPa
            "stage": "HP",
            "extractions": [],
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="turbine",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """
        计算汽轮机出口参数

        步骤:
        1. 获取入口蒸汽参数 (p_in, t_in, h_in, s_in, m_in)
        2. 计算等熵膨胀终点焓: h_out_is = ph_to_s(p_out, s_in) 对应的焓
           实际上: s_out_is = s_in, h_out_is = 由(p_out, s_in)确定
        3. 计算实际出口焓: h_out = h_in - eta * (h_in - h_out_is)
        4. 计算出口温度: t_out = ph_to_t(p_out, h_out)
        5. 计算内功率: W = m * (h_in - h_out)
        6. 处理各级抽汽
        """
        eta_isen = self.params.get("eta_isen", 0.88)
        p_out = self.params.get("p_out", 0.0049)
        stage = self.params.get("stage", "HP")
        extractions = self.params.get("extractions", [])

        # 获取入口参数
        steam_in = self.get_inlet("steam_in")
        if steam_in is None:
            raise ValueError(f"汽轮机 {self.name}: 未找到蒸汽入口 steam_in")

        p_in = steam_in.get("p", 0.0)
        t_in = steam_in.get("t", 0.0)
        h_in = steam_in.get("h", 0.0)
        m_in = steam_in.get("m", 0.0)

        # 计算入口熵
        s_in = steam_in.get("s", 0.0)
        if s_in == 0.0 and p_in > 0 and t_in > 0:
            s_in = pt_to_s(p_in, t_in)

        # 等熵膨胀: 出口熵 = 入口熵
        # 求等熵出口焓
        h_out_is = ph_to_s(p_out, h_in)  # 这里 ph_to_s 返回的是 s
        # 实际上需要: 已知 p_out 和 s_in，求 h_out_is
        # 使用 IAPWS: 由 (p_out, s_in) 求焓
        try:
            from app.properties.steam import px_to_h, saturation_properties
            sat_props = saturation_properties(p_out)
            s_f = sat_props['s_f']
            s_g = sat_props['s_g']
            h_f = sat_props['h_f']
            h_g = sat_props['h_g']

            if s_in >= s_g:
                # 过热区等熵膨胀
                h_out_is = h_g + (s_in - s_g) / (s_g - s_f + 1e-10) * (h_g - h_f) * 0.8
                # 更精确: 使用迭代
                # 过热蒸汽: s = s_g + cp * ln(T/T_sat)
                # h = h_g + cp * (T - T_sat)
                # 所以 h_out_is ≈ h_g + (s_in - s_g) * (h_g - h_f) / (s_g - s_f)
                if s_g > s_f:
                    h_out_is = h_g + (s_in - s_g) * (h_g - h_f) / (s_g - s_f)
            elif s_in <= s_f:
                h_out_is = h_f
            else:
                # 两相区
                x_is = (s_in - s_f) / (s_g - s_f) if (s_g - s_f) > 0 else 0
                h_out_is = h_f + x_is * (h_g - h_f)
        except Exception:
            # 简化: 假设等熵焓降
            h_out_is = h_in - 0.8 * (h_in - 2000)  # 粗略估计

        # 实际出口焓
        h_out = h_in - eta_isen * (h_in - h_out_is)

        # 出口温度
        t_out = ph_to_t(p_out, h_out)
        s_out = ph_to_s(p_out, h_out)

        # 出口流量 = 入口流量 - 抽汽总量
        m_extraction_total = 0.0
        extraction_results = []

        m_remaining = m_in
        for ext in extractions:
            ext_name = ext.get("name", "extraction")
            ext_p = ext.get("p", 0.0)
            ext_m_frac = ext.get("m_frac", 0.0)

            # 抽汽量
            ext_m = m_in * ext_m_frac
            m_extraction_total += ext_m
            m_remaining -= ext_m

            # 抽汽焓: 假设抽汽在入口到出口之间的等熵膨胀线上
            # 简化: 线性插值
            if p_in > ext_p > p_out:
                frac = (p_in - ext_p) / (p_in - p_out) if (p_in - p_out) > 0 else 0
                h_ext = h_in - frac * eta_isen * (h_in - h_out_is)
            else:
                h_ext = h_in

            t_ext = ph_to_t(ext_p, h_ext)
            s_ext = ph_to_s(ext_p, h_ext)

            extraction_results.append({
                "name": ext_name,
                "p": ext_p,
                "t": t_ext,
                "h": h_ext,
                "s": s_ext,
                "m": ext_m,
                "m_frac": ext_m_frac,
            })

        # 确保出口流量不为负
        m_out = max(m_remaining, 0.0)

        # 内功率
        w_internal = m_in * (h_in - h_out)  # 简化计算（未扣除抽汽做功差异）

        # 更精确的功率计算: 考虑各级做功
        w_detailed = 0.0
        m_stage = m_in
        prev_h = h_in
        prev_p = p_in

        for ext in extractions:
            ext_p = ext.get("p", 0.0)
            ext_m_frac = ext.get("m_frac", 0.0)
            ext_m = m_in * ext_m_frac

            # 该级焓降
            if p_in > ext_p > p_out:
                frac = (prev_p - ext_p) / (p_in - p_out) if (p_in - p_out) > 0 else 0
                h_ext = h_in - frac * eta_isen * (h_in - h_out_is)
            else:
                h_ext = prev_h

            w_detailed += m_stage * (prev_h - h_ext)
            prev_h = h_ext
            prev_p = ext_p
            m_stage -= ext_m

        # 末级做功
        w_detailed += m_stage * (prev_h - h_out)

        self.results = {
            "w_internal": w_detailed,  # 内功率 (kW)
            "w_internal_mw": w_detailed / 1000.0,  # 内功率 (MW)
            "eta_isen": eta_isen,
            "stage": stage,
            "h_in": h_in,
            "h_out": h_out,
            "h_out_is": h_out_is,
            "s_in": s_in,
            "s_out": s_out,
            "m_in": m_in,
            "m_out": m_out,
            "m_extraction_total": m_extraction_total,
            "extractions": extraction_results,
        }

        # 更新出口端口
        self.set_outlet("steam_out", {
            "name": "steam_out",
            "p": p_out,
            "t": t_out,
            "h": h_out,
            "s": s_out,
            "m": m_out,
        })

        # 更新抽汽端口
        for ext_result in extraction_results:
            self.set_outlet(ext_result["name"], ext_result)

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Turbine":
        """从字典创建汽轮机实例"""
        return cls(
            name=data.get("name", "Turbine"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )
