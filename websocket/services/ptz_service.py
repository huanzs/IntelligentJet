#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : ptz_service.py
# @Project : intelligent-jet


import asyncio
import json
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web

from services import broadcast_to
from utils.ptz.ptz_control import (
    query_horizontal_angle,
    query_vertical_angle,
    rotate_horizontal,
    rotate_vertical,
    yt_turn,
    send_command,
)


class PtzService:
    """PTZ（云台）服务：连接管理、角度轮询、控制、WebSocket 通信。"""

    def __init__(
        self,
        ip: str | None = None,
        port: int | None = None,
        poll_interval: float = 0.2,
        reconnect_delay: float = 3.0,
        h_angle_min: float = 0.0,
        h_angle_max: float = 360.0,
        v_angle_min: float = -90.0,
        v_angle_max: float = 90.0,
        max_consecutive_failures: int = 3,
    ):
        # ── 配置 ──
        self.ip = ip or os.getenv("PTZ_IP", "10.1.1.81")
        self.port = port or int(os.getenv("PTZ_PORT", "10123"))
        self.poll_interval = poll_interval
        self.reconnect_delay = reconnect_delay
        self.h_angle_min = h_angle_min
        self.h_angle_max = h_angle_max
        self.v_angle_min = v_angle_min
        self.v_angle_max = v_angle_max
        self.max_consecutive_failures = max_consecutive_failures

        # ── 运行时状态 ──
        self.sock: socket.socket | None = None
        self.ws_clients: set[web.WebSocketResponse] = set()
        self._sock_lock = threading.Lock()
        self._consecutive_failures = 0
        self.is_auto: bool = False
        self._fire_cooldown_until = 0.0  # 火焰追踪冷却截止时间
        self.slm_service = None  # 由 server.py 注入，用于自动模式下同步消防炮

    # ================================================================
    #  连接管理
    # ================================================================

    def _connect_sync(self) -> socket.socket | None:
        """同步连接云台控制器，供线程池调用。"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.ip, self.port))
            print(f"[PTZ] 连接成功 {self.ip}:{self.port}")
            return sock
        except Exception as e:
            print(f"[PTZ] 连接失败: {e}")
            return None

    async def ensure_connected(self, app: web.Application) -> None:
        """尝试建立 PTZ 连接，失败时定时重试。"""
        loop = asyncio.get_event_loop()

        while True:
            if self.sock is None:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    sock = await loop.run_in_executor(executor, self._connect_sync)
                if sock is not None:
                    self.sock = sock
                    print(f"[PTZ] 已连接 {self.ip}:{self.port}")
                    await broadcast_to(self.ws_clients, {"type": "status", "message": "云台设备已连接"})
                else:
                    print(f"[PTZ] 连接失败，{self.reconnect_delay}s 后重试...")
                    await broadcast_to(self.ws_clients, {
                        "type": "error",
                        "message": f"云台连接失败，{self.reconnect_delay}s 后重试...",
                    })
                    await asyncio.sleep(self.reconnect_delay)
                    continue

            await asyncio.sleep(self.poll_interval)

    def _mark_disconnected(self) -> None:
        """标记连接已断开，关闭 socket 并重置失败计数。"""
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self._consecutive_failures = 0
        print("[PTZ] 连接已断开，等待重连...")

    # ================================================================
    #  同步操作（加锁保护 socket 并发）
    # ================================================================

    def _query_angles_sync(self, sock):
        """同步查询水平和垂直角度。"""
        with self._sock_lock:
            h = query_horizontal_angle(sock)
            v = query_vertical_angle(sock)
        return h, v

    def _do_rotate_absolute_sync(self, sock, h_angle, v_angle):
        """同步执行绝对角度旋转。"""
        with self._sock_lock:
            h_resp = rotate_horizontal(sock, h_angle)
            v_resp = rotate_vertical(sock, v_angle)
        return h_resp, v_resp

    def _do_search_sync(self, sock):
        """同步执行右转搜索。"""
        with self._sock_lock:
            yt_turn(sock)

    def _do_stop_sync(self, sock):
        """同步发送停止命令。"""
        with self._sock_lock:
            stop_command = "FF 01 00 00 00 00 01"
            return send_command(sock, stop_command)

    # ================================================================
    #  角度轮询循环
    # ================================================================

    async def angle_poll_loop(self, app: web.Application) -> None:
        """每 poll_interval 秒：读取角度 → 广播数据。"""
        loop = asyncio.get_event_loop()

        while True:
            if not self.ws_clients:
                await asyncio.sleep(self.poll_interval)
                continue

            if self.sock is None:
                await asyncio.sleep(self.poll_interval)
                continue

            # 查询实时角度
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    h_angle, v_angle = await loop.run_in_executor(
                        executor, self._query_angles_sync, self.sock
                    )
            except Exception as e:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.max_consecutive_failures:
                    self._mark_disconnected()
                    await broadcast_to(self.ws_clients, {
                        "type": "error", "message": "云台连接已断开，等待重连..."
                    })
                else:
                    await broadcast_to(self.ws_clients, {
                        "type": "error", "message": f"查询角度异常: {e}"
                    })
                await asyncio.sleep(self.poll_interval)
                continue

            if h_angle is None or v_angle is None:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.max_consecutive_failures:
                    self._mark_disconnected()
                    await broadcast_to(self.ws_clients, {
                        "type": "error", "message": "云台连接已断开，等待重连..."
                    })
                else:
                    await broadcast_to(self.ws_clients, {
                        "type": "warning", "message": "未获取到角度数据"
                    })
                await asyncio.sleep(self.poll_interval)
                continue

            # 查询成功，重置失败计数
            self._consecutive_failures = 0

            # 广播角度数据
            await broadcast_to(self.ws_clients, {
                "type": "angle_data",
                "data": {
                    "horizontal_angle": round(h_angle, 2),
                    "vertical_angle": round(v_angle, 2),
                },
            })

            await asyncio.sleep(self.poll_interval)

    # ================================================================
    #  WebSocket 处理
    # ================================================================

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """处理 PTZ WebSocket 连接生命周期。"""
        loop = asyncio.get_event_loop()
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.ws_clients.add(ws)
        client_count = len(self.ws_clients)
        print(f"[WS-PTZ] 新客户端连接，当前共 {client_count} 个")
        await broadcast_to(self.ws_clients, {
            "type": "status", "message": f"客户端已连接，当前 {client_count} 个连接"
        })

        # 通知新客户端当前设备状态
        if self.sock is not None:
            await ws.send_str(json.dumps({
                "type": "status", "message": "云台设备已连接"
            }, ensure_ascii=False))
        else:
            await ws.send_str(json.dumps({
                "type": "warning", "message": "云台设备未连接，等待重连..."
            }, ensure_ascii=False))

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue

                    action = data.get("action", "").strip().lower()
                    if not action:
                        continue

                    # ── 绝对角度旋转 ──
                    if action == "rotate_absolute":
                        if self.sock is None:
                            await ws.send_str(json.dumps({
                                "type": "error", "message": "云台未连接"
                            }, ensure_ascii=False))
                            continue
                        h = float(data.get("h", 0))
                        v = float(data.get("v", 0))
                        h = max(self.h_angle_min, min(self.h_angle_max, h))
                        v = max(self.v_angle_min, min(self.v_angle_max, v))
                        try:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                await loop.run_in_executor(
                                    executor, self._do_rotate_absolute_sync, self.sock, h, v
                                )
                            await broadcast_to(self.ws_clients, {
                                "type": "status",
                                "message": f"旋转到 水平:{h}° 垂直:{v}°",
                            })
                        except Exception as e:
                            await broadcast_to(self.ws_clients, {
                                "type": "error", "message": f"旋转失败: {e}"
                            })

                    # ── 搜索（右转） ──
                    elif action == "search":
                        if self.sock is None:
                            await ws.send_str(json.dumps({
                                "type": "error", "message": "云台未连接"
                            }, ensure_ascii=False))
                            continue
                        try:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                await loop.run_in_executor(
                                    executor, self._do_search_sync, self.sock
                                )
                            await broadcast_to(self.ws_clients, {
                                "type": "status", "message": "云台开始右转搜索"
                            })
                        except Exception as e:
                            await broadcast_to(self.ws_clients, {
                                "type": "error", "message": f"搜索失败: {e}"
                            })

                    # ── 设置自动模式 ──
                    elif action == "set_auto":
                        value = data.get("value", False)
                        self.is_auto = bool(value)
                        print(f"[WS-PTZ] is_auto → {self.is_auto}")
                        await broadcast_to(self.ws_clients, {
                            "type": "auto_state", "is_auto": self.is_auto
                        })

                    # ── 急停 ──
                    elif action == "emergency_stop":
                        if self.sock is None:
                            continue
                        try:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                await loop.run_in_executor(
                                    executor, self._do_stop_sync, self.sock
                                )
                            await broadcast_to(self.ws_clients, {
                                "type": "status", "message": "云台已急停"
                            })
                        except Exception as e:
                            await broadcast_to(self.ws_clients, {
                                "type": "error", "message": f"急停失败: {e}"
                            })

        finally:
            self.ws_clients.discard(ws)
            client_count = len(self.ws_clients)
            print(f"[WS-PTZ] 客户端断开，当前共 {client_count} 个")

        return ws

    # ================================================================
    #  火焰追踪
    # ================================================================

    async def handle_fire_target(self, cx, cy, frame_w, frame_h, hfov, vfov) -> None:
        """处理火焰追踪：根据火焰中心坐标计算绝对偏转角度并旋转。

        参数:
            cx: 火焰中心 X 坐标（像素）
            cy: 火焰中心 Y 坐标（像素）
            frame_w: 画面宽度（像素）
            frame_h: 画面高度（像素）
            hfov: 水平视场角（度）
            vfov: 垂直视场角（度）
        """
        # 检查冷却（防抖：旋转后 10s 内不再追踪）
        now = time.time()
        if now < self._fire_cooldown_until:
            remaining = self._fire_cooldown_until - now
            print(f"[PTZ] 火焰追踪冷却中，剩余 {remaining:.1f}s")
            return

        if self.sock is None:
            print("[PTZ] 云台未连接，无法追踪火焰")
            return

        # 计算像素偏差（火焰中心相对于画面中心的偏移）
        center_x = frame_w / 2
        center_y = frame_h / 2
        error_x = cx - center_x       # 正值：目标在右侧
        error_y = center_y - cy       # 正值：目标在上方（图像 Y 轴反转）

        # 像素偏差 → 角度偏差
        pixels_per_degree_x = frame_w / hfov
        pixels_per_degree_y = frame_h / vfov
        angle_error_h = error_x / pixels_per_degree_x  # 水平角度偏差
        angle_error_v = error_y / pixels_per_degree_y  # 垂直角度偏差

        # 查询当前角度
        loop = asyncio.get_event_loop()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                h_angle, v_angle = await loop.run_in_executor(
                    executor, self._query_angles_sync, self.sock
                )
        except Exception as e:
            print(f"[PTZ] 火焰追踪查询角度失败: {e}")
            return

        if h_angle is None or v_angle is None:
            print("[PTZ] 火焰追踪：无法获取当前角度")
            return

        # 计算新的绝对角度
        new_h = h_angle + angle_error_h
        new_v = v_angle + angle_error_v

        # 限制角度范围
        new_h = max(self.h_angle_min, min(self.h_angle_max, new_h))
        new_v = max(self.v_angle_min, min(self.v_angle_max, new_v))

        print(f"[PTZ] 火焰追踪: 当前({h_angle:.1f}°, {v_angle:.1f}°) → "
              f"目标({new_h:.1f}°, {new_v:.1f}°)，"
              f"偏差({angle_error_h:.2f}°, {angle_error_v:.2f}°)")

        # 执行旋转
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                await loop.run_in_executor(
                    executor, self._do_rotate_absolute_sync, self.sock, new_h, new_v
                )
        except Exception as e:
            print(f"[PTZ] 火焰追踪旋转失败: {e}")
            return

        # 自动模式下同步消防炮
        if self.is_auto and self.slm_service is not None:
            slm = self.slm_service
            if slm.gcan_sock is not None:
                slm_target_h = new_h
                # 同步角度换算差距
                if slm_target_h > 180:
                    slm_target_h -= 360
                slm_target_v = 20.0  # 俯仰角固定20°
                try:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        from utils.slm.control import move_to_angle
                        await loop.run_in_executor(
                            executor, move_to_angle, slm.gcan_sock, slm_target_h, slm_target_v
                        )
                    print(f"[PTZ] 自动模式：消防炮同步 水平={slm_target_h:.1f}° 俯仰={slm_target_v:.1f}°")
                except Exception as e:
                    print(f"[PTZ] 自动模式：消防炮同步失败: {e}")
            else:
                print("[PTZ] 自动模式：消防炮 GCAN 未连接，跳过同步")
        elif self.is_auto:
            print("[PTZ] 自动模式：未注入 slm_service，跳过消防炮同步")

        # 设置冷却（10秒内不再追踪）
        self._fire_cooldown_until = time.time() + 10.0
        print("[PTZ] 火焰追踪完成，进入10s冷却")

        # 通知客户端
        await broadcast_to(self.ws_clients, {
            "type": "fire_track",
            "message": f"火焰追踪: 旋转到 水平:{new_h:.1f}° 垂直:{new_v:.1f}°",
            "data": {
                "horizontal_angle": round(new_h, 2),
                "vertical_angle": round(new_v, 2),
            },
        })

    # ================================================================
    #  清理
    # ================================================================

    def cleanup(self) -> None:
        """释放 PTZ 连接。"""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
