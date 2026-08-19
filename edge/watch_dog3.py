#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : watch_dog3.py
# @Project : intelligent-jet
import json
import queue
import threading
import time

import slm_driver
from camera_control3 import CameraControlSearching
from slm_driver import SLMDriver

# 主程序
def main():
    fire_detected_event = threading.Event()
    stop_searching_event = threading.Event()

    # 相机相关参数属性初始化
    result_queue = queue.Queue()

    # 消防炮相关参数属性初始化
    #server_ip = '192.168.1.10'
    server_ip = '10.1.1.119'
    server_port = 4001  # TCP服务器端口
    can_data = '88 0C FD FE 00 10 00 04 00 10 00 00 00'

    slm_driver = SLMDriver(server_ip,server_port)

    # 定义火源目标发现后的处理函数
    def handle_fire_detected():
        if fire_detected_event.is_set():
            print("Fire detected! Triggering fire search system...")
            # 在这里可以启动另一个线程来执行射流操作，或者调用其他函数
            #set_fire_cannon_position()

            result = result_queue.get()
            result_json = json.loads(result)  # 序列化
            cannon_position = result_json['position']

            cannon_thread = threading.Thread(target=slm_driver.set_fire_cannon_position, args=(cannon_position,))
            cannon_thread.start()
            # 如果需要重置事件以便它可以再次被触发，可以取消注释下一行
            # fire_detected_event.clear()

    # 创建并启动寻火线程
    searching_thread = CameraControlSearching(fire_detected_event, stop_searching_event,result_queue)
    searching_thread.start()
    print(f"1_watch_dog_3 CameraControlSearching 子线程 started.")

    # 监听火源发现事件（这里使用轮询方式，后续采用更高效的机制）
    while searching_thread.is_alive():
        if fire_detected_event.is_set():
            handle_fire_detected()
            # 如果不需要再次触发，可以停止寻火线程
            stop_searching_event.set()
            break
        time.sleep(0.1)  # 主线程轮询间隔

    # 等待寻火线程结束（如果需要的话）
    searching_thread.join()

    print("Searching thread has finished.")


if __name__ == "__main__":
    main()