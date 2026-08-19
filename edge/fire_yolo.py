#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : fire_yolo.py
# @Project : intelligent-jet
import sys
import os


# 添加 YOLOv5 目录到 Python 路径
yolo_path = r'C:\projects\fire_test\yolov5-master'
sys.path.append(yolo_path)
from detect import run
# 假设我们有一个模拟的detect函数，实际上你应该使用YOLOv5的API来加载模型并预测
# 这里我们使用一个占位符函数来模拟detect.run的行为
def mock_detect(weights, source, **kwargs):
    # 模拟的检测结果
    # 在实际中，这里应该是YOLOv5模型的预测结果
    mock_detections = [
        {'x1': 100, 'y1': 200, 'x2': 300, 'y2': 400, 'confidence': 0.95, 'class': 0, 'name': 'fire'},
        # 可以添加更多模拟的检测结果
    ]
    return mock_detections

class FireYOLODetector:
    def __init__(self, yolo_path, weights_path, data_path):
        self.yolo_path = yolo_path
        self.weights_path = os.path.join(yolo_path, weights_path)
        self.data_path = os.path.join(yolo_path, data_path)
        # 初始化检测结果存储
        self.fire_info = {}

    def detect_fire(self, image):
        # 真实生产模式下，这里会加载YOLO模型，处理图像，并返回检测结果
        # 这里模拟测试直接返回一个模拟的检测结果
        # 假设我们总是检测到火焰
        return True  # 表示检测到火焰

    def detect_fire2(self, image_source):
       """
        # 注意：在实际应用中，image_source是一个图像文件路径、视频文件路径或视频流URL
        # 但由于我们在这里模拟，我们将忽略它，并直接调用mock_detect函数

        # 模拟的YOLOv5检测过程
        detections = mock_detect(self.weights_path, image_source, data=self.data_path, imgsz=(640, 640), conf_thres=0.8,
                                 iou_thres=0.45)

        # 处理检测结果
        self.fire_info = {
            'detected': len(detections) > 0,
            'count': len(detections),
            'detections': detections
        }

        # 打印或返回检测结果（这里我们同时做两者）
        print(self.fire_info)
        return self.fire_info
     """
       weights = os.path.join(yolo_path, r"last.pt")
       source = "rtsp://10.1.1.126:554/0/888888:888888/main"
       fire_info = {}
       print(f"fire_yolo_1 detection_callback调用前:")
       # 内嵌检测回调函数，用于捕捉检测结果
       def detection_callback(det):
              nonlocal fire_info
              '''
              fire_info = {
                          'detected': len(det) > 0,
                          'count': len(det),
                          'detections': det
                        }
             '''
              fire_info = {
                  'detected': len(det) > 0,
                  'count': len(det),  # 这里假设 count 总是 2，或者你可以根据实际需求修改它
                  #'position': '88 0C FD FE 00 12 00 04 00 04 00 00 00'
                  'position':'88 0C FD FE 00 12 0B 84 16 84 00 00 00'
              }
              print(f"fire_yolo detection_callback调用后:")

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


# 测试
if __name__ == "__main__":
    detector = FireYOLODetector(yolo_path, "last.pt", 'data/coco128.yaml')
    source = "rtsp://10.1.1.126:554/0/888888:888888/main"
    fire_info = detector.detect_fire2(source)
    #print("Returned fire info:", fire_info)
    print(f"fire_yolo_10 Returned fire info: {fire_info}")
