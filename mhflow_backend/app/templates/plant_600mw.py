"""MHFlow 600MW超超临界机组模板

定义一个典型的600MW超超临界一次再热机组热力系统模型。

系统参数(对标660MW设计值):
- 主蒸汽: 28.0 MPa, 600°C
- 再热蒸汽: 5.48 MPa, 610°C
- 8级回热抽汽 (3高加 + 1除氧 + 4低加)
- 凝汽器压力: 11 kPa
- 锅炉效率: 95%
- 汽轮机效率: HP 87.9%, IP 88.3%, LP 87%
- 发电机效率: 99.5%
"""
from typing import Dict, Any


def get_600mw_template() -> Dict[str, Any]:
    """
    获取600MW超超临界一次再热机组完整模型

    返回:
        完整的JSON模型数据
    """
    model = {
        "name": "600MW超超临界一次再热机组",
        "description": "典型600MW超超临界一次再热凝汽式汽轮发电机组热力系统模型",
        "capacity_mw": 600,
        "initial_conditions": {
            "main_steam_flow": 501.6,  # kg/s (约1805.8 t/h)
            "feedwater_temp": 295.0,  # °C
            "feedwater_pressure": 30.0,  # MPa
            "condenser_pressure": 0.011,  # MPa (11 kPa)
        },
        "components": [
            # ===== 锅炉 =====
            {
                "component_type": "boiler",
                "name": "Boiler",
                "inlet_ports": [
                    {"name": "feedwater_in", "p": 30.0, "t": 295.0, "h": 0.0, "m": 501.6},
                    {"name": "reheat_in", "p": 4.5, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "steam_out", "p": 28.0, "t": 600.0, "h": 0.0, "m": 501.6},
                    {"name": "reheat_out", "p": 5.48, "t": 610.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "boiler_efficiency": 95.0,
                    "blowdown_rate": 0.0,
                    "fuel_lower_heating_value": 21000.0,
                    "main_steam_pressure": 28.0,
                    "main_steam_temperature": 600.0,
                    "reheat_pressure_drop": 0.3,
                    "reheat_temperature": 610.0,
                },
            },

            # ===== 高压缸 =====
            {
                "component_type": "turbine",
                "name": "HP_Turbine",
                "inlet_ports": [
                    {"name": "steam_in", "p": 28.0, "t": 600.0, "h": 0.0, "m": 501.6},
                    {"name": "power_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w": 0.0},
                ],
                "outlet_ports": [
                    {"name": "steam_out", "p": 5.78, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "power_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w": 0.0},
                ],
                "params": {
                    "eta_isen": 0.879,
                    "p_out": 5.78,
                    "stage": "HP",
                    "extractions": [
                        {"name": "ext_hp1", "p": 7.741, "m_frac": 0.082},  # 第1级抽汽(高加1)
                        {"name": "ext_hp2", "p": 5.893, "m_frac": 0.078},  # 第2级抽汽(高加2)
                        {"name": "ext_hp3", "p": 5.78, "m_frac": 0.035},  # 第3级抽汽(高加3/再热冷段)
                    ],
                },
            },

            # ===== 中压缸 =====
            {
                "component_type": "turbine",
                "name": "IP_Turbine",
                "inlet_ports": [
                    {"name": "steam_in", "p": 5.48, "t": 610.0, "h": 0.0, "m": 0.0},
                    {"name": "power_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w": 0.0},
                ],
                "outlet_ports": [
                    {"name": "steam_out", "p": 1.0, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "power_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w": 0.0},
                ],
                "params": {
                    "eta_isen": 0.883,
                    "p_out": 1.0,
                    "stage": "IP",
                    "extractions": [
                        {"name": "ext_ip1", "p": 2.936, "m_frac": 0.060},  # 第4级抽汽(除氧器)
                        {"name": "ext_ip2", "p": 1.239, "m_frac": 0.035},  # 第5级抽汽(低加5)
                    ],
                },
            },

            # ===== 低压缸 =====
            {
                "component_type": "turbine",
                "name": "LP_Turbine",
                "inlet_ports": [
                    {"name": "steam_in", "p": 1.0, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "power_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w": 0.0},
                ],
                "outlet_ports": [
                    {"name": "steam_out", "p": 0.0049, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "power_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w": 0.0},
                ],
                "params": {
                    "eta_isen": 0.87,
                    "p_out": 0.011,
                    "stage": "LP",
                    "extractions": [
                        {"name": "ext_lp1", "p": 0.523, "m_frac": 0.030},  # 第6级抽汽(低加6)
                        {"name": "ext_lp2", "p": 0.26, "m_frac": 0.025},  # 第7级抽汽(低加7)
                        {"name": "ext_lp3", "p": 0.11, "m_frac": 0.020},  # 第8级抽汽(低加8)
                    ],
                },
            },

            # ===== 凝汽器 =====
            {
                "component_type": "condenser",
                "name": "Condenser",
                "inlet_ports": [
                    {"name": "steam_in", "p": 0.011, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "cooling_in", "p": 0.1, "t": 20.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 0.011, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "cooling_out", "p": 0.1, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "ttd": 5.0,
                    "delta_t_cw": 10.0,
                    "p_cond": 0.011,
                    "eta_heat_transfer": 0.98,
                },
            },

            # ===== 凝结水泵 =====
            {
                "component_type": "pump",
                "name": "CondensatePump",
                "inlet_ports": [
                    {"name": "water_in", "p": 0.0049, "t": 33.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 2.5, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "eta_pump": 0.65,
                    "p_out": 2.5,
                    "eta_motor": 0.95,
                },
            },

            # ===== 低压加热器 =====
            {
                "component_type": "heater",
                "name": "LP_Heater_8",
                "inlet_ports": [
                    {"name": "water_in", "p": 1.5, "t": 35.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 0.11, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 1.5, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 0.08, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "LP",
                    "ttd": 3.0,
                    "dca": 5.0,
                    "eta": 0.99,
                    "p_heater": 0.11,
                    "p_water_out": 1.5,
                },
            },
            {
                "component_type": "heater",
                "name": "LP_Heater_7",
                "inlet_ports": [
                    {"name": "water_in", "p": 1.5, "t": 55.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 0.26, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 1.5, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 0.25, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "LP",
                    "ttd": 3.0,
                    "dca": 5.0,
                    "eta": 0.99,
                    "p_heater": 0.26,
                    "p_water_out": 1.5,
                },
            },
            {
                "component_type": "heater",
                "name": "LP_Heater_6",
                "inlet_ports": [
                    {"name": "water_in", "p": 1.5, "t": 80.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 0.523, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 1.5, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 0.6, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "LP",
                    "ttd": 3.0,
                    "dca": 5.0,
                    "eta": 0.99,
                    "p_heater": 0.523,
                    "p_water_out": 1.5,
                },
            },
            {
                "component_type": "heater",
                "name": "LP_Heater_5",
                "inlet_ports": [
                    {"name": "water_in", "p": 1.5, "t": 110.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 1.239, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 1.5, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 1.5, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "LP",
                    "ttd": 3.0,
                    "dca": 5.0,
                    "eta": 0.99,
                    "p_heater": 1.239,
                    "p_water_out": 1.5,
                },
            },

            # ===== 除氧器 =====
            {
                "component_type": "heater",
                "name": "Deaerator",
                "inlet_ports": [
                    {"name": "water_in", "p": 0.8, "t": 140.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 0.8, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 0.8, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 0.8, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "DA",
                    "ttd": 0.0,
                    "dca": 0.0,
                    "eta": 0.99,
                    "p_heater": 0.8,
                    "p_water_out": 0.8,
                },
            },

            # ===== 给水泵 =====
            {
                "component_type": "pump",
                "name": "FeedwaterPump",
                "inlet_ports": [
                    {"name": "water_in", "p": 0.8, "t": 170.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 31.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "eta_pump": 0.65,
                    "p_out": 31.0,
                    "eta_motor": 0.95,
                    "mass_flow": 1800,  # 给水流量 t/h（约500 kg/s），用于变工况计算
                },
            },

            # ===== 高压加热器 =====
            {
                "component_type": "heater",
                "name": "HP_Heater_3",
                "inlet_ports": [
                    {"name": "water_in", "p": 28.0, "t": 195.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 5.78, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 28.0, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 4.5, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "HP",
                    "ttd": 3.9,
                    "dca": 5.0,
                    "eta": 0.99,
                    "p_heater": 5.78,
                    "p_water_out": 28.0,
                },
            },
            {
                "component_type": "heater",
                "name": "HP_Heater_2",
                "inlet_ports": [
                    {"name": "water_in", "p": 28.0, "t": 230.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 5.893, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 28.0, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 5.2, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "HP",
                    "ttd": 4.2,
                    "dca": 5.0,
                    "eta": 0.99,
                    "p_heater": 5.893,
                    "p_water_out": 28.0,
                },
            },
            {
                "component_type": "heater",
                "name": "HP_Heater_1",
                "inlet_ports": [
                    {"name": "water_in", "p": 28.0, "t": 260.0, "h": 0.0, "m": 0.0},
                    {"name": "steam_in", "p": 6.2, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "outlet_ports": [
                    {"name": "water_out", "p": 28.0, "t": 0.0, "h": 0.0, "m": 0.0},
                    {"name": "drain_out", "p": 6.2, "t": 0.0, "h": 0.0, "m": 0.0},
                ],
                "params": {
                    "heater_type": "HP",
                    "ttd": 4.5,
                    "dca": 5.0,
                    "eta": 0.99,
                    "p_heater": 7.741,
                    "p_water_out": 28.0,
                },
            },

            # ===== 发电机 =====
            {
                "component_type": "generator",
                "name": "Generator",
                "inlet_ports": [
                    {"name": "mechanical_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w_mechanical": 0.0},
                ],
                "outlet_ports": [
                    {"name": "electrical_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w_electrical": 0.0},
                ],
                "params": {
                    "eta_gen": 0.995,
                    "eta_mech": 0.995,
                },
            },
        ],

        "connections": [
            # 锅炉 -> 高压缸
            {"from": "Boiler.steam_out", "to": "HP_Turbine.steam_in"},
            # 高压缸排汽 -> 锅炉再热
            {"from": "HP_Turbine.steam_out", "to": "Boiler.reheat_in"},
            # 锅炉再热 -> 中压缸
            {"from": "Boiler.reheat_out", "to": "IP_Turbine.steam_in"},
            # 中压缸排汽 -> 低压缸
            {"from": "IP_Turbine.steam_out", "to": "LP_Turbine.steam_in"},
            # 低压缸排汽 -> 凝汽器
            {"from": "LP_Turbine.steam_out", "to": "Condenser.steam_in"},
            # 凝汽器 -> 凝结水泵
            {"from": "Condenser.water_out", "to": "CondensatePump.water_in"},
            # 凝结水泵 -> 低加8
            {"from": "CondensatePump.water_out", "to": "LP_Heater_8.water_in"},
            # 低加8 -> 低加7
            {"from": "LP_Heater_8.water_out", "to": "LP_Heater_7.water_in"},
            # 低加7 -> 低加6
            {"from": "LP_Heater_7.water_out", "to": "LP_Heater_6.water_in"},
            # 低加6 -> 低加5
            {"from": "LP_Heater_6.water_out", "to": "LP_Heater_5.water_in"},
            # 低加5 -> 除氧器
            {"from": "LP_Heater_5.water_out", "to": "Deaerator.water_in"},
            # 除氧器 -> 给水泵
            {"from": "Deaerator.water_out", "to": "FeedwaterPump.water_in"},
            # 给水泵 -> 高加3
            {"from": "FeedwaterPump.water_out", "to": "HP_Heater_3.water_in"},
            # 高加3 -> 高加2
            {"from": "HP_Heater_3.water_out", "to": "HP_Heater_2.water_in"},
            # 高加2 -> 高加1
            {"from": "HP_Heater_2.water_out", "to": "HP_Heater_1.water_in"},
            # 高加1 -> 锅炉
            {"from": "HP_Heater_1.water_out", "to": "Boiler.feedwater_in"},
            # 抽汽连接
            {"from": "HP_Turbine.ext_hp1", "to": "HP_Heater_1.steam_in"},
            {"from": "HP_Turbine.ext_hp2", "to": "HP_Heater_2.steam_in"},
            {"from": "HP_Turbine.ext_hp3", "to": "HP_Heater_3.steam_in"},
            {"from": "IP_Turbine.ext_ip1", "to": "Deaerator.steam_in"},
            {"from": "IP_Turbine.ext_ip2", "to": "LP_Heater_5.steam_in"},
            {"from": "LP_Turbine.ext_lp1", "to": "LP_Heater_6.steam_in"},
            {"from": "LP_Turbine.ext_lp2", "to": "LP_Heater_7.steam_in"},
            {"from": "LP_Turbine.ext_lp3", "to": "LP_Heater_8.steam_in"},
            # 疏水连接 (逐级自流)
            {"from": "HP_Heater_1.drain_out", "to": "HP_Heater_2.drain_in"},
            {"from": "HP_Heater_2.drain_out", "to": "HP_Heater_3.drain_in"},
            {"from": "HP_Heater_3.drain_out", "to": "Deaerator.drain_in"},
            {"from": "LP_Heater_5.drain_out", "to": "LP_Heater_6.drain_in"},
            {"from": "LP_Heater_6.drain_out", "to": "LP_Heater_7.drain_in"},
            {"from": "LP_Heater_7.drain_out", "to": "LP_Heater_8.drain_in"},
            # 功率连接（缸体串联）
            {"from": "HP_Turbine.power_out", "to": "IP_Turbine.power_in"},
            {"from": "IP_Turbine.power_out", "to": "LP_Turbine.power_in"},
            {"from": "LP_Turbine.power_out", "to": "Generator.mechanical_in"},
        ],

        "calculation_order": [
            "Condenser",
            "CondensatePump",
            "LP_Heater_8",
            "LP_Heater_7",
            "LP_Heater_6",
            "LP_Heater_5",
            "Deaerator",
            "FeedwaterPump",
            "HP_Heater_3",
            "HP_Heater_2",
            "HP_Heater_1",
            "Boiler",
            "HP_Turbine",
            "IP_Turbine",
            "LP_Turbine",
            "Generator",
        ],
    }

    return model
