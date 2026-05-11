"""MHFlow 凝汽器模型"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent
from app.properties.steam import (
    pt_to_h, pt_to_s, ph_to_t, ph_to_s,
    saturation_temperature, saturation_properties,
)


class Condenser(BaseComponent):
    """
    凝汽器模型

    将汽轮机排汽冷凝为饱和水。

    入口端口:
        - steam_in: 乏汽入口 (p, t, h, m)
        - cooling_in: 冷却水入口 (p, t, h, m)
    出口端口:
        - water_out: 凝结水出口 (p, t, h, m)
        - cooling_out: 冷却水出口 (p, t, h, m)

    参数:
        - ttd: 端差 (°C), 即凝结水温度与冷却水出口温度之差
        - delta_t_cw: 冷却水温升 (°C)
        - p_cond: 凝汽器压力 (MPa)
        - eta_heat_transfer: 传热效率 (0~1)
    """

    def __init__(
        self,
        name: str = "Condenser",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "steam_in", "p": 0.0049, "t": 0.0, "h": 0.0, "m": 0.0},
            {"name": "cooling_in", "p": 0.1, "t": 20.0, "h": 0.0, "m": 0.0},
        ]
        default_outlets = [
            {"name": "water_out", "p": 0.0049, "t": 0.0, "h": 0.0, "m": 0.0},
            {"name": "cooling_out", "p": 0.1, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_params = {
            "ttd": 5.0,  # 端差 °C
            "delta_t_cw": 10.0,  # 冷却水温升 °C
            "p_cond": 0.0049,  # 凝汽器压力 MPa
            "eta_heat_transfer": 0.98,
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="condenser",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """
        计算凝汽器出口参数

        步骤:
        1. 获取凝汽器压力下的饱和温度
        2. 凝结水出口温度 = 饱和温度 - 端差
        3. 冷却水出口温度 = 凝结水出口温度 - 端差
        4. 计算冷凝放热量 Q = m_steam * (h_steam_in - h_water_out)
        5. 计算冷却水量 m_cw = Q / (cp_cw * delta_t_cw)
        """
        p_cond = self.params.get("p_cond", 0.0049)
        ttd = self.params.get("ttd", 5.0)
        delta_t_cw = self.params.get("delta_t_cw", 10.0)
        eta_ht = self.params.get("eta_heat_transfer", 0.98)

        # 获取入口参数
        steam_in = self.get_inlet("steam_in")
        cooling_in = self.get_inlet("cooling_in")

        if steam_in is None:
            raise ValueError(f"凝汽器 {self.name}: 未找到乏汽入口 steam_in")

        m_steam = steam_in.get("m", 0.0)
        h_steam_in = steam_in.get("h", 0.0)
        p_steam_in = steam_in.get("p", p_cond)

        # 使用实际凝汽器压力
        p_cond_actual = p_steam_in if p_steam_in > 0 else p_cond

        # 饱和温度
        t_sat = saturation_temperature(p_cond_actual)

        # 凝结水出口温度 (饱和温度)
        t_water_out = t_sat

        # 冷却水出口温度
        t_cw_in = cooling_in.get("t", 20.0) if cooling_in else 20.0
        t_cw_out = t_cw_in + delta_t_cw

        # 凝结水焓 (饱和水)
        sat_props = saturation_properties(p_cond_actual)
        h_water_out = sat_props['h_f']
        s_water_out = sat_props['s_f']

        # 冷凝放热量
        q_cond = m_steam * (h_steam_in - h_water_out) * eta_ht

        # 冷却水比热
        cp_cw = 4.18  # kJ/(kg·K)

        # 冷却水量
        if delta_t_cw > 0:
            m_cw = q_cond / (cp_cw * delta_t_cw)
        else:
            m_cw = 0.0

        # 冷却水出口焓
        h_cw_out = cp_cw * t_cw_out

        # 凝汽器热负荷
        q_total = q_cond

        self.results = {
            "q_cond": q_cond,  # 冷凝放热量 (kW)
            "q_total": q_total,  # 总热负荷 (kW)
            "t_sat": t_sat,  # 饱和温度 (°C)
            "t_water_out": t_water_out,  # 凝结水出口温度 (°C)
            "t_cw_out": t_cw_out,  # 冷却水出口温度 (°C)
            "m_cw": m_cw,  # 冷却水量 (kg/s)
            "m_cw_hour": m_cw * 3600,  # 冷却水量 (t/h)
            "ttd": ttd,
            "delta_t_cw": delta_t_cw,
            "p_cond": p_cond_actual,
        }

        # 更新出口端口
        self.set_outlet("water_out", {
            "name": "water_out",
            "p": p_cond_actual,
            "t": t_water_out,
            "h": h_water_out,
            "s": s_water_out,
            "m": m_steam,
        })

        self.set_outlet("cooling_out", {
            "name": "cooling_out",
            "p": cooling_in.get("p", 0.1) if cooling_in else 0.1,
            "t": t_cw_out,
            "h": h_cw_out,
            "m": m_cw,
        })

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Condenser":
        """从字典创建凝汽器实例"""
        return cls(
            name=data.get("name", "Condenser"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )
