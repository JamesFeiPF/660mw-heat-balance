"""MHFlow API路由

提供热力系统仿真软件的REST API接口。
"""
import json
import logging
import os
from typing import Dict, Any, Optional

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


@router.post("/model/load")
async def load_model(request: ModelLoadRequest):
    """
    加载模板模型

    根据模板ID加载预定义的热力系统模型，
    可选地覆盖部分参数。
    """
    try:
        model_data = get_template(request.template_id)

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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
