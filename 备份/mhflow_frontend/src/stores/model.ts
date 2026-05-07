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
      main_steam_pressure: 16.7,
      main_steam_temperature: 540,
      reheat_temperature: 540,
      boiler_efficiency: 92,
      feedwater_temperature: 275,
    },
    paramDefs: [
      { key: 'main_steam_pressure', label: '主蒸汽压力', unit: 'MPa', default: 16.7, min: 1, max: 30, step: 0.1 },
      { key: 'main_steam_temperature', label: '主蒸汽温度', unit: '°C', default: 540, min: 200, max: 650, step: 1 },
      { key: 'reheat_temperature', label: '再热蒸汽温度', unit: '°C', default: 540, min: 200, max: 650, step: 1 },
      { key: 'boiler_efficiency', label: '锅炉效率', unit: '%', default: 92, min: 80, max: 99, step: 0.1 },
      { key: 'feedwater_temperature', label: '给水温度', unit: '°C', default: 275, min: 100, max: 320, step: 1 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '给水进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '主蒸汽出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'out2', name: '再热蒸汽出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  turbine: {
    type: 'turbine',
    label: '汽轮机',
    color: '#3498db',
    icon: 'turbine',
    defaultParams: {
      inlet_pressure: 16.7,
      inlet_temperature: 540,
      isentropic_efficiency: 88,
      mechanical_efficiency: 99,
      extraction_pressures: 4.0,
    },
    paramDefs: [
      { key: 'inlet_pressure', label: '进汽压力', unit: 'MPa', default: 16.7, min: 1, max: 30, step: 0.1 },
      { key: 'inlet_temperature', label: '进汽温度', unit: '°C', default: 540, min: 200, max: 650, step: 1 },
      { key: 'isentropic_efficiency', label: '等熵效率', unit: '%', default: 88, min: 70, max: 99, step: 0.5 },
      { key: 'mechanical_efficiency', label: '机械效率', unit: '%', default: 99, min: 95, max: 99.9, step: 0.1 },
      { key: 'extraction_pressures', label: '抽汽压力', unit: 'MPa', default: 4.0, min: 0, max: 10, step: 0.1 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '主蒸汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'in2', name: '再热蒸汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '排汽出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
  },
  condenser: {
    type: 'condenser',
    label: '凝汽器',
    color: '#1abc9c',
    icon: 'condenser',
    defaultParams: {
      condenser_pressure: 0.005,
      cooling_water_inlet_temp: 20,
      terminal_temperature_difference: 5,
      cooling_range: 10,
    },
    paramDefs: [
      { key: 'condenser_pressure', label: '凝汽器压力', unit: 'MPa', default: 0.005, min: 0.002, max: 0.02, step: 0.001 },
      { key: 'cooling_water_inlet_temp', label: '冷却水进口温度', unit: '°C', default: 20, min: 5, max: 35, step: 1 },
      { key: 'terminal_temperature_difference', label: '端差', unit: '°C', default: 5, min: 1, max: 15, step: 0.5 },
      { key: 'cooling_range', label: '冷却水温升', unit: '°C', default: 10, min: 3, max: 20, step: 0.5 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '汽轮机排汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '凝结水出口', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
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
      type: 0,
    },
    paramDefs: [
      { key: 'extraction_pressure', label: '抽汽压力', unit: 'MPa', default: 1.0, min: 0.02, max: 10, step: 0.01 },
      { key: 'terminal_temperature_difference', label: '端差', unit: '°C', default: 3, min: 0, max: 10, step: 0.5 },
      { key: 'drain_cooler_approach', label: '疏水冷却端差', unit: '°C', default: 5, min: 0, max: 15, step: 0.5 },
      { key: 'type', label: '类型(0=混合,1=表面)', unit: '', default: 1, min: 0, max: 1, step: 1 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '抽汽进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
      { id: 'in2', name: '被加热水进口', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
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
      isentropic_efficiency: 82,
      motor_efficiency: 95,
    },
    paramDefs: [
      { key: 'outlet_pressure', label: '出口压力', unit: 'MPa', default: 1.0, min: 0.1, max: 30, step: 0.1 },
      { key: 'isentropic_efficiency', label: '等熵效率', unit: '%', default: 82, min: 60, max: 95, step: 0.5 },
      { key: 'motor_efficiency', label: '电机效率', unit: '%', default: 95, min: 85, max: 99, step: 0.5 },
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
  generator: {
    type: 'generator',
    label: '发电机',
    color: '#2ecc71',
    icon: 'generator',
    defaultParams: {
      rated_power: 600,
      efficiency: 98.5,
      power_factor: 0.85,
    },
    paramDefs: [
      { key: 'rated_power', label: '额定功率', unit: 'MW', default: 600, min: 50, max: 1200, step: 10 },
      { key: 'efficiency', label: '效率', unit: '%', default: 98.5, min: 95, max: 99.9, step: 0.1 },
      { key: 'power_factor', label: '功率因数', unit: '', default: 0.85, min: 0.8, max: 1.0, step: 0.01 },
    ],
    defaultInletPorts: [
      { id: 'in1', name: '机械功输入', type: 'inlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
    ],
    defaultOutletPorts: [
      { id: 'out1', name: '电力输出', type: 'outlet', p: 0, t: 0, h: 0, m: 0, s: 0 },
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

  /** 生成600MW超临界机组模板 */
  function generate600MWTemplate(): SystemModel {
    const boiler = {
      id: 'tpl_boiler',
      type: 'boiler' as ComponentType,
      name: '锅炉',
      x: 100,
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

    const hpTurbine = {
      id: 'tpl_hp_turbine',
      type: 'turbine' as ComponentType,
      name: 'HP_Turbine',
      x: 350,
      y: 180,
      params: { eta_isen: 0.875, p_out: 4.2, stage: 'HP', extractions: [
        { name: 'ext_hp1', p: 7.2, m_frac: 0.082 },
        { name: 'ext_hp2', p: 5.2, m_frac: 0.078 },
        { name: 'ext_hp3', p: 4.5, m_frac: 0.035 },
      ]},
      inlet_ports: [{ id: 'tpl_hp_in1', name: 'steam_in', type: 'inlet' as const, p: 24.2, t: 566, h: 3395, m: 485, s: 6.36 }],
      outlet_ports: [
        { id: 'tpl_hp_out1', name: 'steam_out', type: 'outlet' as const, p: 4.2, t: 310, h: 3040, m: 410, s: 6.58 },
      ],
    }

    const ipTurbine = {
      id: 'tpl_ip_turbine',
      type: 'turbine' as ComponentType,
      name: 'IP_Turbine',
      x: 600,
      y: 180,
      params: { eta_isen: 0.90, p_out: 1.0, stage: 'IP', extractions: [
        { name: 'ext_ip1', p: 2.5, m_frac: 0.060 },
        { name: 'ext_ip2', p: 1.5, m_frac: 0.035 },
      ]},
      inlet_ports: [
        { id: 'tpl_ip_in1', name: 'steam_in', type: 'inlet' as const, p: 4.2, t: 566, h: 3595, m: 410, s: 7.42 },
      ],
      outlet_ports: [
        { id: 'tpl_ip_out1', name: 'steam_out', type: 'outlet' as const, p: 1.0, t: 250, h: 2970, m: 380, s: 7.68 },
      ],
    }

    const lpTurbine = {
      id: 'tpl_lp_turbine',
      type: 'turbine' as ComponentType,
      name: 'LP_Turbine',
      x: 850,
      y: 180,
      params: { eta_isen: 0.88, p_out: 0.0049, stage: 'LP', extractions: [
        { name: 'ext_lp1', p: 0.6, m_frac: 0.030 },
        { name: 'ext_lp2', p: 0.25, m_frac: 0.025 },
        { name: 'ext_lp3', p: 0.08, m_frac: 0.020 },
      ]},
      inlet_ports: [
        { id: 'tpl_lp_in1', name: 'steam_in', type: 'inlet' as const, p: 1.0, t: 250, h: 2970, m: 380, s: 7.68 },
      ],
      outlet_ports: [
        { id: 'tpl_lp_out1', name: 'steam_out', type: 'outlet' as const, p: 0.0049, t: 33, h: 2320, m: 320, s: 7.82 },
      ],
    }

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
      params: { eta_pump: 0.83, p_out: 29.0, eta_motor: 0.95 },
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
      boiler, hpTurbine, ipTurbine, lpTurbine,
      condenser, condensatePump, feedPump, generator,
      heater1, heater2, heater3, deaerator,
      lpHeater5, lpHeater6, lpHeater7, lpHeater8,
    ]

    // 连接列表（使用后端模板格式）
    const connections_list: Connection[] = [
      // 锅炉 -> 高压缸
      { id: 'tpl_conn1', from: { componentId: 'tpl_boiler', portIndex: 0 }, to: { componentId: 'tpl_hp_turbine', portIndex: 0 } },
      // 高压缸排汽 -> 锅炉再热
      { id: 'tpl_conn2', from: { componentId: 'tpl_hp_turbine', portIndex: 0 }, to: { componentId: 'tpl_boiler', portIndex: 1 } },
      // 锅炉再热 -> 中压缸
      { id: 'tpl_conn3', from: { componentId: 'tpl_boiler', portIndex: 1 }, to: { componentId: 'tpl_ip_turbine', portIndex: 0 } },
      // 中压缸排汽 -> 低压缸
      { id: 'tpl_conn4', from: { componentId: 'tpl_ip_turbine', portIndex: 0 }, to: { componentId: 'tpl_lp_turbine', portIndex: 0 } },
      // 低压缸排汽 -> 凝汽器
      { id: 'tpl_conn5', from: { componentId: 'tpl_lp_turbine', portIndex: 0 }, to: { componentId: 'tpl_condenser', portIndex: 0 } },
      // 凝汽器 -> 凝结水泵
      { id: 'tpl_conn6', from: { componentId: 'tpl_condenser', portIndex: 0 }, to: { componentId: 'tpl_cond_pump', portIndex: 0 } },
      // 凝结水泵 -> 低加8
      { id: 'tpl_conn7', from: { componentId: 'tpl_cond_pump', portIndex: 0 }, to: { componentId: 'tpl_lph8', portIndex: 0 } },
      // 低加8 -> 低加7
      { id: 'tpl_conn8', from: { componentId: 'tpl_lph8', portIndex: 0 }, to: { componentId: 'tpl_lph7', portIndex: 0 } },
      // 低加7 -> 低加6
      { id: 'tpl_conn9', from: { componentId: 'tpl_lph7', portIndex: 0 }, to: { componentId: 'tpl_lph6', portIndex: 0 } },
      // 低加6 -> 低加5
      { id: 'tpl_conn10', from: { componentId: 'tpl_lph6', portIndex: 0 }, to: { componentId: 'tpl_lph5', portIndex: 0 } },
      // 低加5 -> 除氧器
      { id: 'tpl_conn11', from: { componentId: 'tpl_lph5', portIndex: 0 }, to: { componentId: 'tpl_deaerator', portIndex: 0 } },
      // 除氧器 -> 给水泵
      { id: 'tpl_conn12', from: { componentId: 'tpl_deaerator', portIndex: 0 }, to: { componentId: 'tpl_feed_pump', portIndex: 0 } },
      // 给水泵 -> 高加3
      { id: 'tpl_conn13', from: { componentId: 'tpl_feed_pump', portIndex: 0 }, to: { componentId: 'tpl_heater3', portIndex: 0 } },
      // 高加3 -> 高加2
      { id: 'tpl_conn14', from: { componentId: 'tpl_heater3', portIndex: 0 }, to: { componentId: 'tpl_heater2', portIndex: 0 } },
      // 高加2 -> 高加1
      { id: 'tpl_conn15', from: { componentId: 'tpl_heater2', portIndex: 0 }, to: { componentId: 'tpl_heater1', portIndex: 0 } },
      // 高加1 -> 锅炉
      { id: 'tpl_conn16', from: { componentId: 'tpl_heater1', portIndex: 0 }, to: { componentId: 'tpl_boiler', portIndex: 0 } },
    ]

    return { components: components_list, connections: connections_list }
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
