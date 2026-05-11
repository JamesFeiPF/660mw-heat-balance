"""MHFlow 全局配置"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "MHFlow 热力系统仿真软件"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 求解器配置
    MAX_ITERATIONS: int = 100
    CONVERGENCE_TOLERANCE: float = 0.01  # kJ/kg
    DAMPING_FACTOR: float = 0.5  # 迭代阻尼因子

    # 文件存储
    MODEL_DIR: str = os.path.join(os.path.dirname(__file__), "..", "models_data")
    EXPORT_DIR: str = os.path.join(os.path.dirname(__file__), "..", "exports")

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()
