#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : control.py
# @Project : intelligent-jet

"""
消防炮控制模块 - 通过 GCAN-212 协议实现方向和角度控制
"""



import socket

from utils.slm.angle_conversion import BinaryProcessor

# 协议常量
EXT_FRAME_PREFIX = "88"
CONTROL_HEAD = "0C FD FE 00"
CONTROL_TYPE_POSITION = "12"


def move_to_angle(sock: socket.socket, horizontal_angle: float, vertical_angle: float) -> bool:
    """
    控制消防炮移动到目标角度。

    参数:
        sock: 已连接的 GCAN TCP socket
        horizontal_angle: 水平角度（-180 ~ 180）
        vertical_angle: 俯仰角度（-180 ~ 180）

    返回:
        bool: 指令是否发送成功
    """
    processor = BinaryProcessor()
    hex_h, hex_v = processor.process_and_convert(
        int(round(horizontal_angle)),
        int(round(vertical_angle)),
    )

    can_protocol = " ".join([
        EXT_FRAME_PREFIX,
        CONTROL_HEAD,
        CONTROL_TYPE_POSITION,
        hex_h,
        hex_v,
        "00", "00", "00",
    ])

    try:
        raw = bytes.fromhex(can_protocol.replace(" ", ""))
        sock.sendall(raw)
        print(f"[控制] 发送指令: {can_protocol}  → 目标角度 H={horizontal_angle:+.1f}° V={vertical_angle:+.1f}°")
        return True
    except Exception as e:
        print(f"[控制] 发送控制指令失败: {e}")
        return False
