#!/usr/bin/env python3
"""Test new 660MW template parameters."""
import sys, json, requests

sys.stdout.reconfigure(encoding='utf-8')

url = 'http://localhost:8000'

def post(endpoint, data):
    r = requests.post(f'{url}{endpoint}', json=data, timeout=30)
    return r.json()

# Load template
r = requests.get(f'{url}/api/templates/600mw').json()
if r.get('status') != 'success':
    print('Template load failed:', r)
    sys.exit(1)
model = r['data']

# Update params
model['components'][0]['params']['main_steam_pressure'] = 28.0
model['components'][0]['params']['main_steam_temperature'] = 600.0
model['components'][0]['params']['reheat_temperature'] = 610.0

# Solve
result = post('/api/solve', {'model': model})
if result.get('status') != 'success':
    print('Solve failed:', result.get('message', 'unknown'))
    sys.exit(1)

summary = result['data']['summary']
print('=== New Results (28MPa/600C/610C/11kPa) ===')
print(f'Power output: {summary.get("power_output", 0):.2f} MW')
print(f'Heat rate: {summary.get("heat_rate", 0):.1f} kJ/kWh')
print(f'Thermal efficiency: {summary.get("thermal_efficiency", 0):.2f} %')
print(f'Coal consumption: {summary.get("coal_consumption", 0):.1f} g/kWh')
print(f'Feedwater temp: {summary.get("feedwater_temperature", 0):.1f} C')
print(f'Feedwater flow: {summary.get("feedwater_flow", 0):.1f} t/h')
