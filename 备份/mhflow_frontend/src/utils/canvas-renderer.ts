import type { Component, Connection, CanvasTransform, SolveResult } from '../types'

/** 元件尺寸常量 */
const COMP_WIDTH = 120
const COMP_HEIGHT = 60
const PORT_RADIUS = 6
const PORT_HIT_RADIUS = 10

/** 元件类型颜色映射 */
const TYPE_COLORS: Record<string, string> = {
  boiler: '#e74c3c',
  turbine: '#3498db',
  condenser: '#1abc9c',
  heater: '#f39c12',
  pump: '#9b59b6',
  pipe: '#95a5a6',
  generator: '#2ecc71',
}

/** 元件类型中文名映射 */
const TYPE_LABELS: Record<string, string> = {
  boiler: '锅炉',
  turbine: '汽轮机',
  condenser: '凝汽器',
  heater: '加热器',
  pump: '水泵',
  pipe: '管道',
  generator: '发电机',
}

/** 元件类型图标符号 */
const TYPE_ICONS: Record<string, string> = {
  boiler: 'B',
  turbine: 'T',
  condenser: 'C',
  heater: 'H',
  pump: 'P',
  pipe: '—',
  generator: 'G',
}

/** 获取元件颜色 */
export function getComponentColor(type: string): string {
  return TYPE_COLORS[type] || '#7f8c8d'
}

/** 获取元件端口位置 */
export function getPortPosition(
  comp: Component,
  portType: 'inlet' | 'outlet',
  portIndex: number
): { x: number; y: number } {
  const ports = portType === 'inlet' ? comp.inlet_ports : comp.outlet_ports
  const totalPorts = ports.length
  const spacing = COMP_HEIGHT / (totalPorts + 1)

  if (portType === 'inlet') {
    return {
      x: comp.x,
      y: comp.y + spacing * (portIndex + 1),
    }
  } else {
    return {
      x: comp.x + COMP_WIDTH,
      y: comp.y + spacing * (portIndex + 1),
    }
  }
}

/** 绘制网格背景 */
export function drawGrid(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  transform: CanvasTransform
): void {
  const gridSize = 30
  ctx.save()
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)'
  ctx.lineWidth = 1

  const startX = Math.floor(-transform.offsetX / transform.scale / gridSize) * gridSize
  const startY = Math.floor(-transform.offsetY / transform.scale / gridSize) * gridSize
  const endX = startX + width / transform.scale + gridSize * 2
  const endY = startY + height / transform.scale + gridSize * 2

  ctx.beginPath()
  for (let x = startX; x <= endX; x += gridSize) {
    const screenX = x * transform.scale + transform.offsetX
    ctx.moveTo(screenX, 0)
    ctx.lineTo(screenX, height)
  }
  for (let y = startY; y <= endY; y += gridSize) {
    const screenY = y * transform.scale + transform.offsetY
    ctx.moveTo(0, screenY)
    ctx.lineTo(width, screenY)
  }
  ctx.stroke()

  // 绘制粗网格
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)'
  const majorGridSize = gridSize * 5
  const majorStartX = Math.floor(-transform.offsetX / transform.scale / majorGridSize) * majorGridSize
  const majorStartY = Math.floor(-transform.offsetY / transform.scale / majorGridSize) * majorGridSize
  const majorEndX = majorStartX + width / transform.scale + majorGridSize * 2
  const majorEndY = majorStartY + height / transform.scale + majorGridSize * 2

  ctx.beginPath()
  for (let x = majorStartX; x <= majorEndX; x += majorGridSize) {
    const screenX = x * transform.scale + transform.offsetX
    ctx.moveTo(screenX, 0)
    ctx.lineTo(screenX, height)
  }
  for (let y = majorStartY; y <= majorEndY; y += majorGridSize) {
    const screenY = y * transform.scale + transform.offsetY
    ctx.moveTo(0, screenY)
    ctx.lineTo(width, screenY)
  }
  ctx.stroke()

  ctx.restore()
}

/** 绘制单个元件 */
export function drawComponent(
  ctx: CanvasRenderingContext2D,
  comp: Component,
  isSelected: boolean,
  transform: CanvasTransform,
  _solveResult: SolveResult | null
): void {
  ctx.save()

  const sx = comp.x * transform.scale + transform.offsetX
  const sy = comp.y * transform.scale + transform.offsetY
  const sw = COMP_WIDTH * transform.scale
  const sh = COMP_HEIGHT * transform.scale

  const color = getComponentColor(comp.type)

  // 阴影
  ctx.shadowColor = 'rgba(0, 0, 0, 0.3)'
  ctx.shadowBlur = 8
  ctx.shadowOffsetX = 2
  ctx.shadowOffsetY = 2

  // 元件主体 - 圆角矩形
  const radius = 8 * transform.scale
  ctx.beginPath()
  ctx.moveTo(sx + radius, sy)
  ctx.lineTo(sx + sw - radius, sy)
  ctx.arcTo(sx + sw, sy, sx + sw, sy + radius, radius)
  ctx.lineTo(sx + sw, sy + sh - radius)
  ctx.arcTo(sx + sw, sy + sh, sx + sw - radius, sy + sh, radius)
  ctx.lineTo(sx + radius, sy + sh)
  ctx.arcTo(sx, sy + sh, sx, sy + sh - radius, radius)
  ctx.lineTo(sx, sy + radius)
  ctx.arcTo(sx, sy, sx + radius, sy, radius)
  ctx.closePath()

  // 填充
  const gradient = ctx.createLinearGradient(sx, sy, sx, sy + sh)
  gradient.addColorStop(0, color + 'cc')
  gradient.addColorStop(1, color + '88')
  ctx.fillStyle = gradient
  ctx.fill()

  // 边框
  ctx.shadowColor = 'transparent'
  ctx.strokeStyle = isSelected ? '#ffffff' : color
  ctx.lineWidth = isSelected ? 2.5 : 1.5
  ctx.stroke()

  // 选中高亮
  if (isSelected) {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
    ctx.lineWidth = 1
    ctx.setLineDash([4, 4])
    ctx.strokeRect(sx - 4, sy - 4, sw + 8, sh + 8)
    ctx.setLineDash([])
  }

  // 类型图标圆圈
  const iconRadius = 12 * transform.scale
  const iconCx = sx + iconRadius + 6 * transform.scale
  const iconCy = sy + sh / 2

  ctx.beginPath()
  ctx.arc(iconCx, iconCy, iconRadius, 0, Math.PI * 2)
  ctx.fillStyle = color
  ctx.fill()
  ctx.strokeStyle = '#ffffff44'
  ctx.lineWidth = 1
  ctx.stroke()

  // 类型图标文字
  ctx.fillStyle = '#ffffff'
  ctx.font = `bold ${Math.round(12 * transform.scale)}px "Microsoft YaHei", sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(TYPE_ICONS[comp.type] || '?', iconCx, iconCy)

  // 元件名称
  ctx.fillStyle = '#ffffff'
  ctx.font = `${Math.round(11 * transform.scale)}px "Microsoft YaHei", sans-serif`
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  const nameX = sx + iconRadius * 2 + 12 * transform.scale
  ctx.fillText(truncateText(ctx, comp.name, sw - iconRadius * 2 - 16 * transform.scale), nameX, sy + sh / 2 - 8 * transform.scale)

  // 类型标签
  ctx.fillStyle = 'rgba(255, 255, 255, 0.6)'
  ctx.font = `${Math.round(9 * transform.scale)}px "Microsoft YaHei", sans-serif`
  ctx.fillText(TYPE_LABELS[comp.type] || comp.type, nameX, sy + sh / 2 + 8 * transform.scale)

  // 绘制端口
  drawPorts(ctx, comp, transform)

  ctx.restore()
}

/** 绘制端口 */
function drawPorts(
  ctx: CanvasRenderingContext2D,
  comp: Component,
  transform: CanvasTransform
): void {
  const pr = PORT_RADIUS * transform.scale

  // 进口端口
  comp.inlet_ports.forEach((port, idx) => {
    const pos = getPortPosition(comp, 'inlet', idx)
    const sx = pos.x * transform.scale + transform.offsetX
    const sy = pos.y * transform.scale + transform.offsetY

    ctx.beginPath()
    ctx.arc(sx, sy, pr, 0, Math.PI * 2)
    ctx.fillStyle = '#3498db'
    ctx.fill()
    ctx.strokeStyle = '#ffffff88'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // 端口标签
    if (transform.scale > 0.6) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
      ctx.font = `${Math.round(8 * transform.scale)}px sans-serif`
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillText(port.name, sx - pr - 4, sy)
    }
  })

  // 出口端口
  comp.outlet_ports.forEach((port, idx) => {
    const pos = getPortPosition(comp, 'outlet', idx)
    const sx = pos.x * transform.scale + transform.offsetX
    const sy = pos.y * transform.scale + transform.offsetY

    ctx.beginPath()
    ctx.arc(sx, sy, pr, 0, Math.PI * 2)
    ctx.fillStyle = '#e74c3c'
    ctx.fill()
    ctx.strokeStyle = '#ffffff88'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // 端口标签
    if (transform.scale > 0.6) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
      ctx.font = `${Math.round(8 * transform.scale)}px sans-serif`
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      ctx.fillText(port.name, sx + pr + 4, sy)
    }
  })
}

/** 绘制连接线 */
export function drawConnection(
  ctx: CanvasRenderingContext2D,
  connection: Connection,
  components: Component[],
  transform: CanvasTransform,
  solveResult: SolveResult | null
): void {
  const fromComp = components.find((c) => c.id === connection.from.componentId)
  const toComp = components.find((c) => c.id === connection.to.componentId)
  if (!fromComp || !toComp) return

  const fromPos = getPortPosition(fromComp, 'outlet', connection.from.portIndex)
  const toPos = getPortPosition(toComp, 'inlet', connection.to.portIndex)

  const fromSx = fromPos.x * transform.scale + transform.offsetX
  const fromSy = fromPos.y * transform.scale + transform.offsetY
  const toSx = toPos.x * transform.scale + transform.offsetX
  const toSy = toPos.y * transform.scale + transform.offsetY

  // 贝塞尔曲线控制点
  const dx = Math.abs(toSx - fromSx)
  const cpOffset = Math.max(dx * 0.4, 50 * transform.scale)

  const cp1x = fromSx + cpOffset
  const cp1y = fromSy
  const cp2x = toSx - cpOffset
  const cp2y = toSy

  ctx.save()

  // 连线主体
  ctx.beginPath()
  ctx.moveTo(fromSx, fromSy)
  ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, toSx, toSy)

  // 根据是否有求解结果决定颜色
  const fromPort = fromComp.outlet_ports[connection.from.portIndex]
  let lineColor = 'rgba(255, 255, 255, 0.4)'
  let lineWidth = 2 * transform.scale

  if (solveResult?.success && fromPort) {
    // 根据温度着色：低温蓝色 -> 高温红色
    const temp = fromPort.t
    const t = Math.min(Math.max((temp - 30) / 540, 0), 1)
    const r = Math.round(50 + t * 205)
    const g = Math.round(100 + (1 - Math.abs(t - 0.5) * 2) * 100)
    const b = Math.round(255 - t * 205)
    lineColor = `rgb(${r}, ${g}, ${b})`
    lineWidth = Math.max(2, Math.min(5, fromPort.m / 100)) * transform.scale
  }

  ctx.strokeStyle = lineColor
  ctx.lineWidth = lineWidth
  ctx.stroke()

  // 箭头
  drawArrow(ctx, cp2x, cp2y, toSx, toSy, transform.scale, lineColor)

  // 流量标签
  if (solveResult?.success && fromPort && transform.scale > 0.5) {
    const midX = (fromSx + toSx) / 2
    const midY = (fromSy + toSy) / 2 - 12 * transform.scale

    const label = `${fromPort.m.toFixed(1)} kg/s | ${fromPort.t.toFixed(1)}°C`

    ctx.font = `${Math.round(9 * transform.scale)}px "Microsoft YaHei", sans-serif`
    const textWidth = ctx.measureText(label).width
    const padding = 4 * transform.scale

    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
    ctx.beginPath()
    ctx.roundRect(
      midX - textWidth / 2 - padding,
      midY - 8 * transform.scale - padding,
      textWidth + padding * 2,
      16 * transform.scale + padding * 2,
      4 * transform.scale
    )
    ctx.fill()

    ctx.fillStyle = '#ffffff'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(label, midX, midY)
  }

  ctx.restore()
}

/** 绘制箭头 */
function drawArrow(
  ctx: CanvasRenderingContext2D,
  fromX: number,
  fromY: number,
  toX: number,
  toY: number,
  scale: number,
  color: string
): void {
  const headLen = 10 * scale
  const angle = Math.atan2(toY - fromY, toX - fromX)

  ctx.save()
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.moveTo(toX, toY)
  ctx.lineTo(
    toX - headLen * Math.cos(angle - Math.PI / 6),
    toY - headLen * Math.sin(angle - Math.PI / 6)
  )
  ctx.lineTo(
    toX - headLen * Math.cos(angle + Math.PI / 6),
    toY - headLen * Math.sin(angle + Math.PI / 6)
  )
  ctx.closePath()
  ctx.fill()
  ctx.restore()
}

/** 绘制正在创建的连接线（鼠标跟随） */
export function drawTempConnection(
  ctx: CanvasRenderingContext2D,
  fromX: number,
  fromY: number,
  toX: number,
  toY: number,
  _transform: CanvasTransform
): void {
  ctx.save()
  ctx.beginPath()
  ctx.setLineDash([6, 4])
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)'
  ctx.lineWidth = 2

  const dx = Math.abs(toX - fromX)
  const cpOffset = Math.max(dx * 0.4, 50)

  ctx.moveTo(fromX, fromY)
  ctx.bezierCurveTo(fromX + cpOffset, fromY, toX - cpOffset, toY, toX, toY)
  ctx.stroke()
  ctx.setLineDash([])
  ctx.restore()
}

/** 检测点击是否在元件上 */
export function hitTestComponent(
  x: number,
  y: number,
  comp: Component,
  transform: CanvasTransform
): boolean {
  const sx = comp.x * transform.scale + transform.offsetX
  const sy = comp.y * transform.scale + transform.offsetY
  const sw = COMP_WIDTH * transform.scale
  const sh = COMP_HEIGHT * transform.scale

  return x >= sx && x <= sx + sw && y >= sy && y <= sy + sh
}

/** 检测点击是否在端口上 */
export function hitTestPort(
  x: number,
  y: number,
  comp: Component,
  transform: CanvasTransform
): { portType: 'inlet' | 'outlet'; portIndex: number } | null {
  const pr = PORT_HIT_RADIUS * transform.scale

  // 检查出口端口
  for (let i = 0; i < comp.outlet_ports.length; i++) {
    const pos = getPortPosition(comp, 'outlet', i)
    const sx = pos.x * transform.scale + transform.offsetX
    const sy = pos.y * transform.scale + transform.offsetY
    const dist = Math.sqrt((x - sx) ** 2 + (y - sy) ** 2)
    if (dist <= pr) {
      return { portType: 'outlet', portIndex: i }
    }
  }

  // 检查进口端口
  for (let i = 0; i < comp.inlet_ports.length; i++) {
    const pos = getPortPosition(comp, 'inlet', i)
    const sx = pos.x * transform.scale + transform.offsetX
    const sy = pos.y * transform.scale + transform.offsetY
    const dist = Math.sqrt((x - sx) ** 2 + (y - sy) ** 2)
    if (dist <= pr) {
      return { portType: 'inlet', portIndex: i }
    }
  }

  return null
}

/** 截断文本 */
function truncateText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string {
  if (ctx.measureText(text).width <= maxWidth) return text
  let truncated = text
  while (truncated.length > 0 && ctx.measureText(truncated + '...').width > maxWidth) {
    truncated = truncated.slice(0, -1)
  }
  return truncated + '...'
}

/** 获取元件矩形 */
export function getComponentRect(comp: Component) {
  return {
    x: comp.x,
    y: comp.y,
    width: COMP_WIDTH,
    height: COMP_HEIGHT,
  }
}

/** 屏幕坐标转画布坐标 */
export function screenToCanvas(
  screenX: number,
  screenY: number,
  transform: CanvasTransform
): { x: number; y: number } {
  return {
    x: (screenX - transform.offsetX) / transform.scale,
    y: (screenY - transform.offsetY) / transform.scale,
  }
}

/** 画布坐标转屏幕坐标 */
export function canvasToScreen(
  canvasX: number,
  canvasY: number,
  transform: CanvasTransform
): { x: number; y: number } {
  return {
    x: canvasX * transform.scale + transform.offsetX,
    y: canvasY * transform.scale + transform.offsetY,
  }
}
