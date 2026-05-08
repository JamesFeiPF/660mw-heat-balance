"""MHFlow 水泵模型"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t, ph_to_s


class Pump(BaseComponent):
    """
    水泵模型

    将水的压力升高，消耗功。

    入口端口:
        - water_in: 水入口 (p, t, h, m)
    出口端口:
        - water_out: 水出口 (p, t, h, m)

    参数:
        - eta_pump: 泵效率 (0~1)
        - p_out: 出口压力 (MPa)
        - eta_motor: 电机效率 (0~1)
        - isentropic_efficiency: 等熵效率 (%) - 兼容前端命名
        - pump_head: 扬程 (m)
        - outlet_pressure: 出口压力 (MPa) - 兼容前端命名
    """

    def __init__(
        self,
        name: str = "Pump",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "water_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_outlets = [
            {"name": "water_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_params = {
            "eta_pump": 0.85,
            "p_out": 1.0,
            "eta_motor": 0.95,
            "isentropic_efficiency": 85.0,  # 等熵效率 %
            "pump_head": 350.0,  # 扬程 m
            "outlet_pressure": 1.0,  # 兼容前端命名
            "mass_flow": 485.0,  # 给水流量 t/h - 用于变工况计算
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="pump",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """
        计算水泵出口参数

        步骤:
        1. 获取入口水参数
        2. 计算水的比容 v ≈ 0.001 m³/kg
        3. 理论功: W_theory = v * (p_out - p_in) * 1000 (转换为 kJ/kg)
        4. 实际功: W_actual = W_theory / eta_pump
        5. 出口焓: h_out = h_in + W_actual
        6. 出口温度: t_out = ph_to_t(p_out, h_out)
        7. 泵功率: P = m * W_actual
        """
        # 支持新旧参数命名
        eta_pump = self.params.get("eta_pump", self.params.get("isentropic_efficiency", 85.0) / 100.0)
        p_out = self.params.get("p_out", self.params.get("outlet_pressure", 1.0))
        eta_motor = self.params.get("eta_motor", 0.95)

        # 获取入口参数
        water_in = self.get_inlet("water_in")
        if water_in is None:
            raise ValueError(f"水泵 {self.name}: 未找到水入口 water_in")

        p_in = water_in.get("p", 0.0)
        t_in = water_in.get("t", 0.0)
        h_in = water_in.get("h", 0.0)
        m = water_in.get("m", 0.0)

        # 水的比容 (简化: 液态水 ≈ 0.001 m³/kg)
        v_water = 0.001  # m³/kg

        # 压力差 (MPa -> kPa)
        dp = (p_out - p_in) * 1000  # kPa

        # 理论功 (kJ/kg): W = v * dp
        w_theory = v_water * dp

        # 实际功 (考虑泵效率)
        w_actual = w_theory / eta_pump if eta_pump > 0 else 0.0

        # 出口焓
        h_out = h_in + w_actual

        # 出口温度
        t_out = ph_to_t(p_out, h_out)
        s_out = ph_to_s(p_out, h_out)

        # 泵功率
        p_shaft = m * w_actual  # 轴功率 (kW)
        p_motor = p_shaft / eta_motor if eta_motor > 0 else 0.0  # 电机功率 (kW)

        self.results = {
            "w_theory": w_theory,  # 理论比功 (kJ/kg)
            "w_actual": w_actual,  # 实际比功 (kJ/kg)
            "p_shaft": p_shaft,  # 轴功率 (kW)
            "p_motor": p_motor,  # 电机功率 (kW)
            "dp": dp,  # 压力升高 (kPa)
            "eta_pump": eta_pump,
            "eta_motor": eta_motor,
        }

        # 更新出口端口
        self.set_outlet("water_out", {
            "name": "water_out",
            "p": p_out,
            "t": t_out,
            "h": h_out,
            "s": s_out,
            "m": m,
        })

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pump":
        """从字典创建水泵实例"""
        return cls(
            name=data.get("name", "Pump"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )
