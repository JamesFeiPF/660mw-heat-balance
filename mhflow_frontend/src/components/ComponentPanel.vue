<template>
  <div class="component-panel">
    <div class="panel-header">
      <el-icon><Grid /></el-icon>
      <span>热力元件库</span>
    </div>
    <div class="panel-body">
      <div
        v-for="config in componentConfigs"
        :key="config.type"
        class="component-item"
        draggable="true"
        @dragstart="onDragStart($event, config.type)"
        @click="onAddComponent(config.type)"
      >
        <div class="component-icon" :style="{ borderColor: config.color }">
          <component :is="getIconComponent(config.type)" :color="config.color" />
        </div>
        <div class="component-info">
          <span class="component-name">{{ config.label }}</span>
          <span class="component-type">{{ config.type }}</span>
        </div>
      </div>
    </div>
    <div class="panel-footer">
      <el-button size="small" type="danger" plain @click="onClearAll" :disabled="componentCount === 0">
        <el-icon><Delete /></el-icon>
        清空画布
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component as VueComponent } from 'vue'
import { Grid, Delete } from '@element-plus/icons-vue'
import { useModelStore } from '../stores/model'
import type { ComponentType } from '../types'
import {
  BoilerIcon,
  TurbineIcon,
  CondenserIcon,
  HeaterIcon,
  PumpIcon,
  PipeIcon,
  GeneratorIcon,
} from './icons'

const store = useModelStore()

const componentConfigs = computed(() => store.getAllComponentConfigs())
const componentCount = computed(() => store.componentCount)

const iconMap: Record<string, VueComponent> = {
  boiler: BoilerIcon,
  turbine: TurbineIcon,
  condenser: CondenserIcon,
  heater: HeaterIcon,
  pump: PumpIcon,
  pipe: PipeIcon,
  generator: GeneratorIcon,
}

function getIconComponent(type: string): VueComponent {
  return iconMap[type] || BoilerIcon
}

function onDragStart(event: DragEvent, type: ComponentType) {
  event.dataTransfer?.setData('component-type', type)
  event.dataTransfer?.setData('text/plain', type)
}

function onAddComponent(type: ComponentType) {
  // 添加到画布中央附近随机位置
  const x = 300 + Math.random() * 200
  const y = 150 + Math.random() * 200
  const comp = store.addComponent(type, Math.round(x), Math.round(y))
  if (comp) store.selectComponent(comp.id)
}

function onClearAll() {
  store.clearModel()
}
</script>

<style scoped>
.component-panel {
  width: 220px;
  height: 100%;
  background: #16213e;
  border-right: 1px solid #0f3460;
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
  color: #3498db;
  font-size: 18px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.component-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.component-item:hover {
  background: rgba(52, 152, 219, 0.1);
  border-color: rgba(52, 152, 219, 0.3);
}

.component-item:active {
  cursor: grabbing;
  background: rgba(52, 152, 219, 0.2);
}

.component-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  border: 2px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.2);
}

.component-icon :deep(svg) {
  width: 28px;
  height: 28px;
}

.component-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.component-name {
  font-size: 13px;
  font-weight: 500;
  color: #e0e0e0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.component-type {
  font-size: 11px;
  color: #888;
  text-transform: uppercase;
}

.panel-footer {
  padding: 10px;
  border-top: 1px solid #0f3460;
}

.panel-footer .el-button {
  width: 100%;
}
</style>
