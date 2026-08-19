# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : angle_conversion.py
# @Project : intelligent-jet

class BinaryProcessor:
    def __init__(self):
        pass

    @staticmethod
    def decimal_to_binary(decimal_number):
        if decimal_number == 0:
            return "0"

        binary_digits = []
        while decimal_number > 0:
            remainder = decimal_number % 2
            binary_digits.append(str(remainder))
            decimal_number = decimal_number // 2

        binary_digits.reverse()
        binary_string = ''.join(binary_digits)
        return binary_string

    @staticmethod
    def binary_addition(bin1, bin2):
        max_len = max(len(bin1), len(bin2))
        bin1 = bin1.zfill(max_len)
        bin2 = bin2.zfill(max_len)

        result = []
        carry = 0

        for i in range(max_len - 1, -1, -1):
            bit1 = int(bin1[i])
            bit2 = int(bin2[i])
            total = bit1 + bit2 + carry
            result_bit = total % 2
            carry = total // 2
            result.append(str(result_bit))

        if carry:
            result.append(str(carry))

        result.reverse()
        return ''.join(result)

    @staticmethod
    def apply_and_operation(binary_str, mask):
        binary_int = int(binary_str, 2)
        mask_int = int(mask, 2)
        result_int = binary_int & mask_int
        result_binary_str = bin(result_int)[2:]
        return result_binary_str.zfill(len(mask))

    def process_and_shift(self, num):
        if num > 0:
            shifted = num << 6
            binary_str = self.decimal_to_binary(shifted)
            mask = '000100'
        elif num < 0:
            num = -num
            shifted = num << 6
            binary_str = self.decimal_to_binary(shifted)
            mask = '000001'
        else:
            shifted = 0
            binary_str = self.decimal_to_binary(shifted)
            mask = '010000'

        print(f"Decimal: {num}, Shifted: {shifted}, Binary: {binary_str}, Mask: {mask}")
        result = self.binary_addition(binary_str, mask)
        return result

    def convert_and_process(self, num):
        processed_num = self.process_and_shift(num)
        return processed_num

    @staticmethod
    def binary_to_hex(binary_str):
        length = len(binary_str)
        if length % 4 != 0:
            binary_str = binary_str.zfill(length + (4 - length % 4))

        if len(binary_str) < 16:
            binary_str = binary_str.zfill(16)
        elif len(binary_str) > 16:
            binary_str = binary_str[-16:]

        hex_str = ''
        for i in range(0, len(binary_str), 4):
            bin_group = binary_str[i:i + 4]
            hex_digit = hex(int(bin_group, 2))[2:].upper()
            hex_str += hex_digit

        return hex_str

    @staticmethod
    def format_hex(hex_str):
        return ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))

    def process_and_convert(self, num1, num2):
        processed_num1 = self.process_and_shift(num1)
        processed_num2 = self.process_and_shift(num2)
        hex_num1 = self.binary_to_hex(processed_num1)
        hex_num2 = self.binary_to_hex(processed_num2)
        formatted_hex_num1 = self.format_hex(hex_num1)
        formatted_hex_num2 = self.format_hex(hex_num2)
        return formatted_hex_num1, formatted_hex_num2


# if __name__ == "__main__":
#     processor = BinaryProcessor()
#
#     try:
#         num1 = int(input("Enter the first decimal number (-180-180): "))
#         num2 = int(input("Enter the second decimal number (-180-360): "))
#
#         if not (-180 <= num1 <= 180) or not (-180 <= num2 <= 180):
#             print("Numbers must be between 0 and 360.")
#         else:
#             hex_num1, hex_num2 = processor.process_and_convert(num1, num2)
#             print(f"Processed Hex for {num1}: {hex_num1} ")
#             print(f"Processed Hex for {num2}: {hex_num2} ")
#     except ValueError:
#         print("Invalid input. Please enter valid integers.")


