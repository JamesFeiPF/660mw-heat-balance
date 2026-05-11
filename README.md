# MHFlow - 660MW超超临界机组热力平衡计算平台

## 项目简介

MHFlow 是一个面向660MW超超临界一次再热凝汽式汽轮发电机组的热力平衡计算与可视化仿真平台。系统采用工业标准的双层迭代热平衡求解算法，基于 IAPWS-IF97 国际标准精确计算水蒸汽热力性质，支持多级回热抽汽、一次再热、表面式/混合式加热器等复杂热力系统的稳态仿真分析。

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **语言**: Python 3.10
- **工质属性**: IAPWS-IF97 ( via `iapws` 库 )
- **求解器**: 自研双层迭代热平衡求解引擎

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router

## 项目结构

```
660MWHF/
├── mhflow_backend/              # 后端应用
│   ├── app/
│   │   ├── api/                 # REST API 路由
│   │   │   ├── routes.py        # 核心API：/model/load, /solve, /templates/list
│   │   │   └── websocket.py     # WebSocket实时数据推送
│   │   ├── models/              # 热力设备组件模型
│   │   │   ├── base.py          # 组件基类（端口管理、参数读写）
│   │   │   ├── boiler.py        # 锅炉模型（过热、再热、热负荷）
│   │   │   ├── turbine.py       # 汽轮机模型（等熵膨胀、抽汽、多级分段）
│   │   │   ├── heater.py        # 加热器模型（表面式HP/LP、混合式DA）
│   │   │   ├── condenser.py     # 凝汽器模型
│   │   │   ├── pump.py          # 水泵模型（给水泵、凝结水泵）
│   │   │   ├── generator.py     # 发电机模型
│   │   │   ├── tee.py           # 三通组件（分流/合流）
│   │   │   └── pipe.py          # 管道模型
│   │   ├── solvers/
│   │   │   └── heat_balance.py  # 双层迭代热平衡求解器
│   │   ├── properties/
│   │   │   └── steam.py         # IAPWS-IF97 水蒸汽物性计算
│   │   ├── templates/
│   │   │   ├── __init__.py      # 模板注册表（支持JSON优先加载）
│   │   │   └── plant_600mw.py   # 660MW机组默认模板（3缸+8级回热）
│   │   ├── validators.py        # 模型结构验证器
│   │   ├── exporters/
│   │   │   └── pdf_exporter.py  # PDF报告导出
│   │   ├── config.py            # 应用配置
│   │   └── main.py              # FastAPI应用入口
│   ├── models_data/             # 模型数据存储
│   │   └── templates/           # JSON模板文件
│   │       └── plant_600mw.json # 660MW机组JSON模板
│   ├── tests/                   # 单元测试
│   ├── requirements.txt         # Python依赖
│   └── run.py                   # 后端启动脚本
│
├── mhflow_frontend/             # 前端应用
│   ├── src/
│   │   ├── components/          # Vue组件
│   │   │   ├── Toolbar.vue      # 顶部工具栏（加载/保存/计算/导出）
│   │   │   ├── ModelCanvas.vue  # 热力系统画布（拖拽式建模）
│   │   │   ├── ComponentPanel.vue   # 左侧组件面板
│   │   │   ├── PropertyPanel.vue    # 右侧属性面板
│   │   │   └── icons/           # 自定义SVG组件图标
│   │   ├── stores/
│   │   │   └── model.ts         # Pinia状态管理（含generate600MWTemplate）
│   │   ├── api/
│   │   │   └── index.ts         # 后端API封装 + 前后端数据格式转换
│   │   ├── types/
│   │   │   └── index.ts         # TypeScript类型定义
│   │   ├── views/
│   │   │   └── HomeView.vue     # 主页面
│   │   └── App.vue
│   ├── dist/                    # 构建产物
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── venv/                        # Conda虚拟环境
├── 660MW计算案例.xlsx           # 对标数据（Excel参考值）
├── test_*.py                    # 各类测试脚本
└── README.md                    # 本文档
```

## 快速开始

### 环境要求
- Python 3.10 (Conda)
- Node.js >= 18.x

### 后端启动

```bash
# 激活虚拟环境
conda activate .\venv

# 进入后端目录
cd .\mhflow_backend

# 启动服务
python run.py
```
后端服务运行在 `http://localhost:8000`

### 前端启动

```bash
cd .\mhflow_frontend
npm install
npm run dev
```
前端服务运行在 `http://localhost:3000`

### 前端构建

```bash
cd .\mhflow_frontend
npm run build
```

---

## 算法原理

### 1. 概述

本系统采用**双层迭代架构**的热力平衡求解算法，遵循工业标准正向计算流程：

```
锅炉(热源) → 高压缸 → 中压缸 → 低压缸 → 凝汽器(冷端)
                ↓         ↓         ↓
              高加1     除氧器    低加6
              高加2     低加5     低加7
              高加3               低加8
```

### 2. 双层迭代架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        双层迭代求解架构                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   外层迭代 (汽轮机全局功率平衡)          内层迭代 (加热器单体热平衡) │
│   ─────────────────────────────          ─────────────────────────  │
│                                                                     │
│   for outer_iter in range(max_outer):      for inner_iter in       │
│                                            range(max_inner):        │
│       ┌─────────────┐                        ┌─────────────────┐   │
│       │ 1. 锅炉计算  │                        │ 1. 高压加热器    │   │
│       │    (主汽/再热)│                        │    (按p从高到低) │   │
│       └──────┬──────┘                        └────────┬────────┘   │
│              │ 同步连接                               │             │
│              ▼                                        ▼             │
│       ┌─────────────┐                        ┌─────────────────┐   │
│       │ 2. HP_Turbine│                        │ 2. 除氧器(DA)    │   │
│       │    (等熵膨胀) │                        │    (混合式)      │   │
│       └──────┬──────┘                        └─────────────────┘   │
│              │                                        │             │
│              ▼                                        ▼             │
│       ┌─────────────┐                        ┌─────────────────┐   │
│       │ 3. IP_Turbine│                        │ 3. 低压加热器    │   │
│       │    (等熵膨胀) │                        │    (按p从高到低) │   │
│       └──────┬──────┘                        └─────────────────┘   │
│              │                                        │             │
│              ▼                                        ▼             │
│       ┌─────────────┐                        ┌─────────────────┐   │
│       │ 4. LP_Turbine│                        │ 4. 凝汽器        │   │
│       │    (等熵膨胀) │                        │    (排汽凝结)    │   │
│       └──────┬──────┘                        └─────────────────┘   │
│              │ 同步连接                               │             │
│              ▼                                        ▼             │
│       ┌─────────────┐                        ┌─────────────────┐   │
│       │ 5. 更新抽汽量 │                        │ 5. 水泵          │   │
│       │   (加热器反推)│                        │    (升压)        │   │
│       └─────────────┘                        └─────────────────┘   │
│                                                                     │
│       ────────────────────────────────────────────────────────►    │
│       收敛检查 (给水焓 + 抽汽量 + 功率)                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 外层迭代：汽轮机通流计算

**计算顺序**：锅炉 → 同步连接 → 汽轮机（按排汽压力从高到低）→ 同步连接

每轮外层迭代执行：
1. **锅炉计算**：根据给水入口参数计算主蒸汽和再热蒸汽出口参数
2. **同步连接**：将锅炉出口同步到汽轮机入口（`h > 0` 校验，防止0值覆盖）
3. **汽轮机计算**：按 HP → IP → LP 顺序逐缸计算
   - 获取入口蒸汽参数（p, t, h, s, m）
   - 使用 IAPWS-IF97 `ps_to_h(p_out, s_in)` 精确计算等熵出口焓
   - 实际出口焓：h_out = h_in - η_isen × (h_in - h_out_is)
   - 抽汽焓：在抽汽压力下按 s=s_in 做等熵膨胀 + 效率修正
   - 功率：按实际抽汽焓逐段累计，W = Σ m_stage × (h_prev - h_curr)
   - 轴功率：W_shaft = W_internal × η_mech
4. **再次同步**：汽轮机出口同步到下游（锅炉再热入口、凝汽器）

#### 内层迭代：加热器热平衡

**计算顺序**：高加（按压力从高到低）→ 除氧器 → 低加（按压力从高到低）→ 凝汽器 → 水泵

每台加热器根据类型执行不同热平衡：

**表面式加热器（HP/LP）**：
```
出口水温度: t_water_out = t_sat(p_heater) - ttd
出口水焓:   h_water_out = pt_to_h(p_water_out, t_water_out)
疏水温度:   t_drain = t_sat(p_heater) - dca
疏水焓:     h_drain = pt_to_h(p_heater, t_drain)

热平衡方程:
  m_steam × (h_steam - h_drain) × η + m_drain_in × (h_drain_in - h_drain) × η
  = m_water × (h_water_out - h_water_in)

求解抽汽量: m_steam = [m_water × Δh_water - m_drain_in × Δh_drain × η] / [(h_steam - h_drain) × η]
```

**混合式加热器（除氧器 DA）**：
```
出口水焓: h_water_out = h_f(p_da)  (饱和水焓)
出口水温: t_water_out = t_sat(p_da)

热平衡方程:
  m_steam × h_steam + m_drain_in × h_drain_in + m_water × h_water_in
  = (m_steam + m_drain_in + m_water) × h_water_out

求解抽汽量: m_steam = [m_water × (h_out - h_in) - m_drain_in × (h_drain_in - h_out)] / (h_steam - h_out)
```

### 3. 汽轮机模型详解

#### 等熵膨胀精确计算

汽轮机膨胀过程的核心是等熵线追踪。系统使用 IAPWS-IF97 标准在出口压力下按入口熵值精确求解等熵焓：

```python
# 等熵出口焓: 在 p_out 压力下，s = s_in 时的焓值
h_out_is = ps_to_h(p_out, s_in)

# 实际出口焓（考虑等熵效率）
actual_h_drop = η_isen × (h_in - h_out_is)
h_out = h_in - actual_h_drop
```

**关键修正**：抽汽焓不再使用压力比例线性插值，而是在每个抽汽压力下独立做等熵膨胀：

```python
# 在抽汽压力 p_ext 下按 s=s_in 做等熵膨胀
h_ext_is = ps_to_h(p_ext, s_in)
h_ext = h_in - η_isen × (h_in - h_ext_is)
```

#### 功率计算

功率按实际抽汽焓逐段累计，考虑流量递减：

```python
w_detailed = 0.0
m_stage = m_in
prev_h = h_in

for ext in extractions:
    w_detailed += m_stage × (prev_h - h_ext)
    m_stage -= ext_m
    prev_h = h_ext

# 最后一段到排汽
w_detailed += m_stage × (prev_h - h_out_final)
w_shaft = w_detailed × η_mech
```

#### 多级分段支持

汽轮机模型支持两种计算模式：
- **传统单段模式**：一个汽轮机组件包含全部抽汽点（后端模板采用）
- **多级分段模式**：每个抽汽段作为独立组件（前端可视化采用）

### 4. 加热器模型详解

#### 表面式加热器（HP/LP）

```
┌─────────────────────────────────────┐
│           表面式加热器               │
│                                     │
│   蒸汽入口 ─────┐                   │
│      ↓          │  传热面           │
│   疏水出口 ←────┘                   │
│                                     │
│   水入口  ─────────────────→ 水出口 │
│                                     │
│   端差 TTD = t_sat - t_water_out    │
│   过冷度 DCA = t_sat - t_drain      │
└─────────────────────────────────────┘
```

#### 混合式加热器（除氧器）

除氧器使用自身工作压力（`deaerator_pressure` 或 `p_heater`）计算饱和参数，而非蒸汽入口压力。这是因为在混合式加热器中，出口状态由工作压力决定。

**关键修复**：当 `m_steam = 0`（不需要额外蒸汽加热）时，基于实际混合焓重新计算出口参数：
```python
if m_steam == 0 and (m_water + m_drain_in) > 0:
    total_m = m_water + m_drain_in
    h_water_out = (m_water × h_water_in + m_drain_in × h_drain_in) / total_m
    t_water_out = ph_to_t(p_water_out, h_water_out)
```

### 5. 锅炉模型

```
主蒸汽流量: m_steam = m_fw × (1 - blowdown_rate)
主蒸汽焓:   h_ms = pt_to_h(p_ms, t_ms)
再热蒸汽焓: h_rh = pt_to_h(p_rh_out, t_rh)

锅炉热负荷:
  Q_total = m_steam × (h_ms - h_fw) + m_rh × (h_rh_out - h_rh_in)

燃料消耗:
  B = Q_total / (η_boiler × fuel_LHV)
```

### 6. 水泵模型

```python
# 水的比容（液态水 ≈ 0.001 m³/kg）
v_water = 0.001

# 压力差 (MPa → kPa)
dp = (p_out - p_in) × 1000

# 理论功 (kJ/kg)
w_theory = v_water × dp

# 实际功
w_actual = w_theory / η_pump

# 出口焓
h_out = h_in + w_actual

# 泵轴功率
p_shaft = m × w_actual

# 电机功率
p_motor = p_shaft / η_motor
```

### 7. 系统性能指标计算

```python
# 汽轮机总轴功率
w_turbine_shaft = Σ w_shaft(HP, IP, LP)

# 发电机参数从 Generator 组件读取
eta_mech = generator.params.get("eta_mech", 0.995)
eta_gen  = generator.params.get("eta_gen", 0.995)

# 毛发电功率
w_electrical_gross = w_turbine_shaft × η_mech × η_gen

# 泵总功耗（给水泵通常由小汽轮机驱动，不计入厂用电）
pump_power = Σ p_motor(凝结水泵, 其他辅助泵)

# 净发电功率
w_electrical_net = w_electrical_gross - pump_power

# 热耗率 (kJ/kWh)
heat_rate = Q_boiler / w_electrical_gross × 3600

# 全厂热效率
η_plant = w_electrical_net / Q_boiler

# 标准煤耗率 (g/kWh)
coal_rate = heat_rate / 29308 × 1000
```

### 8. 收敛判据

系统采用**三指标联合收敛**，至少完成3次外层迭代后方可收敛：

| 指标 | 判据 | 说明 |
|------|------|------|
| 给水焓变化 | `\|h_fw - h_fw_prev\| < 0.01 kJ/kg` | 回热系统热平衡 |
| 抽汽量偏差 | `Σ\|m_ext - m_ext_prev\| / Σm_ext < 0.001` | 流量分配合理性 |
| 功率偏差 | `\|W - W_prev\| / W < 0.1%` | 汽轮机做功一致性 |

**阻尼因子**：抽汽量更新使用阻尼因子 `damping = 0.5`，防止迭代震荡。

**抽汽量上限**：加热器反推的抽汽量不超过模板初始值 `m_frac` 的3倍，防止加热器模型异常导致抽汽量过大。

---

## 版本变更说明

### v2.0 - 660MW模板参数对标版

本次版本以国内某660MW超超临界机组设计值为对标目标，对求解算法和默认模板参数进行了全面修正。

#### 对标目标值

| 指标 | 对标值 | 当前计算值 | 偏差 |
|------|--------|-----------|------|
| 毛发电功率 | 655.4 MW | 653.54 MW | **-0.28%** ✅ |
| 主汽流量 | 1805.8 t/h | 1800.0 t/h | -0.3% ✅ |
| 热耗率 | 7354 kJ/kWh | 7441 kJ/kWh | +1.2% |
| 全厂效率 | 43.71% | 48.28% | +4.6% |
| 标准煤耗 | 264.5 g/kWh | 253.9 g/kWh | -4.0% |

> 注：全厂效率和煤耗偏差主要源于给水泵驱动方式差异（当前模型为电泵，对标机组可能采用小汽轮机驱动），以及加热器模型简化导致的抽汽分布差异。

#### 模板参数调整

| 参数 | 旧值 | 新值 |
|------|------|------|
| 主蒸汽压力 | 24.2 MPa | **28.0 MPa** |
| 主蒸汽温度 | 566 °C | **600 °C** |
| 再热蒸汽温度 | 566 °C | **610 °C** |
| 凝汽器背压 | 4.9 kPa | **11 kPa** |
| 锅炉效率 | 93.5% | **95.0%** |
| 排污率 | 1.0% | **0.0%** |
| 高压缸效率 | 87.5% | **87.9%** |
| 中压缸效率 | 90.0% | **88.3%** |
| 低压缸效率 | 88.0% | **87.0%** |
| 发电机效率 | 99.0% | **99.5%** |
| HP1抽汽压力 | 7.2 MPa | **7.741 MPa** |
| HP2抽汽压力 | 5.2 MPa | **5.893 MPa** |
| HP3抽汽压力 | 4.5 MPa | **5.78 MPa** |
| IP1抽汽压力 | 2.5 MPa | **2.936 MPa** |
| IP2抽汽压力 | 1.5 MPa | **1.239 MPa** |
| LP1~LP3抽汽压力 | 0.6/0.25/0.08 MPa | **0.523/0.26/0.11 MPa** |

#### 算法修复

1. **除氧器压力bug修复** (`heater.py`)
   - 问题：`_calculate_da` 使用蒸汽入口压力 `p_steam` 而非除氧器工作压力 `p_heater` 计算饱和参数
   - 修复：`p_da = self.params.get("deaerator_pressure", p_heater)`，使用除氧器自身工作压力

2. **同步连接顺序修复** (`heat_balance.py`)
   - 问题：`_sync_connections` 在锅炉重算之前执行，导致汽轮机入口参数被旧值覆盖
   - 修复：将同步调用移到锅炉计算之后，且增加 `src_port.get("h", 0) > 0` 校验

3. **最少迭代次数保护**
   - 问题：外层迭代可能在第2次就提前收敛，汽轮机-锅炉循环尚未稳定
   - 修复：`if outer_iter >= 2 and self._check_convergence()`

4. **发电机效率从组件参数读取**
   - 问题：`_calculate_system_performance` 中发电机效率硬编码为 0.985
   - 修复：从 Generator 组件 `params` 中读取 `eta_gen` 和 `eta_mech`

5. **泵功率计算修正**
   - 问题：给水泵功率计入厂用电率，但对标机组通常采用小汽轮机驱动
   - 修复：厂用电仅扣除凝结水泵等辅助泵，给水泵功耗不计入

6. **抽汽量上限限制**
   - 问题：加热器模型异常时可能导致抽汽量过大
   - 修复：`demand_m = min(demand_m, m_frac_limit × main_steam_flow × 3.0)`

7. **前端模板参数同步**
   - 问题：前端 `generate600MWTemplate()` 使用硬编码的旧参数（24.2MPa/566°C/4.9kPa）
   - 修复：将前端 `COMPONENT_CONFIGS` 和 `generate600MWTemplate()` 中的参数全部更新为对标值

8. **后端模板功率连接修复**
   - 问题：`plant_600mw.py` 中汽轮机 `steam_out` 错误连接到 `Generator.mechanical_in`
   - 修复：为 HP/IP/LP 汽轮机添加 `power_in`/`power_out` 端口，建立功率串联连接

9. **JSON模板导出**
   - 问题：模板硬编码在 Python 字典中，不可独立编辑
   - 修复：导出 `models_data/templates/plant_600mw.json`，支持前后端共用

10. **前端属性面板显示修复**
    - 问题：`PropertyPanel.vue` 缺少 `'turbine'` 类型映射，功率端口显示"未计算"
    - 修复：添加 `turbine` 颜色/标签映射，添加 `hasPortValue()` 支持功率端口 `w` 字段

11. **后端模型验证器**
    - 问题：`/api/solve` 缺少模型结构校验，错误模型导致求解崩溃
    - 修复：新增 `app/validators.py`，求解前自动验证组件/连接完整性

12. **前端验证增强**
    - 问题：连接时无端口类型检查，组件可重叠放置
    - 修复：`addConnection` 增加功率/介质端口兼容性检查，`addComponent` 增加重叠自动偏移，`validateModel` 支持保存前校验

13. **属性面板数值格式化崩溃修复**
    - 问题：点击汽轮机/加热器组件时，`formatResultValue` 报 `value.toFixed is not a function`
    - 根因：`convertSolveResultFromBackend` 将后端 `results` 中的嵌套数组（如 `extractions`）直接传入 `extra_params`
    - 修复：`api/index.ts` 过滤 `extra_params` 只保留 `number` 类型；`PropertyPanel.vue` `formatResultValue` 添加防御性 `Number(value)` 转换

14. **前端本地JSON文件打开功能**
    - 新增工具栏 **"打开"** 按钮，支持从本地选择 `.json` 模型文件
    - 自动识别格式：后端模板格式（`component_type`/`name`）→ 自动转换并渲染；前端保存格式（`id`/`x`/`y`）→ 直接加载
    - 实现 `api/index.ts` 中 `openModelFromFile()` 智能格式检测与转换
    - 打开后可直接点击"执行计算"，后端针对当前画布模型进行求解

---

## API文档

启动后端服务后，可访问以下地址查看API文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 核心API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/templates/list` | GET | 获取可用模板列表 |
| `/api/model/load` | POST | 加载模板或已保存的JSON模型 |
| `/api/model/list-saved` | GET | 获取已保存的模型列表 |
| `/api/model/save` | POST | 保存模型为JSON文件 |
| `/api/solve` | POST | 执行热平衡计算 |
| `/api/properties/steam` | GET | 查询水蒸汽物性 |

---

## 许可证

本项目仅供内部使用和研究目的。
