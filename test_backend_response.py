"""测试后端响应参数变化"""
import requests
import json

# 加载模板
response = requests.post('http://localhost:8000/api/model/load', json={'template_id': 'plant_600mw'})
result = response.json()
model_data = result.get('model_data', {})

# 测试不同流量值
print("测试后端对不同流量参数的响应:")
print("-" * 60)

test_cases = [
    {'mass_flow': 1800, 'expected_power': 566},  # 原始值
    {'mass_flow': 1500, 'expected_power': 472},  # 减小流量
    {'mass_flow': 2000, 'expected_power': 629},  # 增大流量
    {'mass_flow': 3000, 'expected_power': 944},  # 大幅增大
]

for tc in test_cases:
    # 深拷贝模型数据
    model_copy = json.loads(json.dumps(model_data))
    
    # 修改给水泵流量
    for comp in model_copy['components']:
        if 'feed' in comp.get('name', '').lower():
            comp['params']['mass_flow'] = tc['mass_flow']
    
    # 发送请求
    response = requests.post('http://localhost:8000/api/solve', json={'model_data': model_copy})
    result = response.json()
    
    if result.get('status') == 'success':
        power = result['system_performance']['w_electrical_mw']
        print(f"流量: {tc['mass_flow']} t/h -> 发电功率: {power:.2f} MW (预期: ~{tc['expected_power']} MW)")
    else:
        print(f"流量: {tc['mass_flow']} t/h -> 计算失败: {result.get('detail')}")

print("-" * 60)
print("测试完成")
