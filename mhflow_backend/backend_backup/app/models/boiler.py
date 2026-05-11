"""MHFlow 锅炉模型"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t


class Boiler(BaseComponent):
    """
    锅炉模型

    功能:
    - 将给水加热为过热蒸汽
    - 计算锅炉热负荷、燃料消耗量
    - 支持一次再热

    入口端口:
        - feedwater_in: 给水入口 (p, t, h, m)
    出口端口:
        - steam_out: 过热蒸汽出口 (p, t, h, m)
        - reheat_in: 冷再热蒸汽入口 (p, t, h, m) [可选]
        - reheat_out: 热再热蒸汽出口 (p, t, h, m) [可选]

    参数:
        - eta_boiler: 锅炉效率 (0~1)
        - fuel_lhv: 燃料低位发热量 (kJ/kg)
        - p_out: 出口蒸汽压力 (MPa)
        - t_out: 出口蒸汽温度 (°C)
        - p_reheat_out: 再热蒸汽出口压力 (MPa)
        - t_reheat_out: 再热蒸汽出口温度 (°C)
    """

    def __init__(
        self,
        name: str = "Boiler",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "feedwater_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
            {"name": "reheat_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_outlets = [
            {"name": "steam_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
            {"name": "reheat_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_params = {
            "eta_boiler": 0.93,
            "fuel_lhv": 21000.0,  # kJ/kg (标准煤)
            "p_out": 25.0,  # MPa
            "t_out": 600.0,  # °C
            "p_reheat_out": 4.5,  # MPa
            "t_reheat_out": 600.0,  # °C
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="boiler",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """
        计算锅炉出口参数

        计算:
        1. 主蒸汽出口焓值 h_out = pt_to_h(p_out, t_out)
        2. 主蒸汽流量 m = 给水流量
        3. 锅炉热负荷 Q = m * (h_out - h_in) + m_rh * (h_rh_out - h_rh_in)
        4. 燃料消耗量 B = Q / (eta_boiler * fuel_lhv)
        """
        eta_boiler = self.params.get("eta_boiler", 0.93)
        fuel_lhv = self.params.get("fuel_lhv", 21000.0)
        p_out = self.params.get("p_out", 25.0)
        t_out = self.params.get("t_out", 600.0)
        p_rh_out = self.params.get("p_reheat_out", 4.5)
        t_rh_out = self.params.get("t_reheat_out", 600.0)

        # 获取入口参数
        fw_in = self.get_inlet("feedwater_in")
        rh_in = self.get_inlet("reheat_in")

        if fw_in is None:
            raise ValueError(f"锅炉 {self.name}: 未找到给水入口 feedwater_in")

        m_fw = fw_in.get("m", 0.0)
        h_fw = fw_in.get("h", 0.0)

        # 主蒸汽出口
        h_steam_out = pt_to_h(p_out, t_out)
        s_steam_out = pt_to_s(p_out, t_out)

        # 主蒸汽热负荷
        q_main = m_fw * (h_steam_out - h_fw)

        # 再热蒸汽
        q_reheat = 0.0
        h_rh_out = 0.0
        m_rh = 0.0
        if rh_in is not None and rh_in.get("m", 0.0) > 0:
            m_rh = rh_in.get("m", 0.0)
            h_rh_in = rh_in.get("h", 0.0)
            h_rh_out = pt_to_h(p_rh_out, t_rh_out)
            q_reheat = m_rh * (h_rh_out - h_rh_in)

        # 总热负荷
        q_total = q_main + q_reheat

        # 燃料消耗量
        b_fuel = q_total / (eta_boiler * fuel_lhv) if eta_boiler > 0 and fuel_lhv > 0 else 0.0

        # 标准煤耗率 (g/kWh) - 暂时设为0，等发电机计算后更新
        # 计算结果
        self.results = {
            "q_main": q_main,  # 主蒸汽吸热量 (kW)
            "q_reheat": q_reheat,  # 再热蒸汽吸热量 (kW)
            "q_total": q_total,  # 总吸热量 (kW)
            "b_fuel": b_fuel,  # 燃料消耗量 (kg/s)
            "b_fuel_hour": b_fuel * 3600,  # 燃料消耗量 (kg/h)
            "eta_boiler": eta_boiler,
        }

        # 更新出口端口
        self.set_outlet("steam_out", {
            "name": "steam_out",
            "p": p_out,
            "t": t_out,
            "h": h_steam_out,
            "s": s_steam_out,
            "m": m_fw,
        })

        if rh_in is not None and rh_in.get("m", 0.0) > 0:
            s_rh_out = pt_to_s(p_rh_out, t_rh_out)
            self.set_outlet("reheat_out", {
                "name": "reheat_out",
                "p": p_rh_out,
                "t": t_rh_out,
                "h": h_rh_out,
                "s": s_rh_out,
                "m": m_rh,
            })

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Boiler":
        """从字典创建锅炉实例"""
        return cls(
            name=data.get("name", "Boiler"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )
