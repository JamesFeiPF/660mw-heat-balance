<template>
  <div
    class="model-canvas"
    ref="canvasContainer"
    @dragover.prevent
    @drop="onDrop"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
    @wheel.prevent="onWheel"
    @contextmenu.prevent
  >
    <canvas ref="canvasEl" :width="canvasWidth" :height="canvasHeight"></canvas>

    <!-- 缩放控制 -->
    <div class="zoom-controls">
      <el-button-group size="small">
        <el-button @click="zoomIn" :icon="ZoomIn" />
        <el-button @click="zoomReset">{{ Math.round(transform.scale * 100) }}%</el-button>
        <el-button @click="zoomOut" :icon="ZoomOut" />
        <el-button @click="fitView" :icon="FullScreen" />
      </el-button-group>
    </div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <span>元件: {{ store.componentCount }}</span>
      <span>|</span>
      <span>连接: {{ store.connectionCount }}</span>
      <span>|</span>
      <span>缩放: {{ Math.round(transform.scale * 100) }}%</span>
      <span>|</span>
      <span>坐标: ({{ Math.round(mouseCanvasPos.x) }}, {{ Math.round(mouseCanvasPos.y) }})</span>
    </div>

    <!-- 操作提示 -->
    <div class="hint-bar" v-if="connectingState.isConnecting">
      <el-tag type="warning" effect="dark" size="small">
        连线模式：点击目标元件的进口端口完成连线，按 Esc 取消
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ZoomIn, ZoomOut, FullScreen } from '@element-plus/icons-vue'
import { useModelStore } from '../stores/model'
import type { ComponentType, CanvasTransform, DragState, ConnectState } from '../types'
import {
  drawGrid,
  drawComponent,
  drawConnection,
  drawTempConnection,
  hitTestComponent,
  hitTestPort,
  screenToCanvas,
  canvasToScreen,
  getPortPosition,
} from '../utils/canvas-renderer'

const store = useModelStore()
const canvasContainer = ref<HTMLDivElement>()
const canvasEl = ref<HTMLCanvasElement>()

const canvasWidth = ref(800)
const canvasHeight = ref(600)

const transform = reactive<CanvasTransform>({
  scale: 1,
  offsetX: 0,
  offsetY: 0,
})

const dragState = reactive<DragState>({
  isDragging: false,
  componentId: null,
  startX: 0,
  startY: 0,
  offsetX: 0,
  offsetY: 0,
})

const connectingState = reactive<ConnectState>({
  isConnecting: false,
  fromComponentId: null,
  fromPortIndex: 0,
  fromPortType: null,
  mouseX: 0,
  mouseY: 0,
})

const mouseCanvasPos = reactive({ x: 0, y: 0 })
const isPanning = ref(false)
const panStart = reactive({ x: 0, y: 0, offsetX: 0, offsetY: 0 })

let animationFrameId: number | null = null

// 监听模型变化重绘
watch(
  () => [store.components.length, store.connections.length, store.selectedComponentId, store.solveResult],
  () => requestRender(),
  { deep: true }
)

onMounted(() => {
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('keydown', onKeyDown)
  startRenderLoop()
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('keydown', onKeyDown)
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
})

function resizeCanvas() {
  if (!canvasContainer.value) return
  const rect = canvasContainer.value.getBoundingClientRect()
  canvasWidth.value = rect.width
  canvasHeight.value = rect.height
  nextTick(() => requestRender())
}

function startRenderLoop() {
  const render = () => {
    renderCanvas()
    animationFrameId = requestAnimationFrame(render)
  }
  animationFrameId = requestAnimationFrame(render)
}

function requestRender() {
  // renderLoop handles it
}

function renderCanvas() {
  const canvas = canvasEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空画布
  ctx.fillStyle = '#1a1a2e'
  ctx.fillRect(0, 0, canvasWidth.value, canvasHeight.value)

  // 绘制网格
  drawGrid(ctx, canvasWidth.value, canvasHeight.value, transform)

  // 绘制连接线
  for (const conn of store.connections) {
    drawConnection(ctx, conn, store.components, transform, store.solveResult)
  }

  // 绘制正在创建的连接线
  if (connectingState.isConnecting && connectingState.fromComponentId) {
    const fromComp = store.components.find((c) => c.id === connectingState.fromComponentId)
    if (fromComp) {
      const fromPos = getPortPosition(
        fromComp,
        connectingState.fromPortType || 'outlet',
        connectingState.fromPortIndex
      )
      const fromScreen = canvasToScreen(fromPos.x, fromPos.y, transform)
      drawTempConnection(ctx, fromScreen.x, fromScreen.y, connectingState.mouseX, connectingState.mouseY, transform)
    }
  }

  // 绘制元件
  for (const comp of store.components) {
    const isSelected = comp.id === store.selectedComponentId
    drawComponent(ctx, comp, isSelected, transform, store.solveResult)
  }
}

// 鼠标事件处理
function onMouseDown(e: MouseEvent) {
  const rect = canvasEl.value?.getBoundingClientRect()
  if (!rect) return

  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top

  // 中键或空格+左键 -> 平移
  if (e.button === 1) {
    isPanning.value = true
    panStart.x = e.clientX
    panStart.y = e.clientY
    panStart.offsetX = transform.offsetX
    panStart.offsetY = transform.offsetY
    return
  }

  if (e.button !== 0) return

  // 检查是否点击了端口
  for (const comp of store.components) {
    const portHit = hitTestPort(mx, my, comp, transform)
    if (portHit) {
      if (portHit.portType === 'outlet') {
        // 开始连线
        connectingState.isConnecting = true
        connectingState.fromComponentId = comp.id
        connectingState.fromPortIndex = portHit.portIndex
        connectingState.fromPortType = 'outlet'
        connectingState.mouseX = mx
        connectingState.mouseY = my
        return
      } else if (portHit.portType === 'inlet' && connectingState.isConnecting) {
        // 完成连线
        if (connectingState.fromComponentId) {
          store.addConnection(
            connectingState.fromComponentId,
            connectingState.fromPortIndex,
            comp.id,
            portHit.portIndex
          )
        }
        resetConnecting()
        return
      }
    }
  }

  // 如果在连线模式中点击空白区域，取消连线
  if (connectingState.isConnecting) {
    resetConnecting()
    return
  }

  // 检查是否点击了元件
  for (let i = store.components.length - 1; i >= 0; i--) {
    const comp = store.components[i]
    if (hitTestComponent(mx, my, comp, transform)) {
      store.selectComponent(comp.id)
      dragState.isDragging = true
      dragState.componentId = comp.id
      const canvasPos = screenToCanvas(mx, my, transform)
      dragState.startX = canvasPos.x
      dragState.startY = canvasPos.y
      dragState.offsetX = comp.x
      dragState.offsetY = comp.y
      return
    }
  }

  // 点击空白区域取消选择
  store.selectComponent(null)

  // 开始平移
  isPanning.value = true
  panStart.x = e.clientX
  panStart.y = e.clientY
  panStart.offsetX = transform.offsetX
  panStart.offsetY = transform.offsetY
}

function onMouseMove(e: MouseEvent) {
  const rect = canvasEl.value?.getBoundingClientRect()
  if (!rect) return

  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top

  const canvasPos = screenToCanvas(mx, my, transform)
  mouseCanvasPos.x = canvasPos.x
  mouseCanvasPos.y = canvasPos.y

  if (isPanning.value) {
    transform.offsetX = panStart.offsetX + (e.clientX - panStart.x)
    transform.offsetY = panStart.offsetY + (e.clientY - panStart.y)
    return
  }

  if (connectingState.isConnecting) {
    connectingState.mouseX = mx
    connectingState.mouseY = my
    return
  }

  if (dragState.isDragging && dragState.componentId) {
    const dx = canvasPos.x - dragState.startX
    const dy = canvasPos.y - dragState.startY
    store.updateComponent(dragState.componentId, {
      x: Math.round(dragState.offsetX + dx),
      y: Math.round(dragState.offsetY + dy),
    })
  }
}

function onMouseUp(_e: MouseEvent) {
  isPanning.value = false
  dragState.isDragging = false
  dragState.componentId = null
}

function onWheel(e: WheelEvent) {
  const rect = canvasEl.value?.getBoundingClientRect()
  if (!rect) return

  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top

  const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.min(Math.max(transform.scale * zoomFactor, 0.2), 5)

  // 以鼠标位置为中心缩放
  transform.offsetX = mx - (mx - transform.offsetX) * (newScale / transform.scale)
  transform.offsetY = my - (my - transform.offsetY) * (newScale / transform.scale)
  transform.scale = newScale
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    resetConnecting()
    store.selectComponent(null)
  }
  // 需要 Shift + Delete 或 Shift + Backspace 才能删除
  if ((e.key === 'Delete' || e.key === 'Backspace') && e.shiftKey) {
    if (store.selectedComponentId) {
      store.removeComponent(store.selectedComponentId)
    }
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  const type = e.dataTransfer?.getData('component-type') as ComponentType
  if (!type) return

  const rect = canvasEl.value?.getBoundingClientRect()
  if (!rect) return

  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top
  const canvasPos = screenToCanvas(mx, my, transform)

  const comp = store.addComponent(type, Math.round(canvasPos.x - 60), Math.round(canvasPos.y - 30))
  if (comp) store.selectComponent(comp.id)
}

function resetConnecting() {
  connectingState.isConnecting = false
  connectingState.fromComponentId = null
  connectingState.fromPortIndex = 0
  connectingState.fromPortType = null
}

function zoomIn() {
  const newScale = Math.min(transform.scale * 1.2, 5)
  const cx = canvasWidth.value / 2
  const cy = canvasHeight.value / 2
  transform.offsetX = cx - (cx - transform.offsetX) * (newScale / transform.scale)
  transform.offsetY = cy - (cy - transform.offsetY) * (newScale / transform.scale)
  transform.scale = newScale
}

function zoomOut() {
  const newScale = Math.max(transform.scale * 0.8, 0.2)
  const cx = canvasWidth.value / 2
  const cy = canvasHeight.value / 2
  transform.offsetX = cx - (cx - transform.offsetX) * (newScale / transform.scale)
  transform.offsetY = cy - (cy - transform.offsetY) * (newScale / transform.scale)
  transform.scale = newScale
}

function zoomReset() {
  transform.scale = 1
  transform.offsetX = 0
  transform.offsetY = 0
}

function fitView() {
  if (store.components.length === 0) {
    zoomReset()
    return
  }

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const comp of store.components) {
    minX = Math.min(minX, comp.x)
    minY = Math.min(minY, comp.y)
    maxX = Math.max(maxX, comp.x + 120)
    maxY = Math.max(maxY, comp.y + 60)
  }

  const padding = 60
  const modelWidth = maxX - minX + padding * 2
  const modelHeight = maxY - minY + padding * 2

  const scaleX = canvasWidth.value / modelWidth
  const scaleY = canvasHeight.value / modelHeight
  transform.scale = Math.min(scaleX, scaleY, 2)

  const centerX = (minX + maxX) / 2
  const centerY = (minY + maxY) / 2
  transform.offsetX = canvasWidth.value / 2 - centerX * transform.scale
  transform.offsetY = canvasHeight.value / 2 - centerY * transform.scale
}
</script>

<style scoped>
.model-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #1a1a2e;
}

.model-canvas canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.zoom-controls {
  position: absolute;
  bottom: 50px;
  right: 16px;
  z-index: 10;
}

.zoom-controls .el-button {
  background: rgba(22, 33, 62, 0.9);
  border-color: #0f3460;
  color: #e0e0e0;
}

.zoom-controls .el-button:hover {
  background: rgba(15, 52, 96, 0.9);
}

.status-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 28px;
  background: rgba(22, 33, 62, 0.95);
  border-top: 1px solid #0f3460;
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 8px;
  font-size: 11px;
  color: #888;
  z-index: 10;
}

.hint-bar {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}
</style>
