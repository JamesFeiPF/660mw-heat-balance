// MHFlow 热力系统仿真软件 - TypeScript 类型定义

/** 端口类型 */
export type PortType = 'inlet' | 'outlet'

/** 端口接口 - 表示元件的进出口 */
export interface Port {
  id: string
  name: string
  type: PortType
  /** 压力 (MPa) */
  p: number
  /** 温度 (°C) */
  t: number
  /** 焓 (kJ/kg) */
  h: number
  /** 质量流量 (kg/s) */
  m: number
  /** 熵 (kJ/(kg·K)) */
  s: number
}

/** 元件类型枚举 */
export type ComponentType =
  | 'boiler'        // 锅炉
  | 'turbine'       // 汽轮机
  | 'condenser'     // 凝汽器
  | 'heater'        // 加热器
  | 'pump'          // 水泵
  | 'pipe'          // 管道
  | 'generator'     // 发电机

/** 元件参数定义 */
export interface ComponentParamDef {
  key: string
  label: string
  unit: string
  default: number
  min: number
  max: number
  step: number
}

/** 元件接口 */
export interface Component {
  id: string
  type: ComponentType
  name: string
  /** 画布上的X坐标 */
  x: number
  /** 画布上的Y坐标 */
  y: number
  /** 元件参数 */
  params: Record<string, number>
  inlet_ports: Port[]
  outlet_ports: Port[]
}

/** 连接类型 */
export type ConnectionType = 'medium' | 'power'

/** 连接接口 */
export interface Connection {
  id: string
  from: {
    componentId: string
    portIndex: number
  }
  to: {
    componentId: string
    portIndex: number
  }
  /** 连接类型：medium-介质连接，power-能量连接 */
  type?: ConnectionType
}

/** 系统模型 */
export interface SystemModel {
  components: Component[]
  connections: Connection[]
}

/** 求解结果 - 元件级别 */
export interface ComponentResult {
  id: string
  name: string
  type: string
  inlet_ports: Port[]
  outlet_ports: Port[]
  extra_params: Record<string, number>
}

/** 求解结果 - 系统摘要 */
export interface SolveSummary {
  /** 发电量 (MW) */
  power_output: number
  /** 热效率 (%) */
  thermal_efficiency: number
  /** 热耗率 (kJ/(kW·h)) */
  heat_rate: number
  /** 煤耗 (g/(kW·h)) */
  coal_consumption: number
  /** 汽耗率 (kg/(kW·h)) */
  steam_rate: number
  /** 厂用电率 (%) */
  auxiliary_power_rate: number
}

/** 求解结果 */
export interface SolveResult {
  success: boolean
  message?: string
  components: ComponentResult[]
  summary: SolveSummary
}

/** 模板接口 */
export interface TemplateInfo {
  id: string
  name: string
  description: string
  model: SystemModel
}

/** 元件类型配置 */
export interface ComponentTypeConfig {
  type: ComponentType
  label: string
  color: string
  icon: string
  defaultParams: Record<string, number>
  paramDefs: ComponentParamDef[]
  defaultInletPorts: Port[]
  defaultOutletPorts: Port[]
}

/** 画布变换状态 */
export interface CanvasTransform {
  scale: number
  offsetX: number
  offsetY: number
}

/** 拖拽状态 */
export interface DragState {
  isDragging: boolean
  componentId: string | null
  startX: number
  startY: number
  offsetX: number
  offsetY: number
}

/** 连线状态 */
export interface ConnectState {
  isConnecting: boolean
  fromComponentId: string | null
  fromPortIndex: number
  fromPortType: PortType | null
  mouseX: number
  mouseY: number
}
