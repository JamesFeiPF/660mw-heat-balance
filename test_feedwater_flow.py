"""测试给水泵流量参数传递"""
import requests
import json

# 加载600MW模板
print("1. 加载600MW模板...")
try:
    response = requests.post('http://localhost:8000/api/model/load', json={'template_id': 'plant_600mw'})
    print(f"   状态码: {response.status_code}")
    print(f"   响应内容: {response.text[:500]}...")
    result = response.json()
    print(f"   返回状态: {result.get('status')}")
    model_data = result.get('model_data', {})
    print(f"   元件数量: {len(model_data.get('components', []))}")
except Exception as e:
    print(f"   请求失败: {e}")
    exit()

# 查看给水泵的初始参数
feed_pump = None
if 'components' in model_data:
    for comp in model_data['components']:
        if comp.get('id') == 'tpl_feed_pump' or comp.get('name') == 'FeedwaterPump':
            feed_pump = comp
            break

if feed_pump:
    print(f"\n2. 给水泵初始参数: {json.dumps(feed_pump.get('params', {}), indent=2)}")
else:
    print("\n2. 未找到给水泵元件")
    exit()

# 测试1: 使用默认流量计算
print("\n3. 测试1: 使用默认流量计算...")
response = requests.post('http://localhost:8000/api/solve', json={'model_data': model_data})
result1 = response.json()
if result1.get('status') == 'success':
    print(f"   计算成功，发电功率: {result1['system_performance']['w_electrical_mw']:.2f} MW")
else:
    print(f"   计算失败: {result1.get('detail', '未知错误')}")

# 修改给水泵流量参数
print("\n4. 修改给水泵流量为 1500 t/h...")
model_data_modified = json.loads(json.dumps(model_data))  # 深拷贝
for comp in model_data_modified['components']:
    if comp.get('id') == 'tpl_feed_pump' or comp.get('name') == 'FeedwaterPump':
        comp['params']['mass_flow'] = 1500
        print(f"   修改后参数: {json.dumps(comp['params'], indent=2)}")
        break

# 测试2: 使用修改后的流量计算
print("\n5. 测试2: 使用修改后的流量(1500 t/h)计算...")
response = requests.post('http://localhost:8000/api/solve', json={'model_data': model_data_modified})
result2 = response.json()
if result2.get('status') == 'success':
    print(f"   计算成功，发电功率: {result2['system_performance']['w_electrical_mw']:.2f} MW")
else:
    print(f"   计算失败: {result2.get('detail', '未知错误')}")

# 对比结果
if result1.get('status') == 'success' and result2.get('status') == 'success':
    power_diff = result1['system_performance']['w_electrical_mw'] - result2['system_performance']['w_electrical_mw']
    print(f"\n6. 结果对比:")
    print(f"   默认流量: {result1['system_performance']['w_electrical_mw']:.2f} MW")
    print(f"   修改后流量(1500 t/h): {result2['system_performance']['w_electrical_mw']:.2f} MW")
    print(f"   功率变化: {power_diff:.2f} MW")
    if abs(power_diff) > 10:
        print("   ✓ 给水泵流量参数生效！")
    else:
        print("   ✗ 给水泵流量参数未生效")

print("\n测试完成")
