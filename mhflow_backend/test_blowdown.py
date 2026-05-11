#!/usr/bin/env python3
"""Test effect of blowdown rate on system performance."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.templates.plant_600mw import get_600mw_template
from app.solvers.heat_balance import HeatBalanceSolver

t = get_600mw_template()
for c in t['components']:
    if c['name'] == 'Boiler':
        c['params']['blowdown_rate'] = 0.0

solver = HeatBalanceSolver(t)
result = solver.solve()
perf = result.get('system_performance', {})
comps = result.get('components', {})

print('Blowdown=0%:')
print(f"  P_gross={perf.get('w_electrical_gross_mw',0):.2f} MW")
print(f"  P_net={perf.get('w_electrical_mw',0):.2f} MW")
print(f"  HR={perf.get('heat_rate_kj_kwh',0):.1f}")
print(f"  eta={perf.get('eta_plant',0):.4f}")
print(f"  m_steam={perf.get('main_steam_flow_kg_s',0):.2f} kg/s")
print(f"  coal={perf.get('coal_consumption_rate_g_kwh',0):.1f} g/kWh")

print("\nExtraction flows:")
for name in ['HP_Turbine', 'IP_Turbine', 'LP_Turbine']:
    c = comps.get(name, {})
    for p in c.get('inlet_ports', []):
        if p.get('name') == 'steam_in':
            print(f"  {name} steam_in m={p.get('m',0):.2f}")
    for p in c.get('outlet_ports', []):
        if 'ext' in p.get('name', ''):
            print(f"    {p.get('name')}: m={p.get('m',0):.2f} ({p.get('m_frac',0)*100:.2f}%)")
