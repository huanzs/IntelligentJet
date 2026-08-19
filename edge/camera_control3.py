#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : camera_control3.py
# @Project : intelligent-jet

"""
摄像头云台控制模块v3 - 支持随机扫描和线程安全的云台控制
"""

import random
import threading
import time
import json
import sys

from fire_yolo import FireYOLODetector
#功能描述：
#与1代比较：

# 添加 YOLOv5 目录到 Python 路径
yolo_path = r'C:\projects\fire_test\yolov5-master'
sys.path.append(yolo_path)

# 寻火线程
class CameraControlSearching(threading.Thread):
    def __init__(self, fire_detected_event, stop_event,result_queue):
        super().__init__()
        self.fire_detected_event = fire_detected_event
        self.stop_event = stop_event
        self.result_queue = result_queue

    def run(self):
        while not self.stop_event.is_set():
            # 模拟寻火过程
            # time.sleep(1)  # 假设每秒检查一次
            # if random.random() > 0.9:  # 模拟发现火源的概率
            #     self.fire_detected_event.set()  # 触发火源发现事件
            #     # 注意：在实际应用中，你可能希望在这里重置事件，以便它可以再次被触发
            #     # 但在这个示例中，我们假设火源只会被发现一次
            #     break  # 停止寻火循环（如果需要继续寻火，则不移除此行）
            if self.detect_fire():
                parsed_data = {
                    'detected': True,
                    'count': 2,  # 这里假设 count 总是 2，或者你可以根据实际需求修改它
                    'position': '88 0C FD FE 00 12 0B 84 16 84 00 00 00'
                    # 'position':'88 0C FD FE 00 12 0B 84 16 84 00 00 00'
                    # 'position':'88 0C FD FE 00 12 00 04 00 04 00 00 00'  # 'position':'88 0C FD FE 00 12 0B 84 16 84 00 00 00'
                }
                # 将字典转换为 JSON 字符串并返回
                self.result_queue.put(json.dumps(parsed_data))
                return

    def detect_fire(self):

         detector = FireYOLODetector(yolo_path, "last.pt", 'data/coco128.yaml')
         source = "rtsp://10.1.1.126:554/0/888888:888888/main"
         fire_info = detector.detect_fire2(source)
         #fire_info_json = json.dumps(fire_info)
         #fire_info_json_str = json.loads(fire_info_json)  # 序列化

         print(f"camera_control_3 Returned fire info: {fire_info}")
         return fire_info['detected']
