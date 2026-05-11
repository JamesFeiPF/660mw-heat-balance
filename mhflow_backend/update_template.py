#!/usr/bin/env python3
"""Update plant_600mw.py template to match reference values."""

with open('app/templates/plant_600mw.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Document header
content = content.replace(
    """系统参数:
- 主蒸汽: 25.0 MPa, 600°C
- 再热蒸汽: 4.5 MPa, 600°C
- 8级回热抽汽 (3高加 + 1除氧 + 4低加)
- 凝汽器压力: 4.9 kPa
- 锅炉效率: 93%
- 汽轮机效率: HP 88%, IP 90%, LP 88%
- 发电机效率: 99%""",
    """系统参数(对标660MW设计值):
- 主蒸汽: 28.0 MPa, 600°C
- 再热蒸汽: 5.48 MPa, 610°C
- 8级回热抽汽 (3高加 + 1除氧 + 4低加)
- 凝汽器压力: 11 kPa
- 锅炉效率: 95%
- 汽轮机效率: HP 87.9%, IP 88.3%, LP 87%
- 发电机效率: 99.5%""")

# 2. Initial conditions
content = content.replace(
    '"main_steam_flow": 480.0,  # kg/s (约1728 t/h)',
    '"main_steam_flow": 501.6,  # kg/s (约1805.8 t/h)')
content = content.replace(
    '"condenser_pressure": 0.0049,  # MPa',
    '"condenser_pressure": 0.011,  # MPa (11 kPa)')

# 3. Boiler
content = content.replace(
    '{"name": "feedwater_in", "p": 30.0, "t": 295.0, "h": 0.0, "m": 500.0},',
    '{"name": "feedwater_in", "p": 30.0, "t": 295.0, "h": 0.0, "m": 501.6},')
content = content.replace(
    '{"name": "steam_out", "p": 27.0, "t": 600.0, "h": 0.0, "m": 500.0},',
    '{"name": "steam_out", "p": 28.0, "t": 600.0, "h": 0.0, "m": 501.6},')
content = content.replace(
    '{"name": "reheat_out", "p": 4.5, "t": 610.0, "h": 0.0, "m": 0.0},',
    '{"name": "reheat_out", "p": 5.48, "t": 610.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"main_steam_pressure": 27.0,',
    '"main_steam_pressure": 28.0,')

# 4. HP Turbine
content = content.replace(
    '{"name": "steam_in", "p": 27.0, "t": 600.0, "h": 0.0, "m": 500.0},',
    '{"name": "steam_in", "p": 28.0, "t": 600.0, "h": 0.0, "m": 501.6},')
content = content.replace(
    '{"name": "steam_out", "p": 4.5, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_out", "p": 5.78, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"eta_isen": 0.88,\n                    "p_out": 4.5,',
    '"eta_isen": 0.879,\n                    "p_out": 5.78,')
content = content.replace(
    '{"name": "ext_hp1", "p": 8.0, "m_frac": 0.082},  # 第1级抽汽(高加1)',
    '{"name": "ext_hp1", "p": 7.741, "m_frac": 0.082},  # 第1级抽汽(高加1)')
content = content.replace(
    '{"name": "ext_hp2", "p": 5.2, "m_frac": 0.078},  # 第2级抽汽(高加2)',
    '{"name": "ext_hp2", "p": 5.893, "m_frac": 0.078},  # 第2级抽汽(高加2)')
content = content.replace(
    '{"name": "ext_hp3", "p": 4.5, "m_frac": 0.035},  # 第3级抽汽(高加3)',
    '{"name": "ext_hp3", "p": 5.78, "m_frac": 0.035},  # 第3级抽汽(高加3/再热冷段)')

# 5. IP Turbine
content = content.replace(
    '{"name": "steam_in", "p": 4.5, "t": 600.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 5.48, "t": 610.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"eta_isen": 0.90,\n                    "p_out": 1.0,',
    '"eta_isen": 0.883,\n                    "p_out": 1.0,')
content = content.replace(
    '{"name": "ext_ip1", "p": 2.5, "m_frac": 0.060},  # 第4级抽汽(除氧器)',
    '{"name": "ext_ip1", "p": 2.936, "m_frac": 0.060},  # 第4级抽汽(除氧器)')
content = content.replace(
    '{"name": "ext_ip2", "p": 1.5, "m_frac": 0.035},  # 第5级抽汽(低加5)',
    '{"name": "ext_ip2", "p": 1.239, "m_frac": 0.035},  # 第5级抽汽(低加5)')

# 6. LP Turbine
content = content.replace(
    '"eta_isen": 0.88,\n                    "p_out": 0.0049,',
    '"eta_isen": 0.87,\n                    "p_out": 0.011,')
content = content.replace(
    '{"name": "ext_lp1", "p": 0.6, "m_frac": 0.030},  # 第6级抽汽(低加6)',
    '{"name": "ext_lp1", "p": 0.523, "m_frac": 0.030},  # 第6级抽汽(低加6)')
content = content.replace(
    '{"name": "ext_lp2", "p": 0.25, "m_frac": 0.025},  # 第7级抽汽(低加7)',
    '{"name": "ext_lp2", "p": 0.26, "m_frac": 0.025},  # 第7级抽汽(低加7)')
content = content.replace(
    '{"name": "ext_lp3", "p": 0.08, "m_frac": 0.020},  # 第8级抽汽(低加8)',
    '{"name": "ext_lp3", "p": 0.11, "m_frac": 0.020},  # 第8级抽汽(低加8)')

# 7. Condenser
content = content.replace(
    '{"name": "steam_in", "p": 0.0049, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 0.011, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '{"name": "water_out", "p": 0.0049, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "water_out", "p": 0.011, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_cond": 0.0049,',
    '"p_cond": 0.011,')

# 8. Condensate Pump
content = content.replace(
    '{"name": "water_out", "p": 1.6, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "water_out", "p": 2.5, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"eta_pump": 0.82,\n                    "p_out": 1.6,',
    '"eta_pump": 0.65,\n                    "p_out": 2.5,')

# 9. LP Heaters
content = content.replace(
    '{"name": "steam_in", "p": 0.08, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 0.11, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_heater": 0.08,\n                    "p_water_out": 1.5,',
    '"p_heater": 0.11,\n                    "p_water_out": 1.5,')
content = content.replace(
    '{"name": "steam_in", "p": 0.25, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 0.26, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_heater": 0.25,\n                    "p_water_out": 1.5,',
    '"p_heater": 0.26,\n                    "p_water_out": 1.5,')
content = content.replace(
    '{"name": "steam_in", "p": 0.6, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 0.523, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_heater": 0.6,\n                    "p_water_out": 1.5,',
    '"p_heater": 0.523,\n                    "p_water_out": 1.5,')
content = content.replace(
    '{"name": "steam_in", "p": 1.5, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 1.239, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_heater": 1.5,\n                    "p_water_out": 1.5,',
    '"p_heater": 1.239,\n                    "p_water_out": 1.5,')

# 10. Feedwater Pump
content = content.replace(
    '{"name": "water_out", "p": 29.0, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "water_out", "p": 31.0, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"eta_pump": 0.83,\n                    "p_out": 29.0,',
    '"eta_pump": 0.65,\n                    "p_out": 31.0,')

# 11. HP Heaters
content = content.replace(
    '{"name": "steam_in", "p": 4.5, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 5.78, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_heater": 4.5,\n                    "p_water_out": 28.0,',
    '"p_heater": 5.78,\n                    "p_water_out": 28.0,')
content = content.replace(
    '{"name": "steam_in", "p": 5.2, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 5.893, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_heater": 5.2,\n                    "p_water_out": 28.0,',
    '"p_heater": 5.893,\n                    "p_water_out": 28.0,')
content = content.replace(
    '{"name": "steam_in", "p": 8.0, "t": 0.0, "h": 0.0, "m": 0.0},',
    '{"name": "steam_in", "p": 7.741, "t": 0.0, "h": 0.0, "m": 0.0},')
content = content.replace(
    '"p_heater": 8.0,\n                    "p_water_out": 28.0,',
    '"p_heater": 7.741,\n                    "p_water_out": 28.0,')

# 12. TTD adjustments
content = content.replace(
    '"ttd": 3.0,\n                    "dca": 5.0,\n                    "eta": 0.99,\n                    "p_heater": 7.741',
    '"ttd": 4.5,\n                    "dca": 5.0,\n                    "eta": 0.99,\n                    "p_heater": 7.741')
content = content.replace(
    '"ttd": 3.0,\n                    "dca": 5.0,\n                    "eta": 0.99,\n                    "p_heater": 5.893',
    '"ttd": 4.2,\n                    "dca": 5.0,\n                    "eta": 0.99,\n                    "p_heater": 5.893')
content = content.replace(
    '"ttd": 3.0,\n                    "dca": 5.0,\n                    "eta": 0.99,\n                    "p_heater": 5.78',
    '"ttd": 3.9,\n                    "dca": 5.0,\n                    "eta": 0.99,\n                    "p_heater": 5.78')

# 13. Generator
content = content.replace(
    '"eta_gen": 0.99,\n                    "eta_mech": 0.995,',
    '"eta_gen": 0.995,\n                    "eta_mech": 0.995,')

with open('app/templates/plant_600mw.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Template updated successfully')
