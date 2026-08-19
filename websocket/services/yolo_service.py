#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : yolo_service.py
# @Project : intelligent-jet

"""
YOLO 火焰检测 WebSocket 服务 - 推送检测帧和状态数据
"""



import asyncio
import json
import multiprocessing
import os
import sys
import time
from pathlib import Path

from aiohttp import web

from services import broadcast_to, broadcast_bytes_to


# ── YOLOv5 路径 ──
_YOLO_DIR = Path(__file__).resolve().parent.parent / "yolov5"


# ================================================================
#  子进程入口（独立 sys.modules，避免 utils 包名冲突）
# ================================================================

def _detection_process_entry(
    frame_queue: multiprocessing.Queue,
    stop_event: multiprocessing.Event,
    config: dict,
) -> None:
    """在子进程中运行 YOLOv5 检测循环，通过 Queue 传递帧数据。"""
    import cv2

    yolo_dir = config["yolo_dir"]
    source = config["source"]
    conf_thres = config["conf_thres"]
    iou_thres = config["iou_thres"]
    imgsz = config["imgsz"]
    jpeg_quality = config["jpeg_quality"]

    # 移除项目根目录，防止项目自身的 utils 包覆盖 yolov5/utils
    project_root = str(Path(__file__).resolve().parent.parent)
    sys.path = [p for p in sys.path if p != project_root]

    # 将 yolov5 目录插入 sys.path 最前面
    sys.path.insert(0, str(yolo_dir))

    # 清除可能从父进程继承的 utils 模块缓存
    for key in list(sys.modules.keys()):
        if key == "utils" or key.startswith("utils."):
            del sys.modules[key]

    from detect import run

    _frame_times: list[float] = []

    def frame_callback(im0, det) -> None:
        nonlocal _frame_times

        ret, jpeg = cv2.imencode(
            ".jpg", im0, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        )
        if not ret:
            return

        now = time.time()
        _frame_times.append(now)
        _frame_times = [t for t in _frame_times if now - t < 1.0]
        fps = len(_frame_times)
        detection_count = len(det) if det is not None and len(det) else 0

        # 提取检测详细信息（边界框坐标 + 置信度）
        detections = []
        if det is not None and len(det):
            for row in det:
                detections.append({
                    "x1": float(row[0]),
                    "y1": float(row[1]),
                    "x2": float(row[2]),
                    "y2": float(row[3]),
                    "conf": float(row[4]),
                })

        frame_h, frame_w = im0.shape[:2]

        try:
            frame_queue.put_nowait((jpeg.tobytes(), fps, detection_count, detections, frame_w, frame_h))
        except Exception:
            pass  # 队列满，丢弃帧

    while not stop_event.is_set():
        src = source
        if isinstance(src, str) and src.isdigit():
            src = int(src)

        run(
            weights=str(Path(yolo_dir) / "best.pt"),
            source=src,
            data=str(Path(yolo_dir) / "data/coco128.yaml"),
            imgsz=imgsz,
            conf_thres=conf_thres,
            iou_thres=iou_thres,
            max_det=1000,
            device="",
            view_img=False,
            save_txt=False,
            save_csv=False,
            save_conf=False,
            save_crop=False,
            nosave=True,
            classes=None,
            agnostic_nms=False,
            augment=False,
            visualize=False,
            update=False,
            project=str(Path(yolo_dir) / "runs/detect"),
            name="exp",
            exist_ok=False,
            line_thickness=3,
            hide_labels=False,
            hide_conf=False,
            half=False,
            dnn=False,
            vid_stride=1,
            frame_callback=frame_callback,
        )


class YoloService:
    """YOLO 视频流推送服务：子进程检测 + WebSocket 流式推送。"""

    def __init__(
        self,
        source: str | int | None = None,
        conf_thres: float | None = None,
        iou_thres: float = 0.55,
        imgsz: tuple = (640, 640),
        stream_fps: float = 30.0,
        status_interval: float = 0.5,
        jpeg_quality: int = 80,
    ):
        # ── 配置 ──
        self.source = source if source is not None else os.getenv("YOLO_SOURCE", "0")
        self.conf_thres = conf_thres if conf_thres is not None else float(os.getenv("YOLO_CONF_THRES", "0.9"))
        self.iou_thres = iou_thres
        self.imgsz = imgsz
        self.stream_fps = stream_fps
        self.status_interval = status_interval
        self.jpeg_quality = jpeg_quality

        # ── 火焰追踪配置 ──
        self.hfov = float(os.getenv("YOLO_HFOV", "53.27"))           # 水平视场角（度）
        self.vfov = float(os.getenv("YOLO_VFOV", "30.69"))           # 垂直视场角（度）
        self.fire_confirm_frames = int(os.getenv("YOLO_FIRE_CONFIRM_FRAMES", "5"))  # 连续确认帧数

        # ── 运行时状态 ──
        self.ws_clients: set[web.WebSocketResponse] = set()
        self._status_info: dict = {"fps": 0.0, "detection_count": 0}
        self._frame_queue: multiprocessing.Queue | None = None
        self._stop_event: multiprocessing.Event | None = None
        self._detection_process: multiprocessing.Process | None = None
        self._consecutive_fire_frames = 0          # 连续检测到火焰的帧计数
        self._fire_cooldown_until = 0.0            # 火焰追踪冷却截止时间
        self._on_fire_confirmed = None              # 回调: async(cx, cy, frame_w, frame_h, hfov, vfov)

    def set_fire_callback(self, callback) -> None:
        """设置火焰确认后的回调函数。

        回调签名为: async def callback(cx, cy, frame_w, frame_h, hfov, vfov)
        """
        self._on_fire_confirmed = callback

    # ================================================================
    #  帧推送后台循环
    # ================================================================

    async def stream_loop(self, app: web.Application) -> None:
        """后台循环：从帧队列读取数据并推送给 WebSocket 客户端。"""
        loop = asyncio.get_event_loop()
        last_status_time = 0.0

        while True:
            if not self.ws_clients:
                await asyncio.sleep(0.1)
                continue

            # 从子进程队列取帧（阻塞等待，最多 1 秒）
            try:
                jpg_bytes, fps, detection_count, detections, frame_w, frame_h = await loop.run_in_executor(
                    None, self._frame_queue.get, True, 1.0
                )
            except Exception:
                continue

            # 更新本地状态（供新客户端连接时读取）
            self._status_info["fps"] = fps
            self._status_info["detection_count"] = detection_count

            # 推送二进制帧
            await broadcast_bytes_to(self.ws_clients, jpg_bytes)

            # ── 火焰确认逻辑（防误识别：连续帧数 ≥ 阈值才确认） ──
            now = time.time()
            if detection_count > 0:
                self._consecutive_fire_frames += 1
            else:
                self._consecutive_fire_frames = 0

            if (self._consecutive_fire_frames >= self.fire_confirm_frames
                    and self._on_fire_confirmed is not None
                    and now >= self._fire_cooldown_until):
                # 找到面积最大的检测框
                largest = max(detections, key=lambda d: (d["x2"] - d["x1"]) * (d["y2"] - d["y1"]))
                cx = (largest["x1"] + largest["x2"]) / 2
                cy = (largest["y1"] + largest["y2"]) / 2

                print(f"[YOLO] 火焰确认！连续 {self._consecutive_fire_frames} 帧，"
                      f"最大目标中心: ({cx:.0f}, {cy:.0f})，画面: {frame_w}x{frame_h}")

                asyncio.create_task(
                    self._on_fire_confirmed(cx, cy, frame_w, frame_h, self.hfov, self.vfov)
                )

                # 重置计数器并进入冷却（与 PTZ 防抖一致）
                self._consecutive_fire_frames = 0
                self._fire_cooldown_until = now + 5.0 # 聚焦火焰冷却

            # 定期推送状态
            if now - last_status_time >= self.status_interval:
                await broadcast_to(self.ws_clients, {
                    "type": "status",
                    "fps": round(fps, 1),
                    "detection_count": detection_count,
                    "fire_detected": detection_count > 0,
                    "consecutive_fire_frames": self._consecutive_fire_frames,
                })
                last_status_time = now

    # ================================================================
    #  启动检测
    # ================================================================

    async def start_detection(self, app: web.Application) -> None:
        """启动 YOLOv5 检测子进程。"""
        self._frame_queue = multiprocessing.Queue(maxsize=2)
        self._stop_event = multiprocessing.Event()

        config = {
            "yolo_dir": str(_YOLO_DIR),
            "source": self.source,
            "conf_thres": self.conf_thres,
            "iou_thres": self.iou_thres,
            "imgsz": self.imgsz,
            "jpeg_quality": self.jpeg_quality,
        }

        self._detection_process = multiprocessing.Process(
            target=_detection_process_entry,
            args=(self._frame_queue, self._stop_event, config),
            daemon=True,
        )
        self._detection_process.start()
        print(f"[YOLO] 检测进程已启动，PID: {self._detection_process.pid}，源: {self.source}")

    # ================================================================
    #  WebSocket 处理
    # ================================================================

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """处理 YOLO WebSocket 连接生命周期。"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.ws_clients.add(ws)
        client_count = len(self.ws_clients)
        print(f"[WS-YOLO] 新客户端连接，当前共 {client_count} 个")

        # 通知新客户端当前状态
        await ws.send_str(json.dumps({
            "type": "status",
            "message": "YOLO 检测服务已连接",
            "fps": round(self._status_info["fps"], 1),
            "detection_count": self._status_info["detection_count"],
        }, ensure_ascii=False))

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue

                    action = data.get("action", "").strip().lower()

                    if action == "ping":
                        await ws.send_str(json.dumps({"type": "pong"}))
                    elif action == "set_conf_thres":
                        val = data.get("value")
                        if val is not None:
                            self.conf_thres = float(val)
                            print(f"[WS-YOLO] conf_thres → {self.conf_thres}")
                elif msg.type == web.WSMsgType.ERROR:
                    print(f"[WS-YOLO] WebSocket 错误: {ws.exception()}")
        finally:
            self.ws_clients.discard(ws)
            client_count = len(self.ws_clients)
            print(f"[WS-YOLO] 客户端断开，当前共 {client_count} 个")

        return ws

    # ================================================================
    #  清理
    # ================================================================

    def cleanup(self) -> None:
        """停止检测子进程，清理资源。"""
        if self._stop_event is not None:
            self._stop_event.set()
        if self._detection_process is not None and self._detection_process.is_alive():
            self._detection_process.terminate()
            self._detection_process.join(timeout=5.0)
        print("[YOLO] 检测进程已停止")
