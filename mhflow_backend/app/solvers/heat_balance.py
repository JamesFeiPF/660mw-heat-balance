"""MHFlow 热平衡求解引擎

实现基于双层迭代的热力系统热平衡求解算法。
遵循工业标准流程：锅炉→汽轮机→加热器→凝汽器→水泵

主要改进：
1. 修正计算顺序：从热源（锅炉）开始，正向流向冷端
2. 双层迭代架构：内层-加热器单体热平衡，外层-汽轮机全局功率平衡
3. 多指标联合收敛判据
"""
import copy
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.models import create_component, BaseComponent, Boiler, Turbine, Condenser, Heater, Pump, Pipe, Generator
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t, ph_to_s, saturation_temperature, saturation_properties

logger = logging.getLogger(__name__)


class HeatBalanceSolver:
    """
    热平衡求解引擎（优化版）
    
    求解流程（工业标准）:
    1. 模型构建：JSON解析设备 + 拓扑连接
    2. 边界初始化：主汽流量、初终参数、环境参数、设备设计端差
    3. 迭代求解（双层迭代）
       - 外层：汽轮机通流计算→各级抽汽压力/焓/初抽汽量
       - 内层：按高加→除氧器→低加顺序逐台做热平衡
    4. 更新抽汽份额、给水/疏水流量
    5. 多指标联合收敛（焓值、流量、功率偏差）
    6. 全设备工况结果归集
    7. 整机性能指标：热耗、煤耗、厂用电、循环效率核算
    """

    def __init__(
        self,
        model_data: Dict[str, Any],
        max_outer_iterations: int = 50,
        max_inner_iterations: int = 20,
        convergence_tolerance: float = 0.01,
        power_tolerance: float = 0.1,  # 功率偏差 tolerance (%)
        extraction_tolerance: float = 0.001,  # 抽汽量偏差 tolerance
    ):
        """
        初始化求解器

        参数:
            model_data: JSON模型数据
            max_outer_iterations: 外层最大迭代次数（汽轮机全局平衡）
            max_inner_iterations: 内层最大迭代次数（加热器单体平衡）
            convergence_tolerance: 焓值收敛判据 (kJ/kg)
            power_tolerance: 功率偏差收敛判据 (%)
            extraction_tolerance: 抽汽量偏差收敛判据
        """
        self.model_data = model_data
        self.max_outer_iterations = max_outer_iterations
        self.max_inner_iterations = max_inner_iterations
        self.convergence_tolerance = convergence_tolerance
        self.power_tolerance = power_tolerance
        self.extraction_tolerance = extraction_tolerance

        self.components: Dict[str, BaseComponent] = {}
        self.connections: List[Dict[str, Any]] = []
        self.node_data: Dict[str, Dict[str, Any]] = {}

        self.converged = False
        self.outer_iteration_count = 0
        self.inner_iteration_count = 0
        self.results: Dict[str, Any] = {}

        # 关键状态变量
        self.main_steam_flow = 500.0  # kg/s
        self.feedwater_h = 0.0
        self.prev_feedwater_h = 0.0
        self.prev_extraction_masses: Dict[str, float] = {}
        self.prev_power = 0.0
        self.current_power = 0.0

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

        # 2. 初始化边界条件
        self._initialize_boundary_conditions()

        # 3. 双层迭代求解
        self._double_layer_iteration()

        # 4. 计算系统性能指标
        self._calculate_system_performance()

        logger.info(
            f"热平衡求解完成: {'收敛' if self.converged else '未收敛'}, "
            f"外层迭代: {self.outer_iteration_count}, 内层迭代: {self.inner_iteration_count}"
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

    def _initialize_boundary_conditions(self):
        """初始化边界条件"""
        # 从模型数据获取初始参数
        initial_conditions = self.model_data.get("initial_conditions", {})

        # 设置主蒸汽流量 (优先从给水泵获取)
        self.main_steam_flow = initial_conditions.get("main_steam_flow", 500.0)
        
        for comp_data in self.model_data.get("components", []):
            comp_name = comp_data.get("name", "")
            comp_type = comp_data.get("type", "") or comp_data.get("component_type", "")
            if "feed" in comp_name.lower() and comp_type == "pump":
                mass_flow_tph = comp_data.get("params", {}).get("mass_flow", 0)
                logger.info(f"找到给水泵: {comp_name}, mass_flow={mass_flow_tph} t/h")
                if mass_flow_tph > 0:
                    self.main_steam_flow = mass_flow_tph * 1000 / 3600
                    logger.info(f"从给水泵获取给水流量: {mass_flow_tph} t/h = {self.main_steam_flow:.2f} kg/s")
                    break

        # 初始化给水焓（从锅炉参数估算）
        boiler = self._get_component_by_type("boiler")
        if boiler:
            fw_temp = boiler.params.get("feedwater_temperature", 275.0)
            fw_pressure = boiler.params.get("main_steam_pressure", 28.0) + 2.0  # 给水压力略高于主汽压力
            self.feedwater_h = pt_to_h(fw_pressure, fw_temp)
        else:
            self.feedwater_h = pt_to_h(28.0, 275.0)
        
        self.prev_feedwater_h = self.feedwater_h
        logger.info(f"初始化: 主蒸汽流量={self.main_steam_flow:.2f} kg/s, 给水焓={self.feedwater_h:.2f} kJ/kg")

    def _double_layer_iteration(self):
        """
        双层迭代求解
        - 外层：汽轮机全局功率平衡
        - 内层：加热器单体热平衡
        """
        for outer_iter in range(self.max_outer_iterations):
            self.outer_iteration_count = outer_iter + 1
            logger.info(f"外层迭代 {outer_iter + 1}")

            # === 外层：汽轮机通流计算 ===
            self._outer_turbine_calculation()

            # === 内层：加热器热平衡迭代 ===
            self._inner_heater_iteration()

            # === 检查收敛 ===
            if self._check_convergence():
                self.converged = True
                logger.info(f"在第 {outer_iter + 1} 次外层迭代后收敛")
                break

            # === 更新抽汽份额估计 ===
            self._update_extraction_shares()

        # 收集最终结果
        self._collect_results()

    def _outer_turbine_calculation(self):
        """
        外层：汽轮机通流计算
        
        计算顺序：锅炉 → 汽轮机各级（高→中→低压缸）
        """
        logger.debug("  执行汽轮机通流计算")

        # 1. 计算锅炉
        boilers = [comp for name, comp in self.components.items() if comp.component_type == "boiler"]
        for boiler in boilers:
            self._setup_boiler_inputs(boiler)
            boiler.calculate()
            logger.debug(f"    锅炉计算完成: {boiler.name}")

        # 2. 计算汽轮机（按压力等级从高到低）
        turbines = [comp for name, comp in self.components.items() if comp.component_type == "turbine"]
        # 按蒸汽流动顺序计算：高压缸 → 中压缸 → 低压缸
        sorted_turbines = sorted(turbines, key=lambda t: t.params.get("p_out", 0), reverse=True)
        
        for turbine in sorted_turbines:
            self._setup_turbine_inputs(turbine)
            turbine.calculate()
            
            # 更新抽汽量估计
            self._update_turbine_extractions(turbine)
            logger.debug(f"    汽轮机计算完成: {turbine.name}, p_out={turbine.params.get('p_out', 0):.3f} MPa")

    def _inner_heater_iteration(self):
        """
        内层：加热器热平衡迭代
        
        计算顺序：高加 → 除氧器 → 低加（按压力从高到低）
        """
        logger.debug("  执行加热器热平衡迭代")

        for inner_iter in range(self.max_inner_iterations):
            self.inner_iteration_count += 1
            
            prev_h = self.feedwater_h

            # 1. 高压加热器（按压力从高到低）
            hp_heaters = sorted(
                [h for name, h in self.components.items() 
                 if h.component_type == "heater" and h.params.get("heater_type") == "HP"],
                key=lambda h: h.params.get("p_heater", 0),
                reverse=True
            )
            for heater in hp_heaters:
                self._setup_heater_inputs(heater)
                heater.calculate()
                logger.debug(f"      高加计算: {heater.name}, p={heater.params.get('p_heater', 0):.2f} MPa")

            # 2. 除氧器
            da_heaters = [h for name, h in self.components.items() 
                         if h.component_type == "heater" and h.params.get("heater_type") == "DA"]
            for heater in da_heaters:
                self._setup_heater_inputs(heater)
                heater.calculate()
                logger.debug(f"      除氧器计算: {heater.name}")

            # 3. 低压加热器（按压力从高到低）
            lp_heaters = sorted(
                [h for name, h in self.components.items() 
                 if h.component_type == "heater" and h.params.get("heater_type") == "LP"],
                key=lambda h: h.params.get("p_heater", 0),
                reverse=True
            )
            for heater in lp_heaters:
                self._setup_heater_inputs(heater)
                heater.calculate()
                logger.debug(f"      低加计算: {heater.name}, p={heater.params.get('p_heater', 0):.3f} MPa")

            # 4. 凝汽器
            condensers = [comp for name, comp in self.components.items() if comp.component_type == "condenser"]
            for condenser in condensers:
                self._setup_condenser_inputs(condenser)
                condenser.calculate()

            # 5. 水泵（凝结水泵 → 给水泵）
            pumps = [comp for name, comp in self.components.items() if comp.component_type == "pump"]
            for pump in pumps:
                if "condensate" in pump.name.lower():
                    self._setup_pump_inputs(pump, "condenser")
                elif "feed" in pump.name.lower():
                    self._setup_pump_inputs(pump, "deaerator")
                pump.calculate()

            # 更新给水焓
            self._update_feedwater_enthalpy()

            # 内层收敛检查
            dh = abs(self.feedwater_h - prev_h)
            if dh < self.convergence_tolerance * 0.1:  # 内层更严格
                logger.debug(f"      内层收敛，焓变化: {dh:.4f} kJ/kg")
                break

    def _update_turbine_extractions(self, turbine: Turbine):
        """更新汽轮机抽汽量估计"""
        if hasattr(turbine, 'results') and turbine.results:
            for ext in turbine.results.get("extractions", []):
                ext_name = f"{turbine.name}_{ext.get('name', '')}"
                self.prev_extraction_masses[ext_name] = ext.get("m", 0.0)

    def _update_feedwater_enthalpy(self):
        """更新给水焓值（从最后一级高加出口获取）"""
        hp_heaters = [
            comp for name, comp in self.components.items()
            if comp.component_type == "heater" and comp.params.get("heater_type") == "HP"
        ]

        if hp_heaters:
            # 获取压力最高的高加（最后一级）
            last_hp = max(hp_heaters, key=lambda h: h.params.get("p_heater", 0))
            water_out = last_hp.get_outlet("water_out")
            if water_out:
                self.feedwater_h = water_out.get("h", self.feedwater_h)
                logger.debug(f"      更新给水焓: {self.feedwater_h:.2f} kJ/kg")

    def _check_convergence(self) -> bool:
        """
        多指标联合收敛检查
        
        收敛条件（全部满足）:
        1. 给水焓变化 < tolerance (kJ/kg)
        2. 抽汽量偏差 < extraction_tolerance
        3. 机组功率偏差 < power_tolerance (%)
        """
        # 1. 给水焓变化检查
        dh = abs(self.feedwater_h - self.prev_feedwater_h)
        logger.debug(f"    收敛检查 - 给水焓变化: {dh:.4f} kJ/kg")
        
        if dh > self.convergence_tolerance:
            self.prev_feedwater_h = self.feedwater_h
            return False

        # 2. 抽汽量偏差检查
        extraction_ok = True
        total_extraction = 0.0
        total_extraction_diff = 0.0
        
        for name, comp in self.components.items():
            if comp.component_type == "turbine" and hasattr(comp, 'results') and comp.results:
                for ext in comp.results.get("extractions", []):
                    ext_name = f"{name}_{ext.get('name', '')}"
                    current_m = ext.get("m", 0.0)
                    prev_m = self.prev_extraction_masses.get(ext_name, current_m)
                    diff = abs(current_m - prev_m)
                    total_extraction += current_m
                    total_extraction_diff += diff
                    self.prev_extraction_masses[ext_name] = current_m
        
        if total_extraction > 0:
            avg_diff_ratio = total_extraction_diff / total_extraction
            logger.debug(f"    收敛检查 - 抽汽量平均偏差: {avg_diff_ratio:.6f}")
            if avg_diff_ratio > self.extraction_tolerance:
                extraction_ok = False

        # 3. 功率偏差检查
        power_ok = True
        self._calculate_current_power()
        if self.prev_power > 0:
            power_diff = abs(self.current_power - self.prev_power) / self.prev_power * 100
            logger.debug(f"    收敛检查 - 功率偏差: {power_diff:.4f}%")
            if power_diff > self.power_tolerance:
                power_ok = False
        
        self.prev_power = self.current_power

        # 综合判断
        converged = extraction_ok and power_ok
        if converged:
            logger.debug(f"    所有收敛条件满足")
        
        return converged

    def _calculate_current_power(self):
        """计算当前机组功率"""
        self.current_power = 0.0
        for name, comp in self.components.items():
            if comp.component_type == "turbine" and hasattr(comp, 'results') and comp.results:
                self.current_power += comp.results.get("w_internal", 0.0)

    def _update_extraction_shares(self):
        """更新抽汽份额估计（简化版：根据加热器热负荷调整）"""
        total_heat_load = 0.0
        extraction_adjustments: Dict[str, float] = {}

        for name, comp in self.components.items():
            if comp.component_type == "heater" and hasattr(comp, 'results') and comp.results:
                heat_load = comp.results.get("q_heat", 0.0)
                total_heat_load += heat_load
                extraction_adjustments[name] = heat_load

        # 根据热负荷比例调整抽汽量
        if total_heat_load > 0:
            for name, comp in self.components.items():
                if comp.component_type == "heater" and hasattr(comp, 'results') and comp.results:
                    heat_load = comp.results.get("q_heat", 0.0)
                    ratio = heat_load / total_heat_load
                    # 简单调整抽汽量
                    if ratio > 0:
                        current_ext_m = comp.results.get("extraction_mass", 0.0)
                        target_ext_m = self.main_steam_flow * ratio * 0.3  # 经验系数
                        # 阻尼更新
                        new_ext_m = current_ext_m + 0.3 * (target_ext_m - current_ext_m)
                        comp.results["extraction_mass"] = max(0.0, new_ext_m)

    def _setup_boiler_inputs(self, boiler: Boiler):
        """设置锅炉入口参数"""
        # 给水入口: 从连接关系获取，使用主蒸汽流量
        upstream = self._find_upstream(boiler.name, "feedwater_in")
        if upstream:
            feedwater_in = {**upstream, "m": self.main_steam_flow}
            boiler.set_inlet("feedwater_in", feedwater_in)
        else:
            # 使用当前给水焓作为边界条件
            boiler.set_inlet("feedwater_in", {
                "name": "feedwater_in",
                "p": boiler.params.get("main_steam_pressure", 28.0) + 2.0,
                "h": self.feedwater_h,
                "m": self.main_steam_flow,
            })

        # 再热蒸汽入口: 从高压缸出口获取
        upstream_rh = self._find_upstream(boiler.name, "reheat_in")
        if upstream_rh:
            boiler.set_inlet("reheat_in", upstream_rh)

    def _setup_turbine_inputs(self, turbine: Turbine):
        """设置汽轮机入口参数"""
        upstream = self._find_upstream(turbine.name, "steam_in")
        if upstream:
            turbine.set_inlet("steam_in", upstream)
        else:
            # 从锅炉获取主蒸汽参数
            boiler = self._get_component_by_type("boiler")
            if boiler:
                steam_out = boiler.get_outlet("steam_out")
                if steam_out:
                    turbine.set_inlet("steam_in", steam_out)

    def _setup_heater_inputs(self, heater: Heater):
        """设置加热器入口参数"""
        heater_type = heater.params.get("heater_type", "HP")

        # 被加热水入口
        water_in = self._find_upstream(heater.name, "water_in")
        if water_in:
            heater.set_inlet("water_in", water_in)
        else:
            # 使用默认值
            heater.set_inlet("water_in", {
                "name": "water_in",
                "p": heater.params.get("p_water_out", 1.0),
                "h": self.feedwater_h * 0.8,  # 估计值
                "m": self.main_steam_flow,
            })

        # 蒸汽入口: 从汽轮机抽汽获取
        p_heater = heater.params.get("p_heater", 1.0)
        sat_props = saturation_properties(p_heater)
        
        steam_source = self._find_turbine_extraction(p_heater)
        if steam_source:
            heater.set_inlet("steam_in", steam_source)
        else:
            heater.set_inlet("steam_in", {
                "name": "steam_in",
                "p": p_heater,
                "h": sat_props['h_g'],
                "m": self.main_steam_flow * 0.05,  # 初始估计抽汽量
            })

        # 疏水入口
        drain_in = self._find_upstream(heater.name, "drain_in")
        if drain_in:
            heater.set_inlet("drain_in", drain_in)

    def _setup_condenser_inputs(self, condenser: Condenser):
        """设置凝汽器入口参数"""
        # 获取低压缸排汽
        lp_turbines = [comp for name, comp in self.components.items() 
                       if comp.component_type == "turbine" and comp.params.get("stage") == "LP"]
        
        if lp_turbines:
            lp_turbine = lp_turbines[-1]  # 最后一个低压缸
            exhaust = lp_turbine.get_outlet("steam_out")
            if exhaust and exhaust.get("h", 0) > 0:
                condenser.set_inlet("steam_in", exhaust)
                return

        # 初始估计
        p_cond = condenser.params.get("p_cond", 0.0049)
        sat = saturation_properties(p_cond)
        h_exhaust = sat['h_f'] + 0.88 * (sat['h_g'] - sat['h_f'])
        condenser.set_inlet("steam_in", {
            "name": "steam_in",
            "p": p_cond,
            "h": h_exhaust,
            "m": self.main_steam_flow * 0.85,
        })

    def _setup_pump_inputs(self, pump: Pump, source_type: str):
        """设置水泵入口参数"""
        if source_type == "condenser":
            condensers = [comp for name, comp in self.components.items() if comp.component_type == "condenser"]
            if condensers:
                water_out = condensers[0].get_outlet("water_out")
                if water_out:
                    pump.set_inlet("water_in", water_out)
        elif source_type == "deaerator":
            da_heaters = [h for name, h in self.components.items() 
                         if h.component_type == "heater" and h.params.get("heater_type") == "DA"]
            if da_heaters:
                water_out = da_heaters[0].get_outlet("water_out")
                if water_out:
                    pump.set_inlet("water_in", water_out)

    def _find_upstream(self, component_name: str, port_name: str) -> Optional[Dict[str, Any]]:
        """根据连接关系查找上游元件的出口"""
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

    def _find_turbine_extraction(self, target_pressure: float) -> Optional[Dict[str, Any]]:
        """查找匹配压力的汽轮机抽汽"""
        for name, comp in self.components.items():
            if comp.component_type == "turbine" and hasattr(comp, 'results') and comp.results:
                for ext in comp.results.get("extractions", []):
                    if abs(ext.get("p", 0) - target_pressure) < 0.5:  # 压力容差
                        return ext
        return None

    def _get_component_by_type(self, comp_type: str) -> Optional[BaseComponent]:
        """根据类型获取元件"""
        for name, comp in self.components.items():
            if comp.component_type == comp_type:
                return comp
        return None

    def _collect_results(self):
        """收集所有元件的计算结果"""
        component_results = {}
        for name, comp in self.components.items():
            component_results[name] = comp.to_dict()

        self.results = {
            "converged": self.converged,
            "outer_iteration_count": self.outer_iteration_count,
            "inner_iteration_count": self.inner_iteration_count,
            "components": component_results,
            "system_performance": {},
        }

    def _calculate_system_performance(self):
        """计算系统性能指标"""
        boiler_results = {}
        turbine_results = {}
        generator_results = {}

        for name, comp in self.components.items():
            if comp.component_type == "boiler" and hasattr(comp, 'results') and comp.results:
                boiler_results[name] = comp.results
            elif comp.component_type == "turbine" and hasattr(comp, 'results') and comp.results:
                turbine_results[name] = comp.results
            elif comp.component_type == "generator" and hasattr(comp, 'results') and comp.results:
                generator_results[name] = comp.results

        # 汽轮机总内功率
        w_turbine_internal = sum(res.get("w_internal", 0.0) for res in turbine_results.values())

        # 锅炉总热负荷
        q_boiler = sum(res.get("q_total", 0.0) for res in boiler_results.values())
        eta_boiler = next((res.get("eta_boiler", 0.93) for res in boiler_results.values()), 0.93)

        # 发电机输出功率（考虑机械效率和发电机效率）
        eta_mech = 0.995
        eta_gen = 0.985
        w_electrical = w_turbine_internal * eta_mech * eta_gen

        # 热耗率
        heat_rate = q_boiler / w_electrical * 3600 if w_electrical > 0 else 0.0

        # 全厂热效率
        eta_plant = w_electrical / q_boiler if q_boiler > 0 else 0.0

        # 标准煤耗率
        coal_lhv = 29308.0
        coal_consumption_rate = heat_rate / coal_lhv * 1000 if w_electrical > 0 else 0.0

        # 汽耗率
        steam_rate = self.main_steam_flow * 3600 / w_electrical if w_electrical > 0 else 0.0

        performance = {
            "w_electrical_mw": round(w_electrical / 1000.0, 2),
            "w_electrical_kw": round(w_electrical, 2),
            "w_turbine_internal_mw": round(w_turbine_internal / 1000.0, 2),
            "q_boiler_mw": round(q_boiler / 1000.0, 2),
            "heat_rate_kj_kwh": round(heat_rate, 2),
            "eta_boiler": round(eta_boiler, 4),
            "eta_plant": round(eta_plant, 4),
            "coal_consumption_rate_g_kwh": round(coal_consumption_rate, 2),
            "steam_rate_kg_kwh": round(steam_rate, 4),
            "main_steam_flow_kg_s": round(self.main_steam_flow, 2),
            "main_steam_flow_t_h": round(self.main_steam_flow * 3.6, 2),
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
            if comp.component_type == "turbine" and hasattr(comp, 'results') and comp.results:
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
            if comp.component_type == "heater" and hasattr(comp, 'results') and comp.results:
                heater_balances.append({
                    "name": name,
                    "heater_type": comp.params.get("heater_type", ""),
                    **comp.results,
                })
        return heater_balances
