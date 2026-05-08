"""测试完整的前后端交互流程"""
import requests
import json

print("=== 测试完整求解流程 ===\n")

# 1. 加载模板
print("1. 加载600MW模板...")
response = requests.post('http://localhost:8000/api/model/load', json={'template_id': 'plant_600mw'})
result = response.json()
model_data = result.get('model_data', {})
print(f"   状态: {result.get('status')}, 元件数: {len(model_data.get('components', []))}")

# 2. 修改锅炉参数
print("\n2. 修改锅炉主蒸汽温度为600°C...")
for comp in model_data['components']:
    if comp.get('name') == 'Boiler':
        comp['params']['main_steam_temperature'] = 600
        print(f"   修改成功: main_steam_temperature = {comp['params']['main_steam_temperature']}°C")
        break

# 3. 执行求解
print("\n3. 执行求解...")
response = requests.post('http://localhost:8000/api/solve', json={'model_data': model_data})
result = response.json()

if result.get('status') == 'success':
    perf = result.get('system_performance', {})
    print(f"   ✅ 计算成功")
    print(f"   发电功率: {perf.get('w_electrical_mw', 0):.2f} MW")
    print(f"   锅炉热负荷: {perf.get('q_boiler_mw', 0):.2f} MW")
    print(f"   收敛迭代: {result.get('iteration_count', 0)} 次")
    
    # 检查锅炉结果
    boiler_result = result.get('components', {}).get('Boiler', {})
    print(f"\n   锅炉出口参数:")
    for port in boiler_result.get('outlet_ports', []):
        print(f"     {port.get('name')}: p={port.get('p', 0):.2f} MPa, t={port.get('t', 0):.1f}°C, h={port.get('h', 0):.0f} kJ/kg")
else:
    print(f"   ❌ 计算失败: {result.get('detail')}")

print("\n=== 测试完成 ===")
