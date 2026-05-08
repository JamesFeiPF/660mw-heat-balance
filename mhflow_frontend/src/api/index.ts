import axios from 'axios'
import type { SystemModel, SolveResult, TemplateInfo, ComponentResult, SolveSummary } from '../types'

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

/** 加载模型 */
export async function loadModel(modelId: string): Promise<SystemModel> {
  const response = await apiClient.post<SystemModel>('/model/load', { template_id: modelId })
  return response.data
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

  // 保存映射信息供后续使用
  (window as any).__idToNameMap = idToNameMap

  const result = {
    ...model,
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
    
    components.push({
      id: frontEndId,
      name: compName,
      type: data.component_type || data.type || '',
      inlet_ports: data.inlet_ports || [],
      outlet_ports: data.outlet_ports || [],
      extra_params: data.params || data.results || {},
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
    auxiliary_power_rate: 0, // 后端未提供此数据
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
