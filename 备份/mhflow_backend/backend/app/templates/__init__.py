"""MHFlow 模板包"""
from .plant_600mw import get_600mw_template

# 模板注册表
TEMPLATES = {
    "600MW超超临界一次再热机组": {
        "id": "plant_600mw",
        "name": "600MW超超临界一次再热机组",
        "description": "典型600MW超超临界一次再热凝汽式汽轮发电机组",
        "capacity": 600,
        "factory": get_600mw_template,
    },
}


def get_template(template_id: str):
    """根据ID获取模板"""
    for tid, tinfo in TEMPLATES.items():
        if tinfo["id"] == template_id:
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
