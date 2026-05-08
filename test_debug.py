"""调试给水泵流量参数传递"""
import requests
import json

# 加载600MW模板
print("1. 加载600MW模板...")
response = requests.post('http://localhost:8000/api/model/load', json={'template_id': 'plant_600mw'})
result = response.json()
model_data = result.get('model_data', {})

# 查看给水泵信息
print("\n2. 给水泵信息:")
for comp in model_data.get('components', []):
    if 'feed' in comp.get('name', '').lower():
        print(f"   名称: {comp.get('name')}")
        print(f"   类型: {comp.get('component_type')}")
        print(f"   参数: {json.dumps(comp.get('params', {}), indent=4)}")
        print(f"   类型小写: {comp.get('name', '').lower()}")
        print(f"   'feed' in 名称: {'feed' in comp.get('name', '').lower()}")

# 直接检查initial_conditions
print("\n3. 初始条件:")
print(f"   main_steam_flow: {model_data.get('initial_conditions', {}).get('main_steam_flow')}")

# 测试使用不同流量值
print("\n4. 测试不同流量值的影响:")
test_flows = [1800, 1500, 2000]
for flow in test_flows:
    model_copy = json.loads(json.dumps(model_data))
    for comp in model_copy['components']:
        if 'feed' in comp.get('name', '').lower():
            comp['params']['mass_flow'] = flow
    
    response = requests.post('http://localhost:8000/api/solve', json={'model_data': model_copy})
    result = response.json()
    if result.get('status') == 'success':
        power = result['system_performance']['w_electrical_mw']
        print(f"   流量 {flow} t/h -> 发电功率: {power:.2f} MW")
    else:
        print(f"   流量 {flow} t/h -> 计算失败: {result.get('detail')}")
