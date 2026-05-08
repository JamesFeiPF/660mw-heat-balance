"""MHFlow 发电机模型"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent


class Generator(BaseComponent):
    """
    发电机模型

    将汽轮机机械功率转换为电功率。

    入口端口:
        - mechanical_in: 机械功率输入 (p, t, h, m, w_mechanical)
    出口端口:
        - electrical_out: 电功率输出 (p, t, h, m, w_electrical)

    参数:
        - eta_gen: 发电机效率 (0~1)
        - eta_mech: 机械传动效率 (0~1)
        - rated_power: 额定功率 (MW)
        - power_factor: 功率因数
        - station_service_power_rate: 厂用电率 (%)
        - efficiency: 效率 (%) - 兼容前端命名
    """

    def __init__(
        self,
        name: str = "Generator",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "mechanical_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w_mechanical": 0.0},
        ]
        default_outlets = [
            {"name": "electrical_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w_electrical": 0.0},
        ]
        default_params = {
            "eta_gen": 0.99,
            "eta_mech": 0.995,
            "rated_power": 660.0,  # MW
            "power_factor": 0.85,
            "station_service_power_rate": 6.0,  # %
            "efficiency": 98.5,  # % - 兼容前端命名
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="generator",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """
        计算发电机输出参数

        步骤:
        1. 获取输入机械功率
        2. 计算电功率: P_elec = P_mech * eta_mech * eta_gen
        """
        eta_gen = self.params.get("eta_gen", 0.99)
        eta_mech = self.params.get("eta_mech", 0.995)

        mech_in = self.get_inlet("mechanical_in")
        if mech_in is None:
            raise ValueError(f"发电机 {self.name}: 未找到机械功率输入 mechanical_in")

        w_mechanical = mech_in.get("w_mechanical", 0.0)  # kW

        # 机械传动损失
        w_after_mech = w_mechanical * eta_mech

        # 电功率
        w_electrical = w_after_mech * eta_gen

        # 损失
        w_loss_mech = w_mechanical - w_after_mech
        w_loss_gen = w_after_mech - w_electrical
        w_loss_total = w_mechanical - w_electrical

        self.results = {
            "w_mechanical": w_mechanical,  # 机械功率 (kW)
            "w_mechanical_mw": w_mechanical / 1000.0,
            "w_electrical": w_electrical,  # 电功率 (kW)
            "w_electrical_mw": w_electrical / 1000.0,
            "w_loss_mech": w_loss_mech,
            "w_loss_gen": w_loss_gen,
            "w_loss_total": w_loss_total,
            "eta_gen": eta_gen,
            "eta_mech": eta_mech,
            "eta_overall": eta_mech * eta_gen,
        }

        # 更新出口端口
        self.set_outlet("electrical_out", {
            "name": "electrical_out",
            "p": 0.0,
            "t": 0.0,
            "h": 0.0,
            "m": 0.0,
            "w_mechanical": w_mechanical,
            "w_electrical": w_electrical,
        })

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Generator":
        """从字典创建发电机实例"""
        return cls(
            name=data.get("name", "Generator"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )
