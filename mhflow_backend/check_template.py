#!/usr/bin/env python3
"""Check template parameters after update."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.templates.plant_600mw import get_600mw_template

t = get_600mw_template()
for c in t['components']:
    name = c['name']
    p = c.get('params', {})
    if name == 'Boiler':
        print(f"{name}: P_ms={p.get('main_steam_pressure')}, T_ms={p.get('main_steam_temperature')}, T_rh={p.get('reheat_temperature')}, blowdown={p.get('blowdown_rate')}, eta={p.get('eta_boiler')}")
    elif 'Turbine' in name:
        ext = [(e.get('p'), e.get('m_frac')) for e in p.get('extractions', [])]
        print(f"{name}: eta={p.get('eta_isen')}, p_out={p.get('p_out')}, ext={ext}")
    elif name == 'Condenser':
        print(f"{name}: p_cond={p.get('p_cond')}")
    elif 'Pump' in name:
        print(f"{name}: p_out={p.get('p_out')}, eta={p.get('eta_pump')}")
    elif 'Heater' in name:
        print(f"{name}: p_heater={p.get('p_heater')}, ttd={p.get('ttd')}, type={p.get('heater_type')}")
    elif name == 'Generator':
        print(f"{name}: eta_gen={p.get('eta_gen')}, eta_mech={p.get('eta_mech')}")
