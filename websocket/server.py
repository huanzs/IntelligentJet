#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : server.py
# @Project : intelligent-jet


import asyncio
import os
from pathlib import Path

from aiohttp import web
from dotenv import load_dotenv

from services.slm_service import SlmService
from services.ptz_service import PtzService
from services.yolo_service import YoloService
from utils.slm.get_angle import GCAN_IP, GCAN_PORT

# ── 加载环境变量 ──────────────────────────────────────
load_dotenv()

# ── 通用配置 ──────────────────────────────────────────
WS_PORT = int(os.getenv("WS_PORT", "8765"))   # WebSocket / HTTP 服务端口
STATIC_DIR = Path(__file__).parent / "static"

# ── 服务实例 ──────────────────────────────────────────
slm = SlmService()
ptz = PtzService()
yolo = YoloService()


# ================================================================
#  HTTP 处理
# ================================================================

async def handle_index(request: web.Request) -> web.Response:
    """返回 index.html 页面。"""
    html_path = STATIC_DIR / "index.html"
    return web.FileResponse(html_path)


# ================================================================
#  应用生命周期
# ================================================================

async def on_startup(app: web.Application) -> None:
    """服务启动时创建后台任务。"""
    app["gcan_task"] = asyncio.create_task(slm.ensure_connected(app))
    app["slm_control_task"] = asyncio.create_task(slm.control_loop(app))
    app["ptz_task"] = asyncio.create_task(ptz.ensure_connected(app))
    app["ptz_poll_task"] = asyncio.create_task(ptz.angle_poll_loop(app))
    app["yolo_stream_task"] = asyncio.create_task(yolo.stream_loop(app))
    app["yolo_detection_task"] = asyncio.create_task(yolo.start_detection(app))

    # 连接 YOLO → PTZ 火焰追踪
    yolo.set_fire_callback(ptz.handle_fire_target)

    # 注入 SLM 服务引用，支持自动模式下 PTZ 同步消防炮
    ptz.slm_service = slm

    print(f"[服务] 已启动，HTTP + WebSocket 端口: {WS_PORT}")
    print(f"[服务] GCAN 目标: {GCAN_IP}:{GCAN_PORT}")
    print(f"[服务] PTZ 目标: {ptz.ip}:{ptz.port}")
    print(f"[服务] YOLO 源: {yolo.source}")


async def on_cleanup(app: web.Application) -> None:
    """服务关闭时清理资源。"""
    # 取消后台任务
    for key in ("gcan_task", "slm_control_task", "ptz_task", "ptz_poll_task", "yolo_stream_task", "yolo_detection_task"):
        task = app.get(key)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    # 关闭所有 WebSocket
    for ws in list(slm.ws_clients):
        await ws.close()
    slm.ws_clients.clear()
    for ws in list(ptz.ws_clients):
        await ws.close()
    ptz.ws_clients.clear()
    for ws in list(yolo.ws_clients):
        await ws.close()
    yolo.ws_clients.clear()

    # 关闭设备连接
    slm.cleanup()
    ptz.cleanup()
    yolo.cleanup()

    print("[服务] 已关闭")


# ================================================================
#  入口
# ================================================================

def create_app() -> web.Application:
    app = web.Application()

    # 静态页面
    app.router.add_get("/", handle_index)

    # WebSocket 端点
    app.router.add_get("/ws/slm", slm.websocket_handler)
    app.router.add_get("/ws/ptz", ptz.websocket_handler)
    app.router.add_get("/ws/yolo", yolo.websocket_handler)

    # 静态文件（HTML 面板）
    app.router.add_static("/static", STATIC_DIR, name="static")

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=WS_PORT)
