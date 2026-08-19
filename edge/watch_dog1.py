#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : watch_dog1.py
# @Project : intelligent-jet

"""
智能联动主控模块v1 - 基础版联动控制
"""

import threading

from camera_control import CameraControl
from fire_yolo import FireYOLODetector
from slm_driver import SLMDriver


def camera_thread(camera_control, timeout):
    camera_control.Searching(timeout)


def cannon_thread(slm_driver, position):
    slm_driver.SetIntelligentFireCannon(position)


def main():
    detector = FireYOLODetector()
    camera_control = CameraControl(detector)
    slm_driver = SLMDriver()

    # 创建线程
    camera_thread_timeout = 10  # 相机搜索超时时间，单位秒
    camera_thread_obj = threading.Thread(target=camera_thread, args=(camera_control, camera_thread_timeout))

    # 启动相机搜索线程
    camera_thread_obj.start()

    # 等待火焰检测事件或超时
    camera_thread_obj.join(camera_thread_timeout)  # 等待线程完成或超时
    if not camera_control.fire_detected.is_set():
        print("No fire detected within timeout, setting default cannon position.")
        # 启动消防炮设置线程
        cannon_position = "default_position"
        cannon_thread_obj = threading.Thread(target=cannon_thread, args=(slm_driver, cannon_position))
        cannon_thread_obj.start()
        cannon_thread_obj.join()  # 等待消防炮设置线程完成


if __name__ == "__main__":
    main()