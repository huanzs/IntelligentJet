#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : slm_driver.py
# @Project : intelligent-jet
import socket


class SLMDriver:
    def __init__(self, server_ip, server_port):
        # 生产模式下，这里包含与硬件通信的初始化代码
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            print(f"slm_driver_2 Connected to server {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.client_socket = None

    def disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            print("slm_driver_6 Disconnected from server.\n")
            self.client_socket = None

    def send_data(self, raw_data):
        if not self.client_socket:
            print("Not connected to server. Please connect first.")
            return
        print(f"slm_driver_4 提交过来的原始指令数据，parse_can_raw_data {raw_data}")
        parsed_data = self.parse_can_raw_data(raw_data)
        try:
            self.client_socket.sendall(parsed_data)
            print(f"slm_driver_5 Data sent successfully: {parsed_data.hex()}")
        except Exception as e:
            print(f"Error sending data: {e}")

    @staticmethod
    def parse_can_raw_data(raw_data):
        # 移除字符串中的空格，并使用fromhex转换为字节
        #return bytes.fromhex(''.join(raw_data.split()))
        # 移除所有非十六进制字符（包括空格）
        cleaned_data = ''.join(c for c in raw_data if c in '0123456789abcdefABCDEF')

        # 检查清理后的数据是否为空
        if not cleaned_data:
            raise ValueError
            self.send_data(position)
            print(f"\nslm_driver_1 循环执行send_data {i}")
        self.disconnect()
