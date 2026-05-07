"""MHFlow WebSocket 通信模块"""
import json
import logging
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"新WebSocket连接, 当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket断开, 当前连接数: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """向所有连接广播消息"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """向指定连接发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            self.disconnect(websocket)


# 全局连接管理器
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点

    支持的消息类型:
    - solve: 执行热平衡求解
    - update_params: 更新元件参数
    - get_properties: 查询物性参数
    - ping: 心跳检测
    """
    await manager.connect(websocket)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": "无效的JSON格式",
                })
                continue

            msg_type = message.get("type", "")

            if msg_type == "ping":
                await manager.send_personal(websocket, {
                    "type": "pong",
                    "timestamp": message.get("timestamp", ""),
                })

            elif msg_type == "solve":
                # 执行热平衡求解
                await _handle_solve(websocket, message)

            elif msg_type == "update_params":
                # 更新元件参数
                await manager.send_personal(websocket, {
                    "type": "params_updated",
                    "message": "参数已更新",
                })

            elif msg_type == "get_properties":
                # 查询物性参数
                await _handle_properties(websocket, message)

            else:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": f"未知的消息类型: {msg_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        manager.disconnect(websocket)
        logger.error(f"WebSocket错误: {e}")


async def _handle_solve(websocket: WebSocket, message: Dict[str, Any]):
    """处理求解请求"""
    from app.solvers.heat_balance import HeatBalanceSolver

    model_data = message.get("model_data", {})
    if not model_data:
        await manager.send_personal(websocket, {
            "type": "error",
            "message": "缺少模型数据",
        })
        return

    # 发送开始消息
    await manager.send_personal(websocket, {
        "type": "solve_started",
        "message": "开始热平衡求解...",
    })

    try:
        solver = HeatBalanceSolver(model_data)
        results = solver.solve()

        await manager.send_personal(websocket, {
            "type": "solve_completed",
            "results": results,
        })
    except Exception as e:
        logger.error(f"求解失败: {e}")
        await manager.send_personal(websocket, {
            "type": "solve_error",
            "message": f"求解失败: {str(e)}",
        })


async def _handle_properties(websocket: WebSocket, message: Dict[str, Any]):
    """处理物性查询请求"""
    from app.properties.steam import (
        pt_to_h, pt_to_s, ph_to_t, ph_to_s,
        ps_to_t, get_steam_properties,
    )

    params = message.get("params", {})
    p = params.get("p", 0.0)
    t = params.get("t", 0.0)
    h = params.get("h", 0.0)
    s = params.get("s", 0.0)

    result = {}

    try:
        if p > 0 and t > 0:
            result["pt_to_h"] = pt_to_h(p, t)
            result["pt_to_s"] = pt_to_s(p, t)

        if p > 0 and h > 0:
            result["ph_to_t"] = ph_to_t(p, h)
            result["ph_to_s"] = ph_to_s(p, h)

        if p > 0 and s > 0:
            result["ps_to_t"] = ps_to_t(p, s)

        if p > 0 and t > 0:
            full_props = get_steam_properties(p, t)
            result["full_properties"] = full_props

        await manager.send_personal(websocket, {
            "type": "properties_result",
            "data": result,
        })
    except Exception as e:
        await manager.send_personal(websocket, {
            "type": "error",
            "message": f"物性计算失败: {str(e)}",
        })
