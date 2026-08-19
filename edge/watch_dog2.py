#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : watch_dog2.py
# @Project : intelligent-jet

"""
智能联动主控模块v2 - 引入消息队列优化联动流程
"""

import queue


def main():
    result_queue = queue.Queue()
    camera_control = CameraControl(result_queue)
    slm_driver = SLMDriver()

    # 启动相机搜索线程
    camera_control.start_searching(30)
    print("Camera thread started.")

    try:
        while True:
            if not camera_control.is_alive():
                print("Camera thread has stopped.")
                break

            try:
                result = result_queue.get(timeout=1)  # 缩短超时以更频繁地检查
                result_json = json.loads(result)
                if result_json['detected']:
                    cannon_position = result_json['position']
                    cannon_thread = threading.Thread(target=slm_driver.set_fire_cannon_position,
                                                     args=(cannon_position,))
                    cannon_thread.start()
                    print(f"Cannon thread started to position {cannon_position}")
            except queue.Empty:
                pass

                # 可以在这里添加更多逻辑，比如检查其他线程或执行其他任务

            time.sleep(0.1)  # 稍微休眠一下，避免过度占用CPU

    except KeyboardInterrupt:
        print("Main loop interrupted by user.")

        # 等待所有线程完成（在这个例子中，我们可能不等待cannon_thread，因为它可能在主循环结束后还在运行）
    if camera_control.is_alive():
        camera_control.searching_thread.join()


if __name__ == "__main__":
    main()
