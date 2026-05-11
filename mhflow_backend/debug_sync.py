#!/usr/bin/env python3
"""Debug synchronization issue."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.templates.plant_600mw import get_600mw_template
from app.solvers.heat_balance import HeatBalanceSolver
from app.models.turbine import Turbine
from app.models.boiler import Boiler

t = get_600mw_template()

# Monkey-patch to trace IP_Turbine steam_in
original_setup_turbine_inputs = HeatBalanceSolver._setup_turbine_inputs

def patched_setup_turbine_inputs(self, turbine):
    if turbine.name == "IP_Turbine":
        steam_in_before = turbine.get_inlet("steam_in")
        print(f"[SETUP IP_Turbine BEFORE] m={steam_in_before.get('m',0) if steam_in_before else 'None'}, h={steam_in_before.get('h',0) if steam_in_before else 'None'}")
    original_setup_turbine_inputs(self, turbine)
    if turbine.name == "IP_Turbine":
        steam_in_after = turbine.get_inlet("steam_in")
        print(f"[SETUP IP_Turbine AFTER] m={steam_in_after.get('m',0) if steam_in_after else 'None'}, h={steam_in_after.get('h',0) if steam_in_after else 'None'}")

HeatBalanceSolver._setup_turbine_inputs = patched_setup_turbine_inputs

original_sync = HeatBalanceSolver._sync_connections

def patched_sync(self):
    print("[SYNC START]")
    for conn in self.connections:
        if conn.get("to", "") == "IP_Turbine.steam_in":
            src = conn.get("from", "")
            print(f"[SYNC IP_Turbine.steam_in] from={src}")
            parts = src.split(".")
            if len(parts) == 2:
                src_comp = self.components.get(parts[0])
                if src_comp:
                    src_port = src_comp.get_outlet(parts[1])
                    print(f"[SYNC IP_Turbine.steam_in] src_port m={src_port.get('m',0) if src_port else 'None'}, h={src_port.get('h',0) if src_port else 'None'}")
    original_sync(self)
    ip = self.components.get("IP_Turbine")
    if ip:
        steam_in = ip.get_inlet("steam_in")
        print(f"[SYNC END IP_Turbine] m={steam_in.get('m',0) if steam_in else 'None'}")

HeatBalanceSolver._sync_connections = patched_sync

solver = HeatBalanceSolver(t)
result = solver.solve()

print("\n=== Final IP_Turbine steam_in ===")
ip = solver.components.get("IP_Turbine")
if ip:
    steam_in = ip.get_inlet("steam_in")
    print(f"m={steam_in.get('m',0)}, h={steam_in.get('h',0)}")
