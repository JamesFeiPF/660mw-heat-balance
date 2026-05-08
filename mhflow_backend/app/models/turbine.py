"""MHFlow 汽轮机模型 - 支持多级分段"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t, ph_to_s, saturation_properties


class Turbine(BaseComponent):
    """
    汽轮机模型 - 支持多级分段

    汽轮机被按抽汽点分成多个级组段，每段对应一个抽汽点或再热节点。

    高压缸段: 级组 2, 7, 11, 13, 16 (5段)
    中压缸段: 级组 19, 20 (2段)
    低压缸段: 级组 29, 30, 36, 37, 42, 43 (6段) - 两个低压缸

    入口端口:
        - steam_in: 蒸汽入口 (p, t, h, m)
        - reheat_in: 再热蒸汽入口（中压缸）
    出口端口:
        - steam_out: 蒸汽出口 (p, h, m)
        - extraction_N: 抽汽出口 (p, h, m, t) - N从1到抽汽级数
        - interstage_N: 级间抽汽/再热节点

    参数:
        - eta_isen: 等熵效率 (0~1)
        - p_out: 排汽压力 (MPa)
        - stage: 汽缸类型 (HP/IP/LP)
        - extraction_points: 抽汽点配置列表
            [{"name": "ext1", "p": MPa, "h_drop_ratio": 焓降占比, "m_frac": 抽汽质量分数}]
        - n_sections: 分段数量
        - section_params: 各段参数（可选，用于精细化计算）
        - rated_power: 汽轮机额定功率 (MW)
        - exhaust_pressure: 汽轮机排汽压力 (kPa) - 用于系统边界条件
        - hp_efficiency: 高压缸效率 (%)
        - ip_efficiency: 中压缸效率 (%)
        - lp_efficiency: 低压缸效率 (%)
        - shaft_seal_leakage_rate: 轴封漏气率 (%)
        - feedwater_pump_turbine_efficiency: 给水泵汽轮机效率 (%)
    """

    def __init__(
        self,
        name: str = "Turbine",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "steam_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "power_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0, "w": 0.0},  # 功率输入
        ]
        default_outlets = [
            {"name": "steam_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "power_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0, "w": 0.0},  # 功率输出
            # 抽汽端口预留
            {"name": "extraction_1", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "extraction_2", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "extraction_3", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "extraction_4", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "extraction_5", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "extraction_6", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
        ]
        default_params = {
            "eta_isen": 0.88,
            "p_out": 0.0049,  # MPa
            "stage": "HP",
            "n_sections": 1,  # 分段数量
            "extraction_points": [],  # 抽汽点配置
            "section_params": [],     # 各段详细参数
            "mechanical_efficiency": 0.995,  # 机械效率
            "rated_power": 660.0,  # MW
            "exhaust_pressure": 4.9,  # kPa
            "hp_efficiency": 88.0,  # %
            "ip_efficiency": 92.0,  # %
            "lp_efficiency": 89.0,  # %
            "shaft_seal_leakage_rate": 1.0,  # %
            "feedwater_pump_turbine_efficiency": 80.0,  # %
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
        计算汽轮机出口参数 - 支持多级分段

        步骤:
        1. 获取入口蒸汽参数 (p_in, t_in, h_in, s_in, m_in)
        2. 获取功率输入（如果有前级缸体连接）
        3. 根据分段参数计算每段的焓降和抽汽
        4. 逐级计算各段出口参数
        5. 汇总抽汽量和内功率
        6. 更新功率输出端口

        分段结构:
        - 高压缸段: 级组 2, 7, 11, 13, 16 (5段)
        - 中压缸段: 级组 19, 20 (2段)
        - 低压缸段: 级组 29, 30, 36, 37, 42, 43 (6段)
        """
        stage = self.params.get("stage", "HP").upper()
        
        # 根据汽缸类型选择对应的效率
        hp_eff = self.params.get("hp_efficiency", 88.0) / 100.0
        ip_eff = self.params.get("ip_efficiency", 92.0) / 100.0
        lp_eff = self.params.get("lp_efficiency", 89.0) / 100.0
        
        # 选择合适的等熵效率
        if stage == "HP":
            eta_isen = self.params.get("eta_isen", hp_eff)
        elif stage == "IP":
            eta_isen = self.params.get("eta_isen", ip_eff)
        elif stage == "LP":
            eta_isen = self.params.get("eta_isen", lp_eff)
        else:
            eta_isen = self.params.get("eta_isen", 0.88)
        
        p_out = self.params.get("p_out", 0.0049)
        n_sections = self.params.get("n_sections", 1)
        extraction_points = self.params.get("extraction_points", [])
        section_params = self.params.get("section_params", [])
        eta_mech = self.params.get("mechanical_efficiency", 0.995)

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

        # 获取功率输入（来自前级缸体）
        power_in = self.get_inlet("power_in")
        w_in = power_in.get("w", 0.0) if power_in else 0.0

        # 计算总等熵焓降
        h_out_is = self._calculate_isentropic_enthalpy(p_out, s_in, h_in)

        # 总焓降
        total_h_drop = h_in - h_out_is
        actual_h_drop = eta_isen * total_h_drop
        h_out_final = h_in - actual_h_drop

        # 按分段计算
        # 抽汽点按压力从高到低排序
        sorted_extractions = sorted(extraction_points, key=lambda x: -x.get("p", 0))
        
        # 如果没有抽汽点配置，使用传统模式
        if not sorted_extractions and n_sections == 1:
            return self._calculate_traditional(eta_isen, p_out, stage, p_in, t_in, h_in, m_in, s_in, h_out_is, h_out_final, w_in)

        # 多级分段计算
        return self._calculate_multistage(
            eta_isen, p_out, stage, p_in, t_in, h_in, m_in, s_in, 
            h_out_is, h_out_final, sorted_extractions, section_params, eta_mech, w_in
        )

    def _calculate_isentropic_enthalpy(self, p_out: float, s_in: float, h_in: float) -> float:
        """计算等熵出口焓"""
        try:
            sat_props = saturation_properties(p_out)
            s_f = sat_props['s_f']
            s_g = sat_props['s_g']
            h_f = sat_props['h_f']
            h_g = sat_props['h_g']

            if s_in >= s_g:
                # 过热区等熵膨胀 - 使用线性插值
                if s_g > s_f:
                    h_out_is = h_g + (s_in - s_g) * (h_g - h_f) / max(s_g - s_f, 1e-10)
                else:
                    h_out_is = h_g * 0.95  # 粗略估计
            elif s_in <= s_f:
                h_out_is = h_f
            else:
                # 两相区
                x_is = (s_in - s_f) / max(s_g - s_f, 1e-10)
                h_out_is = h_f + x_is * (h_g - h_f)
        except Exception:
            # 简化: 假设等熵焓降
            h_out_is = h_in - 0.8 * (h_in - 2000)

        return h_out_is

    def _calculate_traditional(self, eta_isen, p_out, stage, p_in, t_in, h_in, m_in, s_in, h_out_is, h_out_final, w_in=0.0):
        """传统单段计算模式"""
        t_out = ph_to_t(p_out, h_out_final)
        s_out = ph_to_s(p_out, h_out_final)

        # 传统抽汽配置
        extractions = self.params.get("extractions", [])
        m_extraction_total = 0.0
        extraction_results = []
        m_remaining = m_in

        for ext in extractions:
            ext_name = ext.get("name", "extraction")
            ext_p = ext.get("p", 0.0)
            ext_m_frac = ext.get("m_frac", 0.0)

            ext_m = m_in * ext_m_frac
            m_extraction_total += ext_m
            m_remaining -= ext_m

            # 抽汽焓计算
            if p_in > ext_p > p_out:
                frac = (p_in - ext_p) / max(p_in - p_out, 1e-10)
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

        m_out = max(m_remaining, 0.0)

        # 详细功率计算
        w_detailed = 0.0
        m_stage = m_in
        prev_h = h_in
        prev_p = p_in

        for ext in extractions:
            ext_p = ext.get("p", 0.0)
            ext_m = m_in * ext.get("m_frac", 0.0)

            if p_in > ext_p > p_out:
                frac = (prev_p - ext_p) / max(p_in - p_out, 1e-10)
                h_ext = h_in - frac * eta_isen * (h_in - h_out_is)
            else:
                h_ext = prev_h

            w_detailed += m_stage * (prev_h - h_ext)
            prev_h = h_ext
            prev_p = ext_p
            m_stage -= ext_m

        w_detailed += m_stage * (prev_h - h_out_final)

        # 机械效率修正后的轴功率
        w_shaft = w_detailed * self.params.get("mechanical_efficiency", 0.995)
        
        # 功率输出 = 输入功率 + 当前缸体产生的轴功率
        w_out = w_in + w_shaft

        self.results = {
            "w_internal": w_detailed,
            "w_internal_mw": w_detailed / 1000.0,
            "w_shaft": w_shaft,
            "w_shaft_mw": w_shaft / 1000.0,
            "w_in": w_in,
            "w_out": w_out,
            "w_out_mw": w_out / 1000.0,
            "eta_isen": eta_isen,
            "stage": stage,
            "h_in": h_in,
            "h_out": h_out_final,
            "h_out_is": h_out_is,
            "s_in": s_in,
            "s_out": s_out,
            "m_in": m_in,
            "m_out": m_out,
            "m_extraction_total": m_extraction_total,
            "extractions": extraction_results,
            "n_sections": 1,
            "sections": [],
        }

        self.set_outlet("steam_out", {
            "name": "steam_out",
            "p": p_out,
            "t": t_out,
            "h": h_out_final,
            "s": s_out,
            "m": m_out,
        })

        # 更新功率输出端口
        self.set_outlet("power_out", {
            "name": "power_out",
            "p": 0.0,
            "t": 0.0,
            "h": 0.0,
            "m": 0.0,
            "s": 0.0,
            "w": w_out,
        })

        for ext_result in extraction_results:
            self.set_outlet(ext_result["name"], ext_result)

        return self.to_dict()

    def _calculate_multistage(self, eta_isen, p_out, stage, p_in, t_in, h_in, m_in, s_in, 
                             h_out_is, h_out_final, sorted_extractions, section_params, eta_mech, w_in=0.0):
        """多级分段计算模式"""
        extraction_results = []
        section_results = []
        m_remaining = m_in
        prev_h = h_in
        prev_p = p_in
        w_detailed = 0.0

        # 添加排汽点作为最后一个点
        all_points = sorted_extractions.copy()
        all_points.append({"name": "exhaust", "p": p_out, "m_frac": 0.0, "h_drop_ratio": 1.0})

        # 计算每段的焓降占比
        total_h_drop_ratio = sum(ext.get("h_drop_ratio", 1.0 / len(all_points)) for ext in all_points[:-1])
        if total_h_drop_ratio <= 0:
            total_h_drop_ratio = 1.0

        # 逐级计算
        for i, point in enumerate(all_points):
            point_name = point.get("name", f"point_{i+1}")
            point_p = point.get("p", p_out)
            point_m_frac = point.get("m_frac", 0.0)
            h_drop_ratio = point.get("h_drop_ratio", 1.0 / len(all_points))

            # 当前段的实际焓降
            h_drop_actual = (h_drop_ratio / total_h_drop_ratio) * (h_in - h_out_is) * eta_isen
            
            # 段出口焓
            h_section_out = prev_h - h_drop_actual
            
            # 段出口温度
            t_section_out = ph_to_t(point_p, h_section_out)
            s_section_out = ph_to_s(point_p, h_section_out)

            # 该段抽汽量
            ext_m = m_in * point_m_frac
            m_extraction_total_i = ext_m

            # 计算该段做功
            w_section = m_remaining * (prev_h - h_section_out)
            w_detailed += w_section

            # 记录段结果
            section_results.append({
                "name": f"{self.name}_section_{i+1}",
                "point_name": point_name,
                "p_in": prev_p,
                "p_out": point_p,
                "h_in": prev_h,
                "h_out": h_section_out,
                "t_in": ph_to_t(prev_p, prev_h),
                "t_out": t_section_out,
                "s_in": ph_to_s(prev_p, prev_h),
                "s_out": s_section_out,
                "m_in": m_remaining,
                "m_out": m_remaining - ext_m,
                "m_extracted": ext_m,
                "w_section": w_section,
                "h_drop": h_drop_actual,
            })

            # 如果不是排汽口，记录抽汽结果
            if point_name != "exhaust":
                extraction_results.append({
                    "name": point_name,
                    "p": point_p,
                    "t": t_section_out,
                    "h": h_section_out,
                    "s": s_section_out,
                    "m": ext_m,
                    "m_frac": point_m_frac,
                    "section_index": i,
                })
                # 更新抽汽端口
                port_name = f"extraction_{i+1}" if i < 8 else point_name
                self.set_outlet(port_name, {
                    "name": port_name,
                    "p": point_p,
                    "t": t_section_out,
                    "h": h_section_out,
                    "s": s_section_out,
                    "m": ext_m,
                })

            # 更新状态
            prev_h = h_section_out
            prev_p = point_p
            m_remaining -= ext_m

        m_out = max(m_remaining, 0.0)
        t_out = ph_to_t(p_out, prev_h)
        s_out = ph_to_s(p_out, prev_h)

        # 机械功率（扣除机械损失）
        w_shaft = w_detailed * eta_mech
        
        # 功率输出 = 输入功率 + 当前缸体产生的轴功率
        w_out = w_in + w_shaft

        self.results = {
            "w_internal": w_detailed,          # 内功率 (kW)
            "w_internal_mw": w_detailed / 1000.0,
            "w_shaft": w_shaft,                # 轴功率 (kW)
            "w_shaft_mw": w_shaft / 1000.0,
            "w_in": w_in,                      # 功率输入
            "w_out": w_out,                    # 功率输出
            "w_out_mw": w_out / 1000.0,
            "eta_isen": eta_isen,
            "eta_mech": eta_mech,
            "stage": stage,
            "h_in": h_in,
            "h_out": prev_h,
            "h_out_is": h_out_is,
            "s_in": s_in,
            "s_out": s_out,
            "m_in": m_in,
            "m_out": m_out,
            "m_extraction_total": m_in - m_out,
            "extractions": extraction_results,
            "n_sections": len(section_results),
            "sections": section_results,
        }

        # 更新主蒸汽出口
        self.set_outlet("steam_out", {
            "name": "steam_out",
            "p": p_out,
            "t": t_out,
            "h": prev_h,
            "s": s_out,
            "m": m_out,
        })

        # 更新功率输出端口
        self.set_outlet("power_out", {
            "name": "power_out",
            "p": 0.0,
            "t": 0.0,
            "h": 0.0,
            "m": 0.0,
            "s": 0.0,
            "w": w_out,
        })

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
