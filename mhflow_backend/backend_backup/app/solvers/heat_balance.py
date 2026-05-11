"""MHFlow 热平衡求解引擎

实现基于迭代的热力系统热平衡求解算法。
支持一次再热、多级回热抽汽的复杂热力系统。
"""
import copy
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.models import create_component, BaseComponent, Boiler, Turbine, Condenser, Heater, Pump, Pipe, Generator
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t, ph_to_s, saturation_temperature, saturation_properties

logger = logging.getLogger(__name__)


class HeatBalanceSolver:
    """
    热平衡求解引擎

    求解流程:
    1. 从JSON模型数据构建元件列表和连接关系
    2. 初始化各节点参数
    3. 正向计算：从锅炉开始，依次计算各元件出口参数
    4. 回热系统迭代：给定各抽汽压力，迭代计算各级加热器进出水量直到收敛
    5. 输出完整的系统热平衡结果
    """

    def __init__(
        self,
        model_data: Dict[str, Any],
        max_iterations: int = 100,
        convergence_tolerance: float = 0.01,
        damping_factor: float = 0.5,
    ):
        """
        初始化求解器

        参数:
            model_data: JSON模型数据
            max_iterations: 最大迭代次数
            convergence_tolerance: 收敛判据 (kJ/kg)
            damping_factor: 迭代阻尼因子
        """
        self.model_data = model_data
        self.max_iterations = max_iterations
        self.convergence_tolerance = convergence_tolerance
        self.damping_factor = damping_factor

        self.components: Dict[str, BaseComponent] = {}
        self.connections: List[Dict[str, Any]] = []
        self.node_data: Dict[str, Dict[str, Any]] = {}

        self.converged = False
        self.iteration_count = 0
        self.results: Dict[str, Any] = {}

    def solve(self) -> Dict[str, Any]:
        """
        执行热平衡求解

        返回:
            完整的系统热平衡结果
        """
        logger.info("开始热平衡求解...")

        # 1. 构建元件和连接关系
        self._build_components()
        self._build_connections()

        # 2. 初始化
        self._initialize()

        # 3. 迭代求解
        self._iterate()

        # 4. 计算系统性能指标
        self._calculate_system_performance()

        logger.info(
            f"热平衡求解完成: {'收敛' if self.converged else '未收敛'}, "
            f"迭代次数: {self.iteration_count}"
        )

        return self.results

    def _build_components(self):
        """从模型数据构建元件实例"""
        components_data = self.model_data.get("components", [])
        for comp_data in components_data:
            comp = create_component(comp_data)
            self.components[comp.name] = comp
            logger.debug(f"构建元件: {comp.name} ({comp.component_type})")

    def _build_connections(self):
        """构建连接关系"""
        self.connections = self.model_data.get("connections", [])

    def _initialize(self):
        """初始化各节点参数"""
        # 从模型数据获取初始参数
        initial_conditions = self.model_data.get("initial_conditions", {})

        # 设置主蒸汽流量 (如果指定)
        self.main_steam_flow = initial_conditions.get("main_steam_flow", 500.0)  # kg/s (约600MW)

        # 初始化给水参数
        fw_temp = initial_conditions.get("feedwater_temp", 275.0)
        fw_pressure = initial_conditions.get("feedwater_pressure", 28.0)
        fw_h = pt_to_h(fw_pressure, fw_temp)
        fw_s = pt_to_s(fw_pressure, fw_temp)

        self.feedwater_state = {
            "p": fw_pressure,
            "t": fw_temp,
            "h": fw_h,
            "s": fw_s,
            "m": self.main_steam_flow,
        }

        logger.info(f"初始化: 主蒸汽流量={self.main_steam_flow} kg/s, "
                     f"给水温度={fw_temp}°C, 给水压力={fw_pressure} MPa")

    def _iterate(self):
        """
        迭代求解回热系统

        算法:
        1. 假设初始抽汽量分配
        2. 从锅炉开始正向计算
        3. 计算各级加热器热平衡
        4. 更新抽汽量
        5. 检查收敛
        6. 未收敛则回到步骤2
        """
        prev_feedwater_h = self.feedwater_state["h"]

        for iteration in range(self.max_iterations):
            self.iteration_count = iteration + 1
            logger.debug(f"迭代 {iteration + 1}")

            # 正向计算
            self._forward_calculation()

            # 获取当前给水焓
            current_feedwater_h = self._get_current_feedwater_h()

            # 检查收敛
            dh = abs(current_feedwater_h - prev_feedwater_h)
            logger.debug(f"  给水焓变化: {dh:.4f} kJ/kg")

            if dh < self.convergence_tolerance:
                self.converged = True
                logger.info(f"在第 {iteration + 1} 次迭代后收敛")
                break

            # 阻尼更新
            new_feedwater_h = prev_feedwater_h + self.damping_factor * (current_feedwater_h - prev_feedwater_h)
            self.feedwater_state["h"] = new_feedwater_h
            prev_feedwater_h = new_feedwater_h

        # 收集最终结果
        self._collect_results()

    def _forward_calculation(self):
        """
        正向计算：从锅炉开始依次计算各元件

        计算顺序:
        1. 凝汽器 -> 凝结水泵 -> 低压加热器
        2. 除氧器 -> 给水泵 -> 高压加热器
        3. 锅炉
        4. 高压缸 -> 中压缸 -> 低压缸
        5. 发电机
        """
        # 获取计算顺序
        calc_order = self.model_data.get("calculation_order", [])

        if calc_order:
            # 按指定顺序计算
            for comp_name in calc_order:
                if comp_name in self.components:
                    self._calculate_component(comp_name)
        else:
            # 默认计算顺序
            self._default_forward_calculation()

    def _calculate_component(self, comp_name: str):
        """
        计算单个元件

        根据元件类型设置输入参数并执行计算。
        """
        comp = self.components[comp_name]
        comp_type = comp.component_type

        if comp_type == "condenser":
            self._setup_condenser_inputs(comp)
        elif comp_type == "pump":
            if "condensate" in comp_name.lower():
                self._setup_pump_inputs(comp, "condenser")
            elif "feed" in comp_name.lower():
                self._setup_pump_inputs(comp, "deaerator")
            else:
                self._setup_pump_inputs(comp, "condenser")
        elif comp_type == "heater":
            self._setup_heater_inputs(comp)
        elif comp_type == "boiler":
            self._setup_boiler_inputs(comp)
        elif comp_type == "turbine":
            self._setup_turbine_inputs(comp)
        elif comp_type == "generator":
            self._setup_generator_inputs(comp)

        comp.calculate()

    def _default_forward_calculation(self):
        """默认的正向计算流程"""
        # 按元件类型分组
        boilers = []
        turbines = []
        condensers = []
        heaters = []
        pumps = []
        pipes = []
        generators = []

        for name, comp in self.components.items():
            if comp.component_type == "boiler":
                boilers.append(comp)
            elif comp.component_type == "turbine":
                turbines.append(comp)
            elif comp.component_type == "condenser":
                condensers.append(comp)
            elif comp.component_type == "heater":
                heaters.append(comp)
            elif comp.component_type == "pump":
                pumps.append(comp)
            elif comp.component_type == "pipe":
                pipes.append(comp)
            elif comp.component_type == "generator":
                generators.append(comp)

        # 1. 凝汽器
        for comp in condensers:
            self._setup_condenser_inputs(comp)
            comp.calculate()

        # 2. 凝结水泵
        for comp in pumps:
            if "condensate" in comp.name.lower():
                self._setup_pump_inputs(comp, "condenser")
                comp.calculate()

        # 3. 低压加热器 (按压力从低到高)
        lp_heaters = sorted(
            [h for h in heaters if h.params.get("heater_type") == "LP"],
            key=lambda h: h.params.get("p_heater", 0),
        )
        for comp in lp_heaters:
            self._setup_heater_inputs(comp)
            comp.calculate()

        # 4. 除氧器
        da_heaters = [h for h in heaters if h.params.get("heater_type") == "DA"]
        for comp in da_heaters:
            self._setup_heater_inputs(comp)
            comp.calculate()

        # 5. 给水泵
        for comp in pumps:
            if "feed" in comp.name.lower():
                self._setup_pump_inputs(comp, "deaerator")
                comp.calculate()

        # 6. 高压加热器 (按压力从低到高)
        hp_heaters = sorted(
            [h for h in heaters if h.params.get("heater_type") == "HP"],
            key=lambda h: h.params.get("p_heater", 0),
        )
        for comp in hp_heaters:
            self._setup_heater_inputs(comp)
            comp.calculate()

        # 7. 管道
        for comp in pipes:
            comp.calculate()

        # 8. 锅炉
        for comp in boilers:
            self._setup_boiler_inputs(comp)
            comp.calculate()

        # 9. 汽轮机
        for comp in turbines:
            self._setup_turbine_inputs(comp)
            comp.calculate()

        # 10. 发电机
        for comp in generators:
            self._setup_generator_inputs(comp)
            comp.calculate()

    def _setup_condenser_inputs(self, condenser: Condenser):
        """设置凝汽器入口参数"""
        # 获取汽轮机排汽参数
        lp_turbine = None
        for name, comp in self.components.items():
            if comp.component_type == "turbine" and comp.params.get("stage") == "LP":
                lp_turbine = comp
                break

        if lp_turbine and lp_turbine.outlet_ports:
            exhaust = lp_turbine.get_outlet("steam_out")
            if exhaust and exhaust.get("h", 0) > 0:
                condenser.set_inlet("steam_in", exhaust)
                return

        # 首次迭代时汽轮机尚未计算，使用初始估计值
        p_cond = condenser.params.get("p_cond", 0.0049)
        from app.properties.steam import saturation_properties
        sat = saturation_properties(p_cond)
        # 估计排汽焓 (典型值: 湿蒸汽, x≈0.88)
        h_exhaust = sat['h_f'] + 0.88 * (sat['h_g'] - sat['h_f'])
        m_exhaust = self.main_steam_flow * 0.85  # 估计排汽量

        condenser.set_inlet("steam_in", {
            "name": "steam_in",
            "p": p_cond,
            "t": sat['t_sat'],
            "h": h_exhaust,
            "s": sat['s_f'] + 0.88 * (sat['s_g'] - sat['s_f']),
            "m": m_exhaust,
        })

    def _setup_pump_inputs(self, pump: Pump, source_type: str):
        """设置水泵入口参数"""
        # 尝试从连接关系获取
        upstream = self._find_upstream(pump.name, "water_in")
        if upstream:
            pump.set_inlet("water_in", upstream)
            return

        if source_type == "condenser":
            # 凝结水泵: 从凝汽器取水
            for name, comp in self.components.items():
                if comp.component_type == "condenser":
                    water_out = comp.get_outlet("water_out")
                    if water_out and water_out.get("h", 0) > 0:
                        pump.set_inlet("water_in", water_out)
                    break
        elif source_type == "deaerator":
            # 给水泵: 从除氧器取水
            for name, comp in self.components.items():
                if comp.component_type == "heater" and comp.params.get("heater_type") == "DA":
                    water_out = comp.get_outlet("water_out")
                    if water_out and water_out.get("h", 0) > 0:
                        pump.set_inlet("water_in", water_out)
                    break

    def _find_upstream(self, component_name: str, port_name: str) -> Optional[Dict[str, Any]]:
        """
        根据连接关系查找上游元件的出口

        参数:
            component_name: 当前元件名称
            port_name: 当前元件端口名称

        返回:
            上游出口端口数据，或None
        """
        target_key = f"{component_name}.{port_name}"
        for conn in self.connections:
            if conn.get("to", "") == target_key:
                source = conn.get("from", "")
                parts = source.split(".")
                if len(parts) == 2:
                    src_comp_name, src_port_name = parts
                    src_comp = self.components.get(src_comp_name)
                    if src_comp:
                        src_port = src_comp.get_outlet(src_port_name)
                        if src_port and src_port.get("h", 0) > 0:
                            return src_port
        return None

    def _setup_heater_inputs(self, heater: Heater):
        """设置加热器入口参数"""
        heater_type = heater.params.get("heater_type", "HP")
        heater_name = heater.name

        # 被加热水入口: 从上一个元件的出口获取
        # 使用连接关系或默认值
        water_in = heater.get_inlet("water_in")
        if water_in is None or water_in.get("h", 0) == 0:
            # 尝试从连接关系获取
            water_in = self._find_upstream_water(heater_name)
            if water_in:
                heater.set_inlet("water_in", water_in)

        # 蒸汽入口: 从汽轮机抽汽获取
        p_heater = heater.params.get("p_heater", 1.0)
        sat_props = saturation_properties(p_heater)
        h_steam = sat_props['h_g']
        t_steam = sat_props['t_sat']

        # 检查是否有汽轮机抽汽对应
        for name, comp in self.components.items():
            if comp.component_type == "turbine":
                for ext in comp.params.get("extractions", []):
                    if abs(ext.get("p", 0) - p_heater) < 0.5:
                        # 找到对应的抽汽
                        ext_out = comp.get_outlet(ext.get("name", ""))
                        if ext_out and ext_out.get("h", 0) > 0:
                            heater.set_inlet("steam_in", ext_out)
                            return

        # 如果没有找到抽汽，使用饱和蒸汽参数
        steam_in = heater.get_inlet("steam_in")
        if steam_in is None or steam_in.get("h", 0) == 0:
            heater.set_inlet("steam_in", {
                "name": "steam_in",
                "p": p_heater,
                "t": t_steam,
                "h": h_steam,
                "m": 0.0,  # 待迭代确定
            })

    def _find_upstream_water(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        根据连接关系查找上游元件的水出口

        参数:
            component_name: 当前元件名称

        返回:
            上游水出口端口数据，或None
        """
        for conn in self.connections:
            target = conn.get("to", "")
            if target.startswith(f"{component_name}.water_in"):
                source = conn.get("from", "")
                parts = source.split(".")
                if len(parts) == 2:
                    src_comp_name, src_port_name = parts
                    src_comp = self.components.get(src_comp_name)
                    if src_comp:
                        src_port = src_comp.get_outlet(src_port_name)
                        if src_port and src_port.get("h", 0) > 0:
                            return src_port
        return None

    def _setup_boiler_inputs(self, boiler: Boiler):
        """设置锅炉入口参数"""
        # 给水入口: 从连接关系获取
        upstream = self._find_upstream(boiler.name, "feedwater_in")
        if upstream:
            boiler.set_inlet("feedwater_in", upstream)

        # 再热蒸汽入口: 从高压缸出口获取
        upstream_rh = self._find_upstream(boiler.name, "reheat_in")
        if upstream_rh:
            boiler.set_inlet("reheat_in", upstream_rh)

    def _setup_turbine_inputs(self, turbine: Turbine):
        """设置汽轮机入口参数"""
        # 从连接关系获取
        upstream = self._find_upstream(turbine.name, "steam_in")
        if upstream:
            turbine.set_inlet("steam_in", upstream)

    def _setup_generator_inputs(self, generator: Generator):
        """设置发电机入口参数"""
        # 收集所有汽轮机的内功率
        total_w = 0.0
        total_m = 0.0
        for name, comp in self.components.items():
            if comp.component_type == "turbine" and comp.results:
                total_w += comp.results.get("w_internal", 0.0)
                total_m += comp.results.get("m_in", 0.0)

        generator.set_inlet("mechanical_in", {
            "name": "mechanical_in",
            "p": 0.0,
            "t": 0.0,
            "h": 0.0,
            "m": total_m,
            "w_mechanical": total_w,
        })

    def _get_current_feedwater_h(self) -> float:
        """获取当前给水焓值"""
        # 从最后一级高压加热器出口获取
        hp_heaters = [
            comp for name, comp in self.components.items()
            if comp.component_type == "heater" and comp.params.get("heater_type") == "HP"
        ]

        if hp_heaters:
            last_hp = max(hp_heaters, key=lambda h: h.params.get("p_heater", 0))
            water_out = last_hp.get_outlet("water_out")
            if water_out:
                return water_out.get("h", self.feedwater_state["h"])

        return self.feedwater_state["h"]

    def _collect_results(self):
        """收集所有元件的计算结果"""
        component_results = {}
        for name, comp in self.components.items():
            component_results[name] = comp.to_dict()

        self.results = {
            "converged": self.converged,
            "iteration_count": self.iteration_count,
            "components": component_results,
            "system_performance": {},
        }

    def _calculate_system_performance(self):
        """
        计算系统性能指标

        包括:
        - 发电功率
        - 锅炉效率
        - 汽轮机热耗率
        - 全厂热效率
        - 标准煤耗
        - 发电煤耗率
        """
        # 收集各元件结果
        boiler_results = {}
        turbine_results = {}
        generator_results = {}
        condenser_results = {}

        for name, comp in self.components.items():
            if comp.component_type == "boiler" and comp.results:
                boiler_results[name] = comp.results
            elif comp.component_type == "turbine" and comp.results:
                turbine_results[name] = comp.results
            elif comp.component_type == "generator" and comp.results:
                generator_results[name] = comp.results
            elif comp.component_type == "condenser" and comp.results:
                condenser_results[name] = comp.results

        # 发电功率
        w_electrical = 0.0
        for name, res in generator_results.items():
            w_electrical += res.get("w_electrical", 0.0)

        # 汽轮机总内功率
        w_turbine_internal = 0.0
        for name, res in turbine_results.items():
            w_turbine_internal += res.get("w_internal", 0.0)

        # 锅炉总热负荷
        q_boiler = 0.0
        eta_boiler = 0.93
        for name, res in boiler_results.items():
            q_boiler += res.get("q_total", 0.0)
            eta_boiler = res.get("eta_boiler", 0.93)

        # 主蒸汽流量
        m_steam = self.main_steam_flow

        # 热耗率 (kJ/kWh)
        if w_electrical > 0:
            heat_rate = q_boiler / w_electrical * 3600  # kJ/kWh
        else:
            heat_rate = 0.0

        # 全厂热效率
        if q_boiler > 0:
            eta_plant = w_electrical / q_boiler
        else:
            eta_plant = 0.0

        # 管道效率 (简化)
        eta_pipe = 0.99

        # 汽轮机内效率
        if q_boiler > 0:
            eta_turbine_cycle = w_turbine_internal / q_boiler
        else:
            eta_turbine_cycle = 0.0

        # 标准煤耗率 (g/kWh)
        # 标准煤低位发热量: 29308 kJ/kg
        coal_lhv = 29308.0
        if w_electrical > 0:
            coal_consumption_rate = heat_rate / coal_lhv * 1000  # g/kWh
        else:
            coal_consumption_rate = 0.0

        # 年发电量 (假设年利用小时数 5500h)
        annual_hours = 5500
        annual_generation = w_electrical / 1000.0 * annual_hours  # MWh
        annual_coal = coal_consumption_rate * w_electrical / 1000.0 * annual_hours / 1000.0  # 吨

        # 汽耗率 (kg/kWh)
        if w_electrical > 0:
            steam_rate = m_steam * 3600 / w_electrical
        else:
            steam_rate = 0.0

        performance = {
            "w_electrical_mw": round(w_electrical / 1000.0, 2),
            "w_electrical_kw": round(w_electrical, 2),
            "w_turbine_internal_mw": round(w_turbine_internal / 1000.0, 2),
            "q_boiler_mw": round(q_boiler / 1000.0, 2),
            "q_boiler_kw": round(q_boiler, 2),
            "heat_rate_kj_kwh": round(heat_rate, 2),
            "eta_boiler": round(eta_boiler, 4),
            "eta_pipe": round(eta_pipe, 4),
            "eta_turbine_cycle": round(eta_turbine_cycle, 4),
            "eta_plant": round(eta_plant, 4),
            "coal_consumption_rate_g_kwh": round(coal_consumption_rate, 2),
            "steam_rate_kg_kwh": round(steam_rate, 4),
            "main_steam_flow_kg_s": round(m_steam, 2),
            "main_steam_flow_t_h": round(m_steam * 3.6, 2),
            "annual_generation_mwh": round(annual_generation, 0),
            "annual_coal_tons": round(annual_coal, 0),
        }

        self.results["system_performance"] = performance

    def get_node_data(self) -> Dict[str, Dict[str, Any]]:
        """获取所有节点的热力参数"""
        nodes = {}
        for name, comp in self.components.items():
            for port in comp.outlet_ports:
                node_name = f"{name}.{port.get('name', 'out')}"
                nodes[node_name] = {
                    "component": name,
                    "port": port.get("name", ""),
                    "p": port.get("p", 0.0),
                    "t": port.get("t", 0.0),
                    "h": port.get("h", 0.0),
                    "s": port.get("s", 0.0),
                    "m": port.get("m", 0.0),
                }
        return nodes

    def get_extraction_data(self) -> List[Dict[str, Any]]:
        """获取抽汽参数汇总"""
        extractions = []
        for name, comp in self.components.items():
            if comp.component_type == "turbine" and comp.results:
                for ext in comp.results.get("extractions", []):
                    extractions.append({
                        "turbine": name,
                        **ext,
                    })
        return extractions

    def get_heater_balance(self) -> List[Dict[str, Any]]:
        """获取加热器热平衡汇总"""
        heater_balances = []
        for name, comp in self.components.items():
            if comp.component_type == "heater" and comp.results:
                heater_balances.append({
                    "name": name,
                    "heater_type": comp.params.get("heater_type", ""),
                    **comp.results,
                })
        return heater_balances
