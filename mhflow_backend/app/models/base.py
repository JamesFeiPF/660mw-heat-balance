"""MHFlow 元件抽象基类"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseComponent(ABC):
    """
    热力系统元件抽象基类

    所有热力系统元件（锅炉、汽轮机、凝汽器等）的基类，
    定义了统一的接口和序列化方法。

    端口数据格式:
        {"name": str, "p": float(MPa), "t": float(°C),
         "h": float(kJ/kg), "m": float(kg/s), "s": float(kJ/(kg·K))}
    """

    def __init__(
        self,
        name: str,
        component_type: str,
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化元件

        参数:
            name: 元件名称
            component_type: 元件类型 (boiler/turbine/condenser/heater/pump/pipe/generator)
            inlet_ports: 入口端口列表
            outlet_ports: 出口端口列表
            params: 设备参数
        """
        self.name = name
        self.component_type = component_type
        self.inlet_ports = inlet_ports or []
        self.outlet_ports = outlet_ports or []
        self.params = params or {}
        self.results: Dict[str, Any] = {}  # 计算结果

    @abstractmethod
    def calculate(self) -> Dict[str, Any]:
        """
        根据入口参数和设备参数，计算出口参数

        返回:
            包含计算结果的字典，至少包含更新后的 outlet_ports
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为JSON兼容字典

        返回:
            包含完整元件信息的字典
        """
        return {
            "component_type": self.component_type,
            "name": self.name,
            "inlet_ports": self.inlet_ports,
            "outlet_ports": self.outlet_ports,
            "params": self.params,
            "results": self.results,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseComponent":
        """
        从JSON兼容字典反序列化

        参数:
            data: 包含元件信息的字典

        返回:
            元件实例
        """
        # 支持两种字段名: type (前端) 和 component_type (后端)
        component_type = data.get("component_type", "") or data.get("type", "unknown")
        return cls(
            name=data.get("name", "unnamed"),
            component_type=component_type,
            inlet_ports=data.get("inlet_ports", []),
            outlet_ports=data.get("outlet_ports", []),
            params=data.get("params", {}),
        )

    def get_inlet(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定名称的入口端口"""
        for port in self.inlet_ports:
            if port.get("name") == name:
                return port
        return None

    def get_outlet(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定名称的出口端口"""
        for port in self.outlet_ports:
            if port.get("name") == name:
                return port
        return None

    def set_inlet(self, name: str, port_data: Dict[str, Any]):
        """设置指定名称的入口端口"""
        # 确保端口数据使用指定的名称
        data = dict(port_data)
        data["name"] = name
        for i, port in enumerate(self.inlet_ports):
            if port.get("name") == name:
                self.inlet_ports[i] = data
                return
        # 如果不存在则添加
        self.inlet_ports.append(data)

    def set_outlet(self, name: str, port_data: Dict[str, Any]):
        """设置指定名称的出口端口"""
        # 确保端口数据使用指定的名称
        data = dict(port_data)
        data["name"] = name
        for i, port in enumerate(self.outlet_ports):
            if port.get("name") == name:
                self.outlet_ports[i] = data
                return
        self.outlet_ports.append(data)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, type={self.component_type})>"
