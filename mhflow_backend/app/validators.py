"""模型验证器

对热力系统模型进行结构和参数验证。
"""
from typing import Dict, Any, List, Tuple


def validate_model(model_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证模型数据的完整性和一致性

    Returns:
        (is_valid, error_messages)
    """
    errors = []
    components = model_data.get("components", [])
    connections = model_data.get("connections", [])

    if not components:
        errors.append("模型中没有组件")
        return False, errors

    # 1. 组件名称唯一性
    names = [c.get("name", "") for c in components]
    dupes = [n for n in set(names) if names.count(n) > 1]
    if dupes:
        errors.append(f"组件名称重复: {', '.join(dupes)}")

    # 2. 构建组件和端口索引
    comp_map = {}
    for comp in components:
        cname = comp.get("name", "")
        if not cname:
            errors.append(f"发现未命名组件 (type={comp.get('component_type', '?')})")
            continue
        # 收集出口端口（包括 outlet_ports 和 params.extractions）
        outlet_ports = {p.get("name", "") for p in comp.get("outlet_ports", [])}
        extractions = comp.get("params", {}).get("extractions", [])
        for ext in extractions:
            outlet_ports.add(ext.get("name", ""))
        comp_map[cname] = {
            "type": comp.get("component_type", comp.get("type", "")),
            "inlet_ports": {p.get("name", "") for p in comp.get("inlet_ports", [])},
            "outlet_ports": outlet_ports,
        }

    # 3. 验证连接
    used_outlets = set()
    used_inlets = set()
    for i, conn in enumerate(connections):
        from_str = conn.get("from", "")
        to_str = conn.get("to", "")

        if "." not in from_str or "." not in to_str:
            errors.append(f"连接 #{i+1} 格式错误: '{from_str}' -> '{to_str}'")
            continue

        from_comp, from_port = from_str.rsplit(".", 1)
        to_comp, to_port = to_str.rsplit(".", 1)

        # 检查组件存在
        if from_comp not in comp_map:
            errors.append(f"连接 #{i+1}: 源组件 '{from_comp}' 不存在")
        else:
            # 检查出口端口存在
            if from_port not in comp_map[from_comp]["outlet_ports"]:
                errors.append(
                    f"连接 #{i+1}: 组件 '{from_comp}' 没有出口端口 '{from_port}'"
                )

        if to_comp not in comp_map:
            errors.append(f"连接 #{i+1}: 目标组件 '{to_comp}' 不存在")
        else:
            # 检查入口端口存在
            if to_port not in comp_map[to_comp]["inlet_ports"]:
                errors.append(
                    f"连接 #{i+1}: 组件 '{to_comp}' 没有入口端口 '{to_port}'"
                )

        used_outlets.add(from_str)
        used_inlets.add(to_str)

    # 4. 检查一源多入（同一个入口被多个出口连接）
    inlet_targets = [c.get("to", "") for c in connections]
    dup_inlets = [t for t in set(inlet_targets) if inlet_targets.count(t) > 1]
    if dup_inlets:
        errors.append(f"多个出口连接到同一入口: {', '.join(dup_inlets)}")

    # 5. 检查基本组件类型
    types = {c["type"] for c in comp_map.values()}
    if "boiler" not in types:
        errors.append("模型缺少锅炉组件")
    if "generator" not in types:
        errors.append("模型缺少发电机组件")
    if "condenser" not in types:
        errors.append("模型缺少凝汽器组件")

    # 6. 检查汽轮机功率连接（如果存在多缸汽轮机）
    turbines = [n for n, info in comp_map.items() if info["type"] == "turbine"]
    if len(turbines) > 1:
        # 检查是否有功率串联连接
        power_conns = [
            c for c in connections
            if "power" in c.get("from", "") or "power" in c.get("to", "")
        ]
        if not power_conns:
            errors.append(
                "多缸汽轮机模型缺少功率串联连接 (HP.power_out -> IP.power_in -> ... -> Generator)"
            )

    return len(errors) == 0, errors
