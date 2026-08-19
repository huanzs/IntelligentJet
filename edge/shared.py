# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : shared.py
# @Project : intelligent-jet

"""
边缘端共享状态模块 - 线程间共享的火焰检测状态和控制信号
"""


import threading

FIRE_CONFIRM_COUNT = 5

# 全局变量用于存储目标位置
target = None
frame_size = None
target_last_seen = 0.0
fire_detection_streak = 0
fire_confirmed_last_seen = 0.0
infrared_frame = None
program_exit_requested = False
max_temperature = None
max_temperature_last_seen = 0.0

# 线程锁用于保护对 target1 的访问
target_lock = threading.Lock()
infrared_lock = threading.Lock()
temperature_lock = threading.Lock()
