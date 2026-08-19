#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : __init__.py
# @Project : intelligent-jet

"""
WebSocket 服务模块聚合包
"""



import json

from aiohttp import web


async def broadcast_to(clients: set[web.WebSocketResponse], msg: dict) -> None:
    """向指定客户端集合广播 JSON 消息。"""
    if not clients:
        return
    payload = json.dumps(msg, ensure_ascii=False)
    dead = set()
    for ws in clients:
        try:
            await ws.send_str(payload)
        except Exception:
            dead.add(ws)
    clients -= dead


async def broadcast_bytes_to(clients: set[web.WebSocketResponse], data: bytes) -> None:
    """向指定客户端集合广播二进制数据。"""
    if not clients:
        return
    dead = set()
    for ws in clients:
        try:
            await ws.send_bytes(data)
        except Exception:
            dead.add(ws)
    clients -= dead
