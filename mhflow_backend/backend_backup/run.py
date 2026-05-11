#!/usr/bin/env python3
"""MHFlow 热力系统仿真软件 - 启动脚本"""
import uvicorn


def main():
    """启动FastAPI服务"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
