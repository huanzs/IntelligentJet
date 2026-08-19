#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : slm_service.py
# @Project : intelligent-jet

"""
消防炮(SLM) WebSocket 服务 - 处理消防炮方向控制和状态查询
"""



import asyncio
import json
import socket
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web

from services import broadcast_to
from utils.slm.get_angle import connect_gcan, get_angle, GCAN_IP, GCAN_PORT
from utils.slm.control import move_to_angle


class SlmService:
    """SLM（消防炮）服务：GCAN 连接管理、角度轮询、控制、WebSocket 通信。"""

    def __init__(
        self,
        poll_interval: float = 0.1,
        reconnect_delay: float = 3.0,
        angle_offset: int = 4,
        v_angle_min: float = 0.0,
        v_angle_max: float = 90.0,
    ):
        # ── 配置 ──
        self.poll_interval = poll_interval
        self.reconnect_delay = reconnect_delay
        self.angle_offset = angle_offset
        self.v_angle_min = v_angle_min
        self.v_angle_max = v_angle_max
        self.valid_move_states = {"stop", "left", "right", "up", "down"}

        # ── 运行时状态 ──
        self.gcan_sock: socket.socket | None = None
        self.ws_clients: set[web.WebSocketResponse] = set()
        self.move_state: str = "stop"

    # ================================================================
    #  GCAN 连接管理
    # ================================================================

    @staticmethod
    def _connect_gcan_sync() -> socket.socket | None:
        """同步连接 GCAN，供线程池调用。"""
        return connect_gcan()

    async def ensure_connected(self, app: web.Application) -> None:
        """尝试建立 GCAN 连接，失败时定时重试。"""
        loop = asyncio.get_event_loop()

        while True:
            if self.gcan_sock is not None:
                try:
                    from utils.slm.get_angle import _build_empty_operation_command
                    self.gcan_sock.sendall(_build_empty_operation_command())
                except Exception:
                    print("[GCAN] 连接已断开，准备重连...")
                    try:
                        self.gcan_sock.close()
                    except Exception:
                        pass
                    self.gcan_sock = None

            if self.gcan_sock is None:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    sock = await loop.run_in_executor(executor, self._connect_gcan_sync)
                if sock is not None:
                    self.gcan_sock = sock
                    print(f"[GCAN] 已连接 {GCAN_IP}:{GCAN_PORT}")
                    await broadcast_to(self.ws_clients, {"type": "status", "message": "GCAN 设备已连接"})
                else:
                    print(f"[GCAN] 连接失败，{self.reconnect_delay}s 后重试...")
                    await broadcast_to(self.ws_clients, {
                        "type": "error",
                        "message": f"GCAN 连接失败，{self.reconnect_delay}s 后重试...",
                    })
                    await asyncio.sleep(self.reconnect_delay)
                    continue

            await asyncio.sleep(self.poll_interval)

    # ================================================================
    #  控制逻辑
    # ================================================================

    def _compute_target_angle(self, current_h: float, current_v: float, direction: str):
        """根据当前角度和方向计算目标角度，返回 (target_h, target_v, clipped)。"""
        target_h, target_v = current_h, current_v

        if direction == "left":
            target_h = current_h - self.angle_offset
        elif direction == "right":
            target_h = current_h + self.angle_offset
        elif direction == "up":
            target_v = current_v + self.angle_offset
        elif direction == "down":
            target_v = current_v - self.angle_offset

        clipped = False
        if target_v < self.v_angle_min:
            target_v = self.v_angle_min
            clipped = True
        elif target_v > self.v_angle_max:
            target_v = self.v_angle_max
            clipped = True

        if clipped:
            self.move_state = "stop"

        return target_h, target_v, clipped

    def _do_control_sync(self, sock, direction, current_h, current_v):
        """同步执行 SLM 控制逻辑（供线程池调用）。"""
        target_h, target_v, clipped = self._compute_target_angle(current_h, current_v, direction)
        success = move_to_angle(sock, target_h, target_v)
        return target_h, target_v, clipped, success

    # ================================================================
    #  控制循环
    # ================================================================

    async def control_loop(self, app: web.Application) -> None:
        """每 poll_interval 秒：读取角度 → 执行控制（如有）→ 广播数据。"""
        loop = asyncio.get_event_loop()

        while True:
            if not self.ws_clients:
                await asyncio.sleep(self.poll_interval)
                continue

            if self.gcan_sock is None:
                await asyncio.sleep(self.poll_interval)
                continue

            # 1. 获取实时角度
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    result = await loop.run_in_executor(executor, get_angle, self.gcan_sock)
            except Exception as e:
                await broadcast_to(self.ws_clients, {"type": "error", "message": f"获取角度异常: {e}"})
                await asyncio.sleep(self.poll_interval)
                continue

            if result is None:
                await broadcast_to(self.ws_clients, {"type": "warning", "message": "未获取到角度数据"})
                await asyncio.sleep(self.poll_interval)
                continue

            current_h = result["horizontal_angle"]
            current_v = result["vertical_angle"]

            # 2. 若有移动指令，执行控制
            if self.move_state != "stop":
                direction = self.move_state
                try:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        target_h, target_v, clipped, success = await loop.run_in_executor(
                            executor, self._do_control_sync, self.gcan_sock, direction, current_h, current_v,
                        )
                    if clipped:
                        await broadcast_to(self.ws_clients, {
                            "type": "warning",
                            "message": "俯仰角到达边界，已停止移动",
                        })
                    if success:
                        result["horizontal_angle"] = target_h
                        result["vertical_angle"] = target_v
                except Exception as e:
                    await broadcast_to(self.ws_clients, {"type": "error", "message": f"控制执行异常: {e}"})

            # 3. 广播角度数据（含 move_state）
            await broadcast_to(self.ws_clients, {
                "type": "angle_data", "data": result, "move_state": self.move_state
            })

            await asyncio.sleep(self.poll_interval)

    # ================================================================
    #  WebSocket 处理
    # ================================================================

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """处理 SLM WebSocket 连接生命周期。"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.ws_clients.add(ws)
        client_count = len(self.ws_clients)
        print(f"[WS-SLM] 新客户端连接，当前共 {client_count} 个")
        await broadcast_to(self.ws_clients, {
            "type": "status", "message": f"客户端已连接，当前 {client_count} 个连接"
        })

        # 通知新客户端当前 GCAN 状态与控制状态
        if self.gcan_sock is not None:
            await ws.send_str(json.dumps({"type": "status", "message": "GCAN 设备已连接"}, ensure_ascii=False))
        else:
            await ws.send_str(json.dumps({"type": "warning", "message": "GCAN 设备未连接，等待重连..."}, ensure_ascii=False))
        await ws.send_str(json.dumps({"type": "move_state", "move_state": self.move_state}, ensure_ascii=False))

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    text = msg.data.strip().lower()

                    # ── 回归原点 ──
                    if text == "home":
                        self.move_state = "stop"
                        print("[WS-SLM] move_state → stop (home)")
                        await broadcast_to(self.ws_clients, {
                            "type": "move_state", "move_state": "stop"
                        })
                        if self.gcan_sock is not None:
                            try:
                                with ThreadPoolExecutor(max_workers=1) as executor:
                                    await asyncio.get_event_loop().run_in_executor(
                                        executor, move_to_angle, self.gcan_sock, 0, 0
                                    )
                                await broadcast_to(self.ws_clients, {
                                    "type": "status", "message": "已回归原点 (0, 0)"
                                })
                            except Exception as e:
                                await broadcast_to(self.ws_clients, {
                                    "type": "error", "message": f"回归原点失败: {e}"
                                })
                        else:
                            await ws.send_str(json.dumps({
                                "type": "error", "message": "GCAN 设备未连接，无法回归原点"
                            }, ensure_ascii=False))
                        continue
                    # —— 移动 ——
                    if text in self.valid_move_states:
                        if text == self.move_state and text != "stop":
                            self.move_state = "stop"
                        else:
                            self.move_state = text
                        print(f"[WS-SLM] move_state → {self.move_state}")
                        await broadcast_to(self.ws_clients, {
                            "type": "move_state", "move_state": self.move_state
                        })
        finally:
            self.ws_clients.discard(ws)
            client_count = len(self.ws_clients)
            print(f"[WS-SLM] 客户端断开，当前共 {client_count} 个")

            if not self.ws_clients:
                self.move_state = "stop"
                print("[WS-SLM] 无客户端，move_state 重置为 stop")

        return ws

    # ================================================================
    #  清理
    # ================================================================

    def cleanup(self) -> None:
        """释放 GCAN 连接。"""
        if self.gcan_sock:
            try:
                self.gcan_sock.close()
            except Exception:
                pass
            self.gcan_sock = None
