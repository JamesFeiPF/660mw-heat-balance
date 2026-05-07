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
function convertModelToBackendFormat(model: SystemModel): SystemModel {
  // 转换连接格式
  const convertedConnections = model.connections.map((conn) => {
    // 能量连接不需要转换
    if (conn.type === 'power') {
      return conn
    }
    
    // 找到源元件和端口
    const fromComp = model.components.find((c) => c.id === conn.from.componentId)
    const toComp = model.components.find((c) => c.id === conn.to.componentId)
    
    if (fromComp && toComp) {
      const fromPort = fromComp.outlet_ports[conn.from.portIndex]
      const toPort = toComp.inlet_ports[conn.to.portIndex]
      
      return {
        from: `${fromComp.name}.${fromPort?.name || 'out'}`,
        to: `${toComp.name}.${toPort?.name || 'in'}`,
      }
    }
    return conn
  })

  return {
    ...model,
    connections: convertedConnections,
  }
}

/** 将后端求解结果转换为前端格式 */
function convertSolveResultFromBackend(rawResult: any): SolveResult {
  const components: ComponentResult[] = []
  
  // 转换元件结果
  const backendComponents = rawResult.components || {}
  for (const [name, compData] of Object.entries(backendComponents)) {
    // 使用名称作为ID（后端元件名称与前端模板名称一致）
    const compName = compData.name || name
    components.push({
      id: compName,
      name: compName,
      type: compData.component_type || compData.type || '',
      inlet_ports: compData.inlet_ports || [],
      outlet_ports: compData.outlet_ports || [],
      extra_params: compData.params || compData.results || {},
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
  const convertedModel = convertModelToBackendFormat(model)
  const response = await apiClient.post<any>('/solve', { model_data: convertedModel })
  return convertSolveResultFromBackend(response.data)
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
