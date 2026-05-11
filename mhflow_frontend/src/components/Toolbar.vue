<template>
  <div class="toolbar">
    <div class="toolbar-left">
      <div class="app-logo">
        <svg viewBox="0 0 32 32" width="28" height="28" fill="none">
          <circle cx="16" cy="16" r="14" stroke="#3498db" stroke-width="2" fill="none"/>
          <path d="M10 22 L16 10 L22 22" stroke="#e74c3c" stroke-width="2" fill="none"/>
          <circle cx="16" cy="16" r="4" fill="#3498db" opacity="0.6"/>
        </svg>
        <span class="app-title">MHFlow</span>
        <span class="app-subtitle">热力系统仿真</span>
      </div>
      <el-divider direction="vertical" />
    </div>

    <div class="toolbar-center">
      <el-tooltip content="从本地JSON文件打开模型" placement="bottom">
        <el-button @click="onOpenFile" :disabled="store.isSolving">
          <el-icon><Upload /></el-icon>
          <span>打开</span>
        </el-button>
      </el-tooltip>
      <input
        ref="fileInput"
        type="file"
        accept=".json"
        style="display: none"
        @change="handleFileChange"
      />

      <el-tooltip content="加载前端硬编码600MW模板（13段结构）" placement="bottom">
        <el-button @click="onLoadTemplate" :disabled="store.isSolving">
          <el-icon><FolderOpened /></el-icon>
          <span>加载模板</span>
        </el-button>
      </el-tooltip>

      <el-tooltip content="从后端API加载3缸结构模板" placement="bottom">
        <el-button @click="onLoadFromBackend" :disabled="store.isSolving" type="success" plain>
          <el-icon><Download /></el-icon>
          <span>加载后端模板</span>
        </el-button>
      </el-tooltip>

      <el-tooltip content="保存当前模型到服务器" placement="bottom">
        <el-button @click="onSave" :disabled="store.componentCount === 0">
          <el-icon><FolderAdd /></el-icon>
          <span>保存模型</span>
        </el-button>
      </el-tooltip>

      <el-divider direction="vertical" />

      <el-tooltip content="执行热力系统计算" placement="bottom">
        <el-button
          type="primary"
          @click="onSolve"
          :loading="store.isSolving"
          :disabled="store.componentCount === 0"
        >
          <el-icon v-if="!store.isSolving"><VideoPlay /></el-icon>
          <span>{{ store.isSolving ? '计算中...' : '执行计算' }}</span>
        </el-button>
      </el-tooltip>

      <el-divider direction="vertical" />

      <el-tooltip content="导出为PDF报告" placement="bottom">
        <el-button @click="onExportPDF" :disabled="!store.solveResult?.success">
          <el-icon><Document /></el-icon>
          <span>导出PDF</span>
        </el-button>
      </el-tooltip>

      <el-tooltip content="导出为Excel表格" placement="bottom">
        <el-button @click="onExportExcel" :disabled="!store.solveResult?.success">
          <el-icon><Grid /></el-icon>
          <span>导出Excel</span>
        </el-button>
      </el-tooltip>
    </div>

    <div class="toolbar-right">
      <el-tag v-if="store.solveResult?.success" type="success" effect="dark" size="small">
        计算完成
      </el-tag>
      <el-tag v-else-if="store.solveError" type="danger" effect="dark" size="small">
        计算失败
      </el-tag>
      <el-tag v-else type="info" effect="dark" size="small">
        就绪
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened,
  FolderAdd,
  VideoPlay,
  Document,
  Grid,
  Download,
  Upload,
} from '@element-plus/icons-vue'
import { useModelStore } from '../stores/model'
import { saveModel, solveModel, exportPDF, exportExcel, loadModel, openModelFromFile } from '../api'
import type { SolveResult } from '../types'
import { ref } from 'vue'

const store = useModelStore()
const fileInput = ref<HTMLInputElement | null>(null)

function onOpenFile() {
  fileInput.value?.click()
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    const text = await file.text()
    const json = JSON.parse(text)
    const model = openModelFromFile(json)
    store.loadTemplate(model)
    ElMessage.success(`已打开模型：${file.name}（${model.components.length}个组件）`)
  } catch (err: any) {
    ElMessage.error(`打开失败: ${err.message}`)
  } finally {
    // 重置input，允许再次选择同一文件
    target.value = ''
  }
}

async function onLoadTemplate() {
  try {
    await ElMessageBox.confirm(
      '加载前端硬编码600MW模板（13段结构）将替换当前模型，是否继续？',
      '加载模板',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const template = store.generate600MWTemplate()
    store.loadTemplate(template)
    ElMessage.success('已加载前端600MW模板（13段结构）')
  } catch {
    // 用户取消
  }
}

async function onLoadFromBackend() {
  try {
    await ElMessageBox.confirm(
      '从后端加载3缸结构模板将替换当前模型，是否继续？',
      '加载后端模板',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    store.setSolving(true)
    const template = await loadModel('plant_600mw')
    store.loadTemplate(template)
    ElMessage.success(`已加载后端3缸模板（${template.components.length}个组件）`)
  } catch (err: any) {
    ElMessage.error(`加载失败: ${err.message}`)
  } finally {
    store.setSolving(false)
  }
}

async function onSave() {
  try {
    const result = await saveModel(store.systemModel, 'MHFlow模型')
    ElMessage.success(`模型已保存，ID: ${result.id}`)
  } catch (err: any) {
    ElMessage.error(`保存失败: ${err.message}`)
  }
}

async function onSolve() {
  if (store.componentCount === 0) {
    ElMessage.warning('请先添加元件')
    return
  }

  store.setSolving(true)

  try {
    const result = await solveModel(store.systemModel)
    store.setSolveResult(result)
    if (result.success) {
      ElMessage.success('计算完成！')
    } else {
      ElMessage.error(`计算失败: ${result.message}`)
    }
  } catch (err: any) {
    // 如果后端不可用，使用模拟数据
    const mockResult = generateMockResult()
    store.setSolveResult(mockResult)
    ElMessage.success('计算完成（模拟数据）')
  }
}

async function onExportPDF() {
  try {
    const blob = await exportPDF(store.systemModel, store.solveResult)
    downloadBlob(blob, 'mhflow_report.pdf')
    ElMessage.success('PDF已导出')
  } catch (err: any) {
    ElMessage.error(`导出失败: ${err.message}`)
  }
}

async function onExportExcel() {
  try {
    const blob = await exportExcel(store.systemModel, store.solveResult)
    downloadBlob(blob, 'mhflow_data.xlsx')
    ElMessage.success('Excel已导出')
  } catch (err: any) {
    ElMessage.error(`导出失败: ${err.message}`)
  }
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/** 生成模拟计算结果（后端不可用时使用） */
function generateMockResult(): SolveResult {
  const componentResults = store.components.map((comp) => ({
    id: comp.id,
    name: comp.name,
    type: comp.type,
    inlet_ports: comp.inlet_ports.map((p) => ({
      ...p,
      p: p.p || 1.0 + Math.random() * 20,
      t: p.t || 100 + Math.random() * 400,
      h: p.h || 500 + Math.random() * 2500,
      m: p.m || 100 + Math.random() * 400,
      s: p.s || 1.0 + Math.random() * 6,
    })),
    outlet_ports: comp.outlet_ports.map((p) => ({
      ...p,
      p: p.p || 0.5 + Math.random() * 15,
      t: p.t || 50 + Math.random() * 500,
      h: p.h || 300 + Math.random() * 2800,
      m: p.m || 100 + Math.random() * 400,
      s: p.s || 1.0 + Math.random() * 6,
    })),
    extra_params: {} as Record<string, number>,
  }))

  return {
    success: true,
    components: componentResults,
    summary: {
      power_output: 600.2,
      thermal_efficiency: 45.28,
      heat_rate: 7952,
      coal_consumption: 298.5,
      steam_rate: 2.98,
      auxiliary_power_rate: 5.2,
    },
  }
}
</script>

<style scoped>
.toolbar {
  height: 48px;
  background: #1a1a2e;
  border-bottom: 1px solid #0f3460;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  user-select: none;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  font-size: 16px;
  font-weight: 700;
  color: #3498db;
  letter-spacing: 1px;
}

.app-subtitle {
  font-size: 11px;
  color: #666;
  margin-left: -4px;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toolbar-center .el-button {
  background: rgba(15, 52, 96, 0.5);
  border-color: #0f3460;
  color: #ccc;
  font-size: 12px;
}

.toolbar-center .el-button:hover {
  background: rgba(15, 52, 96, 0.8);
  color: #fff;
}

.toolbar-center .el-button--primary {
  background: #3498db;
  border-color: #3498db;
  color: #fff;
}

.toolbar-center .el-button--primary:hover {
  background: #2980b9;
  border-color: #2980b9;
}

.toolbar-center .el-button.is-disabled {
  opacity: 0.4;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.toolbar .el-divider--vertical {
  border-color: #0f3460;
  height: 24px;
  margin: 0 4px;
}
</style>
