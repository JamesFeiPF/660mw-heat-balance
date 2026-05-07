"""MHFlow 热力系统仿真软件 - FastAPI 主入口"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import router as api_router
from app.api.websocket import websocket_endpoint


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger.info(f"MHFlow {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 创建必要的目录
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)

    logger.info("MHFlow 启动完成")
    yield
    logger.info("MHFlow 关闭")


# 创建FastAPI应用
app = FastAPI(
    title="MHFlow 热力系统仿真软件",
    description="基于IAPWS-IF97标准的热力系统热平衡仿真计算后端",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router)

# 注册WebSocket
app.websocket("/ws/solve")(websocket_endpoint)


@app.get("/")
async def root():
    """根路径"""
    settings = get_settings()
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
