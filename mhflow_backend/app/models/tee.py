"""MHFlow 三通组件模型"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent


class Tee(BaseComponent):
    """
    三通组件 - 用于流体分流/合流
    
    入口端口:
        - inlet: 进口 (p, t, h, m)
    
    出口端口:
        - outlet1: 出口1 (分流后)
        - outlet2: 出口2 (分流后)
    
    参数:
        - split_ratio: 分流比 (流向outlet1的流量比例，0~1)
    """

    def __init__(
        self,
        name: str = "Tee",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "inlet", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
        ]
        default_outlets = [
            {"name": "outlet1", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
            {"name": "outlet2", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
        ]
        default_params = {
            "split_ratio": 0.5,
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="tee",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """计算三通分流"""
        split_ratio = self.params.get("split_ratio", 0.5)
        
        # 限制分流比范围
        split_ratio = max(0.01, min(0.99, split_ratio))

        # 获取入口参数
        inlet = self.get_inlet("inlet")
        if inlet is None:
            raise ValueError(f"三通 {self.name}: 未找到入口 inlet")

        p_in = inlet.get("p", 0.0)
        t_in = inlet.get("t", 0.0)
        h_in = inlet.get("h", 0.0)
        m_in = inlet.get("m", 0.0)
        s_in = inlet.get("s", 0.0)

        # 分流计算 - 假设等焓分流
        m_out1 = m_in * split_ratio
        m_out2 = m_in * (1 - split_ratio)

        # 更新出口端口
        self.set_outlet("outlet1", {
            "name": "outlet1",
            "p": p_in,
            "t": t_in,
            "h": h_in,
            "m": m_out1,
            "s": s_in,
        })

        self.set_outlet("outlet2", {
            "name": "outlet2",
            "p": p_in,
            "t": t_in,
            "h": h_in,
            "m": m_out2,
            "s": s_in,
        })

        self.results = {
            "m_in": m_in,
            "m_out1": m_out1,
            "m_out2": m_out2,
            "split_ratio": split_ratio,
        }

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tee":
        """从字典创建三通实例"""
        return cls(
            name=data.get("name", "Tee"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )