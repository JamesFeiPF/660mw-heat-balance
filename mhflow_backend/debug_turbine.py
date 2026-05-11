#!/usr/bin/env python3
"""Debug turbine calculation for LP_Turbine."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.models.turbine import Turbine
from app.properties.steam import pt_to_h, pt_to_s, ph_to_t, ph_to_s, ps_to_h

# Create LP_Turbine with current params
t = Turbine(
    name="LP_Turbine",
    inlet_ports=[
        {"name": "steam_in", "p": 1.0, "t": 363.41, "h": 3186.63, "m": 363.90, "s": 7.3480},
    ],
    outlet_ports=[
        {"name": "steam_out", "p": 0.011, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
        {"name": "power_out", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0, "w": 0.0},
        {"name": "extraction_1", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
        {"name": "extraction_2", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
        {"name": "extraction_3", "p": 0.0, "t": 0.0, "h": 0.0, "m": 0.0, "s": 0.0},
    ],
    params={
        "eta_isen": 0.87,
        "p_out": 0.011,
        "stage": "LP",
        "extractions": [
            {"name": "ext_lp1", "p": 0.523, "m_frac": 0.03},
            {"name": "ext_lp2", "p": 0.26, "m_frac": 0.025},
            {"name": "ext_lp3", "p": 0.11, "m_frac": 0.02},
        ],
    }
)

result = t.calculate()
print("=== LP Turbine Calculation ===")
for p in t.outlet_ports:
    print(f"{p['name']}: p={p.get('p',0):.4f}, t={p.get('t',0):.2f}, h={p.get('h',0):.2f}, m={p.get('m',0):.2f}")

print(f"\nresults: {t.results}")

# Manual check
h_in = 3186.63
s_in = 7.3480
p_out = 0.011
eta = 0.87

h_out_is = ps_to_h(p_out, s_in)
print(f"\nManual check:")
print(f"h_out_is = ps_to_h({p_out}, {s_in}) = {h_out_is:.2f}")
print(f"total_h_drop = {h_in - h_out_is:.2f}")
print(f"actual_h_drop = {eta * (h_in - h_out_is):.2f}")
print(f"h_out_final = {h_in - eta * (h_in - h_out_is):.2f}")
