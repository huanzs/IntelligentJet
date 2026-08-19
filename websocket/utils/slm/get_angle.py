#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : get_angle.py
# @Project : intelligent-jet


import socket
import struct

GCAN_IP = '10.1.1.119'
GCAN_PORT = 4001
RECV_TIMEOUT = 3.0
MAX_RECV_ATTEMPTS = 5

CONTROL_CAN_ID = 0x0CFDFE00
BROADCAST_CAN_ID = 0x18EFFE00
BROADCAST_CAN_MASK = 0x00FFFF00

EXT_FRAME_PREFIX = 0x88


def connect_gcan(ip=GCAN_IP, port=GCAN_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(RECV_TIMEOUT)
    try:
        sock.connect((ip, port))
        return sock
    except Exception as e:
        print(f"[错误] 连接 GCAN-212 失败: {e}")
        return None


def _build_can_tcp_frame(can_id, data_bytes):
    frame = bytes([EXT_FRAME_PREFIX])
    frame += struct.pack('>I', can_id)
    frame += bytes(data_bytes)
    return frame


def _build_empty_operation_command():
    can_data = [0x10, 0x00, 0x10, 0x00, 0x10, 0x00, 0x00, 0x00]
    return _build_can_tcp_frame(CONTROL_CAN_ID, can_data)


def _parse_tcp_frame(frame):
    if len(frame) < 13 or frame[0] != EXT_FRAME_PREFIX:
        return None
    can_id = struct.unpack('>I', frame[1:5])[0]
    can_data = list(frame[5:13])
    return can_id, can_data


def _is_broadcast_frame(can_id):
    return (can_id & BROADCAST_CAN_MASK) == (BROADCAST_CAN_ID & BROADCAST_CAN_MASK)


def _parse_broadcast_data(data):
    if len(data) < 8:
        return None

    byte1 = data[0]
    control_type = (byte1 >> 4) & 0x0F
    status_type = byte1 & 0x0F

    x_word = (data[1] << 8) | data[2]
    x_offset_raw = (x_word >> 4) & 0x0FFF
    x_positive = (x_word >> 2) & 0x03
    x_negative = x_word & 0x03

    x_angle = x_offset_raw * 0.1
    if x_positive == 0b01:
        x_angle = +x_angle
    elif x_negative == 0b01:
        x_angle = -x_angle

    y_word = (data[3] << 8) | data[4]
    y_offset_raw = (y_word >> 4) & 0x0FFF
    y_positive = (y_word >> 2) & 0x03
    y_negative = y_word & 0x03

    y_angle = y_offset_raw * 0.1
    if y_positive == 0b01:
        y_angle = +y_angle
    elif y_negative == 0b01:
        y_angle = -y_angle

    pressure = data[5] * 0.01

    x_pos_limit = (data[7] >> 6) & 0x03
    x_neg_limit = (data[7] >> 4) & 0x03
    y_pos_limit = (data[7] >> 2) & 0x03
    y_neg_limit = data[7] & 0x03
    z_pos_limit = (data[6] >> 4) & 0x03
    z_neg_limit = (data[6] >> 2) & 0x03

    status_map = {0: '无效', 1: '有效', 2: '错误', 3: '不使用'}

    return {
        'control_type': control_type,
        'status_type': status_type,
        'horizontal_angle': round(x_angle, 1),
        'vertical_angle': round(y_angle, 1),
        'x_positive_status': status_map.get(x_positive, '未知'),
        'x_negative_status': status_map.get(x_negative, '未知'),
        'y_positive_status': status_map.get(y_positive, '未知'),
        'y_negative_status': status_map.get(y_negative, '未知'),
        'pressure_mpa': round(pressure, 2),
        'x_pos_limit': status_map.get(x_pos_limit, '未知'),
        'x_neg_limit': status_map.get(x_neg_limit, '未知'),
        'y_pos_limit': status_map.get(y_pos_limit, '未知'),
        'y_neg_limit': status_map.get(y_neg_limit, '未知'),
    }


def get_angle(sock):
    """
    查询消防炮当前水平和垂直角度。

    参数:
        sock: 已连接的 TCP socket（由 connect_gcan() 获取）

    返回:
        dict: 包含 horizontal_angle、vertical_angle、pressure_mpa 等字段，失败返回 None
    """
    if sock is None:
        print("[错误] socket 为 None，请先调用 connect_gcan() 建立连接")
        return None
    cmd = _build_empty_operation_command()
    try:
        sock.sendall(cmd)
    except Exception as e:
        print(f"[错误] 发送失败: {e}")
        return None

    for _ in range(MAX_RECV_ATTEMPTS):
        try:
            data = sock.recv(1024)
            if not data:
                continue

            offset = 0
            while offset + 13 <= len(data):
                frame = data[offset:offset + 13]
                result = _parse_tcp_frame(frame)
                if result is None:
                    offset += 1
                    continue

                can_id, can_data = result
                if _is_broadcast_frame(can_id):
                    parsed = _parse_broadcast_data(can_data)
                    if parsed and parsed['control_type'] == 2:
                        return parsed

                offset += 13

        except socket.timeout:
            continue
        except Exception as e:
            print(f"[错误] 接收失败: {e}")
            return None

    return None


if __name__ == '__main__':
    sock = connect_gcan()
    if sock:
        try:
            result = get_angle(sock)
            if result:
                print(f"水平角度: {result['horizontal_angle']:+.1f}°")
                print(f"垂直角度: {result['vertical_angle']:+.1f}°")
                print(f"管道压力: {result['pressure_mpa']:.2f} MPa")
            else:
                print("[失败] 未能获取角度数据")
        finally:
            sock.close()