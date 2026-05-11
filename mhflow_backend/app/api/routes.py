"""MHFlow API路由

提供热力系统仿真软件的REST API接口。
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.properties.steam import (
    pt_to_h, pt_to_s, ph_to_t, ph_to_s,
    ps_to_t, get_steam_properties, saturation_properties,
    IAPWS_AVAILABLE,
)
from app.templates import get_template, list_templates
from app.solvers.heat_balance import HeatBalanceSolver
from app.config import get_settings
from app.validators import validate_model
from app.exporters import PDFExporter, ExcelExporter
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["MHFlow"])

# 当前工作模型存储
_current_models: Dict[str, Dict[str, Any]] = {}


# ============================================================
# 请求/响应模型
# ============================================================

class SteamPropertyQuery(BaseModel):
    """水蒸汽物性查询请求"""
    p: float = Field(..., description="压力 (MPa)")
    t: Optional[float] = Field(None, description="温度 (°C)")
    h: Optional[float] = Field(None, description="比焓 (kJ/kg)")
    s: Optional[float] = Field(None, description="比熵 (kJ/(kg·K))")


class ModelLoadRequest(BaseModel):
    """加载模型请求"""
    template_id: str = Field(..., description="模板ID")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定义参数")


class ModelSaveRequest(BaseModel):
    """保存模型请求"""
    model_id: str = Field(..., description="模型ID")
    model_data: Dict[str, Any] = Field(..., description="模型数据")


class ModelUpdateRequest(BaseModel):
    """更新元件参数请求"""
    model_id: str = Field(..., description="模型ID")
    component_name: str = Field(..., description="元件名称")
    param_name: str = Field(..., description="参数名称")
    param_value: Any = Field(..., description="参数值")


class SolveRequest(BaseModel):
    """求解请求"""
    model_data: Optional[Dict[str, Any]] = Field(None, description="模型数据 (为空则使用当前模型)")
    model_id: Optional[str] = Field(None, description="模型ID")
    max_iterations: Optional[int] = Field(None, description="最大迭代次数")
    convergence_tolerance: Optional[float] = Field(None, description="收敛容差")


class ComponentUpdateRequest(BaseModel):
    """更新元件请求"""
    model_id: str = Field(..., description="模型ID")
    component_name: str = Field(..., description="元件名称")
    component_data: Dict[str, Any] = Field(..., description="元件数据")


# ============================================================
# API路由
# ============================================================

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "app": "MHFlow",
        "iapws_available": IAPWS_AVAILABLE,
    }


@router.get("/templates/list")
async def get_templates():
    """
    获取可用模板列表

    返回所有可用的热力系统模板。
    """
    templates = list_templates()
    return {
        "templates": templates,
        "count": len(templates),
    }


@router.get("/model/list-saved")
async def list_saved_models():
    """
    获取已保存的模型列表

    返回 models_data 目录中所有 .json 模型文件。
    """
    try:
        settings = get_settings()
        model_dir = settings.MODEL_DIR
        models = []
        if os.path.isdir(model_dir):
            for fname in os.listdir(model_dir):
                if fname.endswith(".json"):
                    fpath = os.path.join(model_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        models.append({
                            "model_id": fname[:-5],
                            "name": data.get("name", fname[:-5]),
                            "description": data.get("description", ""),
                            "component_count": len(data.get("components", [])),
                            "connection_count": len(data.get("connections", [])),
                            "file_path": fpath,
                        })
                    except Exception:
                        pass
        return {
            "models": models,
            "count": len(models),
        }
    except Exception as e:
        logger.error(f"列出模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出模型失败: {str(e)}")


def _load_model_from_file(model_id: str) -> Optional[Dict[str, Any]]:
    """从 models_data 目录加载已保存的JSON模型"""
    settings = get_settings()
    file_path = os.path.join(settings.MODEL_DIR, f"{model_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


@router.post("/model/load")
async def load_model(request: ModelLoadRequest):
    """
    加载模型

    支持两种模式：
    1. 模板ID: 从内置模板加载（如 plant_600mw）
    2. 已保存模型: 从 models_data 目录加载 .json 文件
    """
    try:
        # 先尝试加载内置模板
        try:
            model_data = get_template(request.template_id)
        except ValueError:
            # 如果不是模板ID，尝试从文件加载
            model_data = _load_model_from_file(request.template_id)
            if model_data is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"未找到模板或模型: {request.template_id}"
                )

        # 应用自定义参数
        if request.custom_params:
            model_data = _apply_custom_params(model_data, request.custom_params)

        # 存储当前模型
        model_id = request.template_id
        _current_models[model_id] = model_data

        return {
            "status": "success",
            "model_id": model_id,
            "model_name": model_data.get("name", ""),
            "component_count": len(model_data.get("components", [])),
            "connection_count": len(model_data.get("connections", [])),
            "model_data": model_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载模型失败: {str(e)}")


@router.post("/model/save")
async def save_model(request: ModelSaveRequest):
    """
    保存模型

    将模型数据保存到服务器。
    """
    try:
        settings = get_settings()
        model_dir = settings.MODEL_DIR
        os.makedirs(model_dir, exist_ok=True)

        file_path = os.path.join(model_dir, f"{request.model_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(request.model_data, f, ensure_ascii=False, indent=2)

        _current_models[request.model_id] = request.model_data

        return {
            "status": "success",
            "model_id": request.model_id,
            "file_path": file_path,
        }
    except Exception as e:
        logger.error(f"保存模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存模型失败: {str(e)}")


@router.post("/model/update")
async def update_model(request: ComponentUpdateRequest):
    """
    更新元件参数

    更新指定模型中某个元件的参数。
    """
    try:
        model_data = _current_models.get(request.model_id)
        if model_data is None:
            raise HTTPException(status_code=404, detail=f"模型 {request.model_id} 未找到")

        # 查找并更新元件
        components = model_data.get("components", [])
        found = False
        for comp in components:
            if comp.get("name") == request.component_name:
                # 更新元件数据
                for key, value in request.component_data.items():
                    if key == "params":
                        comp.setdefault("params", {}).update(value)
                    elif key == "inlet_ports":
                        comp["inlet_ports"] = value
                    elif key == "outlet_ports":
                        comp["outlet_ports"] = value
                    else:
                        comp[key] = value
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=404,
                detail=f"元件 {request.component_name} 未找到",
            )

        return {
            "status": "success",
            "model_id": request.model_id,
            "component_name": request.component_name,
            "message": "元件参数已更新",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新元件失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新元件失败: {str(e)}")


@router.post("/solve")
async def solve(request: SolveRequest):
    """
    执行热平衡计算

    对给定的热力系统模型执行热平衡求解，
    返回各节点的热力参数和系统性能指标。
    """
    try:
        # 获取模型数据
        model_data = request.model_data
        if model_data is None and request.model_id:
            model_data = _current_models.get(request.model_id)

        if model_data is None:
            raise HTTPException(
                status_code=400,
                detail="请提供 model_data 或 model_id",
            )

        # 验证模型
        is_valid, errors = validate_model(model_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"模型验证失败: {'; '.join(errors)}"
            )

        # 创建求解器
        settings = get_settings()
        solver = HeatBalanceSolver(
            model_data=model_data,
            max_outer_iterations=request.max_iterations or settings.MAX_ITERATIONS,
            convergence_tolerance=request.convergence_tolerance or settings.CONVERGENCE_TOLERANCE,
        )

        # 执行求解
        results = solver.solve()

        return {
            "status": "success",
            "converged": results.get("converged", False),
            "iteration_count": results.get("iteration_count", 0),
            "system_performance": results.get("system_performance", {}),
            "components": results.get("components", {}),
            "node_data": solver.get_node_data(),
            "extraction_data": solver.get_extraction_data(),
            "heater_balance": solver.get_heater_balance(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"求解失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"求解失败: {str(e)}")


@router.get("/properties/steam")
async def query_steam_properties(
    p: float = Query(..., description="压力 (MPa)"),
    t: Optional[float] = Query(None, description="温度 (°C)"),
    h: Optional[float] = Query(None, description="比焓 (kJ/kg)"),
    s: Optional[float] = Query(None, description="比熵 (kJ/(kg·K))"),
):
    """
    查询水蒸汽物性参数

    根据给定的压力和温度/焓/熵，计算水蒸汽的热物性参数。
    """
    try:
        result = {"p": p}

        if t is not None:
            result["t"] = t
            result["h"] = pt_to_h(p, t)
            result["s"] = pt_to_s(p, t)
            full = get_steam_properties(p, t)
            result.update(full)

        if h is not None:
            result["h_input"] = h
            result["t_from_ph"] = ph_to_t(p, h)
            result["s_from_ph"] = ph_to_s(p, h)

        if s is not None:
            result["s_input"] = s
            result["t_from_ps"] = ps_to_t(p, s)

        return {
            "status": "success",
            "iapws_available": IAPWS_AVAILABLE,
            "data": result,
        }
    except Exception as e:
        logger.error(f"物性查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"物性查询失败: {str(e)}")


@router.get("/properties/saturation")
async def query_saturation_properties(
    p: Optional[float] = Query(None, description="压力 (MPa)"),
    t: Optional[float] = Query(None, description="温度 (°C)"),
):
    """
    查询饱和参数

    根据压力或温度查询饱和水和饱和蒸汽的参数。
    """
    try:
        if p is not None:
            sat = saturation_properties(p)
        elif t is not None:
            from app.properties.steam import saturation_pressure
            p_sat = saturation_pressure(t)
            sat = saturation_properties(p_sat)
        else:
            raise HTTPException(status_code=400, detail="请提供压力或温度")

        return {
            "status": "success",
            "data": sat,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"饱和参数查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"饱和参数查询失败: {str(e)}")


# ============================================================
# 导出路由
# ============================================================

class ExportRequest(BaseModel):
    """导出请求"""
    model: Optional[Dict[str, Any]] = Field(None, description="模型数据")
    result: Optional[Dict[str, Any]] = Field(None, description="计算结果")


def _normalize_export_results(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    将前端格式的计算结果转换为导出器期望的后端格式。

    前端格式 (SolveResult):
        {
            "success": bool,
            "message": str,
            "components": [  // 数组
                {"id": ..., "name": ..., "type": ..., "inlet_ports": [...], "outlet_ports": [...], "extra_params": {...}}
            ],
            "summary": {
                "power_output": float,
                "thermal_efficiency": float,   // %
                "heat_rate": float,
                "coal_consumption": float,
                "steam_rate": float,
                "auxiliary_power_rate": float, // %
            }
        }

    后端格式 (solver.results):
        {
            "converged": bool,
            "iteration_count": int,
            "components": {  // 字典
                "Boiler": {"component_type": ..., "results": {...}, "outlet_ports": [...], "inlet_ports": [...]}
            },
            "system_performance": {
                "w_electrical_mw": float,
                "eta_plant": float,              // 小数
                "heat_rate_kj_kwh": float,
                ...
            }
        }
    """
    if result is None:
        return {}

    # 如果已经是后端格式（components 是 dict），直接返回
    components = result.get("components")
    if isinstance(components, dict):
        return result

    # 否则按前端格式进行转换
    normalized: Dict[str, Any] = {}

    # 基本字段映射
    normalized["converged"] = result.get("success", False)
    normalized["iteration_count"] = 0

    # components: list -> dict
    comp_dict: Dict[str, Any] = {}
    if isinstance(components, list):
        for comp in components:
            if not isinstance(comp, dict):
                continue
            name = comp.get("name") or comp.get("id", "unknown")
            comp_dict[name] = {
                "component_type": comp.get("type", ""),
                "results": comp.get("extra_params", {}),
                "inlet_ports": comp.get("inlet_ports", []),
                "outlet_ports": comp.get("outlet_ports", []),
            }
    normalized["components"] = comp_dict

    # summary -> system_performance
    summary = result.get("summary", {})
    if isinstance(summary, dict):
        normalized["system_performance"] = {
            "w_electrical_mw": summary.get("power_output", 0),
            "w_turbine_internal_mw": 0,
            "q_boiler_mw": 0,
            "heat_rate_kj_kwh": summary.get("heat_rate", 0),
            "eta_boiler": 0,
            "eta_plant": (summary.get("thermal_efficiency", 0) / 100.0),
            "coal_consumption_rate_g_kwh": summary.get("coal_consumption", 0),
            "steam_rate_kg_kwh": summary.get("steam_rate", 0),
            "main_steam_flow_t_h": 0,
            "annual_generation_mwh": 0,
            "annual_coal_tons": 0,
        }
    else:
        normalized["system_performance"] = {}

    return normalized


def _normalize_export_model(model: Dict[str, Any]) -> Dict[str, Any]:
    """将前端格式的模型数据转换为导出器期望的格式"""
    if model is None:
        return {}

    # 如果已经有 name 字段，说明可能是后端模板格式
    if "name" in model:
        return model

    # 前端 SystemModel 只有 components 和 connections
    # 尝试从 components 中推断模型名称或返回默认值
    normalized = dict(model)
    normalized.setdefault("name", "MHFlow Model")
    normalized.setdefault("description", "")
    return normalized


@router.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    """
    导出PDF报告

    将模型和计算结果导出为PDF格式的报告。
    """
    try:
        if not request.result:
            raise HTTPException(status_code=400, detail="请提供计算结果 result")

        results = _normalize_export_results(request.result)
        model_data = _normalize_export_model(request.model or {})

        exporter = PDFExporter(results=results, model_data=model_data)
        pdf_data = exporter.export()

        from io import BytesIO
        buffer = BytesIO(pdf_data)
        filename = f"mhflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF导出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF导出失败: {str(e)}")


@router.post("/export/excel")
async def export_excel(request: ExportRequest):
    """
    导出Excel报告

    将模型和计算结果导出为Excel格式的工作簿，
    包含概览、系统性能、元件结果、节点参数等sheet。
    """
    try:
        if not request.result:
            raise HTTPException(status_code=400, detail="请提供计算结果 result")

        results = _normalize_export_results(request.result)
        model_data = _normalize_export_model(request.model or {})

        exporter = ExcelExporter(results=results, model_data=model_data)
        excel_data = exporter.export()

        from io import BytesIO
        buffer = BytesIO(excel_data)
        filename = f"mhflow_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel导出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Excel导出失败: {str(e)}")


# ============================================================
# 辅助函数
# ============================================================

def _apply_custom_params(model_data: Dict[str, Any], custom_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    应用自定义参数到模型

    支持覆盖:
    - initial_conditions: 初始条件
    - components[name].params: 元件参数
    """
    import copy
    model = copy.deepcopy(model_data)

    # 覆盖初始条件
    if "initial_conditions" in custom_params:
        model.setdefault("initial_conditions", {}).update(
            custom_params["initial_conditions"]
        )

    # 覆盖元件参数
    if "components" in custom_params:
        for comp_name, comp_updates in custom_params["components"].items():
            for comp in model.get("components", []):
                if comp.get("name") == comp_name:
                    if "params" in comp_updates:
                        comp.setdefault("params", {}).update(comp_updates["params"])
                    if "inlet_ports" in comp_updates:
                        comp["inlet_ports"] = comp_updates["inlet_ports"]
                    if "outlet_ports" in comp_updates:
                        comp["outlet_ports"] = comp_updates["outlet_ports"]
                    break

    return model
