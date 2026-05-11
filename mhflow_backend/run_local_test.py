#!/usr/bin/env python3
"""Run heat balance calculation locally with new template."""
import sys, traceback
sys.stdout.reconfigure(encoding='utf-8')

from app.templates.plant_600mw import get_600mw_template
from app.solvers.heat_balance import HeatBalanceSolver

t = get_600mw_template()

# Print initial conditions
print("=== Initial Conditions ===")
print(f"main_steam_flow: {t['initial_conditions']['main_steam_flow']} kg/s")
print(f"condenser_pressure: {t['initial_conditions']['condenser_pressure']} MPa")

# Solve
try:
    solver = HeatBalanceSolver(t)
    result = solver.solve()
    print(f"\nConverged: {result.get('converged')}")
    print(f"Outer iterations: {result.get('outer_iteration_count')}")
    print(f"Inner iterations: {result.get('inner_iteration_count')}")
    
    perf = result.get('system_performance', {})
    print("\n=== System Performance ===")
    for k, v in perf.items():
        print(f"  {k}: {v}")
    
    components = result['components']
    print("\n=== Turbine Details ===")
    for name in ['HP_Turbine', 'IP_Turbine', 'LP_Turbine']:
        c = components.get(name, {})
        print(f"\n{name}:")
        # Try different structures
        for key in c.keys():
            val = c[key]
            if isinstance(val, dict) and 'p' in val:
                print(f"  {key}: p={val.get('p',0):.3f}, t={val.get('t',0):.1f}, h={val.get('h',0):.1f}, m={val.get('m',0):.2f}")
            elif isinstance(val, list):
                print(f"  {key}: {val}")
            elif isinstance(val, (int, float)):
                print(f"  {key}: {val}")
    
    print("\n=== Heaters ===")
    for name in ['HP_Heater_1', 'HP_Heater_2', 'HP_Heater_3', 'Deaerator', 'LP_Heater_5', 'LP_Heater_6', 'LP_Heater_7', 'LP_Heater_8']:
        c = components.get(name, {})
        print(f"\n{name}:")
        for key in c.keys():
            val = c[key]
            if isinstance(val, dict) and 'p' in val:
                print(f"  {key}: p={val.get('p',0):.3f}, t={val.get('t',0):.1f}, h={val.get('h',0):.1f}, m={val.get('m',0):.2f}")
            elif isinstance(val, list):
                print(f"  {key}: {val}")
            elif isinstance(val, (int, float)):
                print(f"  {key}: {val}")
    
    print("\n=== Boiler & Generator ===")
    for name in ['Boiler', 'Generator']:
        c = components.get(name, {})
        print(f"\n{name}:")
        for key in c.keys():
            val = c[key]
            if isinstance(val, dict) and 'p' in val:
                print(f"  {key}: p={val.get('p',0):.3f}, t={val.get('t',0):.1f}, h={val.get('h',0):.1f}, m={val.get('m',0):.2f}")
            elif isinstance(val, list):
                print(f"  {key}: {val}")
            elif isinstance(val, (int, float)):
                print(f"  {key}: {val}")

except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
    sys.exit(1)
