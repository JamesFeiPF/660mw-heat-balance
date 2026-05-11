#!/usr/bin/env python3
"""Test effect of pump efficiency on system performance."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.templates.plant_600mw import get_600mw_template
from app.solvers.heat_balance import HeatBalanceSolver

def run_with_pump_eff(feed_eff, cond_eff):
    t = get_600mw_template()
    for c in t['components']:
        if c['name'] == 'FeedwaterPump':
            c['params']['eta_pump'] = feed_eff
        if c['name'] == 'CondensatePump':
            c['params']['eta_pump'] = cond_eff
    
    solver = HeatBalanceSolver(t)
    result = solver.solve()
    perf = result.get('system_performance', {})
    
    return {
        'feed_eff': feed_eff,
        'cond_eff': cond_eff,
        'power_gross': perf.get('w_electrical_gross_mw', 0),
        'power_net': perf.get('w_electrical_mw', 0),
        'heat_rate': perf.get('heat_rate_kj_kwh', 0),
        'efficiency': perf.get('eta_plant', 0),
        'pump_power': perf.get('pump_power_mw', 0),
    }

print("Testing pump efficiency sweep...")
print(f"{'feed':>6} {'cond':>6} {'P_gross':>10} {'P_net':>10} {'HR':>10} {'eta':>8} {'pump':>10}")
for feed_eff in [0.65, 0.75, 0.85]:
    for cond_eff in [0.65, 0.75, 0.85]:
        r = run_with_pump_eff(feed_eff, cond_eff)
        print(f"{r['feed_eff']:>6.2f} {r['cond_eff']:>6.2f} {r['power_gross']:>10.2f} {r['power_net']:>10.2f} {r['heat_rate']:>10.1f} {r['efficiency']:>8.4f} {r['pump_power']:>10.2f}")
