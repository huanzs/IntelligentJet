#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : ptz_control.py
# @Project : intelligent-jet

"""
云台控制模块
功能：云台协议命令构建、角度转换、旋转控制、查询、初始化、搜索
从 模块测试/ptz/utils/ptz_control.py 中提取
"""

import socket


# ============== 协议命令构建 ==============

def calculate_low_byte_of_sum_plus_one(hex_string):
    """
    计算校验和：所有字节相加 + 1，取低字节

    参数:
        hex_string: 十六进制字符串（带空格或不带）

    返回:
        str: 两位十六进制字符串（大写）

    示例:
        输入："FF 01 00 4B" → 输出："4C"
    """
    bytes_list = [int(hex_string[i:i + 2], 16) for i in range(0, len(hex_string), 2)]
    total_sum = sum(bytes_list)
    low_byte = total_sum & 0xFF
    incremented_byte = (low_byte + 1) & 0xFF
    return format(incremented_byte, '02X')


def set_angle_command(base_cmd, angle):
    """
    生成设置角度的命令帧

    参数:
        base_cmd: 基础命令（如'FF 01 00 4B'）
        angle: 目标角度值（十进制度数）

    返回:
        str: 完整的命令帧（带校验和）
    """
    angle_int = int(float(angle) * 100)
    angle_hex = '{:04X}'.format(angle_int)
    cmd = f"{base_cmd} {angle_hex[:2]} {angle_hex[2:]} "
    cmd += calculate_low_byte_of_sum_plus_one(cmd.replace(" ", ""))
    return cmd


def send_command(sock, cmd):
    """
    发送命令到云台控制器并接收响应

    参数:
        sock: TCP Socket 对象
        cmd: 命令（十六进制字符串或 bytes）

    返回:
        str: 云台响应的十六进制字符串，或 None（超时/出错）
    """
    try:
        if isinstance(cmd, bytes):
            message = cmd
        else:
            message = bytes.fromhex(cmd.replace(" ", ""))

        sock.sendall(message)
        sock.settimeout(2.0)
        try:
            data = sock.recv(16)
            return data.hex()
        except socket.timeout:
            return None
    except Exception as e:
        print(f"[PTZ] 发送命令出错: {e}")
        return None


# ============== 角度转换 ==============

def convert_vertical_angle(angle):
    """
    将物理垂直角度转换为云台协议角度

    物理坐标系：上转为正 (+)，下转为负 (-)，范围：-90° ~ +90°
    协议坐标系：顺时针 0° ~ 360°

    转换规则:
        物理角度 ≥ 0:  协议角度 = 360 - 物理角度
        物理角度 < 0:  协议角度 = |物理角度|
    """
    if angle < -90 or angle > 90:
        raise ValueError("角度超出范围，应在 -90 到 90 度之间")
    if angle >= 0:
        return 360 - angle
    else:
        return abs(angle)


def reverse_convert_vertical_angle(converted_angle):
    """
    将云台协议角度逆向转换为物理角度

    逆转换规则:
        270° ≤ 角度 < 360°: 物理角度 = 360 - 协议角度
        0° ≤ 角度 < 270°:   物理角度 = -协议角度
    """
    if converted_angle < 0 or converted_angle >= 360:
        raise ValueError("转换后的角度超出范围，应在 0 到 360 度之间")
    converted_angle = round(converted_angle, 2)
    if 270 <= converted_angle < 360:
        return round(360 - converted_angle, 2)
    else:
        return round(-converted_angle, 2)


# ============== 旋转控制 ==============

def rotate_horizontal(sock, angle):
    """控制云台水平旋转到指定角度"""
    base_cmd = 'FF 01 00 4B'
    cmd = set_angle_command(base_cmd, angle)
    response = send_command(sock, cmd)
    return response


def rotate_vertical(sock, angle):
    """控制云台垂直旋转到指定角度（物理角度，需先转换）"""
    converted_angle = convert_vertical_angle(angle)
    base_cmd = 'FF 01 00 4D'
    cmd = set_angle_command(base_cmd, converted_angle)
    response = send_command(sock, cmd)
    return response


# ============== 响应解析 ==============

def parse_vertical_angle(response):
    """解析云台返回的垂直角度响应数据"""
    try:
        angle_hex = response[8:12]
        angle_value = int(angle_hex, 16)
        angle = angle_value / 100.0
        return angle
    except ValueError:
        print("[PTZ] 解析垂直角度数据时出错")
        return None


def parse_horizontal_angle(response):
    """解析云台返回的水平角度响应数据"""
    try:
        angle_hex = response[8:12]
        angle_value = int(angle_hex, 16)
        angle = angle_value / 100.0
        return angle
    except ValueError:
        print("[PTZ] 解析水平角度数据时出错")
        return None


# ============== 角度查询 ==============

def query_vertical_angle(sock):
    """查询云台当前垂直角度（物理角度，已转换）"""
    query_cmd = 'FF 01 00 53 00 00 54'
    response = send_command(sock, query_cmd)
    if response:
        angle = parse_vertical_angle(response)
        reverse_angle = reverse_convert_vertical_angle(angle)
        return reverse_angle
    return None


def query_horizontal_angle(sock):
    """查询云台当前水平角度"""
    query_cmd = 'FF 01 00 51 00 00 52'
    response = send_command(sock, query_cmd)
    if response:
        angle = parse_horizontal_angle(response)
        return angle
    return None


# ============== 初始化与搜索 ==============

def yt_initialization(sock):
    """云台初始化：水平和垂直方向归零"""
    initialization_command_horizontal = "FF 01 00 4B 00 00 4C"
    send_command(sock, initialization_command_horizontal)
    initialization_command_vertical = "FF 01 00 4D 00 00 4E"
    send_command(sock, initialization_command_vertical)


# def yt_turn(sock):
#     """云台右转搜索"""
#     right_command = "FF 01 00 02 0A 00 0D"
#     send_command(sock, right_command)

def yt_turn(sock):
    """云台右转搜索（不等待响应，快速返回）"""
    right_command = "FF 01 00 02 0A 00 0D"
    return send_command_no_wait(sock, right_command)

# ============== 优化部分 只发送不等待 ==============

def send_command_no_wait(sock, cmd):
    """发送命令但不等待响应（用于 fire-and-forget 控制命令如右转搜索）。"""
    try:
        if isinstance(cmd, bytes):
            message = cmd
        else:
            message = bytes.fromhex(cmd.replace(" ", ""))
        sock.sendall(message)
        return True
    except Exception as e:
        print(f"[PTZ] 发送命令出错: {e}")
        return False


# def drain_socket(sock):
#     """排空 socket 接收缓冲区中的残留数据，防止干扰后续命令的响应读取。"""
#     try:
#         sock.settimeout(0.0)
#         while True:
#             try:
#                 sock.recv(1024)
#             except (BlockingIOError, socket.timeout):
#                 break
#     except Exception:
#         pass
