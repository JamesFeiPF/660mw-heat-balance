<template>
  <div class="property-panel">
    <div class="panel-header">
      <el-icon><Setting /></el-icon>
      <span>属性与结果</span>
    </div>

    <el-tabs v-model="activeTab" class="panel-tabs">
      <!-- Tab1: 属性编辑 -->
      <el-tab-pane label="属性编辑" name="properties">
        <div v-if="selectedComponent" class="tab-content">
          <div class="comp-header">
            <div class="comp-type-badge" :style="{ background: getComponentColor(selectedComponent.type) }">
              {{ getTypeLabel(selectedComponent.type) }}
            </div>
            <el-input
              v-model="editableName"
              size="small"
              class="comp-name-input"
              @blur="onNameChange"
            />
          </div>

          <div class="section-title">元件参数</div>
          <div class="params-form">
            <div
              v-for="paramDef in paramDefs"
              :key="paramDef.key"
              class="param-item"
            >
              <label class="param-label">
                <span v-if="paramDef.required" class="required-flag" title="必填参数">*</span>
                {{ paramDef.label }}
                <span class="param-unit">({{ paramDef.unit }})</span>
                <el-tooltip v-if="paramDef.description" :content="paramDef.description" placement="top">
                  <span class="param-help">?</span>
                </el-tooltip>
              </label>
              <el-select
                v-if="paramDef.options"
                :model-value="selectedComponent.params[paramDef.key]"
                size="small"
                class="param-input"
                @change="(val: string) => onParamChange(paramDef.key, val)"
              >
                <el-option
                  v-for="opt in paramDef.options"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
              <el-input-number
                v-else
                :model-value="selectedComponent.params[paramDef.key]"
                size="small"
                :min="paramDef.min"
                :max="paramDef.max"
                :step="paramDef.step"
                :precision="paramDef.step && paramDef.step < 1 ? (paramDef.step < 0.01 ? 3 : paramDef.step < 0.1 ? 2 : 1) : 0"
                controls-position="right"
                class="param-input"
                @change="(val: number) => onParamChange(paramDef.key, val)"
              />
            </div>
          </div>

          <div class="section-title">端口信息</div>
          <div class="ports-info">
            <div class="port-group">
              <div class="port-group-title inlet">进口端口</div>
              <div
                v-for="port in selectedComponent.inlet_ports"
                :key="port.id"
                class="port-detail"
              >
                <span class="port-name">{{ port.name }}</span>
                <div class="port-values" v-if="hasPortValue(port)">
                  <span v-if="port.p > 0" class="port-value">{{ port.p.toFixed(3) }} MPa</span>
                  <span v-if="port.t > 0" class="port-value">{{ port.t.toFixed(1) }} °C</span>
                  <span v-if="port.m > 0" class="port-value">{{ port.m.toFixed(1) }} kg/s</span>
                  <span v-if="port.h > 0" class="port-value">{{ port.h.toFixed(0) }} kJ/kg</span>
                  <span v-if="port.w && port.w > 0" class="port-value">{{ port.w.toFixed(0) }} kW</span>
                </div>
                <div class="port-values" v-else>
                  <span class="port-value muted">未计算</span>
                </div>
              </div>
            </div>
            <div class="port-group">
              <div class="port-group-title outlet">出口端口</div>
              <div
                v-for="port in selectedComponent.outlet_ports"
                :key="port.id"
                class="port-detail"
              >
                <span class="port-name">{{ port.name }}</span>
                <div class="port-values" v-if="hasPortValue(port)">
                  <span v-if="port.p > 0" class="port-value">{{ port.p.toFixed(3) }} MPa</span>
                  <span v-if="port.t > 0" class="port-value">{{ port.t.toFixed(1) }} °C</span>
                  <span v-if="port.m > 0" class="port-value">{{ port.m.toFixed(1) }} kg/s</span>
                  <span v-if="port.h > 0" class="port-value">{{ port.h.toFixed(0) }} kJ/kg</span>
                  <span v-if="port.w && port.w > 0" class="port-value">{{ port.w.toFixed(0) }} kW</span>
                </div>
                <div class="port-values" v-else>
                  <span class="port-value muted">未计算</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 计算结果 - 设备级别 -->
          <div class="section-title">计算结果</div>
          <div class="calc-results" v-if="componentResult">
            <!-- 进口参数 -->
            <div class="port-section" v-if="componentResult.inlet_ports && componentResult.inlet_ports.length > 0">
              <div class="port-section-title">进口参数</div>
              <div class="port-detail" v-for="(port, idx) in componentResult.inlet_ports" :key="'in-' + idx">
                <span class="port-name">{{ port.name }}</span>
                <div class="port-values">
                  <span class="port-value" :class="{ 'has-value': port.p > 0 }">p: {{ port.p > 0 ? port.p.toFixed(3) : '-' }} MPa</span>
                  <span class="port-value" :class="{ 'has-value': port.t > 0 }">t: {{ port.t > 0 ? port.t.toFixed(1) : '-' }} °C</span>
                  <span class="port-value" :class="{ 'has-value': port.m > 0 }">m: {{ port.m > 0 ? port.m.toFixed(2) : '-' }} kg/s</span>
                  <span class="port-value" :class="{ 'has-value': port.h > 0 }">h: {{ port.h > 0 ? port.h.toFixed(0) : '-' }} kJ/kg</span>
                </div>
              </div>
            </div>
            
            <!-- 出口参数 -->
            <div class="port-section" v-if="componentResult.outlet_ports && componentResult.outlet_ports.length > 0">
              <div class="port-section-title">出口参数</div>
              <div class="port-detail" v-for="(port, idx) in componentResult.outlet_ports" :key="'out-' + idx">
                <span class="port-name">{{ port.name }}</span>
                <div class="port-values">
                  <span class="port-value" :class="{ 'has-value': port.p > 0 }">p: {{ port.p > 0 ? port.p.toFixed(3) : '-' }} MPa</span>
                  <span class="port-value" :class="{ 'has-value': port.t > 0 }">t: {{ port.t > 0 ? port.t.toFixed(1) : '-' }} °C</span>
                  <span class="port-value" :class="{ 'has-value': port.m > 0 }">m: {{ port.m > 0 ? port.m.toFixed(2) : '-' }} kg/s</span>
                  <span class="port-value" :class="{ 'has-value': port.h > 0 }">h: {{ port.h > 0 ? port.h.toFixed(0) : '-' }} kJ/kg</span>
                </div>
              </div>
            </div>
            
            <!-- 其他计算结果 -->
            <div class="other-results" v-if="Object.keys(componentResult.extra_params).length > 0">
              <div class="port-section-title">性能指标</div>
              <div class="result-item" v-for="(value, key) in componentResult.extra_params" :key="key">
                <span class="result-label">{{ getResultLabel(key) }}</span>
                <span class="result-value">{{ formatResultValue(key, value) }}</span>
              </div>
            </div>
            
            <div v-if="(!componentResult.inlet_ports || componentResult.inlet_ports.length === 0) && 
                      (!componentResult.outlet_ports || componentResult.outlet_ports.length === 0) && 
                      Object.keys(componentResult.extra_params).length === 0" class="empty-results">
              <span class="muted">暂无计算结果</span>
            </div>
          </div>
          <div class="calc-results" v-else-if="store.solveResult?.success">
            <div class="empty-results">
              <span class="muted">该元件暂无详细计算结果</span>
            </div>
          </div>
          <div class="calc-results" v-else>
            <div class="empty-results">
              <span class="muted">请先执行计算</span>
            </div>
          </div>

          <el-button
            type="danger"
            size="small"
            plain
            class="delete-btn"
            @click="onDeleteComponent"
          >
            <el-icon><Delete /></el-icon>
            删除元件
          </el-button>
        </div>

        <div v-else class="empty-state">
          <el-icon :size="40" color="#555"><InfoFilled /></el-icon>
          <p>请选择一个元件查看属性</p>
        </div>
      </el-tab-pane>

      <!-- Tab2: 计算结果 -->
      <el-tab-pane label="计算结果" name="results">
        <div v-if="store.solveResult?.success" class="tab-content">
          <div class="result-header success">
            <el-icon><SuccessFilled /></el-icon>
            <span>计算完成</span>
          </div>

          <el-table
            :data="store.solveResult.components"
            size="small"
            stripe
            max-height="400"
            class="result-table"
          >
            <el-table-column prop="name" label="元件" width="100" fixed />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                {{ getTypeLabel(row.type) }}
              </template>
            </el-table-column>
            <el-table-column label="进口参数">
              <template #default="{ row }">
                <div v-for="(port, idx) in row.inlet_ports" :key="idx" class="port-cell">
                  <span>{{ port.p.toFixed(2) }}MPa</span>
                  <span>{{ port.t.toFixed(1) }}°C</span>
                  <span>{{ port.h.toFixed(0) }}kJ/kg</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="出口参数">
              <template #default="{ row }">
                <div v-for="(port, idx) in row.outlet_ports" :key="idx" class="port-cell">
                  <span>{{ port.p.toFixed(2) }}MPa</span>
                  <span>{{ port.t.toFixed(1) }}°C</span>
                  <span>{{ port.h.toFixed(0) }}kJ/kg</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-else-if="store.solveError" class="tab-content">
          <div class="result-header error">
            <el-icon><CircleCloseFilled /></el-icon>
            <span>计算失败</span>
          </div>
          <el-alert :title="store.solveError" type="error" :closable="false" show-icon />
        </div>

        <div v-else class="empty-state">
          <el-icon :size="40" color="#555"><DataAnalysis /></el-icon>
          <p>尚未执行计算</p>
          <p class="sub">请先搭建系统模型，然后点击"执行计算"</p>
        </div>
      </el-tab-pane>

      <!-- Tab3: 系统指标 -->
      <el-tab-pane label="系统指标" name="summary">
        <div v-if="store.solveResult?.success" class="tab-content">
          <div class="summary-cards">
            <div class="summary-card">
              <div class="card-icon" style="background: rgba(46, 204, 113, 0.15)">
                <el-icon :size="24" color="#2ecc71"><Odometer /></el-icon>
              </div>
              <div class="card-info">
                <span class="card-label">发电量</span>
                <span class="card-value">{{ store.solveResult.summary.power_output.toFixed(1) }} <small>MW</small></span>
              </div>
            </div>

            <div class="summary-card">
              <div class="card-icon" style="background: rgba(52, 152, 219, 0.15)">
                <el-icon :size="24" color="#3498db"><TrendCharts /></el-icon>
              </div>
              <div class="card-info">
                <span class="card-label">热效率</span>
                <span class="card-value">{{ store.solveResult.summary.thermal_efficiency.toFixed(2) }} <small>%</small></span>
              </div>
            </div>

            <div class="summary-card">
              <div class="card-icon" style="background: rgba(231, 76, 60, 0.15)">
                <el-icon :size="24" color="#e74c3c"><Sunny /></el-icon>
              </div>
              <div class="card-info">
                <span class="card-label">热耗率</span>
                <span class="card-value">{{ store.solveResult.summary.heat_rate.toFixed(0) }} <small>kJ/(kW·h)</small></span>
              </div>
            </div>

            <div class="summary-card">
              <div class="card-icon" style="background: rgba(243, 156, 18, 0.15)">
                <el-icon :size="24" color="#f39c12"><Coin /></el-icon>
              </div>
              <div class="card-info">
                <span class="card-label">煤耗</span>
                <span class="card-value">{{ store.solveResult.summary.coal_consumption.toFixed(1) }} <small>g/(kW·h)</small></span>
              </div>
            </div>

            <div class="summary-card">
              <div class="card-icon" style="background: rgba(155, 89, 182, 0.15)">
                <el-icon :size="24" color="#9b59b6"><WindPower /></el-icon>
              </div>
              <div class="card-info">
                <span class="card-label">汽耗率</span>
                <span class="card-value">{{ store.solveResult.summary.steam_rate.toFixed(2) }} <small>kg/(kW·h)</small></span>
              </div>
            </div>

            <div class="summary-card">
              <div class="card-icon" style="background: rgba(26, 188, 156, 0.15)">
                <el-icon :size="24" color="#1abc9c"><Lightning /></el-icon>
              </div>
              <div class="card-info">
                <span class="card-label">厂用电率</span>
                <span class="card-value">{{ store.solveResult.summary.auxiliary_power_rate.toFixed(2) }} <small>%</small></span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <el-icon :size="40" color="#555"><DataLine /></el-icon>
          <p>暂无系统指标</p>
          <p class="sub">完成计算后将显示系统整体性能指标</p>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Setting,
  Delete,
  InfoFilled,
  SuccessFilled,
  CircleCloseFilled,
  DataAnalysis,
  Odometer,
  TrendCharts,
  Sunny,
  Coin,
  WindPower,
  Lightning,
  DataLine,
} from '@element-plus/icons-vue'
import { useModelStore } from '../stores/model'
import type { ComponentTypeConfig } from '../types'

const store = useModelStore()
const activeTab = ref('properties')
const editableName = ref('')

const selectedComponent = computed(() => store.selectedComponent)

const paramDefs = computed<ComponentTypeConfig['paramDefs']>(() => {
  if (!selectedComponent.value) return []
  const config = store.getComponentConfig(selectedComponent.value.type)
  return config?.paramDefs || []
})

const componentResult = computed(() => {
  if (!selectedComponent.value || !store.solveResult?.success) return null
  return store.solveResult.components.find(
    (comp) => comp.id === selectedComponent.value?.id
  ) || null
})

function getResultLabel(key: string): string {
  const labels: Record<string, string> = {
    power_output: '功率输出',
    efficiency: '效率',
    heat_rate: '热耗率',
    coal_consumption: '煤耗',
    steam_rate: '汽耗率',
    enthalpy_drop: '焓降',
    mass_flow: '质量流量',
    pressure_ratio: '压比',
    temperature_rise: '温升',
    heat_duty: '热负荷',
    pump_power: '泵功率',
    turbine_power: '汽轮机功率',
    generator_power: '发电机功率',
    w_mechanical: '机械功率',
    w_electrical: '电功率',
    w_internal: '内功率',
    w_internal_mw: '内功率(MW)',
    w_shaft: '轴功率',
    w_shaft_mw: '轴功率(MW)',
    eta_isen: '等熵效率',
    eta_mech: '机械效率',
    eta_gen: '发电效率',
    m_steam: '抽汽量',
    q_water: '水侧吸热量',
    q_steam: '蒸汽放热量',
    p_shaft: '泵轴功率',
    p_motor: '泵电机功率',
    h_drop_isen: '等熵焓降',
    h_drop_actual: '实际焓降',
  }
  return labels[key] || key
}

function formatResultValue(key: string, value: any): string {
  // 防御性转换：处理 numpy 类型、字符串、null 等非原生 number
  const num = typeof value === 'number' ? value : Number(value)
  if (!isFinite(num)) {
    return String(value)
  }

  if (key.includes('power') || key.includes('Power') || key.includes('_mw')) {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(2)} MW`
    }
    return `${num.toFixed(0)} kW`
  }
  if (key.includes('efficiency') || key.includes('eta')) {
    return `${num.toFixed(2)} %`
  }
  if (key.includes('heat_rate')) {
    return `${num.toFixed(0)} kJ/(kW·h)`
  }
  if (key.includes('coal_consumption')) {
    return `${num.toFixed(1)} g/(kW·h)`
  }
  if (key.includes('steam_rate')) {
    return `${num.toFixed(2)} kg/(kW·h)`
  }
  if (key.includes('enthalpy') || key.includes('h_') || key.includes('h_drop')) {
    return `${num.toFixed(0)} kJ/kg`
  }
  if (key.includes('mass_flow') || key === 'm_steam' || key === 'm') {
    return `${num.toFixed(2)} kg/s`
  }
  if (key.includes('pressure') || key.includes('p_') || key.includes('p_out')) {
    return `${num.toFixed(3)} MPa`
  }
  if (key.includes('temperature') || key.includes('t_')) {
    return `${num.toFixed(1)} °C`
  }
  if (key.includes('ratio')) {
    return `${num.toFixed(3)}`
  }
  return `${num.toFixed(2)}`
}

watch(selectedComponent, (comp) => {
  if (comp) {
    editableName.value = comp.name
  }
}, { immediate: true })

function onNameChange() {
  if (selectedComponent.value && editableName.value.trim()) {
    store.updateComponent(selectedComponent.value.id, { name: editableName.value.trim() })
  }
}

function onParamChange(key: string, value: number | string) {
  if (selectedComponent.value) {
    store.updateComponentParam(selectedComponent.value.id, key, value)
  }
}

function onDeleteComponent() {
  if (selectedComponent.value) {
    store.removeComponent(selectedComponent.value.id)
  }
}

function hasPortValue(port: any): boolean {
  // 功率端口检查 w 字段
  if (port.name?.includes('power') && port.w !== undefined) {
    return port.w !== 0
  }
  // 普通端口检查 p/t/m/h
  return (port.p > 0 || port.t > 0 || port.m > 0 || port.h > 0)
}

function getComponentColor(type: string): string {
  const colors: Record<string, string> = {
    boiler: '#e74c3c',
    turbine: '#3498db',
    turbine_hp: '#3498db',
    turbine_ip: '#2980b9',
    turbine_lp: '#1a5276',
    condenser: '#1abc9c',
    heater: '#f39c12',
    pump: '#9b59b6',
    pipe: '#95a5a6',
    generator: '#2ecc71',
  }
  return colors[type] || '#7f8c8d'
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    boiler: '锅炉',
    turbine: '汽轮机',
    turbine_hp: '高压缸',
    turbine_ip: '中压缸',
    turbine_lp: '低压缸',
    condenser: '凝汽器',
    heater: '加热器',
    pump: '水泵',
    pipe: '管道',
    generator: '发电机',
  }
  return labels[type] || type
}
</script>

<style scoped>
.property-panel {
  width: 320px;
  height: 100%;
  background: #16213e;
  border-left: 1px solid #0f3460;
  display: flex;
  flex-direction: column;
  user-select: none;
}

.panel-header {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #e0e0e0;
  border-bottom: 1px solid #0f3460;
  background: #1a1a2e;
}

.panel-header .el-icon {
  color: #f39c12;
  font-size: 18px;
}

.panel-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-tabs :deep(.el-tabs__header) {
  margin: 0;
  background: #1a1a2e;
  border-bottom: 1px solid #0f3460;
}

.panel-tabs :deep(.el-tabs__item) {
  color: #888;
  font-size: 12px;
  padding: 0 12px;
  height: 36px;
  line-height: 36px;
}

.panel-tabs :deep(.el-tabs__item.is-active) {
  color: #3498db;
}

.panel-tabs :deep(.el-tabs__nav-wrap::after) {
  background: #0f3460;
}

.panel-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}

.tab-content {
  padding: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #666;
  text-align: center;
}

.empty-state p {
  margin-top: 12px;
  font-size: 13px;
}

.empty-state .sub {
  font-size: 11px;
  color: #555;
  margin-top: 4px;
}

.comp-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.comp-type-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.comp-name-input {
  flex: 1;
}

.comp-name-input :deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.2);
  box-shadow: none;
  border: 1px solid #0f3460;
}

.comp-name-input :deep(.el-input__inner) {
  color: #e0e0e0;
  font-size: 13px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  margin: 16px 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #0f3460;
}

.params-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.param-label {
  font-size: 12px;
  color: #ccc;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 3px;
}

.param-unit {
  color: #666;
  font-size: 10px;
}

.required-flag {
  color: #f39c12;
  font-weight: bold;
  font-size: 14px;
}

.param-help {
  color: #3498db;
  font-size: 12px;
  font-weight: bold;
  cursor: help;
  margin-left: 2px;
}

.param-input {
  width: 130px;
}

.param-input :deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.2);
  box-shadow: none;
  border: 1px solid #0f3460;
}

.param-input :deep(.el-input__inner) {
  color: #e0e0e0;
  font-size: 12px;
}

.ports-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.port-group-title {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
  margin-bottom: 4px;
  display: inline-block;
}

.port-group-title.inlet {
  background: rgba(52, 152, 219, 0.2);
  color: #3498db;
}

.port-group-title.outlet {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.port-detail {
  padding: 6px 8px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  margin-bottom: 4px;
}

.port-name {
  font-size: 11px;
  color: #aaa;
  display: block;
  margin-bottom: 2px;
}

.port-values {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.port-value {
  font-size: 11px;
  color: #e0e0e0;
  font-family: 'Consolas', monospace;
}

.port-value.muted {
  color: #555;
  font-style: italic;
}

.calc-results {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  padding: 8px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.result-item:last-child {
  border-bottom: none;
}

.result-label {
  font-size: 11px;
  color: #888;
}

.result-value {
  font-size: 12px;
  color: #3498db;
  font-family: 'Consolas', monospace;
  font-weight: 500;
}

.empty-results {
  padding: 8px;
  text-align: center;
}

.port-section {
  margin-bottom: 12px;
}

.port-section-title {
  font-size: 11px;
  color: #3498db;
  font-weight: 500;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(52, 152, 219, 0.2);
}

.port-value.has-value {
  color: #2ecc71;
}

.other-results {
  margin-top: 12px;
}

.delete-btn {
  width: 100%;
  margin-top: 20px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 500;
}

.result-header.success {
  background: rgba(46, 204, 113, 0.1);
  color: #2ecc71;
  border: 1px solid rgba(46, 204, 113, 0.3);
}

.result-header.error {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  border: 1px solid rgba(231, 76, 60, 0.3);
}

.result-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(15, 52, 96, 0.5);
  --el-table-text-color: #ccc;
  --el-table-header-text-color: #aaa;
  --el-table-border-color: #0f3460;
  --el-table-row-hover-bg-color: rgba(52, 152, 219, 0.08);
  font-size: 11px;
}

.port-cell {
  display: flex;
  flex-direction: column;
  gap: 1px;
  font-size: 10px;
  font-family: 'Consolas', monospace;
}

.summary-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  border: 1px solid #0f3460;
}

.card-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-label {
  font-size: 11px;
  color: #888;
}

.card-value {
  font-size: 18px;
  font-weight: 700;
  color: #e0e0e0;
  font-family: 'Consolas', monospace;
}

.card-value small {
  font-size: 11px;
  font-weight: 400;
  color: #888;
}
</style>
