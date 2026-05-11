"""MHFlow 模板包"""
import json
import os
from .plant_600mw import get_600mw_template

# 模板注册表
TEMPLATES = {
    "600MW超超临界一次再热机组": {
        "id": "plant_600mw",
        "name": "600MW超超临界一次再热机组",
        "description": "典型600MW超超临界一次再热凝汽式汽轮发电机组",
        "capacity": 600,
        "factory": get_600mw_template,
        "json_file": "plant_600mw.json",
    },
}

# 模板JSON文件根目录
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models_data", "templates")


def _load_template_from_json(json_file: str) -> dict:
    """从JSON文件加载模板"""
    path = os.path.join(TEMPLATES_DIR, json_file)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_template(template_id: str) -> dict:
    """根据ID获取模板，优先从JSON文件加载，回退到Python函数"""
    for tid, tinfo in TEMPLATES.items():
        if tinfo["id"] == template_id:
            # 优先尝试JSON文件
            if tinfo.get("json_file"):
                data = _load_template_from_json(tinfo["json_file"])
                if data is not None:
                    return data
            # 回退到Python工厂函数
            return tinfo["factory"]()
    raise ValueError(f"未找到模板: {template_id}")


def list_templates() -> list:
    """获取可用模板列表"""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "capacity": t["capacity"],
        }
        for t in TEMPLATES.values()
    ]


__all__ = ["get_600mw_template", "get_template", "list_templates", "TEMPLATES"]
