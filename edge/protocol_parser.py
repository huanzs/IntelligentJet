#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : protocol_parser.py
# @Project : intelligent-jet

class ProtocolParser:
    def __init__(self, delimiter=' '):
        """
        初始化协议解析器
        :param delimiter: 字段之间的分隔符，默认为逗号或者空格
        """
        # 扩展帧，TCP扩展帧,GCAN-212设备协议数据
        self.data_extend = "88 "
        # 控制头，来自威特龙手册
        self.data_head = "0C FD FE 00 "

        self.delimiter = delimiter

    def parse(self, raw_string):
        """
        解析原始字符串
        :param raw_string: 待解析的原始字符串
        :return: 封装后的字典的字符串表示
        """
        # 按分隔符分割原始字符串
        fields = raw_string.split(self.delimiter)

        # 假设我们有一个固定的字段映射，这里为了简单起见，我们使用简单的索引映射
        # 在实际应用中，你可能需要根据字段的实际含义来映射
        parsed_data = {
            'detected': fields[0] if len(fields) > 0 else None,
            'field2': fields[1] if len(fields) > 1 else None,
            'field3': fields[2] if len(fields) > 2 else None,
            # 可以根据需要继续添加字段
        }

        # 将字典转换为字符串
        # 注意：这里使用了简单的str.format()方法，实际应用中可能需要更复杂的格式化
        return str(parsed_data)

    # 示例使用
if __name__ == "__main__":
    parser = ProtocolParser()
    raw_string = "value1,value2,value3"
    parsed_string = parser.parse(raw_string)
    print(parsed_string)  # 输出类似于：{'field1': 'value1', 'field2': 'value2', 'field3': 'value3'}