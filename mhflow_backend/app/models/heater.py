"""MHFlow 加热器模型（高加/低加/除氧器）"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent
from app.properties.steam import (
    pt_to_h, pt_to_s, ph_to_t, ph_to_s,
    saturation_temperature, saturation_properties,
)


class Heater(BaseComponent):
    """
    加热器模型

    支持表面式加热器（高加、低加）和混合式加热器（除氧器）。

    表面式加热器:
        入口: 被加热水(给水/凝结水) + 加热蒸汽(抽汽)
        出口: 加热后的水 + 疏水
        热平衡: m_steam * (h_steam - h_drain) = m_water * (h_water_out - h_water_in)

    混合式加热器（除氧器）:
        入口: 被加热水 + 加热蒸汽
        出口: 混合后的水
        热平衡: m_steam * h_steam + m_water * h_water_in = (m_steam + m_water) * h_water_out

    入口端口:
        - water_in: 被加热水入口 (p, t, h, m)
        - steam_in: 加热蒸汽入口 (p, t, h, m)
        - drain_in: 上级疏水入口 (p, t, h, m) [可选]
    出口端口:
        - water_out: 加热后水出口 (p, t, h, m)
        - drain_out: 疏水出口 (p, t, h, m) [表面式]

    参数:
        - heater_type: 加热器类型 (HP/LP/DA)
            HP: 高压加热器 (表面式)
            LP: 低压加热器 (表面式)
            DA: 除氧器 (混合式)
        - ttd: 端差 (°C), 表面式加热器
        - dca: 疏水冷却度 (°C), 表面式加热器
        - eta: 加热器效率 (0~1)
        - p_heater: 加热器压力 (MPa)
        - p_water_out: 出口水压力 (MPa)
        - hp_ttd: 高加上端差 (°C)
        - hp_dca: 高加下端差/过冷度 (°C)
        - lp_ttd: 低加上端差 (°C)
        - lp_dca: 低加下端差/过冷度 (°C)
        - deaerator_pressure: 除氧器工作压力 (MPa)
        - heat_loss_rate: 加热器散热损失 (%)
    """

    def __init__(
        self,
        name: str = "Heater",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "water_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
            {"name": "steam_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
            {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_outlets = [
            {"name": "water_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
            {"name": "drain_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_params = {
            "heater_type": "HP",
            "ttd": 3.0,  # 端差 °C
            "dca": 5.0,  # 疏水冷却度 °C
            "eta": 0.99,
            "p_heater": 1.0,  # 加热器压力 MPa
            "p_water_out": 1.0,
            "hp_ttd": 3.0,  # 高加上端差 °C
            "hp_dca": 5.0,  # 高加下端差/过冷度 °C
            "lp_ttd": 2.8,  # 低加上端差 °C
            "lp_dca": 5.0,  # 低加下端差/过冷度 °C
            "deaerator_pressure": 0.7,  # 除氧器工作压力 MPa
            "heat_loss_rate": 0.2,  # 加热器散热损失 %
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="heater",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """
        计算加热器出口参数

        根据加热器类型执行不同的热平衡计算。
        """
        heater_type = self.params.get("heater_type", "HP")
        eta = self.params.get("eta", 0.99)
        p_heater = self.params.get("p_heater", 1.0)
        p_water_out = self.params.get("p_water_out", p_heater)
        
        # 根据加热器类型选择对应的端差和过冷度
        if heater_type == "HP":
            ttd = self.params.get("ttd", self.params.get("hp_ttd", -1.7))
            dca = self.params.get("dca", self.params.get("hp_dca", 5.0))
        elif heater_type == "LP":
            ttd = self.params.get("ttd", self.params.get("lp_ttd", 2.8))
            dca = self.params.get("dca", self.params.get("lp_dca", 5.0))
        elif heater_type == "DA":
            ttd = 0.0
            dca = 0.0
            # 使用除氧器工作压力
            p_heater = self.params.get("deaerator_pressure", p_heater)
        else:
            ttd = self.params.get("ttd", 3.0)
            dca = self.params.get("dca", 5.0)

        # 获取入口参数
        water_in = self.get_inlet("water_in")
        steam_in = self.get_inlet("steam_in")
        drain_in = self.get_inlet("drain_in")

        if water_in is None:
            raise ValueError(f"加热器 {self.name}: 未找到水入口 water_in")
        if steam_in is None:
            raise ValueError(f"加热器 {self.name}: 未找到蒸汽入口 steam_in")

        m_water = water_in.get("m", 0.0)
        h_water_in = water_in.get("h", 0.0)
        t_water_in = water_in.get("t", 0.0)

        h_steam = steam_in.get("h", 0.0)
        t_steam = steam_in.get("t", 0.0)
        p_steam = steam_in.get("p", p_heater)

        m_drain_in = drain_in.get("m", 0.0) if drain_in else 0.0
        h_drain_in = drain_in.get("h", 0.0) if drain_in else 0.0

        # 使用实际蒸汽压力
        p_heater_actual = p_steam if p_steam > 0 else p_heater

        # 饱和参数
        sat_props = saturation_properties(p_heater_actual)
        t_sat = sat_props['t_sat']
        h_f = sat_props['h_f']
        h_g = sat_props['h_g']
        s_f = sat_props['s_f']

        # 端差校验: 表面式加热器不允许负端差
        if heater_type != "DA" and ttd < 0:
            import logging
            logging.getLogger(__name__).warning(
                f"加热器 {self.name}: 端差 {ttd}°C 为负值，物理上不可能，已取绝对值 {abs(ttd)}°C"
            )
            ttd = abs(ttd)

        if heater_type == "DA":
            # 混合式加热器（除氧器）
            # 除氧器使用自身工作压力计算饱和参数，而非蒸汽入口压力
            p_da = self.params.get("p_heater", 1.0)
            sat_props_da = saturation_properties(p_da)
            return self._calculate_da(
                m_water, h_water_in, h_steam,
                m_drain_in, h_drain_in,
                sat_props_da['t_sat'], sat_props_da['h_f'], sat_props_da['s_f'],
                p_da, p_water_out, eta,
            )
        else:
            # 表面式加热器（高加/低加）
            return self._calculate_surface(
                m_water, h_water_in, h_steam,
                m_drain_in, h_drain_in,
                t_sat, h_f, s_f, p_heater_actual, p_water_out,
                ttd, dca, eta, heater_type,
            )

    def _calculate_surface(
        self,
        m_water: float, h_water_in: float, h_steam: float,
        m_drain_in: float, h_drain_in: float,
        t_sat: float, h_f: float, s_f: float,
        p_heater: float, p_water_out: float,
        ttd: float, dca: float, eta: float,
        heater_type: str,
    ) -> Dict[str, Any]:
        """表面式加热器计算"""
        # 出口水温度 = 饱和温度 - 端差
        t_water_out = t_sat - ttd

        # 出口水焓 (近似: 饱和水焓)
        h_water_out = pt_to_h(p_water_out, t_water_out)

        # 疏水温度 = 饱和温度 - 疏水冷却度
        t_drain = t_sat - dca
        h_drain = pt_to_h(p_heater, t_drain)

        # 热平衡: m_steam * (h_steam - h_drain) * eta + m_drain_in * (h_drain_in - h_drain) * eta
        #         = m_water * (h_water_out - h_water_in)
        # 求解 m_steam
        q_water = m_water * (h_water_out - h_water_in)

        # 蒸汽放热
        dh_steam = h_steam - h_drain
        if dh_steam > 0:
            q_drain = m_drain_in * (h_drain_in - h_drain) if m_drain_in > 0 else 0.0
            q_steam_needed = q_water - q_drain * eta
            m_steam = q_steam_needed / (dh_steam * eta) if dh_steam > 0 else 0.0
        else:
            m_steam = 0.0

        # 确保蒸汽流量不为负
        m_steam = max(m_steam, 0.0)

        # 疏水出口
        m_drain_out = m_steam + m_drain_in

        s_water_out = pt_to_s(p_water_out, t_water_out)

        self.results = {
            "heater_type": heater_type,
            "t_sat": t_sat,
            "t_water_out": t_water_out,
            "t_drain": t_drain,
            "h_water_out": h_water_out,
            "h_drain": h_drain,
            "m_steam": m_steam,
            "m_drain_out": m_drain_out,
            "q_water": q_water,
            "q_steam": m_steam * (h_steam - h_drain),
            "ttd": ttd,
            "dca": dca,
        }

        # 更新出口端口
        self.set_outlet("water_out", {
            "name": "water_out",
            "p": p_water_out,
            "t": t_water_out,
            "h": h_water_out,
            "s": s_water_out,
            "m": m_water,
        })

        self.set_outlet("drain_out", {
            "name": "drain_out",
            "p": p_heater,
            "t": t_drain,
            "h": h_drain,
            "m": m_drain_out,
        })

        return self.to_dict()

    def _calculate_da(
        self,
        m_water: float, h_water_in: float, h_steam: float,
        m_drain_in: float, h_drain_in: float,
        t_sat: float, h_f: float, s_f: float,
        p_heater: float, p_water_out: float,
        eta: float,
    ) -> Dict[str, Any]:
        """混合式加热器（除氧器）计算"""
        # 出口水焓 = 饱和水焓
        h_water_out = h_f
        t_water_out = t_sat

        # 热平衡: m_steam * h_steam + m_drain_in * h_drain_in + m_water * h_water_in
        #         = (m_steam + m_drain_in + m_water) * h_water_out
        # 除氧器为混合式加热器，无传热端差，效率≈100%
        # 求解 m_steam:
        # m_steam * (h_steam - h_water_out) = m_water * (h_water_out - h_water_in) - m_drain_in * (h_drain_in - h_water_out)
        q_water = m_water * (h_water_out - h_water_in)
        q_drain = m_drain_in * (h_drain_in - h_water_out) if m_drain_in > 0 else 0.0

        dh_steam = h_steam - h_water_out
        if dh_steam > 0:
            m_steam = (q_water - q_drain) / dh_steam
        else:
            m_steam = 0.0

        m_steam = max(m_steam, 0.0)

        # 如果不需要蒸汽，重新计算出口参数（基于实际混合焓）
        if m_steam == 0.0 and (m_water + m_drain_in) > 0:
            total_m = m_water + m_drain_in
            h_water_out = (m_water * h_water_in + m_drain_in * h_drain_in) / total_m
            t_water_out = ph_to_t(p_water_out, h_water_out)

        # 出口总水量
        m_water_out = m_water + m_steam + m_drain_in

        self.results = {
            "heater_type": "DA",
            "t_sat": t_sat,
            "t_water_out": t_water_out,
            "h_water_out": h_water_out,
            "m_steam": m_steam,
            "m_water_out": m_water_out,
            "q_water": q_water,
            "q_steam": m_steam * (h_steam - h_water_out),
        }

        # 更新出口端口
        self.set_outlet("water_out", {
            "name": "water_out",
            "p": p_water_out,
            "t": t_water_out,
            "h": h_water_out,
            "s": s_f,
            "m": m_water_out,
        })

        # 除氧器无疏水出口（混合式）
        self.set_outlet("drain_out", {
            "name": "drain_out",
            "p": p_heater,
            "t": t_water_out,
            "h": h_water_out,
            "m": 0.0,
        })

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Heater":
        """从字典创建加热器实例"""
        return cls(
            name=data.get("name", "Heater"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )
