import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Component,
  Connection,
  ComponentType,
  SolveResult,
  SystemModel,
  ComponentTypeConfig,
} from '../types'

/** 元件类型配置表 */
const COMPONENT_CONFIGS: Record<string, ComponentTypeConfig> = {
  boiler: {
    type: 'boiler',
    label: '锅炉',
    color: '#e74c3c',
    icon: 'boiler',
    defaultParams: {
      main_steam_pressure: 28.0,
      main_steam_temperature: 600,
      reheat_temperature: 610,
      boiler_efficiency: 95.0,
      feedwater_temperature: 299,
      rated_evaporation: 2000,
      reheat_pressure_drop: 0.3,
      exhaust_gas_temperature: 120,
      excess_air_ratio: 1.15,
      fly_ash_carbon: 1.5,
      slag_carbon: 3.0,
      blowdown_rate: 1.0,
      heat_loss: 0.3,
      fuel_lower_heating_value: 21000,
      fuel_moisture: 15,
      fuel_ash: 25,
    },
    paramDefs: [
      { key: 'main_steam_pressure', label: '主蒸汽压力', unit: 'MPa(a)', default: 28.0, min: 1, max: 35, step: 0.1, required: true, description: '锅炉出口主蒸汽压力' },
      { key: 'main_steam_temperature', label: '主蒸汽温度', unit: '°C', default: 600, min: 200, max: 650, step: 1, required: true, description: '锅炉出口主蒸汽温度' },
      { key: 'reheat_temperature', label: '再热蒸汽温度', unit: '°C', default: 610, min: 200, max: 650, step: 1, required: true, description: '再热器出口温度' },
      { key: 'boiler_efficiency', label: '锅炉效率', unit: '%', default: 95.0, min: 80, max: 99, step: 0.1, required: true, description: '锅炉热效率' },
      { key: 'feedwater_temperature', label: '给水温度', unit: '°C', default: 299, min: 100, max: 350, step: 1, required: true, description: '省煤器入口给水温度' },
      { key: 'rated_evaporation', label: '锅炉额定蒸发量', unit: 't/h', default: 2000, min: 500, max: 3000, step: 10, required: true, description: '锅炉BMCR工况蒸发量' },
      { key: 'reheat_pressure_drop', label: '再热蒸汽压降', unit: 'MPa', default: 0.3, min: 0, max: 1, step: 0.05, description: '再热器系统压降' },
      { key: 'exhaust_gas_temperature', label: '排烟温度', unit: '°C', default: 120, min: 80, max: 200, step: 1, description: '省煤器出口排烟温度' },
      { key: 'excess_air_ratio', label: '过量空气系数', unit: '-', default: 1.15, min: 1.0, max: 1.5, step: 0.01, description: '炉膛出口过量空气系数' },
      { key: 'fly_ash_carbon', label: '飞灰含碳量', unit: '%', default: 1.5, min: 0, max: 10, step: 0.1, description: '影响机械不完全燃烧损失' },
      { key: 'slag_carbon', label: '炉渣含碳量', unit: '%', default: 3.0, min: 0, max: 10, step: 0.1, description: '影响机械不完全燃烧损失' },
      { key: 'blowdown_rate', label: '排污率', unit: '%', default: 1.0, min: 0, max: 5, step: 0.1, description: '连续排污比例' },
      { key: 'heat_loss', label: '散热损失', unit: '%', default: 0.3, min: 0, max: 2, step: 0.05, description: '锅炉本体及烟道散热损失' },
      { key: 'fuel_lower_heating_value', label: '燃料低位发热量', unit: 'kJ/kg', default: 21000, min: 10000, max: 30000, step: 100, required: true, description: '入炉煤低位发热量' },
      { key: 'fuel_moisture', label: '燃料收到基水分', unit: '%', default: 15, min: 0, max: 50, step: 1, description: '煤质参数' },
      { key: 'fuel_ash', label: '燃料收到基灰分', unit: '%', default: 25, min: 0, max: 60, step: 1, description: '煤质参数' },
    ],
    defaultInletPorts: [
      { id: 'in1', name: 'feedwater_in', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'in2', name: 'reheat_in', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: 'steam_out', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'out2', name: 'reheat_out', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  turbine: {
    type: 'turbine',
    label: '汽轮机缸体',
    color: '#3498db',
    icon: 'turbine',
    defaultParams: {
      eta_isen: 0.88,
      p_out: 1.0,
      stage: '0',
      mechanical_efficiency: 0.995,
      rated_power: 660,
      exhaust_pressure: 4.9,
      shaft_seal_leakage_rate: 1.0,
      feedwater_pump_turbine_efficiency: 80,
      hp_efficiency: 88,
      ip_efficiency: 92,
      lp_efficiency: 89,
    },
    paramDefs: [
      { key: 'rated_power', label: '汽轮机额定功率', unit: 'MW', default: 660, min: 100, max: 1000, step: 10, required: true, description: '机组额定功率' },
      { key: 'exhaust_pressure', label: '汽轮机排汽压力', unit: 'kPa', default: 4.9, min: 2, max: 20, step: 0.1, required: true, description: '凝汽器背压' },
      { key: 'hp_efficiency', label: '高压缸效率', unit: '%', default: 88, min: 70, max: 98, step: 0.5, required: true, description: '高压缸相对内效率' },
      { key: 'ip_efficiency', label: '中压缸效率', unit: '%', default: 92, min: 70, max: 98, step: 0.5, required: true, description: '中压缸相对内效率' },
      { key: 'lp_efficiency', label: '低压缸效率', unit: '%', default: 89, min: 70, max: 98, step: 0.5, required: true, description: '低压缸相对内效率' },
      { key: 'eta_isen', label: '等熵效率', unit: '', default: 0.88, min: 0.7, max: 0.99, step: 0.005, description: '相对内效率' },
      { key: 'p_out', label: '排汽压力', unit: 'MPa', default: 1.0, min: 0.002, max: 20, step: 0.01 },
      { key: 'mechanical_efficiency', label: '机械效率', unit: '', default: 0.995, min: 0.95, max: 0.999, step: 0.001 },
      { key: 'shaft_seal_leakage_rate', label: '轴封漏气率', unit: '%', default: 1.0, min: 0, max: 5, step: 0.1, description: '高压缸轴封漏气比例' },
      { key: 'feedwater_pump_turbine_efficiency', label: '给水泵汽轮机效率', unit: '%', default: 80, min: 50, max: 95, step: 1, description: '小汽轮机油效率' },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '蒸汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'in2', name: '功率输入', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '蒸汽出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'out2', name: '功率输出', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  turbine_hp: {
    type: 'turbine_hp',
    label: '高压缸',
    color: '#3498db',
    icon: 'turbine',
    defaultParams: {
      eta_isen: 0.875,
      p_out: 4.2,
      stage: 'HP',
      n_sections: 5,
      mechanical_efficiency: 0.995,
      extraction_points: [
        { name: 'ext_hp1', p: 7.2, m_frac: 0.082, h_drop_ratio: 0.25 },
        { name: 'ext_hp2', p: 5.2, m_frac: 0.078, h_drop_ratio: 0.25 },
        { name: 'ext_hp3', p: 4.5, m_frac: 0.035, h_drop_ratio: 0.2 },
        { name: 'ext_hp4', p: 4.3, m_frac: 0.0, h_drop_ratio: 0.15 },
        { name: 'ext_hp5', p: 4.2, m_frac: 0.0, h_drop_ratio: 0.15 },
      ],
    },
    paramDefs: [
      { key: 'eta_isen', label: '等熵效率', unit: '', default: 0.875, min: 0.7, max: 0.99, step: 0.005 },
      { key: 'p_out', label: '排汽压力', unit: 'MPa', default: 4.2, min: 1, max: 10, step: 0.1 },
      { key: 'mechanical_efficiency', label: '机械效率', unit: '', default: 0.995, min: 0.95, max: 0.999, step: 0.001 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '主蒸汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '排汽出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext1', name: '抽汽1', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext2', name: '抽汽2', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext3', name: '抽汽3', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  turbine_ip: {
    type: 'turbine_ip',
    label: '中压缸',
    color: '#3498db',
    icon: 'turbine',
    defaultParams: {
      eta_isen: 0.90,
      p_out: 1.0,
      stage: 'IP',
      n_sections: 2,
      mechanical_efficiency: 0.995,
      extraction_points: [
        { name: 'ext_ip1', p: 2.5, m_frac: 0.060, h_drop_ratio: 0.5 },
        { name: 'ext_ip2', p: 1.5, m_frac: 0.035, h_drop_ratio: 0.5 },
      ],
    },
    paramDefs: [
      { key: 'eta_isen', label: '等熵效率', unit: '', default: 0.90, min: 0.7, max: 0.99, step: 0.005 },
      { key: 'p_out', label: '排汽压力', unit: 'MPa', default: 1.0, min: 0.1, max: 5, step: 0.1 },
      { key: 'mechanical_efficiency', label: '机械效率', unit: '', default: 0.995, min: 0.95, max: 0.999, step: 0.001 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '再热蒸汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '排汽出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext1', name: '抽汽1', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext2', name: '抽汽2', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  turbine_lp: {
    type: 'turbine_lp',
    label: '低压缸',
    color: '#3498db',
    icon: 'turbine',
    defaultParams: {
      eta_isen: 0.88,
      p_out: 0.0049,
      stage: 'LP',
      n_sections: 6,
      mechanical_efficiency: 0.995,
      extraction_points: [
        { name: 'ext_lp1', p: 0.6, m_frac: 0.030, h_drop_ratio: 0.15 },
        { name: 'ext_lp2', p: 0.25, m_frac: 0.025, h_drop_ratio: 0.15 },
        { name: 'ext_lp3', p: 0.08, m_frac: 0.020, h_drop_ratio: 0.15 },
        { name: 'ext_lp4', p: 0.03, m_frac: 0.015, h_drop_ratio: 0.15 },
        { name: 'ext_lp5', p: 0.015, m_frac: 0.010, h_drop_ratio: 0.2 },
        { name: 'ext_lp6', p: 0.008, m_frac: 0.005, h_drop_ratio: 0.2 },
      ],
    },
    paramDefs: [
      { key: 'eta_isen', label: '等熵效率', unit: '', default: 0.88, min: 0.7, max: 0.99, step: 0.005 },
      { key: 'p_out', label: '排汽压力', unit: 'MPa', default: 0.0049, min: 0.002, max: 0.1, step: 0.001 },
      { key: 'mechanical_efficiency', label: '机械效率', unit: '', default: 0.995, min: 0.95, max: 0.999, step: 0.001 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '蒸汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '排汽出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext1', name: '抽汽1', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext2', name: '抽汽2', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext3', name: '抽汽3', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext4', name: '抽汽4', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext5', name: '抽汽5', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'ext6', name: '抽汽6', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  condenser: {
    type: 'condenser',
    label: '凝汽器',
    color: '#1abc9c',
    icon: 'condenser',
    defaultParams: {
      condenser_pressure: 0.0049,
      cooling_water_inlet_temp: 25,
      terminal_temperature_difference: 5.0,
      cooling_range: 10.0,
    },
    paramDefs: [
      { key: 'condenser_pressure', label: '凝汽器压力', unit: 'MPa', default: 0.0049, min: 0.002, max: 0.02, step: 0.001, required: true, description: '凝汽器背压' },
      { key: 'cooling_water_inlet_temp', label: '循环水入口温度', unit: '°C', default: 25, min: 5, max: 35, step: 1, required: true, description: '冷却塔出口水温' },
      { key: 'terminal_temperature_difference', label: '凝汽器端差', unit: '°C', default: 5.0, min: 1, max: 15, step: 0.5, description: '凝汽器传热端差' },
      { key: 'cooling_range', label: '冷却水温升', unit: '°C', default: 10.0, min: 3, max: 20, step: 0.5, description: '循环水温升' },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '汽轮机排汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'in2', name: '冷却水进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '凝结水出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'out2', name: '冷却水出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  heater: {
    type: 'heater',
    label: '加热器',
    color: '#f39c12',
    icon: 'heater',
    defaultParams: {
      extraction_pressure: 1.0,
      terminal_temperature_difference: 3,
      drain_cooler_approach: 5,
      type: 1,
      heat_loss_rate: 0.2,
      deaerator_pressure: 0.7,
    },
    paramDefs: [
      { key: 'extraction_pressure', label: '抽汽压力', unit: 'MPa', default: 1.0, min: 0.02, max: 10, step: 0.01 },
      { key: 'terminal_temperature_difference', label: '端差', unit: '°C', default: 3, min: 0, max: 10, step: 0.5 },
      { key: 'drain_cooler_approach', label: '疏水冷却端差', unit: '°C', default: 5, min: 0, max: 15, step: 0.5 },
      { key: 'type', label: '类型(0=混合,1=表面)', unit: '', default: 1, min: 0, max: 1, step: 1 },
      { key: 'heat_loss_rate', label: '散热损失', unit: '%', default: 0.2, min: 0, max: 2, step: 0.05, description: '单台加热器散热损失' },
      { key: 'deaerator_pressure', label: '除氧器工作压力', unit: 'MPa(a)', default: 0.7, min: 0.1, max: 2, step: 0.05, description: '除氧器运行压力' },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '抽汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'in2', name: '被加热水进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'in3', name: '疏水进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '疏水出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'out2', name: '被加热水出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  pump: {
    type: 'pump',
    label: '水泵',
    color: '#9b59b6',
    icon: 'pump',
    defaultParams: {
      outlet_pressure: 1.0,
      isentropic_efficiency: 85,
      motor_efficiency: 95,
      pump_head: 350,
      mass_flow: 485,  // 给水流量 t/h
    },
    paramDefs: [
      { key: 'mass_flow', label: '给水流量', unit: 't/h', default: 485, min: 100, max: 3000, step: 1, required: true, description: '给水泵流量设定值，用于变工况计算' },
      { key: 'outlet_pressure', label: '出口压力', unit: 'MPa', default: 1.0, min: 0.1, max: 30, step: 0.1 },
      { key: 'isentropic_efficiency', label: '泵效率', unit: '%', default: 85, min: 60, max: 95, step: 0.5, description: '主给水泵效率或凝结水泵效率' },
      { key: 'motor_efficiency', label: '电机效率', unit: '%', default: 95, min: 85, max: 99, step: 0.5 },
      { key: 'pump_head', label: '扬程', unit: 'm', default: 350, min: 50, max: 500, step: 10, description: '给水泵设计扬程' },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  pipe: {
    type: 'pipe',
    label: '管道',
    color: '#95a5a6',
    icon: 'pipe',
    defaultParams: {
      pressure_drop: 0.1,
      heat_loss: 0.5,
      insulation_thickness: 0.1,
    },
    paramDefs: [
      { key: 'pressure_drop', label: '压降', unit: 'MPa', default: 0.1, min: 0, max: 2, step: 0.01 },
      { key: 'heat_loss', label: '热损失', unit: 'kJ/kg', default: 0.5, min: 0, max: 50, step: 0.1 },
      { key: 'insulation_thickness', label: '保温层厚度', unit: 'm', default: 0.1, min: 0, max: 0.5, step: 0.01 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  tee: {
    type: 'tee',
    label: '三通',
    color: '#7f8c8d',
    icon: 'tee',
    defaultParams: {
      split_ratio: 0.5,
    },
    paramDefs: [
      { key: 'split_ratio', label: '分流比', unit: '', default: 0.5, min: 0, max: 1, step: 0.01 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '出口1', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'out2', name: '出口2', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  generator: {
    type: 'generator',
    label: '发电机',
    color: '#2ecc71',
    icon: 'generator',
    defaultParams: {
      rated_power: 660,
      efficiency: 98.5,
      power_factor: 0.85,
      station_service_power_rate: 6.0,
    },
    paramDefs: [
      { key: 'rated_power', label: '额定功率', unit: 'MW', default: 660, min: 50, max: 1200, step: 10, required: true },
      { key: 'efficiency', label: '效率', unit: '%', default: 98.5, min: 95, max: 99.9, step: 0.1, required: true },
      { key: 'power_factor', label: '功率因数', unit: '', default: 0.85, min: 0.8, max: 1.0, step: 0.01 },
      { key: 'station_service_power_rate', label: '厂用电率', unit: '%', default: 6.0, min: 3, max: 10, step: 0.1, description: '机组厂用电率' },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '机械功输入', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '电力输出', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
    ],
  },
}

let idCounter = 0
function generateId(prefix: string = 'comp'): string {
  idCounter++
  return `${prefix}_${Date.now()}_${idCounter}`
}

export const useModelStore = defineStore('model', () => {
  // 状态
  const components = ref<Component[]>([])
  const connections = ref<Connection[]>([])
  const selectedComponentId = ref<string | null>(null)
  const solveResult = ref<SolveResult | null>(null)
  const isSolving = ref(false)
  const solveError = ref<string | null>(null)

  // 计算属性
  const selectedComponent = computed(() => {
    if (!selectedComponentId.value) return null
    return components.value.find((c) => c.id === selectedComponentId.value) || null
  })

  const systemModel = computed<SystemModel>(() => ({
    components: components.value,
    connections: connections.value,
  }))

  const componentCount = computed(() => components.value.length)
  const connectionCount = computed(() => connections.value.length)

  // 方法
  function addComponent(type: ComponentType, x: number, y: number): Component {
    const config = COMPONENT_CONFIGS[type]
    if (!config) throw new Error(`Unknown component type: ${type}`)

    const comp: Component = {
      id: generateId(type),
      type,
      name: `${config.label}_${components.value.filter((c) => c.type === type).length + 1}`,
      x,
      y,
      params: { ...config.defaultParams },
      inlet_ports: config.defaultInletPorts.map((p) => ({ ...p, id: `${generateId('port')}` })),
      outlet_ports: config.defaultOutletPorts.map((p) => ({ ...p, id: `${generateId('port')}` })),
    }

    components.value.push(comp)
    return comp
  }

  function removeComponent(id: string) {
    components.value = components.value.filter((c) => c.id !== id)
    connections.value = connections.value.filter(
      (conn) => conn.from.componentId !== id && conn.to.componentId !== id
    )
    if (selectedComponentId.value === id) {
      selectedComponentId.value = null
    }
  }

  function updateComponent(id: string, updates: Partial<Component>) {
    const idx = components.value.findIndex((c) => c.id === id)
    if (idx !== -1) {
      components.value[idx] = { ...components.value[idx], ...updates }
    }
  }

  function updateComponentParam(id: string, key: string, value: number) {
    const comp = components.value.find((c) => c.id === id)
    if (comp) {
      comp.params[key] = value
    }
  }

  function selectComponent(id: string | null) {
    selectedComponentId.value = id
  }

  function addConnection(
    fromComponentId: string,
    fromPortIndex: number,
    toComponentId: string,
    toPortIndex: number
  ): Connection | null {
    // 验证：不能连接自身
    if (fromComponentId === toComponentId) return null

    // 验证：检查是否已存在相同连接
    const exists = connections.value.some(
      (c) =>
        c.from.componentId === fromComponentId &&
        c.from.portIndex === fromPortIndex &&
        c.to.componentId === toComponentId &&
        c.to.portIndex === toPortIndex
    )
    if (exists) return null

    // 验证：一个outlet端口只能连接一个inlet端口
    const fromUsed = connections.value.some(
      (c) =>
        c.from.componentId === fromComponentId && c.from.portIndex === fromPortIndex
    )
    if (fromUsed) return null

    // 验证：一个inlet端口只能接受一个连接
    const toUsed = connections.value.some(
      (c) =>
        c.to.componentId === toComponentId && c.to.portIndex === toPortIndex
    )
    if (toUsed) return null

    const conn: Connection = {
      id: generateId('conn'),
      from: { componentId: fromComponentId, portIndex: fromPortIndex },
      to: { componentId: toComponentId, portIndex: toPortIndex },
    }

    connections.value.push(conn)
    return conn
  }

  function removeConnection(id: string) {
    connections.value = connections.value.filter((c) => c.id !== id)
  }

  function loadTemplate(model: SystemModel) {
    components.value = model.components.map((c) => ({ ...c }))
    connections.value = model.connections.map((c) => ({ ...c }))
    selectedComponentId.value = null
    solveResult.value = null
    solveError.value = null
  }

  function clearModel() {
    components.value = []
    connections.value = []
    selectedComponentId.value = null
    solveResult.value = null
    solveError.value = null
  }

  function setSolveResult(result: SolveResult) {
    solveResult.value = result
    solveError.value = result.success ? null : (result.message || '计算失败')
    isSolving.value = false

    // 将求解结果更新到元件端口上
    if (result.success) {
      for (const compResult of result.components) {
        const comp = components.value.find((c) => c.id === compResult.id)
        if (comp) {
          comp.inlet_ports = compResult.inlet_ports.map((p) => ({ ...p }))
          comp.outlet_ports = compResult.outlet_ports.map((p) => ({ ...p }))
        }
      }
    }
  }

  function setSolving(val: boolean) {
    isSolving.value = val
    if (val) solveError.value = null
  }

  function getComponentConfig(type: ComponentType): ComponentTypeConfig | undefined {
    return COMPONENT_CONFIGS[type]
  }

  function getAllComponentConfigs(): ComponentTypeConfig[] {
    return Object.values(COMPONENT_CONFIGS)
  }

  /** 生成660MW超临界机组模板 - 多级分段汽轮机（13段）*/
  function generate600MWTemplate(): SystemModel {
    const boiler = {
      id: 'tpl_boiler',
      type: 'boiler' as ComponentType,
      name: '锅炉',
      x: 50,
      y: 200,
      params: { main_steam_pressure: 24.2, main_steam_temperature: 566, reheat_temperature: 566, boiler_efficiency: 93.5, feedwater_temperature: 278 },
      inlet_ports: [
        { id: 'tpl_b_in1', name: 'feedwater_in', type: 'inlet' as const, p: 27.5, t: 278, h: 1215, m: 485, s: 3.12 },
        { id: 'tpl_b_in2', name: 'reheat_in', type: 'inlet' as const, p: 4.2, t: 310, h: 3040, m: 410, s: 6.58 },
      ],
      outlet_ports: [
        { id: 'tpl_b_out1', name: 'steam_out', type: 'outlet' as const, p: 24.2, t: 566, h: 3395, m: 485, s: 6.36 },
        { id: 'tpl_b_out2', name: 'reheat_out', type: 'outlet' as const, p: 4.2, t: 566, h: 3595, m: 410, s: 7.42 },
      ],
    }

    // ========== 高压缸段 - 5段级组(2,7,11,13,16) ==========
    const hpStages = [
      { id: 'tpl_hp1', name: 'HP_Stage_2', x: 180, p_out: 7.2, m_frac: 0.082, next: 'tpl_hp2' },
      { id: 'tpl_hp2', name: 'HP_Stage_7', x: 300, p_out: 5.2, m_frac: 0.078, next: 'tpl_hp3' },
      { id: 'tpl_hp3', name: 'HP_Stage_11', x: 420, p_out: 4.5, m_frac: 0.035, next: 'tpl_hp4' },
      { id: 'tpl_hp4', name: 'HP_Stage_13', x: 540, p_out: 4.3, m_frac: 0.0, next: 'tpl_hp5' },
      { id: 'tpl_hp5', name: 'HP_Stage_16', x: 660, p_out: 4.2, m_frac: 0.0, next: null },
    ]

    // ========== 中压缸段 - 2段级组(19,20) ==========
    const ipStages = [
      { id: 'tpl_ip1', name: 'IP_Stage_19', x: 820, p_out: 2.5, m_frac: 0.060, next: 'tpl_ip2' },
      { id: 'tpl_ip2', name: 'IP_Stage_20', x: 940, p_out: 1.0, m_frac: 0.035, next: null },
    ]

    // ========== 低压缸段 - 6段级组(29,30,36,37,42,43) ==========
    const lpStages = [
      { id: 'tpl_lp1', name: 'LP_Stage_29', x: 1100, p_out: 0.6, m_frac: 0.030, next: 'tpl_lp2' },
      { id: 'tpl_lp2', name: 'LP_Stage_30', x: 1220, p_out: 0.25, m_frac: 0.025, next: 'tpl_lp3' },
      { id: 'tpl_lp3', name: 'LP_Stage_36', x: 1340, p_out: 0.08, m_frac: 0.020, next: 'tpl_lp4' },
      { id: 'tpl_lp4', name: 'LP_Stage_37', x: 1460, p_out: 0.03, m_frac: 0.015, next: 'tpl_lp5' },
      { id: 'tpl_lp5', name: 'LP_Stage_42', x: 1580, p_out: 0.015, m_frac: 0.010, next: 'tpl_lp6' },
      { id: 'tpl_lp6', name: 'LP_Stage_43', x: 1700, p_out: 0.0049, m_frac: 0.0, next: null },
    ]

    // 创建汽轮机缸体组件
    const turbines: Component[] = []
    const tees: Component[] = []
    const connections: Connection[] = []

    // 创建高压缸
    let prevM = 485
    let prevP = 24.2
    let prevH = 3395
    hpStages.forEach((stage, idx) => {
      const turbine: Component = {
        id: stage.id,
        type: 'turbine',
        name: stage.name,
        x: stage.x,
        y: 180,
        params: { eta_isen: 0.875, p_out: stage.p_out, stage: 'HP', mechanical_efficiency: 0.995 },
        inlet_ports: [
          { id: `${stage.id}_in1`, name: 'steam_in', type: 'inlet', p: prevP, t: idx === 0 ? 566 : 320 + idx * 10, h: prevH, m: prevM, s: 6.36 + idx * 0.05 },
          { id: `${stage.id}_in2`, name: 'power_in', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
        ],
        outlet_ports: [
          { id: `${stage.id}_out1`, name: 'steam_out', type: 'outlet', p: stage.p_out, t: 320 + idx * 5, h: prevH - 80 * (idx + 1), m: prevM * (1 - stage.m_frac), s: 6.6 + idx * 0.02 },
          { id: `${stage.id}_out2`, name: 'power_out', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
        ],
      }
      turbines.push(turbine)

      // 创建抽汽三通（如果有抽汽）
      if (stage.m_frac > 0) {
        const tee: Component = {
          id: `tpl_tee_${stage.id}`,
          type: 'tee',
          name: `Tee_${stage.name}`,
          x: stage.x + 60,
          y: 180,
          params: { split_ratio: stage.m_frac },
          inlet_ports: [{ id: `tee_${stage.id}_in1`, name: 'inlet', type: 'inlet', p: stage.p_out, t: 320 + idx * 5, h: prevH - 80 * (idx + 1), m: prevM, s: 6.6 + idx * 0.02 }],
          outlet_ports: [
            { id: `tee_${stage.id}_out1`, name: 'outlet1', type: 'outlet', p: stage.p_out, t: 320 + idx * 5, h: prevH - 80 * (idx + 1), m: prevM * stage.m_frac, s: 6.6 + idx * 0.02 },
            { id: `tee_${stage.id}_out2`, name: 'outlet2', type: 'outlet', p: stage.p_out, t: 320 + idx * 5, h: prevH - 80 * (idx + 1), m: prevM * (1 - stage.m_frac), s: 6.6 + idx * 0.02 },
          ],
        }
        tees.push(tee)
        connections.push(
          { id: `conn_${stage.id}_tee`, from: { componentId: stage.id, portIndex: 0 }, to: { componentId: tee.id, portIndex: 0 } },
          { id: `conn_tee_ext_${stage.id}`, from: { componentId: tee.id, portIndex: 0 }, to: { componentId: `tpl_heater${idx + 1}`, portIndex: 1 } }
        )
        if (stage.next) {
          connections.push({ id: `conn_tee_${stage.next}`, from: { componentId: tee.id, portIndex: 1 }, to: { componentId: stage.next, portIndex: 0 } })
        }
      } else if (stage.next) {
        connections.push({ id: `conn_${stage.id}_${stage.next}`, from: { componentId: stage.id, portIndex: 0 }, to: { componentId: stage.next, portIndex: 0 } })
      }

      prevM *= (1 - stage.m_frac)
      prevP = stage.p_out
      prevH -= 80
    })

    // HP5排汽到锅炉再热
    connections.push({ id: 'conn_hp5_reheat', from: { componentId: 'tpl_hp5', portIndex: 0 }, to: { componentId: 'tpl_boiler', portIndex: 1 } })

    // 创建中压缸
    prevM = 410
    prevP = 4.2
    prevH = 3595
    ipStages.forEach((stage, idx) => {
      const turbine: Component = {
        id: stage.id,
        type: 'turbine',
        name: stage.name,
        x: stage.x,
        y: 180,
        params: { eta_isen: 0.90, p_out: stage.p_out, stage: 'IP', mechanical_efficiency: 0.995 },
        inlet_ports: [
          { id: `${stage.id}_in1`, name: 'steam_in', type: 'inlet', p: prevP, t: idx === 0 ? 566 : 350, h: prevH, m: prevM, s: 7.42 + idx * 0.1 },
          { id: `${stage.id}_in2`, name: 'power_in', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
        ],
        outlet_ports: [
          { id: `${stage.id}_out1`, name: 'steam_out', type: 'outlet', p: stage.p_out, t: 280 - idx * 30, h: prevH - 150 * (idx + 1), m: prevM * (1 - stage.m_frac), s: 7.6 + idx * 0.05 },
          { id: `${stage.id}_out2`, name: 'power_out', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
        ],
      }
      turbines.push(turbine)

      if (stage.m_frac > 0) {
        const tee: Component = {
          id: `tpl_tee_${stage.id}`,
          type: 'tee',
          name: `Tee_${stage.name}`,
          x: stage.x + 60,
          y: 180,
          params: { split_ratio: stage.m_frac },
          inlet_ports: [{ id: `tee_${stage.id}_in1`, name: 'inlet', type: 'inlet', p: stage.p_out, t: 280 - idx * 30, h: prevH - 150 * (idx + 1), m: prevM, s: 7.6 + idx * 0.05 }],
          outlet_ports: [
            { id: `tee_${stage.id}_out1`, name: 'outlet1', type: 'outlet', p: stage.p_out, t: 280 - idx * 30, h: prevH - 150 * (idx + 1), m: prevM * stage.m_frac, s: 7.6 + idx * 0.05 },
            { id: `tee_${stage.id}_out2`, name: 'outlet2', type: 'outlet', p: stage.p_out, t: 280 - idx * 30, h: prevH - 150 * (idx + 1), m: prevM * (1 - stage.m_frac), s: 7.6 + idx * 0.05 },
          ],
        }
        tees.push(tee)
        connections.push(
          { id: `conn_${stage.id}_tee`, from: { componentId: stage.id, portIndex: 0 }, to: { componentId: tee.id, portIndex: 0 } }
        )
        // IP2抽汽到低加5
        if (idx === 1) {
          connections.push({ id: `conn_tee_lph5`, from: { componentId: tee.id, portIndex: 0 }, to: { componentId: 'tpl_lph5', portIndex: 1 } })
        }
        // IP1抽汽到除氧器
        if (idx === 0) {
          connections.push({ id: `conn_tee_da`, from: { componentId: tee.id, portIndex: 0 }, to: { componentId: 'tpl_deaerator', portIndex: 1 } })
        }
        if (stage.next) {
          connections.push({ id: `conn_tee_${stage.next}`, from: { componentId: tee.id, portIndex: 1 }, to: { componentId: stage.next, portIndex: 0 } })
        }
      } else if (stage.next) {
        connections.push({ id: `conn_${stage.id}_${stage.next}`, from: { componentId: stage.id, portIndex: 0 }, to: { componentId: stage.next, portIndex: 0 } })
      }

      prevM *= (1 - stage.m_frac)
      prevP = stage.p_out
      prevH -= 150
    })

    // 锅炉再热到IP1
    connections.push({ id: 'conn_reheat_ip1', from: { componentId: 'tpl_boiler', portIndex: 1 }, to: { componentId: 'tpl_ip1', portIndex: 0 } })

    // 创建低压缸
    prevM = 380
    prevP = 1.0
    prevH = 2970
    lpStages.forEach((stage, idx) => {
      const turbine: Component = {
        id: stage.id,
        type: 'turbine',
        name: stage.name,
        x: stage.x,
        y: 180,
        params: { eta_isen: 0.88, p_out: stage.p_out, stage: 'LP', mechanical_efficiency: 0.995 },
        inlet_ports: [
          { id: `${stage.id}_in1`, name: 'steam_in', type: 'inlet', p: prevP, t: 250 - idx * 30, h: prevH, m: prevM, s: 7.68 + idx * 0.08 },
          { id: `${stage.id}_in2`, name: 'power_in', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
        ],
        outlet_ports: [
          { id: `${stage.id}_out1`, name: 'steam_out', type: 'outlet', p: stage.p_out, t: Math.max(33, 120 - idx * 15), h: Math.max(2320, prevH - 100), m: prevM * (1 - stage.m_frac), s: 7.8 + idx * 0.1 },
          { id: `${stage.id}_out2`, name: 'power_out', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0, w: 0 },
        ],
      }
      turbines.push(turbine)

      if (stage.m_frac > 0) {
        const tee: Component = {
          id: `tpl_tee_${stage.id}`,
          type: 'tee',
          name: `Tee_${stage.name}`,
          x: stage.x + 60,
          y: 180,
          params: { split_ratio: stage.m_frac },
          inlet_ports: [{ id: `tee_${stage.id}_in1`, name: 'inlet', type: 'inlet', p: stage.p_out, t: Math.max(33, 120 - idx * 15), h: Math.max(2320, prevH - 100), m: prevM, s: 7.8 + idx * 0.1 }],
          outlet_ports: [
            { id: `tee_${stage.id}_out1`, name: 'outlet1', type: 'outlet', p: stage.p_out, t: Math.max(33, 120 - idx * 15), h: Math.max(2320, prevH - 100), m: prevM * stage.m_frac, s: 7.8 + idx * 0.1 },
            { id: `tee_${stage.id}_out2`, name: 'outlet2', type: 'outlet', p: stage.p_out, t: Math.max(33, 120 - idx * 15), h: Math.max(2320, prevH - 100), m: prevM * (1 - stage.m_frac), s: 7.8 + idx * 0.1 },
          ],
        }
        tees.push(tee)
        connections.push(
          { id: `conn_${stage.id}_tee`, from: { componentId: stage.id, portIndex: 0 }, to: { componentId: tee.id, portIndex: 0 } }
        )
        const heaterId = idx < 3 ? `tpl_lph${idx + 6}` : null
        if (heaterId) {
          connections.push({ id: `conn_tee_${heaterId}`, from: { componentId: tee.id, portIndex: 0 }, to: { componentId: heaterId, portIndex: 1 } })
        }
        if (stage.next) {
          connections.push({ id: `conn_tee_${stage.next}`, from: { componentId: tee.id, portIndex: 1 }, to: { componentId: stage.next, portIndex: 0 } })
        }
      } else if (stage.next) {
        connections.push({ id: `conn_${stage.id}_${stage.next}`, from: { componentId: stage.id, portIndex: 0 }, to: { componentId: stage.next, portIndex: 0 } })
      }

      prevM *= (1 - stage.m_frac)
      prevP = stage.p_out
      prevH -= 100
    })

    // LP6排汽到凝汽器
    connections.push({ id: 'conn_lp6_cond', from: { componentId: 'tpl_lp6', portIndex: 0 }, to: { componentId: 'tpl_condenser', portIndex: 0 } })

    const condenser = {
      id: 'tpl_condenser',
      type: 'condenser' as ComponentType,
      name: 'Condenser',
      x: 850,
      y: 400,
      params: { ttd: 5.0, delta_t_cw: 10.0, p_cond: 0.0049, eta_heat_transfer: 0.98 },
      inlet_ports: [
        { id: 'tpl_c_in1', name: 'steam_in', type: 'inlet' as const, p: 0.0049, t: 33, h: 2320, m: 320, s: 7.82 },
        { id: 'tpl_c_in2', name: 'cooling_in', type: 'inlet' as const, p: 0.1, t: 20, h: 84, m: 0, s: 0.296 },
      ],
      outlet_ports: [
        { id: 'tpl_c_out1', name: 'water_out', type: 'outlet' as const, p: 0.0049, t: 33, h: 138, m: 320, s: 0.47 },
        { id: 'tpl_c_out2', name: 'cooling_out', type: 'outlet' as const, p: 0.1, t: 30, h: 126, m: 0, s: 0.435 },
      ],
    }

    const condensatePump = {
      id: 'tpl_cond_pump',
      type: 'pump' as ComponentType,
      name: 'CondensatePump',
      x: 700,
      y: 450,
      params: { eta_pump: 0.82, p_out: 1.6, eta_motor: 0.95 },
      inlet_ports: [{ id: 'tpl_cp_in1', name: 'water_in', type: 'inlet' as const, p: 0.0049, t: 33, h: 138, m: 320, s: 0.47 }],
      outlet_ports: [{ id: 'tpl_cp_out1', name: 'water_out', type: 'outlet' as const, p: 1.6, t: 34, h: 142, m: 320, s: 0.47 }],
    }

    const feedPump = {
      id: 'tpl_feed_pump',
      type: 'pump' as ComponentType,
      name: 'FeedwaterPump',
      x: 250,
      y: 400,
      params: { eta_pump: 0.83, p_out: 29.0, eta_motor: 0.95, mass_flow: 1800 },
      inlet_ports: [{ id: 'tpl_fp_in1', name: 'water_in', type: 'inlet' as const, p: 0.8, t: 170, h: 720, m: 485, s: 2.04 }],
      outlet_ports: [{ id: 'tpl_fp_out1', name: 'water_out', type: 'outlet' as const, p: 29.0, t: 172, h: 725, m: 485, s: 2.04 }],
    }

    const generator = {
      id: 'tpl_generator',
      type: 'generator' as ComponentType,
      name: 'Generator',
      x: 1050,
      y: 180,
      params: { eta_gen: 0.99, eta_mech: 0.995 },
      inlet_ports: [{ id: 'tpl_g_in1', name: 'mechanical_in', type: 'inlet' as const, p: 0, t: 0, h: 0, m: 0, s: 0, w_mechanical: 0 }],
      outlet_ports: [{ id: 'tpl_g_out1', name: 'electrical_out', type: 'outlet' as const, p: 0, t: 0, h: 0, m: 0, s: 0, w_electrical: 0 }],
    }

    const heater1 = {
      id: 'tpl_heater1',
      type: 'heater' as ComponentType,
      name: 'HP_Heater_1',
      x: 450,
      y: 350,
      params: { heater_type: 'HP', ttd: 3.0, dca: 5.0, eta: 0.99, p_heater: 7.2, p_water_out: 28.0 },
      inlet_ports: [
        { id: 'tpl_h1_in1', name: 'water_in', type: 'inlet' as const, p: 28.0, t: 260, h: 1115, m: 485, s: 2.98 },
        { id: 'tpl_h1_in2', name: 'steam_in', type: 'inlet' as const, p: 7.2, t: 280, h: 2820, m: 39, s: 6.35 },
        { id: 'tpl_h1_in3', name: 'drain_in', type: 'inlet' as const, p: 0, t: 0, h: 0, m: 0, s: 0 },
      ],
      outlet_ports: [
        { id: 'tpl_h1_out1', name: 'water_out', type: 'outlet' as const, p: 28.0, t: 278, h: 1215, m: 485, s: 3.12 },
        { id: 'tpl_h1_out2', name: 'drain_out', type: 'outlet' as const, p: 7.2, t: 265, h: 1118, m: 39, s: 2.99 },
      ],
    }

    const heater2 = {
      id: 'tpl_heater2',
      type: 'heater' as ComponentType,
      name: 'HP_Heater_2',
      x: 350,
      y: 450,
      params: { heater_type: 'HP', ttd: 3.0, dca: 5.0, eta: 0.99, p_heater: 5.2, p_water_out: 28.0 },
      inlet_ports: [
        { id: 'tpl_h2_in1', name: 'water_in', type: 'inlet' as const, p: 28.0, t: 230, h: 993, m: 485, s: 2.62 },
        { id: 'tpl_h2_in2', name: 'steam_in', type: 'inlet' as const, p: 5.2, t: 260, h: 2760, m: 37, s: 6.38 },
        { id: 'tpl_h2_in3', name: 'drain_in', type: 'inlet' as const, p: 7.2, t: 265, h: 1118, m: 39, s: 2.99 },
      ],
      outlet_ports: [
        { id: 'tpl_h2_out1', name: 'water_out', type: 'outlet' as const, p: 28.0, t: 260, h: 1115, m: 485, s: 2.98 },
        { id: 'tpl_h2_out2', name: 'drain_out', type: 'outlet' as const, p: 5.2, t: 235, h: 995, m: 76, s: 2.62 },
      ],
    }

    // 补充更多加热器和除氧器
    const heater3 = {
      id: 'tpl_heater3',
      type: 'heater' as ComponentType,
      name: 'HP_Heater_3',
      x: 350,
      y: 350,
      params: { heater_type: 'HP', ttd: 3.0, dca: 5.0, eta: 0.99, p_heater: 4.5, p_water_out: 28.0 },
      inlet_ports: [
        { id: 'tpl_h3_in1', name: 'water_in', type: 'inlet' as const, p: 28.0, t: 195, h: 830, m: 485, s: 2.28 },
        { id: 'tpl_h3_in2', name: 'steam_in', type: 'inlet' as const, p: 4.5, t: 250, h: 2720, m: 17, s: 6.42 },
        { id: 'tpl_h3_in3', name: 'drain_in', type: 'inlet' as const, p: 5.2, t: 235, h: 995, m: 76, s: 2.62 },
      ],
      outlet_ports: [
        { id: 'tpl_h3_out1', name: 'water_out', type: 'outlet' as const, p: 28.0, t: 230, h: 993, m: 485, s: 2.62 },
        { id: 'tpl_h3_out2', name: 'drain_out', type: 'outlet' as const, p: 4.5, t: 198, h: 840, m: 93, s: 2.30 },
      ],
    }

    const deaerator = {
      id: 'tpl_deaerator',
      type: 'heater' as ComponentType,
      name: 'Deaerator',
      x: 500,
      y: 450,
      params: { heater_type: 'DA', ttd: 0.0, dca: 0.0, eta: 0.99, p_heater: 0.8, p_water_out: 0.8 },
      inlet_ports: [
        { id: 'tpl_da_in1', name: 'water_in', type: 'inlet' as const, p: 1.5, t: 140, h: 592, m: 320, s: 1.72 },
        { id: 'tpl_da_in2', name: 'steam_in', type: 'inlet' as const, p: 0.8, t: 170, h: 2770, m: 165, s: 7.15 },
        { id: 'tpl_da_in3', name: 'drain_in', type: 'inlet' as const, p: 4.5, t: 198, h: 840, m: 93, s: 2.30 },
      ],
      outlet_ports: [
        { id: 'tpl_da_out1', name: 'water_out', type: 'outlet' as const, p: 0.8, t: 170, h: 720, m: 485, s: 2.04 },
        { id: 'tpl_da_out2', name: 'drain_out', type: 'outlet' as const, p: 0.8, t: 170, h: 720, m: 0, s: 2.04 },
      ],
    }

    const lpHeater5 = {
      id: 'tpl_lph5',
      type: 'heater' as ComponentType,
      name: 'LP_Heater_5',
      x: 550,
      y: 400,
      params: { heater_type: 'LP', ttd: 3.0, dca: 5.0, eta: 0.99, p_heater: 1.5, p_water_out: 1.5 },
      inlet_ports: [
        { id: 'tpl_lp5_in1', name: 'water_in', type: 'inlet' as const, p: 1.5, t: 110, h: 462, m: 320, s: 1.34 },
        { id: 'tpl_lp5_in2', name: 'steam_in', type: 'inlet' as const, p: 1.5, t: 198, h: 2750, m: 28, s: 6.68 },
        { id: 'tpl_lp5_in3', name: 'drain_in', type: 'inlet' as const, p: 0, t: 0, h: 0, m: 0, s: 0 },
      ],
      outlet_ports: [
        { id: 'tpl_lp5_out1', name: 'water_out', type: 'outlet' as const, p: 1.5, t: 140, h: 592, m: 320, s: 1.72 },
        { id: 'tpl_lp5_out2', name: 'drain_out', type: 'outlet' as const, p: 1.5, t: 118, h: 495, m: 28, s: 1.43 },
      ],
    }

    const lpHeater6 = {
      id: 'tpl_lph6',
      type: 'heater' as ComponentType,
      name: 'LP_Heater_6',
      x: 600,
      y: 400,
      params: { heater_type: 'LP', ttd: 3.0, dca: 5.0, eta: 0.99, p_heater: 0.6, p_water_out: 1.5 },
      inlet_ports: [
        { id: 'tpl_lp6_in1', name: 'water_in', type: 'inlet' as const, p: 1.5, t: 80, h: 335, m: 320, s: 0.99 },
        { id: 'tpl_lp6_in2', name: 'steam_in', type: 'inlet' as const, p: 0.6, t: 158, h: 2700, m: 23, s: 6.82 },
        { id: 'tpl_lp6_in3', name: 'drain_in', type: 'inlet' as const, p: 1.5, t: 118, h: 495, m: 28, s: 1.43 },
      ],
      outlet_ports: [
        { id: 'tpl_lp6_out1', name: 'water_out', type: 'outlet' as const, p: 1.5, t: 110, h: 462, m: 320, s: 1.34 },
        { id: 'tpl_lp6_out2', name: 'drain_out', type: 'outlet' as const, p: 0.6, t: 88, h: 369, m: 51, s: 1.10 },
      ],
    }

    const lpHeater7 = {
      id: 'tpl_lph7',
      type: 'heater' as ComponentType,
      name: 'LP_Heater_7',
      x: 650,
      y: 400,
      params: { heater_type: 'LP', ttd: 3.0, dca: 5.0, eta: 0.99, p_heater: 0.25, p_water_out: 1.5 },
      inlet_ports: [
        { id: 'tpl_lp7_in1', name: 'water_in', type: 'inlet' as const, p: 1.5, t: 55, h: 230, m: 320, s: 0.68 },
        { id: 'tpl_lp7_in2', name: 'steam_in', type: 'inlet' as const, p: 0.25, t: 127, h: 2650, m: 19, s: 7.05 },
        { id: 'tpl_lp7_in3', name: 'drain_in', type: 'inlet' as const, p: 0.6, t: 88, h: 369, m: 51, s: 1.10 },
      ],
      outlet_ports: [
        { id: 'tpl_lp7_out1', name: 'water_out', type: 'outlet' as const, p: 1.5, t: 80, h: 335, m: 320, s: 0.99 },
        { id: 'tpl_lp7_out2', name: 'drain_out', type: 'outlet' as const, p: 0.25, t: 62, h: 258, m: 70, s: 0.77 },
      ],
    }

    const lpHeater8 = {
      id: 'tpl_lph8',
      type: 'heater' as ComponentType,
      name: 'LP_Heater_8',
      x: 700,
      y: 400,
      params: { heater_type: 'LP', ttd: 3.0, dca: 5.0, eta: 0.99, p_heater: 0.08, p_water_out: 1.5 },
      inlet_ports: [
        { id: 'tpl_lp8_in1', name: 'water_in', type: 'inlet' as const, p: 1.5, t: 35, h: 146, m: 320, s: 0.48 },
        { id: 'tpl_lp8_in2', name: 'steam_in', type: 'inlet' as const, p: 0.08, t: 41, h: 2580, m: 15, s: 7.55 },
        { id: 'tpl_lp8_in3', name: 'drain_in', type: 'inlet' as const, p: 0.25, t: 62, h: 258, m: 70, s: 0.77 },
      ],
      outlet_ports: [
        { id: 'tpl_lp8_out1', name: 'water_out', type: 'outlet' as const, p: 1.5, t: 55, h: 230, m: 320, s: 0.68 },
        { id: 'tpl_lp8_out2', name: 'drain_out', type: 'outlet' as const, p: 0.08, t: 43, h: 180, m: 85, s: 0.61 },
      ],
    }

    const components_list: Component[] = [
      boiler,
      ...turbines,
      ...tees,
      condenser, condensatePump, feedPump, generator,
      heater1, heater2, heater3, deaerator,
      lpHeater5, lpHeater6, lpHeater7, lpHeater8,
    ]

    // 添加额外的连接
    // 锅炉主蒸汽 -> HP1入口
    connections.push({ id: 'conn_boiler_hp1', from: { componentId: 'tpl_boiler', portIndex: 0 }, to: { componentId: 'tpl_hp1', portIndex: 0 } })

    // 锅炉再热出口 -> IP1入口
    connections.push({ id: 'conn_reheat_ip1', from: { componentId: 'tpl_boiler', portIndex: 1 }, to: { componentId: 'tpl_ip1', portIndex: 0 } })

    // IP2排汽 -> LP1入口
    connections.push({ id: 'conn_ip2_lp1', from: { componentId: 'tpl_ip2', portIndex: 0 }, to: { componentId: 'tpl_lp1', portIndex: 0 } })

    // ===== 给水回热回路 =====
    // 凝汽器 -> 凝结水泵
    connections.push({ id: 'conn_cond_cp', from: { componentId: 'tpl_condenser', portIndex: 0 }, to: { componentId: 'tpl_cond_pump', portIndex: 0 } })
    // 凝结水泵 -> 低加8
    connections.push({ id: 'conn_cp_lph8', from: { componentId: 'tpl_cond_pump', portIndex: 0 }, to: { componentId: 'tpl_lph8', portIndex: 0 } })
    // 低加8 -> 低加7
    connections.push({ id: 'conn_lph8_lph7', from: { componentId: 'tpl_lph8', portIndex: 0 }, to: { componentId: 'tpl_lph7', portIndex: 0 } })
    // 低加7 -> 低加6
    connections.push({ id: 'conn_lph7_lph6', from: { componentId: 'tpl_lph7', portIndex: 0 }, to: { componentId: 'tpl_lph6', portIndex: 0 } })
    // 低加6 -> 低加5
    connections.push({ id: 'conn_lph6_lph5', from: { componentId: 'tpl_lph6', portIndex: 0 }, to: { componentId: 'tpl_lph5', portIndex: 0 } })
    // 低加5 -> 除氧器
    connections.push({ id: 'conn_lph5_da', from: { componentId: 'tpl_lph5', portIndex: 0 }, to: { componentId: 'tpl_deaerator', portIndex: 0 } })
    // 除氧器 -> 给水泵
    connections.push({ id: 'conn_da_fp', from: { componentId: 'tpl_deaerator', portIndex: 0 }, to: { componentId: 'tpl_feed_pump', portIndex: 0 } })
    // 给水泵 -> 高加3
    connections.push({ id: 'conn_fp_h3', from: { componentId: 'tpl_feed_pump', portIndex: 0 }, to: { componentId: 'tpl_heater3', portIndex: 0 } })
    // 高加3 -> 高加2
    connections.push({ id: 'conn_h3_h2', from: { componentId: 'tpl_heater3', portIndex: 0 }, to: { componentId: 'tpl_heater2', portIndex: 0 } })
    // 高加2 -> 高加1
    connections.push({ id: 'conn_h2_h1', from: { componentId: 'tpl_heater2', portIndex: 0 }, to: { componentId: 'tpl_heater1', portIndex: 0 } })
    // 高加1 -> 锅炉给水入口
    connections.push({ id: 'conn_h1_boiler', from: { componentId: 'tpl_heater1', portIndex: 0 }, to: { componentId: 'tpl_boiler', portIndex: 0 } })

    // ===== 疏水连接 =====
    // 高加1疏水 -> 高加2疏水入口
    connections.push({ id: 'conn_h1_drain', from: { componentId: 'tpl_heater1', portIndex: 1 }, to: { componentId: 'tpl_heater2', portIndex: 2 } })
    // 高加2疏水 -> 高加3疏水入口
    connections.push({ id: 'conn_h2_drain', from: { componentId: 'tpl_heater2', portIndex: 1 }, to: { componentId: 'tpl_heater3', portIndex: 2 } })
    // 高加3疏水 -> 除氧器
    connections.push({ id: 'conn_h3_drain', from: { componentId: 'tpl_heater3', portIndex: 1 }, to: { componentId: 'tpl_deaerator', portIndex: 2 } })
    // 低加5疏水 -> 低加6疏水入口
    connections.push({ id: 'conn_lp5_drain', from: { componentId: 'tpl_lph5', portIndex: 1 }, to: { componentId: 'tpl_lph6', portIndex: 2 } })
    // 低加6疏水 -> 低加7疏水入口
    connections.push({ id: 'conn_lp6_drain', from: { componentId: 'tpl_lph6', portIndex: 1 }, to: { componentId: 'tpl_lph7', portIndex: 2 } })
    // 低加7疏水 -> 低加8疏水入口
    connections.push({ id: 'conn_lp7_drain', from: { componentId: 'tpl_lph7', portIndex: 1 }, to: { componentId: 'tpl_lph8', portIndex: 2 } })
    // 低加8疏水 -> 凝汽器
    connections.push({ id: 'conn_lp8_drain', from: { componentId: 'tpl_lph8', portIndex: 1 }, to: { componentId: 'tpl_condenser', portIndex: 1 } })

    // ===== 能量连接 =====
    // LP6 -> 发电机（功率输出）
    connections.push({ id: 'conn_lp6_gen', from: { componentId: 'tpl_lp6', portIndex: 1 }, to: { componentId: 'tpl_generator', portIndex: 0 }, type: 'power' })

    return { components: components_list, connections: connections }
  }

  return {
    // 状态
    components,
    connections,
    selectedComponentId,
    selectedComponent,
    solveResult,
    isSolving,
    solveError,
    systemModel,
    componentCount,
    connectionCount,
    // 方法
    addComponent,
    removeComponent,
    updateComponent,
    updateComponentParam,
    selectComponent,
    addConnection,
    removeConnection,
    loadTemplate,
    clearModel,
    setSolveResult,
    setSolving,
    getComponentConfig,
    getAllComponentConfigs,
    generate600MWTemplate,
  }
})
