"""MHFlow 管道/混合器/分流器模型"""
from typing import Dict, Any, Optional, List
from .base import BaseComponent
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t, ph_to_s


class Pipe(BaseComponent):
    """
    管道/混合器/分流器模型

    支持三种模式:
    - pipe: 简单管道，考虑压力损失和温度损失
    - mixer: 混合器，将多股流体混合为一股
    - splitter: 分流器，将一股流体分为多股

    管道模式:
        入口: fluid_in
        出口: fluid_out
        参数: dp (压力损失, MPa), dt (温度损失, °C)

    混合器模式:
        入口: fluid_in_1, fluid_in_2, ...
        出口: fluid_out
        参数: mode="mixer", p_out (混合后压力)

    分流器模式:
        入口: fluid_in
        出口: fluid_out_1, fluid_out_2, ...
        参数: mode="splitter", split_ratios [质量分数列表]
    """

    def __init__(
        self,
        name: str = "Pipe",
        inlet_ports: Optional[List[Dict[str, Any]]] = None,
        outlet_ports: Optional[List[Dict[str, Any]]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        default_inlets = [
            {"name": "fluid_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_outlets = [
            {"name": "fluid_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ]
        default_params = {
            "mode": "pipe",
            "dp": 0.0,  # 压力损失 MPa
            "dt": 0.0,  # 温度损失 °C
            "p_out": 0.0,  # 混合器出口压力
            "split_ratios": [],  # 分流比例
        }

        if inlet_ports is None:
            inlet_ports = default_inlets
        if outlet_ports is None:
            outlet_ports = default_outlets
        if params is None:
            params = default_params

        super().__init__(
            name=name,
            component_type="pipe",
            inlet_ports=inlet_ports,
            outlet_ports=outlet_ports,
            params=params,
        )

    def calculate(self) -> Dict[str, Any]:
        """
        计算管道/混合器/分流器出口参数
        """
        mode = self.params.get("mode", "pipe")

        if mode == "mixer":
            return self._calculate_mixer()
        elif mode == "splitter":
            return self._calculate_splitter()
        else:
            return self._calculate_pipe()

    def _calculate_pipe(self) -> Dict[str, Any]:
        """简单管道计算"""
        dp = self.params.get("dp", 0.0)
        dt = self.params.get("dt", 0.0)

        fluid_in = self.get_inlet("fluid_in")
        if fluid_in is None:
            raise ValueError(f"管道 {self.name}: 未找到流体入口 fluid_in")

        p_in = fluid_in.get("p", 0.0)
        t_in = fluid_in.get("t", 0.0)
        h_in = fluid_in.get("h", 0.0)
        m = fluid_in.get("m", 0.0)

        # 出口参数
        p_out = p_in - dp
        t_out = t_in - dt

        # 出口焓
        if p_out > 0 and t_out > 0:
            h_out = pt_to_h(p_out, t_out)
            s_out = pt_to_s(p_out, t_out)
        else:
            h_out = h_in
            s_out = fluid_in.get("s", 0.0)

        self.results = {
            "mode": "pipe",
            "dp": dp,
            "dt": dt,
            "pressure_loss_pct": (dp / p_in * 100) if p_in > 0 else 0.0,
        }

        self.set_outlet("fluid_out", {
            "name": "fluid_out",
            "p": p_out,
            "t": t_out,
            "h": h_out,
            "s": s_out,
            "m": m,
        })

        return self.to_dict()

    def _calculate_mixer(self) -> Dict[str, Any]:
        """混合器计算"""
        p_out_target = self.params.get("p_out", 0.0)

        # 收集所有入口
        total_m = 0.0
        total_h_m = 0.0  # m * h 的总和
        total_s_m = 0.0

        for port in self.inlet_ports:
            m = port.get("m", 0.0)
            h = port.get("h", 0.0)
            s = port.get("s", 0.0)
            total_m += m
            total_h_m += m * h
            total_s_m += m * s

        if total_m <= 0:
            raise ValueError(f"混合器 {self.name}: 总流量为零")

        # 混合后焓
        h_out = total_h_m / total_m
        s_out = total_s_m / total_m

        # 混合后压力 (取最低入口压力或指定压力)
        p_min = min(port.get("p", 0.0) for port in self.inlet_ports if port.get("p", 0.0) > 0)
        p_out = p_out_target if p_out_target > 0 else p_min

        # 混合后温度
        t_out = ph_to_t(p_out, h_out)

        self.results = {
            "mode": "mixer",
            "total_m": total_m,
            "h_out": h_out,
            "p_out": p_out,
        }

        self.set_outlet("fluid_out", {
            "name": "fluid_out",
            "p": p_out,
            "t": t_out,
            "h": h_out,
            "s": s_out,
            "m": total_m,
        })

        return self.to_dict()

    def _calculate_splitter(self) -> Dict[str, Any]:
        """分流器计算"""
        split_ratios = self.params.get("split_ratios", [])

        fluid_in = self.get_inlet("fluid_in")
        if fluid_in is None:
            raise ValueError(f"分流器 {self.name}: 未找到流体入口 fluid_in")

        p_in = fluid_in.get("p", 0.0)
        t_in = fluid_in.get("t", 0.0)
        h_in = fluid_in.get("h", 0.0)
        s_in = fluid_in.get("s", 0.0)
        m_in = fluid_in.get("m", 0.0)

        # 分流 (等焓等温)
        total_ratio = sum(split_ratios) if split_ratios else 1.0
        if total_ratio <= 0:
            total_ratio = 1.0

        for i, ratio in enumerate(split_ratios):
            m_out = m_in * ratio / total_ratio
            self.set_outlet(f"fluid_out_{i + 1}", {
                "name": f"fluid_out_{i + 1}",
                "p": p_in,
                "t": t_in,
                "h": h_in,
                "s": s_in,
                "m": m_out,
            })

        self.results = {
            "mode": "splitter",
            "m_in": m_in,
            "split_ratios": split_ratios,
        }

        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pipe":
        """从字典创建管道实例"""
        return cls(
            name=data.get("name", "Pipe"),
            inlet_ports=data.get("inlet_ports"),
            outlet_ports=data.get("outlet_ports"),
            params=data.get("params"),
        )
