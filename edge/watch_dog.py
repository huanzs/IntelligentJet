#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : watch_dog.py
# @Project : intelligent-jet

"""
智能联动主控模块 - 火焰检测→定位→瞄准→喷射全自动联动
"""

import json
import threading
import queue
from camera_control import CameraControl
from protocol_parser import ProtocolParser
from slm_driver import SLMDriver

def main():

    # 相机相关参数属性初始化
    result_queue = queue.Queue()
    camera_control = CameraControl(result_queue)

    # 消防炮相关参数属性初始化
    #server_ip = '192.168.1.10'
    server_ip = '10.1.1.119'
    server_port = 4001  # TCP服务器端口
    can_data = '88 0C FD FE 00 10 00 04 00 10 00 00 00'

    slm_driver = SLMDriver(server_ip,server_port)

    # 启动相机搜索线程
    camera_thread = threading.Thread(target=camera_control.Searching, args=(30,))  # 假设超时时间为30秒
    camera_thread.start()
    print(f"watch_dog_1 Setting camera thread started.")

    # 主线程循环检查队列中的结果
    try:
        result = result_queue.get(timeout=30)  # 等待最多30秒来获取结果
       # print(type(result))
        print(f"#########################################{result}")

        result_json = json.loads(result)    #序列化
        fire_detected = result_json['detected']

        print(f"watch_dog_2 result queue get: {result}")
        #if result == "Fire detected!":  # Fire detected!
        if fire_detected:  # Fire detected!
            # 检测到火焰，启动消防炮设置线程
            cannon_position = "target_position"  # 这里是根据火焰位置计算出的消防炮位置，传入进来的位置信息

            cannon_raw_position = cannon_position
            # 位置参数封装，原始数据解析封装
            cannon_last_position = ProtocolParser()

            cannon_position = result_json['position']

            # 启动消防炮处理线程
            print(f"watch_dog_3 cannon_position : {cannon_position}\n")
            cannon_thread = threading.Thread(target=slm_driver.set_fire_cannon_position, args=(cannon_position,))
            #cannon_thread = threading.Thread(target=slm_driver.set_fire_cannon_position, args=(cannon_last_position.parse(cannon_raw_position),))
            #print(f"watch_dog_3 cannon_last_position : {cannon_last_position.parse(cannon_raw_position)}")
            cannon_thread.start()
            print(f"\nwatch_dog_4 Setting cannon thread started.")

            # 等待消防炮设置完成（后续）
            cannon_thread.join()

    except queue.Empty:
        print("No fire detected within the timeout period.")

        # 等待相机搜索线程完成（如果它还没有因为检测到火焰而结束）
    camera_thread.join()

if __name__ == "__main__":
    main()