#!/usr/bin/env python3
"""Test effect of varying HP3 ttd on system performance."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.templates.plant_600mw import get_600mw_template
from app.solvers.heat_balance import HeatBalanceSolver

def run_with_hp3_ttd(ttd_val):
    t = get_600mw_template()
    # Find HP_Heater_3 and modify ttd
    for c in t['components']:
        if c['name'] == 'HP_Heater_3':
            c['params']['ttd'] = ttd_val
    
    solver = HeatBalanceSolver(t)
    result = solver.solve()
    perf = result.get('system_performance', {})
    comps = result.get('components', {})
    
    hp3 = comps.get('HP_Heater_3', {})
    hp3_steam = 0
    for p in hp3.get('inlet_ports', []):
        if p.get('name') == 'steam_in':
            hp3_steam = p.get('m', 0)
    
    return {
        'ttd': ttd_val,
        'power_gross': perf.get('w_electrical_gross_mw', 0),
        'power_net': perf.get('w_electrical_mw', 0),
        'heat_rate': perf.get('heat_rate_kj_kwh', 0),
        'efficiency': perf.get('eta_plant', 0),
        'hp3_steam': hp3_steam,
        'reheat_flow': comps.get('Boiler', {}).get('outlet_ports', [{}])[1].get('m', 0),
    }

print("Testing HP3 ttd sweep...")
print(f"{'ttd':>6} {'P_gross':>10} {'P_net':>10} {'HR':>10} {'eta':>8} {'HP3_stm':>10} {'RH_flow':>10}")
for ttd in [3.9, 10, 20, 30, 40, 50, 80, 100]:
    r = run_with_hp3_ttd(ttd)
    print(f"{r['ttd']:>6.1f} {r['power_gross']:>10.2f} {r['power_net']:>10.2f} {r['heat_rate']:>10.1f} {r['efficiency']:>8.4f} {r['hp3_steam']:>10.2f} {r['reheat_flow']:>10.2f}")
