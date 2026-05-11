"""MHFlow 热平衡求解器测试"""
import sys
import os
import math

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.properties.steam import (
    pt_to_h, pt_to_s, ph_to_t, ph_to_s, ps_to_t,
    saturation_temperature, saturation_pressure,
    saturation_properties, get_steam_properties,
    IAPWS_AVAILABLE,
)
from app.models import (
    Boiler, Turbine, Condenser, Heater, Pump, Pipe, Generator,
)
from app.solvers.heat_balance import HeatBalanceSolver
from app.templates.plant_600mw import get_600mw_template


def test_steam_properties():
    """测试水蒸汽物性计算"""
    print("=" * 60)
    print("测试水蒸汽物性计算")
    print(f"IAPWS库可用: {IAPWS_AVAILABLE}")
    print("=" * 60)

    # 测试1: 饱和水 (0.1 MPa, 99°C - 亚冷水)
    p = 0.1
    t = 99.0
    h = pt_to_h(p, t)
    s = pt_to_s(p, t)
    print(f"\n[测试1] 亚冷水 p={p} MPa, t={t}°C")
    print(f"  h = {h:.2f} kJ/kg (参考值: ~414.0 kJ/kg)")
    print(f"  s = {s:.4f} kJ/(kg·K) (参考值: ~1.306 kJ/(kg·K))")
    assert 300 < h < 500, f"亚冷水焓值异常: {h}"
    assert 1.0 < s < 2.0, f"亚冷水熵值异常: {s}"

    # 测试2: 过热蒸汽 (1.0 MPa, 500°C)
    p = 1.0
    t = 500.0
    h = pt_to_h(p, t)
    s = pt_to_s(p, t)
    print(f"\n[测试2] 过热蒸汽 p={p} MPa, t={t}°C")
    print(f"  h = {h:.2f} kJ/kg (参考值: ~3478.0 kJ/kg)")
    print(f"  s = {s:.4f} kJ/(kg·K) (参考值: ~7.764 kJ/(kg·K))")
    assert 3000 < h < 4000, f"过热蒸汽焓值异常: {h}"
    assert 7.0 < s < 9.0, f"过热蒸汽熵值异常: {s}"

    # 测试3: 主蒸汽参数 (25.0 MPa, 600°C)
    p = 25.0
    t = 600.0
    h = pt_to_h(p, t)
    s = pt_to_s(p, t)
    print(f"\n[测试3] 超超临界主蒸汽 p={p} MPa, t={t}°C")
    print(f"  h = {h:.2f} kJ/kg (参考值: ~3497.0 kJ/kg)")
    print(f"  s = {s:.4f} kJ/(kg·K) (参考值: ~6.345 kJ/(kg·K))")
    assert 3000 < h < 4000, f"主蒸汽焓值异常: {h}"

    # 测试4: ph_to_t
    p = 1.0
    h = 3478.0
    t = ph_to_t(p, h)
    print(f"\n[测试4] ph_to_t: p={p} MPa, h={h} kJ/kg")
    print(f"  t = {t:.2f}°C (参考值: ~500°C)")
    assert 400 < t < 600, f"ph_to_t结果异常: {t}"

    # 测试5: 饱和温度
    p = 0.0049  # 凝汽器压力
    t_sat = saturation_temperature(p)
    print(f"\n[测试5] 饱和温度: p={p} MPa")
    print(f"  t_sat = {t_sat:.2f}°C (参考值: ~32.5°C)")
    assert 25 < t_sat < 45, f"饱和温度异常: {t_sat}"

    # 测试6: 饱和压力
    t = 100.0
    p_sat = saturation_pressure(t)
    print(f"\n[测试6] 饱和压力: t={t}°C")
    print(f"  p_sat = {p_sat:.6f} MPa (参考值: ~0.1013 MPa)")
    assert 0.05 < p_sat < 0.2, f"饱和压力异常: {p_sat}"

    # 测试7: 饱和参数
    p = 1.0
    sat = saturation_properties(p)
    print(f"\n[测试7] 饱和参数: p={p} MPa")
    print(f"  t_sat = {sat['t_sat']:.2f}°C")
    print(f"  h_f = {sat['h_f']:.2f} kJ/kg")
    print(f"  h_g = {sat['h_g']:.2f} kJ/kg")
    print(f"  s_f = {sat['s_f']:.4f} kJ/(kg·K)")
    print(f"  s_g = {sat['s_g']:.4f} kJ/(kg·K)")

    # 测试8: 完整物性
    props = get_steam_properties(25.0, 600.0)
    print(f"\n[测试8] 完整物性: p=25.0 MPa, t=600°C")
    for key, value in props.items():
        print(f"  {key} = {value}")

    print("\n物性测试通过!")


def test_boiler():
    """测试锅炉模型"""
    print("\n" + "=" * 60)
    print("测试锅炉模型")
    print("=" * 60)

    boiler = Boiler(
        name="TestBoiler",
        inlet_ports=[
            {"name": "feedwater_in", "p": 29.0, "t": 275.0, "h": 1200.0, "m": 480.0},
            {"name": "reheat_in", "p": 4.5, "t": 300.0, "h": 3100.0, "m": 400.0},
        ],
        params={
            "eta_boiler": 0.93,
            "fuel_lhv": 21000.0,
            "p_out": 25.0,
            "t_out": 600.0,
            "p_reheat_out": 4.5,
            "t_reheat_out": 600.0,
        },
    )

    result = boiler.calculate()
    print(f"主蒸汽出口: p={result['outlet_ports'][0]['p']} MPa, "
          f"t={result['outlet_ports'][0]['t']}°C, "
          f"h={result['outlet_ports'][0]['h']:.2f} kJ/kg")
    print(f"锅炉热负荷: {boiler.results['q_total']:.2f} kW")
    print(f"燃料消耗量: {boiler.results['b_fuel']:.4f} kg/s")

    assert boiler.results['q_total'] > 0, "锅炉热负荷应为正"
    print("锅炉模型测试通过!")


def test_turbine():
    """测试汽轮机模型"""
    print("\n" + "=" * 60)
    print("测试汽轮机模型")
    print("=" * 60)

    turbine = Turbine(
        name="TestTurbine_HP",
        inlet_ports=[
            {"name": "steam_in", "p": 25.0, "t": 600.0, "h": 3500.0, "m": 480.0},
        ],
        params={
            "eta_isen": 0.88,
            "p_out": 4.5,
            "stage": "HP",
            "extractions": [
                {"name": "ext1", "p": 7.2, "m_frac": 0.08},
            ],
        },
    )

    result = turbine.calculate()
    print(f"排汽: p={result['outlet_ports'][0]['p']} MPa, "
          f"t={result['outlet_ports'][0]['t']:.2f}°C, "
          f"h={result['outlet_ports'][0]['h']:.2f} kJ/kg")
    print(f"内功率: {turbine.results['w_internal']:.2f} kW")
    print(f"内功率: {turbine.results['w_internal_mw']:.2f} MW")

    assert turbine.results['w_internal'] > 0, "汽轮机功率应为正"
    print("汽轮机模型测试通过!")


def test_condenser():
    """测试凝汽器模型"""
    print("\n" + "=" * 60)
    print("测试凝汽器模型")
    print("=" * 60)

    condenser = Condenser(
        name="TestCondenser",
        inlet_ports=[
            {"name": "steam_in", "p": 0.0049, "t": 33.0, "h": 2400.0, "m": 400.0},
            {"name": "cooling_in", "p": 0.1, "t": 20.0, "h": 84.0, "m": 0.0},
        ],
        params={
            "ttd": 5.0,
            "delta_t_cw": 10.0,
            "p_cond": 0.0049,
            "eta_heat_transfer": 0.98,
        },
    )

    result = condenser.calculate()
    print(f"凝结水出口: p={result['outlet_ports'][0]['p']} MPa, "
          f"t={result['outlet_ports'][0]['t']:.2f}°C, "
          f"h={result['outlet_ports'][0]['h']:.2f} kJ/kg")
    print(f"冷却水量: {condenser.results['m_cw']:.2f} kg/s")
    print(f"冷却水量: {condenser.results['m_cw_hour']:.2f} t/h")

    assert condenser.results['q_cond'] > 0, "凝汽器热负荷应为正"
    print("凝汽器模型测试通过!")


def test_pump():
    """测试水泵模型"""
    print("\n" + "=" * 60)
    print("测试水泵模型")
    print("=" * 60)

    pump = Pump(
        name="TestPump",
        inlet_ports=[
            {"name": "water_in", "p": 0.0049, "t": 33.0, "h": 140.0, "m": 400.0},
        ],
        params={
            "eta_pump": 0.85,
            "p_out": 1.6,
            "eta_motor": 0.95,
        },
    )

    result = pump.calculate()
    print(f"出口: p={result['outlet_ports'][0]['p']} MPa, "
          f"t={result['outlet_ports'][0]['t']:.2f}°C, "
          f"h={result['outlet_ports'][0]['h']:.2f} kJ/kg")
    print(f"轴功率: {pump.results['p_shaft']:.2f} kW")

    assert pump.results['p_shaft'] > 0, "泵功率应为正"
    print("水泵模型测试通过!")


def test_heater():
    """测试加热器模型"""
    print("\n" + "=" * 60)
    print("测试加热器模型")
    print("=" * 60)

    # 表面式加热器
    heater_hp = Heater(
        name="TestHP_Heater",
        inlet_ports=[
            {"name": "water_in", "p": 28.0, "t": 230.0, "h": 990.0, "m": 400.0},
            {"name": "steam_in", "p": 5.2, "t": 260.0, "h": 2900.0, "m": 0.0},
            {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ],
        params={
            "heater_type": "HP",
            "ttd": 3.0,
            "dca": 5.0,
            "eta": 0.99,
            "p_heater": 5.2,
            "p_water_out": 28.0,
        },
    )

    result = heater_hp.calculate()
    print(f"[高加] 出口水: t={result['outlet_ports'][0]['t']:.2f}°C, "
          f"h={result['outlet_ports'][0]['h']:.2f} kJ/kg")
    print(f"[高加] 抽汽量: {heater_hp.results['m_steam']:.4f} kg/s")

    # 混合式加热器 (除氧器)
    heater_da = Heater(
        name="TestDA",
        inlet_ports=[
            {"name": "water_in", "p": 0.8, "t": 140.0, "h": 590.0, "m": 400.0},
            {"name": "steam_in", "p": 0.8, "t": 170.0, "h": 2700.0, "m": 0.0},
            {"name": "drain_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0},
        ],
        params={
            "heater_type": "DA",
            "ttd": 0.0,
            "dca": 0.0,
            "eta": 0.99,
            "p_heater": 0.8,
            "p_water_out": 0.8,
        },
    )

    result = heater_da.calculate()
    print(f"[除氧器] 出口水: t={result['outlet_ports'][0]['t']:.2f}°C, "
          f"h={result['outlet_ports'][0]['h']:.2f} kJ/kg")
    print(f"[除氧器] 抽汽量: {heater_da.results['m_steam']:.4f} kg/s")

    print("加热器模型测试通过!")


def test_generator():
    """测试发电机模型"""
    print("\n" + "=" * 60)
    print("测试发电机模型")
    print("=" * 60)

    generator = Generator(
        name="TestGenerator",
        inlet_ports=[
            {"name": "mechanical_in", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "w_mechanical": 600000.0},
        ],
        params={
            "eta_gen": 0.99,
            "eta_mech": 0.995,
        },
    )

    result = generator.calculate()
    print(f"电功率: {generator.results['w_electrical']:.2f} kW")
    print(f"电功率: {generator.results['w_electrical_mw']:.2f} MW")
    print(f"总效率: {generator.results['eta_overall']:.4f}")

    assert generator.results['w_electrical'] > 0, "发电机功率应为正"
    assert generator.results['w_electrical_mw'] > 590, "发电机功率应接近600MW"
    print("发电机模型测试通过!")


def test_pipe():
    """测试管道模型"""
    print("\n" + "=" * 60)
    print("测试管道模型")
    print("=" * 60)

    # 简单管道
    pipe = Pipe(
        name="TestPipe",
        inlet_ports=[
            {"name": "fluid_in", "p": 5.0, "t": 400.0, "h": 3200.0, "m": 100.0},
        ],
        params={
            "mode": "pipe",
            "dp": 0.1,
            "dt": 2.0,
        },
    )

    result = pipe.calculate()
    print(f"[管道] 出口: p={result['outlet_ports'][0]['p']} MPa, "
          f"t={result['outlet_ports'][0]['t']:.2f}°C")

    # 混合器
    mixer = Pipe(
        name="TestMixer",
        inlet_ports=[
            {"name": "fluid_in_1", "p": 1.0, "t": 200.0, "h": 850.0, "m": 50.0},
            {"name": "fluid_in_2", "p": 1.0, "t": 150.0, "h": 635.0, "m": 50.0},
        ],
        params={
            "mode": "mixer",
        },
    )

    result = mixer.calculate()
    print(f"[混合器] 出口: t={result['outlet_ports'][0]['t']:.2f}°C, "
          f"h={result['outlet_ports'][0]['h']:.2f} kJ/kg, "
          f"m={result['outlet_ports'][0]['m']:.2f} kg/s")

    print("管道模型测试通过!")


def test_solver():
    """测试600MW机组热平衡求解"""
    print("\n" + "=" * 60)
    print("测试600MW机组热平衡求解")
    print("=" * 60)

    # 加载模板
    model_data = get_600mw_template()
    print(f"模型名称: {model_data['name']}")
    print(f"元件数量: {len(model_data['components'])}")
    print(f"连接数量: {len(model_data['connections'])}")

    # 创建求解器
    solver = HeatBalanceSolver(
        model_data=model_data,
        max_outer_iterations=50,
        convergence_tolerance=0.01,
    )

    # 执行求解
    results = solver.solve()

    # 输出结果
    print(f"\n收敛状态: {'收敛' if results['converged'] else '未收敛'}")
    print(f"外层迭代次数: {results['outer_iteration_count']}")
    print(f"内层迭代次数: {results['inner_iteration_count']}")

    perf = results.get("system_performance", {})
    print(f"\n系统性能指标:")
    print(f"  发电功率: {perf.get('w_electrical_mw', 0):.2f} MW")
    print(f"  汽轮机内功率: {perf.get('w_turbine_internal_mw', 0):.2f} MW")
    print(f"  锅炉热负荷: {perf.get('q_boiler_mw', 0):.2f} MW")
    print(f"  热耗率: {perf.get('heat_rate_kj_kwh', 0):.2f} kJ/kWh")
    print(f"  锅炉效率: {perf.get('eta_boiler', 0) * 100:.2f}%")
    print(f"  全厂效率: {perf.get('eta_plant', 0) * 100:.2f}%")
    print(f"  标准煤耗率: {perf.get('coal_consumption_rate_g_kwh', 0):.2f} g/kWh")
    print(f"  主蒸汽流量: {perf.get('main_steam_flow_t_h', 0):.2f} t/h")

    # 输出节点参数
    print(f"\n节点参数:")
    node_data = solver.get_node_data()
    for node_name, node in node_data.items():
        if node.get("m", 0) > 0:
            print(f"  {node_name}: p={node['p']:.4f} MPa, "
                  f"t={node['t']:.2f}°C, "
                  f"h={node['h']:.2f} kJ/kg, "
                  f"m={node['m']:.2f} kg/s")

    print("\n求解器测试完成!")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#" * 60)
    print("# MHFlow 热力系统仿真软件 - 单元测试")
    print("#" * 60)

    tests = [
        ("水蒸汽物性", test_steam_properties),
        ("锅炉模型", test_boiler),
        ("汽轮机模型", test_turbine),
        ("凝汽器模型", test_condenser),
        ("水泵模型", test_pump),
        ("加热器模型", test_heater),
        ("发电机模型", test_generator),
        ("管道模型", test_pipe),
        ("600MW求解器", test_solver),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n[PASS] {name}")
        except Exception as e:
            failed += 1
            print(f"\n[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "#" * 60)
    print(f"# 测试结果: {passed} 通过, {failed} 失败, 共 {passed + failed} 项")
    print("#" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
