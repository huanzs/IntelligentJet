# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : camera_control4.py
# @Project : intelligent-jet

import threading


class CameraControlSearchAlign(threading.Thread):
    def __init__(self, fire_detected_event, stop_event,result_queue):
        super().__init__()
        self.fire_detected_event = fire_detected_event
        self.stop_event = stop_event
        self.result_queue = result_queue