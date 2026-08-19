#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : watch_dog6.py
# @Project : intelligent-jet

"""
智能联动主控模块v6(最新) - 完整版联动控制，含PID闭环和GCAN协议
"""



import os
import socket
import sys
import threading
import time

import cv2
import shared

os.environ["YOLO_CONFIG_DIR"] = r"C:\projects\projects\.ultralytics"
base_path = os.path.dirname(os.path.abspath(__file__))
if base_path not in sys.path:
    sys.path.insert(0, base_path)
yolo_path = r"C:\projects\projects\fire_test\yolov5-master"
sys.path.append(yolo_path)
import detect as detect_module

run = detect_module.run


HFOV = 53.27
VFOV = 30.69
CENTER_THRESHOLD_X = 24
CENTER_THRESHOLD_Y = 18
CENTER_LOCK_REGION_SIZE = 50
SEARCH_MOVE_SETTLE = 0.6
ADJUST_COOLDOWN = 1.0
CENTER_PAN_SPEED = 0x10
CENTER_TILT_SPEED = 0x10
CENTER_LOCK_FRAME_COUNT = 10
TARGET_LOST_TIMEOUT = 0.45
VISIBLE_FIRE_CONFIRM_COUNT = shared.FIRE_CONFIRM_COUNT
QUERY_TIMEOUT = 0.3
INITIAL_PAN_ANGLE = 0.0
INITIAL_TILT_ANGLE = 0.0
PTZ_PAN_SPEED = 0x3F
PTZ_TILT_SPEED = 0x3F
STARTUP_CENTER_HOLD_SECONDS = 0.1
STARTUP_TILT_TIMEOUT = 2.0
STARTUP_TILT_SETTLE_SECONDS = 1.0
STARTUP_TILT_CONTINUOUS_SECONDS = 0.8
STARTUP_PAN_SETTLE_SECONDS = 1.2
STARTUP_ANGLE_TOLERANCE = 0.5
ANGLE_QUERY_INTERVAL = 0.2
SEARCH_SOURCE = "rtsp://10.1.1.126:554/0/888888:888888/main"
INFRARED_SOURCE = "rtsp://10.1.1.126:554/1/888888:888888/main"
PTZ_SERVER_ADDRESS = ("10.1.1.82", 10123)
THERMAL_SERVER_ADDRESS = ("10.1.1.126", 502)
THERMAL_MODBUS_UNIT_ID = 1
THERMAL_MODBUS_FUNCTION = 0x04
THERMAL_MAX_TEMPERATURE_REGISTER = 0x0007
THERMAL_QUERY_TIMEOUT = 0.5
THERMAL_POLL_INTERVAL = 0.5
THERMAL_TEMPERATURE_SCALE = 10.0
THERMAL_COORDINATE_SERVER_ADDRESS = ("10.1.1.80", 10123)
THERMAL_COORDINATE_HEADER = b"\xA5\xAE"
THERMAL_COORDINATE_TAIL = b"\xBC\xBE"
THERMAL_COORDINATE_FRAME_LENGTHS = (19, 17)
THERMAL_COORDINATE_CONNECT_RETRY = 1.0
THERMAL_COORDINATE_READ_TIMEOUT = 1.0
THERMAL_COORDINATE_LOG_MAX_AGE = 2.0
LASER_DISTANCE_SCALE = 10.0
FIRE_CANNON_SERVER_ADDRESS = ("10.1.1.119", 4001)
FIRE_CANNON_POSITION = "88 0C FD FE 00 12 03 C4 03 C4 00 00 00"
FIRE_CANNON_STATIONARY_TRIGGER_DELAY = 3.0
FIRE_CANNON_REPEAT_INTERVAL = 3.0
FIRE_CANNON_CENTER_HORIZONTAL = 1.0
FIRE_CANNON_CENTER_VERTICAL = 12.0
FIRE_CANNON_HORIZONTAL_SCALE = 0.35
FIRE_CANNON_VERTICAL_SCALE = 0.25
FIRE_CANNON_HORIZONTAL_OFFSET = 0.0
FIRE_CANNON_VERTICAL_OFFSET = 0.0
CAMERA_CENTER_PAN_ANGLE = 0.0
CAMERA_CENTER_TILT_ANGLE = -10.0

thermal_coordinate_lock = threading.Lock()
latest_thermal_coordinate = None
last_zero_distance_log_time = 0.0


def get_target_snapshot():
    with shared.target_lock:
        return shared.target, shared.frame_size or (1280, 720), shared.target_last_seen


def get_fire_detection_snapshot():
    with shared.target_lock:
        return shared.fire_detection_streak, shared.target_last_seen, shared.fire_confirmed_last_seen


def has_recent_visible_fire(now=None):
    _, target_last_seen, _ = get_fire_detection_snapshot()
    now = time.time() if now is None else now
    return target_last_seen > 0 and (now - target_last_seen) <= TARGET_LOST_TIMEOUT


def has_confirmed_visible_fire(now=None):
    _, _, fire_confirmed_last_seen = get_fire_detection_snapshot()
    now = time.time() if now is None else now
    return fire_confirmed_last_seen > 0 and (now - fire_confirmed_last_seen) <= TARGET_LOST_TIMEOUT


def trim_float(value, digits=1):
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def format_distance(value):
    if value is None:
        return "NA"
    return f"{trim_float(value, digits=1)}m"


def get_latest_thermal_coordinate(now=None):
    with thermal_coordinate_lock:
        measurement = None if latest_thermal_coordinate is None else latest_thermal_coordinate.copy()

    if measurement is None:
        return None

    now = time.time() if now is None else now
    if now - measurement["timestamp"] > THERMAL_COORDINATE_LOG_MAX_AGE:
        return None
    return measurement


def coordinate_checksum_ok(frame, data_length):
    checksum_index = 2 + data_length
    checksum = sum(frame[:checksum_index]) & 0xFF
    return checksum == frame[checksum_index]


def parse_thermal_coordinate_frame(frame):
    data_length = len(frame) - 5
    if not frame.startswith(THERMAL_COORDINATE_HEADER) or not frame.endswith(THERMAL_COORDINATE_TAIL):
        raise ValueError(f"bad coordinate frame boundary: {frame.hex(' ')}")
    if data_length not in (12, 14):
        raise ValueError(f"bad coordinate data length: {data_length}")
    if not coordinate_checksum_ok(frame, data_length):
        raise ValueError(f"bad coordinate checksum: {frame.hex(' ')}")

    data = frame[2:2 + data_length]
    values = [int.from_bytes(data[index:index + 2], "big") for index in range(0, data_length, 2)]
    measurement = {
        "values": values,
        "x": values[0],
        "y": values[1],
        "temperature": float(values[2]),
        "straight_distance": values[3] / LASER_DISTANCE_SCALE if len(values) > 3 else None,
        "horizontal_distance_1": values[4] / LASER_DISTANCE_SCALE if len(values) > 4 else None,
        "horizontal_distance_2": values[5] / LASER_DISTANCE_SCALE if len(values) > 5 else None,
        "reserved": values[6] if len(values) > 6 else None,
        "raw": frame.hex(" "),
        "timestamp": time.time(),
    }
    return measurement


def extract_thermal_coordinate_frames(buffer):
    frames = []

    while True:
        start = buffer.find(THERMAL_COORDINATE_HEADER)
        if start < 0:
            if len(buffer) > 1:
                del buffer[:-1]
            break
        if start > 0:
            del buffer[:start]

        parsed = False
        for frame_length in THERMAL_COORDINATE_FRAME_LENGTHS:
            if len(buffer) < frame_length:
                continue
            if bytes(buffer[frame_length - 2:frame_length]) != THERMAL_COORDINATE_TAIL:
                continue

            data_length = frame_length - 5
            frame = bytes(buffer[:frame_length])
            if coordinate_checksum_ok(frame, data_length):
                frames.append(frame)
                del buffer[:frame_length]
            else:
                del buffer[0]
            parsed = True
            break

        if parsed:
            continue
        if len(buffer) >= max(THERMAL_COORDINATE_FRAME_LENGTHS):
            del buffer[0]
            continue
        break

    return frames


def update_latest_thermal_coordinate(measurement):
    global latest_thermal_coordinate, last_zero_distance_log_time

    with thermal_coordinate_lock:
        latest_thermal_coordinate = measurement

    with shared.temperature_lock:
        shared.max_temperature = measurement["temperature"]
        shared.max_temperature_last_seen = measurement["timestamp"]
        shared.max_temperature_point = (measurement["x"], measurement["y"])
        shared.fire_laser_distance = measurement["straight_distance"]
        shared.thermal_coordinate_last_seen = measurement["timestamp"]

    distance_values = [
        measurement.get("straight_distance"),
        measurement.get("horizontal_distance_1"),
        measurement.get("horizontal_distance_2"),
    ]
    if all(value in (None, 0) for value in distance_values):
        now = time.time()
        if now - last_zero_distance_log_time >= 5.0:
            print(
                "Thermal coordinate stream OK, but laser distance fields are zero: "
                f"values={measurement['values']}, raw={measurement['raw']}"
            )
            last_zero_distance_log_time = now


def get_thermal_measurement_log_text():
    now = time.time()
    measurement = get_latest_thermal_coordinate(now)
    if measurement is not None:
        temperature = trim_float(measurement["temperature"], digits=1)
        parts = [
            f"IR max(x={measurement['x']},y={measurement['y']},temp={temperature}oC)",
        ]

        straight_distance = measurement.get("straight_distance")
        if straight_distance is not None:
            distances_text = (
                f"line={format_distance(straight_distance)},"
                f"h1={format_distance(measurement.get('horizontal_distance_1'))},"
                f"h2={format_distance(measurement.get('horizontal_distance_2'))}"
            )
            if has_recent_visible_fire(now):
                parts.append(f"fire_laser({distances_text})")
            else:
                parts.append(f"laser({distances_text})")

        return ", ".join(parts) + ","

    with shared.temperature_lock:
        temperature = shared.max_temperature
        last_seen = shared.max_temperature_last_seen

    if temperature is None or now - last_seen > THERMAL_COORDINATE_LOG_MAX_AGE:
        return ""
    return detect_module.format_temperature_for_log(temperature)


def install_detection_log_formatter():
    detect_module.get_max_temperature_log_text = get_thermal_measurement_log_text


def calculate_low_byte_of_sum_plus_one(hex_string):
    bytes_list = [int(hex_string[i:i + 2], 16) for i in range(0, len(hex_string), 2)]
    total_sum = sum(bytes_list)
    low_byte = total_sum & 0xFF
    incremented_byte = (low_byte + 1) & 0xFF
    return format(incremented_byte, "02X")


def clamp_speed(speed):
    return max(0, min(int(speed), 0x3F))


def movement_command(command2, pan_speed=0, tilt_speed=0):
    cmd = f"FF 01 00 {command2:02X} {clamp_speed(pan_speed):02X} {clamp_speed(tilt_speed):02X} "
    cmd += calculate_low_byte_of_sum_plus_one(cmd.replace(" ", ""))
    return cmd


def set_angle_command(base_cmd, angle):
    angle_int = int(float(angle) * 100)
    angle_hex = f"{angle_int:04X}"
    cmd = f"{base_cmd} {angle_hex[:2]} {angle_hex[2:]} "
    cmd += calculate_low_byte_of_sum_plus_one(cmd.replace(" ", ""))
    return cmd


def send_command(sock, cmd, expect_response=False, timeout=QUERY_TIMEOUT):
    try:
        message = cmd if isinstance(cmd, bytes) else bytes.fromhex(cmd.replace(" ", ""))
        sock.sendall(message)
        if not expect_response:
            return None

        sock.settimeout(timeout)
        try:
            return sock.recv(16).hex()
        except socket.timeout:
            return None
    except Exception as e:
        print(f"发送云台命令失败: {e}")
        return None


def stop_ptz(sock, repeat=1, interval=0.05):
    for index in range(repeat):
        send_command(sock, "FF 01 00 00 00 00 01")
        if index < repeat - 1:
            time.sleep(interval)


def pan_right(sock, speed=PTZ_PAN_SPEED, log=False):
    cmd = movement_command(0x02, pan_speed=speed)
    if log:
        print(f"发送右转命令: 速度 0x{clamp_speed(speed):02X}, {cmd}")
    send_command(sock, cmd)


def pan_left(sock, speed=PTZ_PAN_SPEED, log=False):
    cmd = movement_command(0x04, pan_speed=speed)
    if log:
        print(f"发送左转命令: 速度 0x{clamp_speed(speed):02X}, {cmd}")
    send_command(sock, cmd)


def tilt_up(sock, speed=PTZ_TILT_SPEED, log=False):
    cmd = movement_command(0x08, tilt_speed=speed)
    if log:
        print(f"发送上转命令: 速度 0x{clamp_speed(speed):02X}, {cmd}")
    send_command(sock, cmd)


def tilt_down(sock, speed=PTZ_TILT_SPEED, log=False):
    cmd = movement_command(0x10, tilt_speed=speed)
    if log:
        print(f"发送下转命令: 速度 0x{clamp_speed(speed):02X}, {cmd}")
    send_command(sock, cmd)


def set_continuous_motion(sock, motion_state, command2, pan_speed=0, tilt_speed=0):
    key = (command2, clamp_speed(pan_speed), clamp_speed(tilt_speed))
    if motion_state.get("current") == key:
        return
    send_command(sock, movement_command(command2, pan_speed=pan_speed, tilt_speed=tilt_speed))
    motion_state["current"] = key


def stop_continuous_motion(sock, motion_state, force=False):
    if not force and motion_state.get("current") == "stop":
        return
    stop_ptz(sock)
    motion_state["current"] = "stop"


def hold_current_position(sock, motion_state):
    stop_continuous_motion(sock, motion_state, force=True)
    stop_ptz(sock, repeat=5, interval=0.1)
    motion_state["current"] = "stop"
    time.sleep(0.2)


def yt_initialization(sock):
    send_command(sock, "FF 01 00 4B 00 00 4C")
    send_command(sock, "FF 01 00 4D 00 00 4E")


def parse_horizontal_angle(response):
    try:
        return int(response[8:12], 16) / 100.0
    except (TypeError, ValueError):
        return None


def parse_vertical_angle(response):
    try:
        return int(response[8:12], 16) / 100.0
    except (TypeError, ValueError):
        return None


def query_horizontal_angle(sock, log=False):
    response = send_command(sock, "FF 01 00 51 00 00 52", expect_response=True)
    if log:
        print(f"水平角度查询响应: {response or '无响应'}")
    if not response:
        return None
    return parse_horizontal_angle(response)


def query_vertical_angle_raw(sock, log=False):
    response = send_command(sock, "FF 01 00 53 00 00 54", expect_response=True)
    if log:
        print(f"垂直角度查询响应: {response or '无响应'}")
    if not response:
        return None
    return parse_vertical_angle(response)


def convert_vertical_to_protocol(angle):
    if angle < -90 or angle > 90:
        raise ValueError("角度超出范围，应在 -90 到 90 度之间")
    if angle > 0:
        return 360 - angle
    return abs(angle)


def convert_protocol_to_vertical(angle):
    if angle is None:
        return None
    if round(angle, 2) == 360.0:
        return 0.0
    if 270 <= angle < 360:
        return round(360 - angle, 2)
    return round(-angle, 2)


def query_vertical_angle(sock, log=False):
    return convert_protocol_to_vertical(query_vertical_angle_raw(sock, log=log))


def normalize_horizontal(angle):
    return angle % 360.0


def clamp_vertical(angle):
    return max(min(angle, 90.0), -90.0)


def rotate_horizontal_to(sock, angle, log=False):
    protocol_angle = normalize_horizontal(angle)
    cmd = set_angle_command("FF 01 00 4B", protocol_angle)
    if log:
        print(f"发送水平绝对角度命令: 水平 {protocol_angle:.1f} 度, {cmd}")
    return send_command(sock, cmd)


def rotate_vertical_to(sock, angle, log=False):
    protocol_angle = convert_vertical_to_protocol(clamp_vertical(angle))
    cmd = set_angle_command("FF 01 00 4D", protocol_angle)
    if log:
        print(f"发送垂直绝对角度命令: 逻辑 {angle:.1f} 度 -> 协议 {protocol_angle:.1f} 度, {cmd}")
    return send_command(sock, cmd)


def move_ptz(sock, ptz_state, pan=None, tilt=None, settle=SEARCH_MOVE_SETTLE):
    if pan is not None:
        pan = normalize_horizontal(pan)
        rotate_horizontal_to(sock, pan)
        ptz_state["pan"] = pan

    if tilt is not None:
        tilt = clamp_vertical(tilt)
        rotate_vertical_to(sock, tilt)
        ptz_state["tilt"] = tilt

    time.sleep(settle)
    stop_ptz(sock)


def wait_for_vertical_angle(sock, ptz_state, target_tilt, timeout=STARTUP_TILT_TIMEOUT):
    deadline = time.time() + timeout
    last_tilt = None
    logged_query = False

    while time.time() < deadline:
        current_tilt = query_vertical_angle(sock, log=not logged_query)
        logged_query = True
        if current_tilt is not None:
            last_tilt = clamp_vertical(current_tilt)
            ptz_state["tilt"] = last_tilt
            if abs(last_tilt - target_tilt) <= STARTUP_ANGLE_TOLERANCE:
                stop_ptz(sock)
                return True, last_tilt

        time.sleep(ANGLE_QUERY_INTERVAL)

    stop_ptz(sock)
    return False, last_tilt


def move_vertical_to_startup_center(sock, ptz_state):
    target_tilt = clamp_vertical(INITIAL_TILT_ANGLE)
    current_tilt = query_vertical_angle(sock, log=True)

    if current_tilt is None:
        print("未读取到垂直角度，先用速度模式抬头，再发送上下 00 定位。")
        tilt_up(sock, speed=PTZ_TILT_SPEED, log=True)
        print(f"连续上转 {STARTUP_TILT_CONTINUOUS_SECONDS:.1f} 秒。")
        time.sleep(STARTUP_TILT_CONTINUOUS_SECONDS)
        stop_ptz(sock)
        time.sleep(0.2)

        rotate_vertical_to(sock, target_tilt, log=True)
        print(f"等待 {STARTUP_TILT_SETTLE_SECONDS:.1f} 秒让云台执行垂直居中。")
        time.sleep(STARTUP_TILT_SETTLE_SECONDS)
        stop_ptz(sock)
        ptz_state["tilt"] = target_tilt
        print(f"云台已发送上下正中命令: 垂直 {target_tilt:.1f} 度。")
        return True
    else:
        current_tilt = clamp_vertical(current_tilt)
        ptz_state["tilt"] = current_tilt

        if current_tilt < target_tilt - STARTUP_ANGLE_TOLERANCE:
            print(f"当前云台低于中心 {current_tilt:.1f} 度，开始抬头到 {target_tilt:.1f} 度。")
            tilt_up(sock, speed=PTZ_TILT_SPEED, log=True)
            ok, current_tilt = wait_for_vertical_angle(sock, ptz_state, target_tilt)
        elif current_tilt > target_tilt + STARTUP_ANGLE_TOLERANCE:
            print(f"当前云台高于中心 {current_tilt:.1f} 度，开始下调到 {target_tilt:.1f} 度。")
            tilt_down(sock, speed=PTZ_TILT_SPEED, log=True)
            ok, current_tilt = wait_for_vertical_angle(sock, ptz_state, target_tilt)
        else:
            ok = True

    if not ok:
        print("连续抬头未确认到位，再发送一次垂直绝对居中命令。")
        rotate_vertical_to(sock, target_tilt, log=True)
        ok, current_tilt = wait_for_vertical_angle(sock, ptz_state, target_tilt)

    if ok:
        ptz_state["tilt"] = current_tilt
        print(f"云台已先抬头到上下正中位置: 垂直 {current_tilt:.1f} 度。")
        return True
    else:
        print(f"云台上下居中未确认到位，最后读取垂直角度: {current_tilt}。")
        return False


def move_horizontal_to_startup_zero(sock, ptz_state):
    target_pan = normalize_horizontal(INITIAL_PAN_ANGLE)
    current_pan = query_horizontal_angle(sock, log=True)

    if current_pan is None:
        print("未读取到水平角度，使用无反馈模式回到水平 00。")
    else:
        ptz_state["pan"] = normalize_horizontal(current_pan)
        print(f"当前水平角度: {ptz_state['pan']:.1f} 度，回到水平 00。")

    rotate_horizontal_to(sock, target_pan, log=True)
    print(f"等待 {STARTUP_PAN_SETTLE_SECONDS:.1f} 秒让云台执行水平 00 定位。")
    time.sleep(STARTUP_PAN_SETTLE_SECONDS)
    stop_ptz(sock)
    ptz_state["pan"] = target_pan
    print(f"云台已发送水平 00 命令: 水平 {target_pan:.1f} 度。")
    return True


def move_to_initial_pose(sock, ptz_state):
    if not move_vertical_to_startup_center(sock, ptz_state):
        print("启动居中失败，停止云台，不进入右转寻火。")
        stop_ptz(sock)
        return False

    time.sleep(STARTUP_CENTER_HOLD_SECONDS)

    move_horizontal_to_startup_zero(sock, ptz_state)
    time.sleep(STARTUP_CENTER_HOLD_SECONDS)
    print(f"云台已回到水平/上下居中位置: 水平 {ptz_state['pan']:.1f} 度, 垂直 {ptz_state['tilt']:.1f} 度。")
    return True


def reset_search_pattern(sock, search_state, motion_state):
    search_state["mode"] = "searching"
    search_state["pan"] = INITIAL_PAN_ANGLE
    search_state["tilt"] = INITIAL_TILT_ANGLE
    set_continuous_motion(sock, motion_state, 0x02, pan_speed=PTZ_PAN_SPEED)
    print(f"开始右转寻火，水平速度 0x{clamp_speed(PTZ_PAN_SPEED):02X}。")


def keep_searching(sock, motion_state):
    set_continuous_motion(sock, motion_state, 0x02, pan_speed=PTZ_PAN_SPEED)


def read_ptz_pose(sock, ptz_state):
    horizontal = query_horizontal_angle(sock)
    vertical = query_vertical_angle(sock)

    if horizontal is not None:
        ptz_state["pan"] = normalize_horizontal(horizontal)
    if vertical is not None:
        ptz_state["tilt"] = clamp_vertical(vertical)
    if horizontal is not None and vertical is not None:
        ptz_state["pose_valid"] = True

    return ptz_state["pan"], ptz_state["tilt"]


def get_target_center(target):
    if isinstance(target, dict):
        return target.get("center")
    return target


def update_estimated_ptz_pose_from_error(ptz_state, error_x, error_y, frame_size):
    frame_width, frame_height = frame_size
    if frame_width <= 0 or frame_height <= 0:
        return

    pixels_per_degree_x = frame_width / HFOV
    pixels_per_degree_y = frame_height / VFOV
    # The visible stream is horizontally mirrored relative to PTZ pan direction.
    estimated_pan_delta = -error_x / pixels_per_degree_x
    estimated_tilt_delta = error_y / pixels_per_degree_y

    ptz_state["pan"] = normalize_horizontal(CAMERA_CENTER_PAN_ANGLE + estimated_pan_delta)
    ptz_state["tilt"] = clamp_vertical(CAMERA_CENTER_TILT_ANGLE + estimated_tilt_delta)
    ptz_state["pose_valid"] = True
    ptz_state["pose_source"] = "vision_estimate"
    print(
        "Estimated PTZ pose from image error: "
        f"delta_pan={estimated_pan_delta:.2f}, delta_tilt={estimated_tilt_delta:.2f}, "
        f"pan={ptz_state['pan']:.1f}, tilt={ptz_state['tilt']:.1f}"
    )


def boxes_overlap(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    return ax1 <= bx2 and ax2 >= bx1 and ay1 <= by2 and ay2 >= by1


def target_overlaps_center_region(target, frame_size):
    if not isinstance(target, dict):
        return False

    frame_width, frame_height = frame_size
    half_size = CENTER_LOCK_REGION_SIZE / 2
    center_region = (
        frame_width / 2 - half_size,
        frame_height / 2 - half_size,
        frame_width / 2 + half_size,
        frame_height / 2 + half_size,
    )

    targets = target.get("targets") or [target]
    for fire_target in targets:
        bbox = fire_target.get("bbox") if isinstance(fire_target, dict) else None
        if bbox is not None and boxes_overlap(bbox, center_region):
            return True
    return False


def get_center_region_status():
    target, frame_size, target_last_seen = get_target_snapshot()
    return target_overlaps_center_region(target, frame_size), target_last_seen


def center_target(sock, motion_state, ptz_state=None):
    target, frame_size, target_last_seen = get_target_snapshot()
    target_position = get_target_center(target)
    if target_position is None:
        stop_continuous_motion(sock, motion_state)
        return False, None, None

    frame_width, frame_height = frame_size
    frame_center_x = frame_width / 2
    frame_center_y = frame_height / 2
    error_x = target_position[0] - frame_center_x
    error_y = frame_center_y - target_position[1]

    centered_x = abs(error_x) <= CENTER_THRESHOLD_X
    centered_y = abs(error_y) <= CENTER_THRESHOLD_Y
    target_in_center_region = target_overlaps_center_region(target, frame_size)
    if target_in_center_region or (centered_x and centered_y):
        stop_continuous_motion(sock, motion_state)
        return target_in_center_region, (error_x, error_y), target_last_seen

    command2 = 0
    pan_speed = 0
    tilt_speed = 0
    if not centered_x:
        pan_speed = CENTER_PAN_SPEED
        # The visible stream is horizontally mirrored relative to the PTZ speed bits.
        if error_x > 0:
            command2 |= 0x04
        else:
            command2 |= 0x02

    if not centered_y:
        tilt_speed = CENTER_TILT_SPEED
        if error_y > 0:
            command2 |= 0x08
        else:
            command2 |= 0x10

    if ptz_state is not None:
        update_estimated_ptz_pose_from_error(ptz_state, error_x, error_y, frame_size)

    set_continuous_motion(sock, motion_state, command2, pan_speed=pan_speed, tilt_speed=tilt_speed)
    return False, (error_x, error_y), target_last_seen


def infrared_reader():
    while True:
        cap = cv2.VideoCapture(INFRARED_SOURCE)
        if not cap.isOpened():
            time.sleep(1)
            continue

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            with shared.infrared_lock:
                shared.infrared_frame = frame

        cap.release()
        time.sleep(0.5)


def thermal_coordinate_reader():
    last_error_log_time = 0.0

    while not shared.program_exit_requested:
        try:
            with socket.create_connection(
                THERMAL_COORDINATE_SERVER_ADDRESS,
                timeout=THERMAL_COORDINATE_READ_TIMEOUT,
            ) as coordinate_sock:
                coordinate_sock.settimeout(THERMAL_COORDINATE_READ_TIMEOUT)
                print(
                    "Thermal coordinate stream connected: "
                    f"{THERMAL_COORDINATE_SERVER_ADDRESS[0]}:{THERMAL_COORDINATE_SERVER_ADDRESS[1]}"
                )

                buffer = bytearray()
                while not shared.program_exit_requested:
                    try:
                        chunk = coordinate_sock.recv(1024)
                    except socket.timeout:
                        continue
                    if not chunk:
                        raise ConnectionError("coordinate stream closed")

                    buffer.extend(chunk)
                    for frame in extract_thermal_coordinate_frames(buffer):
                        measurement = parse_thermal_coordinate_frame(frame)
                        update_latest_thermal_coordinate(measurement)
        except Exception as e:
            now = time.time()
            if now - last_error_log_time >= 10.0:
                print(f"Read thermal coordinate stream failed: {e}")
                last_error_log_time = now

            time.sleep(THERMAL_COORDINATE_CONNECT_RETRY)


def read_max_temperature_once():
    transaction_id = int(time.time() * 1000) & 0xFFFF
    request = (
        transaction_id.to_bytes(2, "big")
        + b"\x00\x00"
        + b"\x00\x06"
        + bytes([THERMAL_MODBUS_UNIT_ID, THERMAL_MODBUS_FUNCTION])
        + THERMAL_MAX_TEMPERATURE_REGISTER.to_bytes(2, "big")
        + b"\x00\x01"
    )

    with socket.create_connection(THERMAL_SERVER_ADDRESS, timeout=THERMAL_QUERY_TIMEOUT) as temp_sock:
        temp_sock.settimeout(THERMAL_QUERY_TIMEOUT)
        temp_sock.sendall(request)
        response = temp_sock.recv(32)

    if len(response) < 11:
        raise ValueError(f"short thermal response: {response.hex()}")
    if response[7] & 0x80:
        raise ValueError(f"thermal modbus exception: {response.hex()}")
    if response[7] != THERMAL_MODBUS_FUNCTION or response[8] < 2:
        raise ValueError(f"unexpected thermal response: {response.hex()}")

    raw_temperature = int.from_bytes(response[9:11], "big", signed=True)
    return raw_temperature / THERMAL_TEMPERATURE_SCALE


def temperature_reader():
    last_error_log_time = 0.0

    while not shared.program_exit_requested:
        try:
            temperature = read_max_temperature_once()
            with shared.temperature_lock:
                shared.max_temperature = temperature
                shared.max_temperature_last_seen = time.time()
        except Exception as e:
            now = time.time()
            if now - last_error_log_time >= 10.0:
                print(f"Read max temperature failed: {e}")
                last_error_log_time = now

        time.sleep(THERMAL_POLL_INTERVAL)


def run_detection():
    weights = os.path.join(yolo_path, "best.pt")
    run(
        weights=weights,
        source=SEARCH_SOURCE,
        data=os.path.join(yolo_path, "data/coco128.yaml"),
        imgsz=(640, 640),
        conf_thres=0.8,
        iou_thres=0.55,
        max_det=1000,
        device="",
        view_img=True,
        save_txt=False,
        save_csv=False,
        save_conf=False,
        save_crop=False,
        nosave=True,
        classes=None,
        agnostic_nms=False,
        augment=False,
        visualize=False,
        update=False,
        project=os.path.join(yolo_path, "runs/detect"),
        name="exp",
        exist_ok=False,
        line_thickness=3,
        hide_labels=False,
        hide_conf=False,
        half=False,
        dnn=False,
        vid_stride=1,
    )


def parse_fire_cannon_raw_data(raw_data):
    cleaned_data = "".join(c for c in raw_data if c in "0123456789abcdefABCDEF")
    if not cleaned_data:
        raise ValueError("empty fire cannon command")
    return bytes.fromhex(cleaned_data)


def signed_shortest_angle(angle):
    return ((angle + 180.0) % 360.0) - 180.0


def encode_fire_cannon_angle(angle):
    angle = int(round(angle))
    if angle > 0:
        encoded = (angle << 6) + 0x04
    elif angle < 0:
        encoded = ((-angle) << 6) + 0x01
    else:
        encoded = 0x10
    return f"{encoded:04X}"[:2] + " " + f"{encoded:04X}"[2:]


def build_fire_cannon_position(horizontal_angle, vertical_angle):
    camera_horizontal_delta = signed_shortest_angle(horizontal_angle - CAMERA_CENTER_PAN_ANGLE)
    camera_vertical_delta = vertical_angle - CAMERA_CENTER_TILT_ANGLE

    horizontal_angle = FIRE_CANNON_CENTER_HORIZONTAL + camera_horizontal_delta * FIRE_CANNON_HORIZONTAL_SCALE
    vertical_angle = FIRE_CANNON_CENTER_VERTICAL + camera_vertical_delta * FIRE_CANNON_VERTICAL_SCALE

    horizontal_angle += FIRE_CANNON_HORIZONTAL_OFFSET
    vertical_angle += FIRE_CANNON_VERTICAL_OFFSET

    horizontal_angle = max(-180.0, min(180.0, horizontal_angle))
    vertical_angle = max(-90.0, min(90.0, vertical_angle))

    horizontal_hex = encode_fire_cannon_angle(horizontal_angle)
    vertical_hex = encode_fire_cannon_angle(vertical_angle)
    command = f"88 0C FD FE 00 12 {horizontal_hex} {vertical_hex} 00 00 00"
    return command, horizontal_angle, vertical_angle


def get_center_fire_cannon_position(sock, ptz_state):
    horizontal = query_horizontal_angle(sock)
    vertical = query_vertical_angle(sock)
    if horizontal is None or vertical is None:
        if ptz_state.get("pose_valid"):
            print("Unable to read current PTZ center pose; use last valid PTZ pose for fire cannon.")
            horizontal = ptz_state["pan"]
            vertical = ptz_state["tilt"]
        else:
            print("Unable to read current PTZ center pose and no valid cached pose; skip this fire cannon trigger.")
            return None
    else:
        ptz_state["pan"] = normalize_horizontal(horizontal)
        ptz_state["tilt"] = clamp_vertical(vertical)
        ptz_state["pose_valid"] = True
        ptz_state["pose_source"] = "ptz_query"

    command, cannon_horizontal, cannon_vertical = build_fire_cannon_position(horizontal, vertical)
    print(
        "Fire cannon command generated from camera center: "
        f"ptz_pan={horizontal:.1f}, ptz_tilt={vertical:.1f}, "
        f"pose_source={ptz_state.get('pose_source', 'unknown')}, "
        f"camera_center=({CAMERA_CENTER_PAN_ANGLE:.1f},{CAMERA_CENTER_TILT_ANGLE:.1f}), "
        f"center=({FIRE_CANNON_CENTER_HORIZONTAL:.1f},{FIRE_CANNON_CENTER_VERTICAL:.1f}), "
        f"scale=({FIRE_CANNON_HORIZONTAL_SCALE:.2f},{FIRE_CANNON_VERTICAL_SCALE:.2f}), "
        f"cannon_horizontal={cannon_horizontal:.1f}, "
        f"cannon_vertical={cannon_vertical:.1f}, command={command}"
    )
    return command


def send_fire_cannon_position(position=FIRE_CANNON_POSITION):
    try:
        payload = parse_fire_cannon_raw_data(position)
        with socket.create_connection(FIRE_CANNON_SERVER_ADDRESS, timeout=2.0) as cannon_sock:
            cannon_sock.sendall(payload)
        print(
            "Fire cannon command sent: "
            f"{FIRE_CANNON_SERVER_ADDRESS[0]}:{FIRE_CANNON_SERVER_ADDRESS[1]}, "
            f"payload={payload.hex(' ')}"
        )
    except Exception as e:
        print(f"Fire cannon command failed: {e}")


def trigger_fire_cannon_async(position=FIRE_CANNON_POSITION):
    cannon_thread = threading.Thread(
        target=send_fire_cannon_position,
        args=(position,),
        daemon=True,
    )
    cannon_thread.start()
    print("Fire cannon positioning thread started.")


def update_fire_cannon_linkage(has_recent_fire, has_confirmed_fire, cannon_state, now, sock, ptz_state, motion_state):
    if not has_recent_fire:
        if cannon_state["active"] or cannon_state["stationary_since"] is not None:
            print("Fire disappeared; reset fire cannon linkage state.")
        cannon_state["active"] = False
        cannon_state["stationary_since"] = None
        cannon_state["last_trigger"] = 0.0
        cannon_state["last_motion"] = "stop"
        cannon_state["confirmed_seen"] = False
        return

    if has_confirmed_fire:
        cannon_state["confirmed_seen"] = True
    if not cannon_state["confirmed_seen"]:
        return

    current_motion = motion_state.get("current")
    ptz_is_stopped = current_motion == "stop"
    if not ptz_is_stopped:
        if cannon_state["last_motion"] == "stop":
            print("PTZ started moving; wait for it to stop before triggering fire cannon.")
        cannon_state["active"] = False
        cannon_state["stationary_since"] = None
        cannon_state["last_motion"] = current_motion
        return

    if cannon_state["stationary_since"] is None or cannon_state["last_motion"] != "stop":
        cannon_state["stationary_since"] = now
        cannon_state["active"] = False
        cannon_state["last_motion"] = "stop"
        print(
            "PTZ stopped with confirmed fire; fire cannon linkage will trigger after "
            f"{FIRE_CANNON_STATIONARY_TRIGGER_DELAY:.1f}s if it remains stationary."
        )
        return

    stationary_duration = now - cannon_state["stationary_since"]
    trigger_due = stationary_duration >= FIRE_CANNON_STATIONARY_TRIGGER_DELAY and (
        not cannon_state["active"]
        or now - cannon_state["last_trigger"] >= FIRE_CANNON_REPEAT_INTERVAL
    )
    if not trigger_due:
        return

    cannon_position = get_center_fire_cannon_position(sock, ptz_state)
    if cannon_position is None:
        return

    trigger_fire_cannon_async(cannon_position)
    cannon_state["active"] = True
    cannon_state["last_trigger"] = now
    print(
        f"PTZ stayed stationary for {stationary_duration:.1f}s with confirmed fire; "
        "fire cannon linkage triggered."
    )


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    motion_state = {"current": "stop"}
    shared.program_exit_requested = False
    install_detection_log_formatter()

    try:
        sock.connect(PTZ_SERVER_ADDRESS)
        connected = True
        print(f"已连接云台控制服务器: {PTZ_SERVER_ADDRESS[0]}:{PTZ_SERVER_ADDRESS[1]}")

        ptz_state = {
            "pan": CAMERA_CENTER_PAN_ANGLE,
            "tilt": CAMERA_CENTER_TILT_ANGLE,
            "pose_valid": False,
            "pose_source": "initial",
        }
        search_state = {
            "pan": INITIAL_PAN_ANGLE,
            "tilt": INITIAL_TILT_ANGLE,
        }

        hold_current_position(sock, motion_state)
        if not move_to_initial_pose(sock, ptz_state):
            return
        ptz_state["pose_valid"] = True
        ptz_state["pose_source"] = "startup_pose"
        ptz_state["pan"] = CAMERA_CENTER_PAN_ANGLE
        ptz_state["tilt"] = CAMERA_CENTER_TILT_ANGLE

        with shared.target_lock:
            shared.target = None
            shared.target_last_seen = 0.0
            shared.fire_detection_streak = 0
            shared.fire_confirmed_last_seen = 0.0

        reset_search_pattern(sock, search_state, motion_state)

        infrared_thread = threading.Thread(target=infrared_reader, daemon=True)
        infrared_thread.start()

        temperature_thread = threading.Thread(target=temperature_reader, daemon=True)
        temperature_thread.start()

        coordinate_thread = threading.Thread(target=thermal_coordinate_reader, daemon=True)
        coordinate_thread.start()

        detection_thread = threading.Thread(target=run_detection, daemon=True)
        detection_thread.start()

        last_adjust_time = 0.0
        target_tracking_active = False
        target_locked = False
        centered_frame_count = 0
        last_centered_target_seen = 0.0
        cannon_state = {
            "active": False,
            "stationary_since": None,
            "last_trigger": 0.0,
            "last_motion": "stop",
            "confirmed_seen": False,
        }

        while True:
            now = time.time()
            has_recent_fire = has_recent_visible_fire(now)
            has_confirmed_fire = has_confirmed_visible_fire(now)

            if shared.program_exit_requested or not detection_thread.is_alive():
                hold_current_position(sock, motion_state)
                print("检测线程已结束，保持当前云台位置并退出。")
                break

            update_fire_cannon_linkage(
                has_recent_fire,
                has_confirmed_fire,
                cannon_state,
                now,
                sock,
                ptz_state,
                motion_state,
            )

            if target_locked:
                if not has_recent_fire:
                    hold_current_position(sock, motion_state)
                    target_locked = False
                    centered_frame_count = 0
                    last_centered_target_seen = 0.0
                    if shared.program_exit_requested or not detection_thread.is_alive():
                        print("程序正在退出，保持当前云台位置。")
                        break
                    read_ptz_pose(sock, ptz_state)
                    search_state["pan"] = ptz_state["pan"]
                    search_state["tilt"] = ptz_state["tilt"]
                    reset_search_pattern(sock, search_state, motion_state)
                    print("当前无目标，解除锁定并恢复连续右转寻火。")
                time.sleep(0.05)
                continue

            if not target_tracking_active and has_confirmed_fire:
                stop_continuous_motion(sock, motion_state, force=True)
                target_tracking_active = True
                centered_frame_count = 0
                last_centered_target_seen = 0.0
                last_adjust_time = 0.0
                print(f"可见光连续 {VISIBLE_FIRE_CONFIRM_COUNT} 帧检测到 fire，停止寻火并开始连续调整云台居中。")

            if target_tracking_active:
                if not has_recent_fire:
                    hold_current_position(sock, motion_state)
                    target_tracking_active = False
                    centered_frame_count = 0
                    last_centered_target_seen = 0.0
                    if shared.program_exit_requested or not detection_thread.is_alive():
                        print("程序正在退出，保持当前云台位置。")
                        break
                    read_ptz_pose(sock, ptz_state)
                    search_state["pan"] = ptz_state["pan"]
                    search_state["tilt"] = ptz_state["tilt"]
                    reset_search_pattern(sock, search_state, motion_state)
                    print("当前无目标，恢复连续右转寻火。")
                    time.sleep(0.05)
                    continue

                target_in_center_region, target_last_seen = get_center_region_status()
                if target_in_center_region:
                    stop_continuous_motion(sock, motion_state)
                    if target_last_seen != last_centered_target_seen:
                        centered_frame_count += 1
                        last_centered_target_seen = target_last_seen
                    if centered_frame_count == 1:
                        print("Fire target entered center 50x50 region, counting stable frames.")
                    if centered_frame_count >= CENTER_LOCK_FRAME_COUNT:
                        stop_continuous_motion(sock, motion_state, force=True)
                        target_tracking_active = False
                        target_locked = True
                        read_ptz_pose(sock, ptz_state)
                        print(f"Fire target stayed in center 50x50 region for {CENTER_LOCK_FRAME_COUNT} frames; PTZ locked.")
                else:
                    centered_frame_count = 0
                    last_centered_target_seen = 0.0

                if target_locked:
                    time.sleep(0.05)
                    continue

                if now - last_adjust_time >= ADJUST_COOLDOWN:
                    centered, _, target_last_seen = center_target(sock, motion_state, ptz_state)
                    last_adjust_time = time.time()
                    if centered:
                        if target_last_seen != last_centered_target_seen:
                            centered_frame_count += 1
                            last_centered_target_seen = target_last_seen
                        if centered_frame_count == 1:
                            print("火焰已进入检测画面中心区域，云台停止调整。")
                        if centered_frame_count >= CENTER_LOCK_FRAME_COUNT:
                            stop_continuous_motion(sock, motion_state, force=True)
                            target_tracking_active = False
                            target_locked = True
                            read_ptz_pose(sock, ptz_state)
                            print(f"火焰连续 {CENTER_LOCK_FRAME_COUNT} 帧位于中心区域，锁定云台位置，停止微调。")
                    else:
                        centered_frame_count = 0
                        last_centered_target_seen = 0.0

                time.sleep(0.05)
                continue

            keep_searching(sock, motion_state)

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("收到退出信号，保持当前云台位置。")
    finally:
        shared.program_exit_requested = True
        if connected:
            hold_current_position(sock, motion_state)
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass
        sock.close()


if __name__ == "__main__":
    main()
