#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : fire_yolo2.py
# @Project : intelligent-jet

"""
火焰 YOLOv5 检测模块v2 - 优化版火焰检测，支持多模型切换
"""

import sys
import os
# 添加 YOLOv5 目录到 Python 路径
#yolo_path = os.path.join(os.path.dirname(__file__), 'yolov5-master')
yolo_path = r'E:\GitDepository\fire_test\yolov5-master'
sys.path.append(yolo_path)

from detect import run
import torch
def detect_fire():
    # 设置参数
    #weights = os.path.join(yolo_path, r"C:\Users\93704\Desktop\Project\yolov5-master\last.pt")
    weights = os.path.join(yolo_path, r"last.pt")
    source = "rtsp://10.1.1.126:554/0/888888:888888/main"
    fire_info = {}

    # 内嵌检测回调函数，用于捕捉检测结果
    def detection_callback(det):
        nonlocal fire_info
        fire_info = {
            'detected': len(det) > 0,
            'count': len(det),
            'detections': det
        }
        #print(fire_info)
        print(f"fire_yolo2_1 Returned fire info: {fire_info}")

    run(weights=weights,
        source=source,
        data=os.path.join(yolo_path, 'data/coco128.yaml'),  # 数据集配置文件路径
        imgsz=(640, 640),  # 推理图像大小（高度, 宽度）
        conf_thres=0.8,  # 置信度阈值
        iou_thres=0.45,  # NMS IOU 阈值，默认值为 0.45
        max_det=1000,  # 每张图像的最大检测数量，默认值为 1000
        device='',  # 使用默认设备（CPU 或 GPU）
        view_img=True,  # 显示检测结果
        save_txt=False,  # 不保存文本结果
        save_csv=False,  # 不保存结果到 CSV 文件
        save_conf=False,  # 不保存置信度
        save_crop=False,  # 不保存裁剪的预测框
        nosave=True,  # 不保存图像/视频
        classes=None,  # 过滤类别
        agnostic_nms=False,  # 类别不可知的 NMS
        augment=False,  # 增强推理
        visualize=False,  # 可视化特征
        update=False,  # 更新所有模型
        project=os.path.join(yolo_path, 'runs/detect'),  # 保存结果的目录
        name='exp',  # 保存结果的子目录
        exist_ok=False,  # 是否覆盖已存在的 project/name
        line_thickness=3,  # 边界框厚度
        hide_labels=False,  # 隐藏标签
        hide_conf=False,  # 隐藏置信度
        half=False,  # 使用 FP16 半精度推理
        dnn=False,  # 使用 OpenCV DNN 进行 ONNX 推理
        vid_stride=1,  # 视频帧率步长，默认值为 1
        detected=detection_callback,  # 添加检测回调函数
    )

    return fire_info

if __name__ == "__main__":
    fire_info = detect_fire()
    #print(fire_info)
    print(f"fire_yolo2_100 Returned fire info: {fire_info}")

