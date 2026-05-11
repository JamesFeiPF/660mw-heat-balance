#!/usr/bin/env python3
"""Debug heater calculation for HP3."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.models.heater import Heater
from app.properties.steam import saturation_properties, pt_to_h

# Create HP3 heater with current params
h = Heater(
    name="HP_Heater_3",
    inlet_ports=[
        {"name": "water_in", "p": 31.0, "t": 177.26, "h": 767.48, "m": 676.76},
        {"name": "steam_in", "p": 5.78, "t": 353.77, "h": 3060.10, "m": 84.22},
        {"name": "drain_in", "p": 5.893, "t": 269.41, "h": 1181.97, "m": 24.42},
    ],
    outlet_ports=[
        {"name": "water_out", "p": 28.0, "t": 0.0, "h": 0.0, "m": 0.0},
        {"name": "drain_out", "p": 5.78, "t": 0.0, "h": 0.0, "m": 0.0},
    ],
    params={
        "heater_type": "HP",
        "ttd": 3.9,
        "dca": 5.0,
        "eta": 0.99,
        "p_heater": 5.78,
        "p_water_out": 28.0,
    }
)

result = h.calculate()
print("=== HP3 Heater Calculation ===")
r = h.results
print(f"t_sat: {r['t_sat']:.2f} C")
print(f"t_water_out: {r['t_water_out']:.2f} C")
print(f"h_water_out: {r['h_water_out']:.2f} kJ/kg")
print(f"t_drain: {r['t_drain']:.2f} C")
print(f"h_drain: {r['h_drain']:.2f} kJ/kg")
print(f"m_steam: {r['m_steam']:.2f} kg/s")
print(f"m_drain_out: {r['m_drain_out']:.2f} kg/s")
print(f"q_water: {r['q_water']:.2f} kW")
print(f"q_steam: {r['q_steam']:.2f} kW")

# Manual check
m_water = 676.76
h_wi = 767.48
h_wo = r['h_water_out']
h_stm = 3060.10
h_drn = r['h_drain']
m_drain_in = 24.42
h_drain_in = 1181.97
eta = 0.99

q_w = m_water * (h_wo - h_wi)
q_d = m_drain_in * (h_drain_in - h_drn)
m_stm_calc = (q_w - q_d * eta) / ((h_stm - h_drn) * eta)
print(f"\n=== Manual Check ===")
print(f"q_water_manual: {q_w:.2f} kW")
print(f"q_drain_manual: {q_d:.2f} kW")
print(f"m_steam_manual: {m_stm_calc:.2f} kg/s")

# Check pt_to_h behavior
print(f"\n=== pt_to_h checks ===")
print(f"pt_to_h(28.0, 269.26) = {pt_to_h(28.0, 269.26):.2f}")
print(f"pt_to_h(5.78, 268.16) = {pt_to_h(5.78, 268.16):.2f}")
sat = saturation_properties(5.78)
print(f"saturation @ 5.78 MPa: t_sat={sat['t_sat']:.2f}, h_f={sat['h_f']:.2f}")
