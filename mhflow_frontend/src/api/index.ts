import axios from 'axios'
import type { SystemModel, SolveResult, TemplateInfo, ComponentResult, SolveSummary, Component, Connection, Port, ComponentType, PortType } from '../types'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', msg)
    return Promise.reject(new Error(msg))
  }
)

/**
 * 判断JSON模型是前端格式还是后端格式
 */
function detectModelFormat(json: any): 'frontend' | 'backend' {
  const comps = json.components || []
  if (comps.length === 0) return 'frontend'
  const first = comps[0]
  // 前端格式特征：有 id, x, y 字段，type 为字符串
  if (first.id !== undefined && first.x !== undefined && first.y !== undefined) {
    return 'frontend'
  }
  // 后端格式特征：有 component_type, name 字段，没有 id
  if (first.component_type !== undefined && first.name !== undefined) {
    return 'backend'
  }
  return 'frontend'
}

/**
 * 从JSON文件打开模型（自动识别前端/后端格式并转换）
 */
export function openModelFromFile(json: any): SystemModel {
  const format = detectModelFormat(json)
  console.log(`[openModel] Detected format: ${format}`)

  if (format === 'backend') {
    return convertBackendToFrontendFormat(json)
  }

  // 前端格式：直接加载，但做基本的校验和补全
  const components: Component[] = []
  for (const comp of json.components || []) {
    components.push({
      id: comp.id || `comp_${Math.random().toString(36).slice(2)}`,
      type: comp.type || 'boiler',
      name: comp.name || '未命名',
      x: comp.x ?? 100,
      y: comp.y ?? 100,
      params: comp.params || {},
      inlet_ports: (comp.inlet_ports || []).map((p: any, idx: number) => ({
        id: p.id || `${comp.id}_in_${idx}`,
        name: p.name || `in_${idx}`,
        type: p.type || 'inlet',
        p: p.p ?? 0,
        t: p.t ?? 0,
        h: p.h ?? 0,
        m: p.m ?? 0,
        s: p.s ?? 0,
        w: p.w ?? 0,
      })),
      outlet_ports: (comp.outlet_ports || []).map((p: any, idx: number) => ({
        id: p.id || `${comp.id}_out_${idx}`,
        name: p.name || `out_${idx}`,
        type: p.type || 'outlet',
        p: p.p ?? 0,
        t: p.t ?? 0,
        h: p.h ?? 0,
        m: p.m ?? 0,
        s: p.s ?? 0,
        w: p.w ?? 0,
      })),
    })
  }

  const connections: Connection[] = (json.connections || []).map((c: any, idx: number) => ({
    id: c.id || `conn_${idx}`,
    from: {
      componentId: c.from?.componentId || '',
      portIndex: c.from?.portIndex ?? 0,
    },
    to: {
      componentId: c.to?.componentId || '',
      portIndex: c.to?.portIndex ?? 0,
    },
  }))

  return { components, connections }
}

/**
 * 将后端模型数据转换为前端格式
 * 处理差异：component_type→type、补充id/x/y、字符串连接→对象连接、 turbine抽汽端口展开
 */
function convertBackendToFrontendFormat(backendModel: any): SystemModel {
  const components: Component[] = []
  const nameToId: Record<string, string> = {}

  // 组件画布布局配置（3缸+8级回热）
  const layoutMap: Record<string, { x: number; y: number }> = {
    Boiler: { x: 100, y: 200 },
    HP_Turbine: { x: 280, y: 200 },
    IP_Turbine: { x: 480, y: 200 },
    LP_Turbine: { x: 680, y: 200 },
    Condenser: { x: 900, y: 400 },
    CondensatePump: { x: 820, y: 450 },
    LP_Heater_8: { x: 800, y: 320 },
    LP_Heater_7: { x: 720, y: 320 },
    LP_Heater_6: { x: 640, y: 320 },
    LP_Heater_5: { x: 560, y: 320 },
    Deaerator: { x: 480, y: 320 },
    FeedwaterPump: { x: 380, y: 400 },
    HP_Heater_3: { x: 360, y: 80 },
    HP_Heater_2: { x: 280, y: 80 },
    HP_Heater_1: { x: 200, y: 80 },
    Generator: { x: 900, y: 200 },
  }

  const typeMap: Record<string, ComponentType> = {
    boiler: 'boiler',
    turbine: 'turbine',
    condenser: 'condenser',
    heater: 'heater',
    pump: 'pump',
    generator: 'generator',
    tee: 'tee',
    pipe: 'pipe',
  }

  let compIndex = 0
  for (const comp of backendModel.components || []) {
    const name = comp.name
    const id = `be_${name.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()}_${compIndex++}`
    nameToId[name] = id

    const layout = layoutMap[name] || { x: 100 + (compIndex % 5) * 150, y: 100 + Math.floor(compIndex / 5) * 120 }

    // 入口端口
    const inlet_ports: Port[] = (comp.inlet_ports || []).map((p: any, idx: number) => ({
      id: `${id}_in_${idx}`,
      name: p.name,
      type: 'inlet' as PortType,
      p: p.p || 0,
      t: p.t || 0,
      h: p.h || 0,
      m: p.m || 0,
      s: p.s || 0,
      w: p.w || 0,
    }))

    // 出口端口
    const outlet_ports: Port[] = (comp.outlet_ports || []).map((p: any, idx: number) => ({
      id: `${id}_out_${idx}`,
      name: p.name,
      type: 'outlet' as PortType,
      p: p.p || 0,
      t: p.t || 0,
      h: p.h || 0,
      m: p.m || 0,
      s: p.s || 0,
      w: p.w || 0,
    }))

    // turbine 组件：根据 extractions / extraction_points 动态添加抽汽出口端口
    if (comp.component_type === 'turbine') {
      const extractions = comp.params?.extractions || comp.params?.extraction_points || []
      for (const ext of extractions) {
        const extName = ext.name
        if (!outlet_ports.find((p: Port) => p.name === extName)) {
          outlet_ports.push({
            id: `${id}_out_${extName}`,
            name: extName,
            type: 'outlet' as PortType,
            p: ext.p || 0,
            t: 0,
            h: 0,
            m: 0,
            s: 0,
          })
        }
      }
    }

    components.push({
      id,
      type: typeMap[comp.component_type] || (comp.component_type as ComponentType),
      name,
      x: layout.x,
      y: layout.y,
      params: { ...comp.params },
      inlet_ports,
      outlet_ports,
    })
  }

  // 转换连接关系："Component.port" → { componentId, portIndex }
  const connections: Connection[] = []
  let connIdx = 0
  for (const conn of backendModel.connections || []) {
    const fromParts = (conn.from || '').split('.')
    const toParts = (conn.to || '').split('.')
    if (fromParts.length !== 2 || toParts.length !== 2) continue

    const fromName = fromParts[0]
    const fromPort = fromParts[1]
    const toName = toParts[0]
    const toPort = toParts[1]

    const fromComp = components.find((c) => nameToId[fromName] === c.id)
    const toComp = components.find((c) => nameToId[toName] === c.id)
    if (!fromComp || !toComp) {
      console.warn(`[convertBackend] Connection skipped: ${conn.from} -> ${conn.to} (component not found)`)
      continue
    }

    const fromPortIndex = fromComp.outlet_ports.findIndex((p) => p.name === fromPort)
    const toPortIndex = toComp.inlet_ports.findIndex((p) => p.name === toPort)
    if (fromPortIndex === -1 || toPortIndex === -1) {
      console.warn(`[convertBackend] Connection skipped: ${conn.from} -> ${conn.to} (port not found)`)
      continue
    }

    connections.push({
      id: `conn_be_${connIdx++}`,
      from: { componentId: fromComp.id, portIndex: fromPortIndex },
      to: { componentId: toComp.id, portIndex: toPortIndex },
    })
  }

  console.log(`[convertBackend] Converted ${components.length} components, ${connections.length} connections`)
  return { components, connections }
}

/** 从后端加载模板模型 */
export async function loadModel(modelId: string): Promise<SystemModel> {
  const response = await apiClient.post<any>('/model/load', { template_id: modelId })
  const backendData = response.data
  if (!backendData.model_data) {
    throw new Error('后端返回数据缺少 model_data')
  }
  return convertBackendToFrontendFormat(backendData.model_data)
}

/** 保存模型 */
export async function saveModel(model: SystemModel, name: string = 'untitled'): Promise<{ id: string }> {
  const response = await apiClient.post<{ id: string }>('/model/save', { model_id: name, model_data: model })
  return response.data
}

/** 将前端模型数据转换为后端格式 */
function convertModelToBackendFormat(model: SystemModel): any {
  console.debug('convertModelToBackendFormat: called with model', model)
  
  // 验证model对象
  if (!model || typeof model !== 'object') {
    console.error('convertModelToBackendFormat: model is not a valid object', model)
    throw new Error('无效的模型数据')
  }
  
  // 验证components
  if (!model.components || !Array.isArray(model.components)) {
    console.error('convertModelToBackendFormat: components is not a valid array', model.components)
    throw new Error('无效的元件数据')
  }
  console.debug('convertModelToBackendFormat: components length', model.components.length)
  
  // 创建前端id到后端name的映射
  const idToNameMap = new Map<string, string>()
  
  // 确保connections是数组 - 处理Vue响应式Proxy对象
  let modelConnections: any[] = []
  if (model.connections) {
    console.debug('convertModelToBackendFormat: connections type', Object.prototype.toString.call(model.connections))
    console.debug('convertModelToBackendFormat: connections value', model.connections)
    // 处理多种可能的数组类型
    if (Array.isArray(model.connections)) {
      modelConnections = model.connections
    } else if (typeof model.connections === 'object' && 'length' in model.connections) {
      // 处理类数组对象或Vue响应式数组
      modelConnections = Array.from(model.connections as any)
    } else {
      console.error('convertModelToBackendFormat: connections is not an array-like object', model.connections)
    }
  }
  console.debug('convertModelToBackendFormat: processed connections length', modelConnections.length)
  
  // 转换连接格式
  const convertedConnections: any[] = []
  for (let index = 0; index < modelConnections.length; index++) {
    const conn = modelConnections[index]
    console.debug('convertModelToBackendFormat: processing connection', index, conn)
    
    if (!conn || typeof conn !== 'object') {
      console.warn('convertModelToBackendFormat: skipping invalid connection', conn)
      continue
    }
    
    if (!conn.from || !conn.to) {
      console.warn('convertModelToBackendFormat: connection missing from/to', conn)
      continue
    }
    
    // 找到源元件和端口
    const fromComp = model.components.find((c) => c.id === conn.from.componentId)
    const toComp = model.components.find((c) => c.id === conn.to.componentId)
    
    if (fromComp && toComp) {
      // 保存映射关系
      idToNameMap.set(fromComp.id, fromComp.name)
      idToNameMap.set(toComp.id, toComp.name)
      
      const fromPort = fromComp.outlet_ports[conn.from.portIndex]
      const toPort = toComp.inlet_ports[conn.to.portIndex]
      
      convertedConnections.push({
        from: `${fromComp.name}.${fromPort?.name || 'out'}`,
        to: `${toComp.name}.${toPort?.name || 'in'}`,
        type: conn.type,
      })
    } else {
      console.warn('convertModelToBackendFormat: could not find components for connection', conn)
    }
  }

  // 转换元件参数: 将前端参数名映射为后端参数名
  const convertedComponents: any[] = []
  for (const comp of model.components) {
    const newComp = { ...comp } as any
    const params = { ...comp.params } as Record<string, any>

    if (comp.type === 'heater') {
      // 向后兼容：旧参数名映射
      if ('terminal_temperature_difference' in params) {
        params.ttd = params.terminal_temperature_difference
        delete params.terminal_temperature_difference
      }
      if ('drain_cooler_approach' in params) {
        params.dca = params.drain_cooler_approach
        delete params.drain_cooler_approach
      }
      if ('extraction_pressure' in params) {
        params.p_heater = params.extraction_pressure
        delete params.extraction_pressure
      }
      if ('deaerator_pressure' in params) {
        params.p_heater = params.deaerator_pressure
        delete params.deaerator_pressure
      }
      if ('type' in params && !('heater_type' in params)) {
        const t = Number(params.type)
        if (t === 0) {
          params.heater_type = 'DA'
        } else {
          const p = params.p_heater || 1.0
          params.heater_type = p > 2.0 ? 'HP' : 'LP'
        }
        delete params.type
      }
    }

    if (comp.type === 'pump') {
      if ('outlet_pressure' in params) {
        params.p_out = params.outlet_pressure
        delete params.outlet_pressure
      }
      if ('isentropic_efficiency' in params) {
        params.eta_pump = params.isentropic_efficiency / 100.0
        delete params.isentropic_efficiency
      }
      if ('motor_efficiency' in params) {
        params.eta_motor = params.motor_efficiency / 100.0
        delete params.motor_efficiency
      }
    }

    if (comp.type === 'condenser') {
      if ('terminal_temperature_difference' in params) {
        params.ttd = params.terminal_temperature_difference
        delete params.terminal_temperature_difference
      }
      if ('cooling_range' in params) {
        params.delta_t_cw = params.cooling_range
        delete params.cooling_range
      }
      if ('condenser_pressure' in params) {
        params.p_cond = params.condenser_pressure
        delete params.condenser_pressure
      }
    }

    if (comp.type === 'generator') {
      if ('efficiency' in params) {
        params.eta_gen = params.efficiency / 100.0
        delete params.efficiency
      }
    }

    newComp.params = params
    convertedComponents.push(newComp)
  }

  // 保存映射信息供后续使用
  (window as any).__idToNameMap = idToNameMap

  const result = {
    ...model,
    components: convertedComponents,
    connections: convertedConnections,
  }
  
  console.debug('convertModelToBackendFormat: returning converted model', result)
  return result
}

/** 将后端求解结果转换为前端格式 */
function convertSolveResultFromBackend(rawResult: any): SolveResult {
  const components: ComponentResult[] = []
  
  // 获取之前保存的映射关系（前端id -> 后端name）
  const idToNameMap = (window as any).__idToNameMap as Map<string, string> || new Map()
  
  // 创建反向映射（后端name -> 前端id）
  const nameToIdMap = new Map<string, string>()
  idToNameMap.forEach((name, id) => {
    nameToIdMap.set(name, id)
  })
  
  // 转换元件结果
  const backendComponents = rawResult.components || {}
  for (const [name, compData] of Object.entries(backendComponents)) {
    const data = compData as {
      name?: string
      component_type?: string
      type?: string
      inlet_ports?: any[]
      outlet_ports?: any[]
      params?: Record<string, any>
      results?: Record<string, any>
    }
    // 使用名称作为ID（后端元件名称与前端模板名称一致）
    const compName = data.name || name
    // 尝试获取前端ID，如果找不到则使用后端名称
    const frontEndId = nameToIdMap.get(compName) || compName
    
    // 只保留 results 中的数值类型参数（过滤掉数组、对象等嵌套结构）
    const rawResults = data.results || {}
    const extra_params: Record<string, number> = {}
    for (const [k, v] of Object.entries(rawResults)) {
      if (typeof v === 'number') {
        extra_params[k] = v
      }
    }

    components.push({
      id: frontEndId,
      name: compName,
      type: data.component_type || data.type || '',
      inlet_ports: data.inlet_ports || [],
      outlet_ports: data.outlet_ports || [],
      extra_params,
    })
  }

  // 转换系统摘要
  const perf = rawResult.system_performance || {}
  const summary: SolveSummary = {
    power_output: perf.w_electrical_mw || 0,
    thermal_efficiency: (perf.eta_plant || 0) * 100, // 转换为百分比
    heat_rate: perf.heat_rate_kj_kwh || 0,
    coal_consumption: perf.coal_consumption_rate_g_kwh || 0,
    steam_rate: perf.steam_rate_kg_kwh || 0,
    auxiliary_power_rate: perf.auxiliary_power_rate || 0,
  }

  return {
    success: rawResult.status === 'success' && rawResult.converged,
    message: rawResult.converged ? undefined : '计算未收敛',
    components,
    summary,
  }
}

/** 执行求解计算 */
export async function solveModel(model: SystemModel): Promise<SolveResult> {
  console.debug('solveModel: called with model', model)
  
  try {
    const convertedModel = convertModelToBackendFormat(model)
    console.debug('solveModel: converted model ready, sending POST to /api/solve')
    
    const response = await apiClient.post<any>('/solve', { model_data: convertedModel })
    console.debug('solveModel: POST request successful, response:', response.data)
    
    return convertSolveResultFromBackend(response.data)
  } catch (error: any) {
    console.error('solveModel: error occurred', error)
    throw error
  }
}

/** 获取水蒸汽物性参数 */
export async function getSteamProperties(params: {
  pressure?: number
  temperature?: number
  enthalpy?: number
  entropy?: number
  quality?: number
}): Promise<Record<string, number>> {
  const response = await apiClient.get<{ data: Record<string, number> }>('/properties/steam', {
    params: {
      p: params.pressure,
      t: params.temperature,
      h: params.enthalpy,
      s: params.entropy,
    },
  })
  return response.data.data
}

/** 获取可用模板列表 */
export async function getTemplates(): Promise<TemplateInfo[]> {
  const response = await apiClient.get<{ templates: TemplateInfo[] }>('/templates/list')
  return response.data.templates
}

/** 导出模型为PDF */
export async function exportPDF(model: SystemModel, result: SolveResult | null): Promise<Blob> {
  const response = await apiClient.post('/export/pdf', { model, result }, {
    responseType: 'blob',
  })
  return response.data
}

/** 导出模型为Excel */
export async function exportExcel(model: SystemModel, result: SolveResult | null): Promise<Blob> {
  const response = await apiClient.post('/export/excel', { model, result }, {
    responseType: 'blob',
  })
  return response.data
}

export default apiClient
