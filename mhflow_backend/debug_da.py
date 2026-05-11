#!/usr/bin/env python3
"""Debug Deaerator calculation."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.models.heater import Heater

d = Heater(
    name="Deaerator",
    inlet_ports=[
        {"name": "water_in", "p": 1.5, "t": 186.41, "h": 791.77, "m": 500.0},
        {"name": "steam_in", "p": 2.936, "t": 510.43, "h": 3481.16, "m": 11.83},
        {"name": "drain_in", "p": 5.78, "t": 268.16, "h": 1175.62, "m": 173.28},
    ],
    outlet_ports=[
        {"name": "water_out", "p": 0.8, "t": 0.0, "h": 0.0, "m": 0.0},
        {"name": "drain_out", "p": 0.8, "t": 0.0, "h": 0.0, "m": 0.0},
    ],
    params={
        "heater_type": "DA",
        "deaerator_pressure": 0.8,
        "p_water_out": 0.8,
        "eta": 0.99,
    }
)

result = d.calculate()
print("=== Deaerator Calculation ===")
for p in d.outlet_ports:
    print(f"{p['name']}: p={p.get('p',0):.3f}, t={p.get('t',0):.2f}, h={p.get('h',0):.2f}, m={p.get('m',0):.2f}")

print(f"\nresults: {d.results}")

# Manual check
m_w = 500.0
m_s = 11.83
m_d = 173.28
h_w = 791.77
h_s = 3481.16
h_d = 1175.62

m_out = m_w + m_s + m_d
print(f"\nManual check: m_out = {m_w} + {m_s} + {m_d} = {m_out:.2f}")
