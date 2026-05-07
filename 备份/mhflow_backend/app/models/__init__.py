"""MHFlow 元件模型包"""
from .base import BaseComponent
from .boiler import Boiler
from .turbine import Turbine
from .condenser import Condenser
from .heater import Heater
from .pump import Pump
from .pipe import Pipe
from .generator import Generator

__all__ = [
    "BaseComponent",
    "Boiler",
    "Turbine",
    "Condenser",
    "Heater",
    "Pump",
    "Pipe",
    "Generator",
]

# 元件类型注册表
COMPONENT_REGISTRY = {
    "boiler": Boiler,
    "turbine": Turbine,
    "condenser": Condenser,
    "heater": Heater,
    "pump": Pump,
    "pipe": Pipe,
    "generator": Generator,
}


def create_component(data: dict) -> "BaseComponent":
    """
    根据JSON数据创建元件实例

    参数:
        data: 包含 type 或 component_type 字段的字典

    返回:
        对应的元件实例
    """
    # 支持两种字段名: type (前端) 和 component_type (后端)
    component_type = data.get("component_type", "") or data.get("type", "")
    cls = COMPONENT_REGISTRY.get(component_type)
    if cls is None:
        raise ValueError(f"未知的元件类型: {component_type}")
    return cls.from_dict(data)
