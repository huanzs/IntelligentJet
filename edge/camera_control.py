#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : camera_control.py
# @Project : intelligent-jet
import json
import sys

from fire_yolo import FireYOLODetector
import cv2

import threading
import time
import cv2
from fire_yolo import FireYOLODetector
import random
# 功能描述：

# 添加 YOLOv5 目录到 Python 路径
yolo_path = r'C:\projects\fire_test\yolov5-master'
sys.path.append(yolo_path)
from detect import run

#包含火焰检测的逻辑
class CameraControl:
    def __init__(self, result_queue):
        self.result_queue = result_queue

    def capture_image(self):
        # 模拟图像捕获，实际中应该是从相机获取
        # 使用OpenCV创建一个模拟图像，真实生产模式下读取相机视频流
        import numpy as np
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        # 假设我们有时能“捕获”到火焰
        if np.random.rand() > 0.9:  # 只有10%的概率模拟检测到火焰
            cv2.rectangle(image, (100, 100), (200, 200), (0, 0, 255), -1)  # 红色方块表示火焰
            return image, True  # 返回图像和检测结果
        return image, False
    """
    def Searching(self, timeout):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.detect_fire():
               # self.result_queue.put("Fire detected!")

               parsed_data = {
                   'detected': True,
                   'count': 2
                   # 可以根据需要继续添加字段
               }
               return str(parsed_data)
            time.sleep(0.1)
      """

    def Searching(self, timeout):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.detect_fire():
                parsed_data = {
                    'detected': True,
                    'count': 2,  # 这里假设 count 总是 2，或者你可以根据实际需求修改它
                    'position':'88 0C FD FE 00 12 0B 84 16 84 00 00 00'   #'position':'88 0C FD FE 00 12 0B 84 16 84 00 00 00'
                    #'position':'88 0C FD FE 00 12 00 04 00 04 00 00 00'  # 'position':'88 0C FD FE 00 12 0B 84 16 84 00 00 00'
                }
                # 将字典转换为 JSON 字符串并返回
                self.result_queue.put(json.dumps(parsed_data))
                return
            time.sleep(0.1)
            # 如果在超时前没有检测到火情，可以选择返回一个表示未检测到火情的字符串
        self.result_queue.put(json.dumps({'detected': False, 'message': 'No fire detected within timeout'}))
        return
    def detect_fire(self):
         # 模拟随机测试火焰检测过程
         #return random.choice([True, False])
         #return True


         detector = FireYOLODetector(yolo_path, "last.pt", 'data/coco128.yaml')
         source = "rtsp://10.1.1.126:554/0/888888:888888/main"
         fire_info = detector.detect_fire2(source)
         #fire_info_json = json.dumps(fire_info)
         #fire_info_json_str = json.loads(fire_info_json)  # 序列化

         print(f"camera_control_1 Returned fire info: {fire_info}")
         return fire_info['detected']
