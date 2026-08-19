# -*- coding: utf-8 -*-

# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : fire_report_qwen.py
# @Project : intelligent-jet

"""
智慧校园消防安全AI监管平台 - 火情报告生成模块
使用通义千问(Qwen)大模型API自动生成结构化火情报告

依赖安装：
    pip install openai

API Key获取：
    访问 https://bailian.console.aliyun.com/?tab=model#/api-key 申请

运行方式：
    python fire_report_qwen.py
"""

import json
import os
from datetime import datetime
from openai import OpenAI


# ==================== 配置区 ====================

# 通义千问API Key —— 请替换为您自己的Key
# 获取地址：https://bailian.console.aliyun.com/?tab=model#/api-key
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-xxxxxxxxxxxxxxxxxxxxxxxx")

# 模型名称：qwen-turbo(最快最便宜) / qwen-plus(均衡) / qwen-max(最强)
MODEL = "qwen-plus"

# 通义千问OpenAI兼容接口地址
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 初始化客户端
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ==================== 核心功能 ====================

def generate_fire_report(fire_data: dict) -> str:
    """
    调用通义千问大模型，根据火情数据生成结构化火情报告。

    参数：
        fire_data: dict，包含以下字段
            - time: 报警时间
            - location: 报警地点
            - coordinates: 火源三维坐标
            - confidence: 识别置信度
            - distance: 火源距离
            - action: 系统处置动作
            - device_id: 触发设备编号

    返回：
        str: 大模型生成的火情报告文本
    """
    system_prompt = (
        "你是智慧校园消防安全AI监管平台的火情分析助手。"
        "你的职责是根据系统自动采集的火情数据，生成专业、准确、结构化的火情报告。"
        "报告将推送至校园保卫处值班人员，用于应急响应和事后复盘。"
        "请使用正式、简洁的公文风格，避免冗余描述。"
    )

    user_prompt = f"""请根据以下火情自动检测数据，生成一份结构化火情报告：

【火情数据】
- 报警时间：{fire_data['time']}
- 报警地点：{fire_data['location']}
- 触发设备：{fire_data['device_id']}
- 火源坐标：{fire_data['coordinates']}
- 火源距离：{fire_data['distance']}
- 识别置信度：{fire_data['confidence']}
- 系统处置动作：{fire_data['action']}

【报告要求】
请按以下结构生成报告：

一、火情概述
（简要描述火情发生的时间、地点、检测方式）

二、检测过程
（描述系统如何发现火情，包括YOLOv5识别、双目视觉定位的过程和关键数据）

三、处置过程
（描述系统自动执行的处置动作和时间节点）

四、风险评估
（根据火源距离、置信度等数据评估火情严重程度）

五、后续建议
（对保卫处值班人员的行动建议）

请确保报告内容专业、数据准确、格式规范。"""

    print("正在调用通义千问大模型生成火情报告...")
    print(f"模型：{MODEL}")
    print(f"地点：{fire_data['location']}")
    print("-" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,      # 低温度保证输出稳定
        max_tokens=2000,
    )

    report = response.choices[0].message.content
    return report


def generate_safety_weekly_report(weekly_data: dict) -> str:
    """
    调用通义千问大模型，根据本周报警统计数据生成校园消防安全周报。

    参数：
        weekly_data: dict，包含以下字段
            - week_range: 本周日期范围
            - total_alarms: 报警总数
            - confirmed_fires: 确认火情数
            - false_alarms: 误报数
            - devices_online: 在线设备数
            - devices_offline: 离线设备数
            - avg_response_time: 平均响应时间

    返回：
        str: 大模型生成的安全周报文本
    """
    system_prompt = (
        "你是智慧校园消防安全AI监管平台的安全分析助手。"
        "你的职责是根据本周消防系统运行数据，生成校园消防安全周报。"
        "周报将发送给校园安全管理部门，用于安全态势研判和决策支持。"
    )

    user_prompt = f"""请根据以下本周消防系统运行数据，生成校园消防安全周报：

【本周数据统计】
- 统计周期：{weekly_data['week_range']}
- 报警总数：{weekly_data['total_alarms']}次
- 确认火情：{weekly_data['confirmed_fires']}次
- 误报次数：{weekly_data['false_alarms']}次
- 在线设备：{weekly_data['devices_online']}台
- 离线设备：{weekly_data['devices_offline']}台
- 平均响应时间：{weekly_data['avg_response_time']}

【周报要求】
请按以下结构生成周报：

一、本周安全态势概述
二、报警数据分析（含误报率分析）
三、设备运行状态分析
四、风险评估与趋势研判
五、下周安全建议

请确保分析客观、数据准确、建议具有可操作性。"""

    print("正在调用通义千问大模型生成安全周报...")
    print("-" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=2000,
    )

    report = response.choices[0].message.content
    return report


def save_report(report: str, filename: str):
    """将报告保存到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存至：{filename}")


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  智慧校园消防安全AI监管平台 - 火情报告生成模块")
    print("  基于通义千问大模型 · Trae AI辅助开发")
    print("=" * 60)
    print()

    # ---------- 示例1：生成火情报告 ----------

    # 模拟火情检测数据（实际使用时由YOLOv5识别模块自动填充）
    fire_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": "滁州学院实验楼A栋302实验室",
        "device_id": "FC-001（东侧走廊消防炮）",
        "coordinates": "X=12.5m, Y=8.3m, Z=2.1m",
        "distance": "15.2米",
        "confidence": "98.7%",
        "action": "系统自动识别火焰，双目视觉定位火源坐标，PID闭环控制消防炮瞄准并喷射灭火，3.2秒完成联动处置",
    }

    try:
        fire_report = generate_fire_report(fire_data)
        print()
        print("=" * 60)
        print("  AI火情报告")
        print("=" * 60)
        print()
        print(fire_report)
        print()
        print("=" * 60)

        save_report(fire_report, "火情报告_{}.txt".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        ))

    except Exception as e:
        print(f"\n[错误] 调用大模型API失败：{e}")
        print("\n可能原因：")
        print("  1. API Key未设置或无效")
        print("  2. 未安装openai库（运行 pip install openai）")
        print("  3. 网络连接问题")
        print("\n替代方案：")
        print("  打开通义千问网页版 https://tongyi.aliyun.com")
        print("  将火情数据粘贴到对话框中，手动获取报告")

    # ---------- 示例2：生成安全周报 ----------

    print()
    print("=" * 60)

    weekly_data = {
        "week_range": "2026年8月4日 - 2026年8月10日",
        "total_alarms": 7,
        "confirmed_fires": 1,
        "false_alarms": 6,
        "devices_online": 12,
        "devices_offline": 1,
        "avg_response_time": "3.5秒",
    }

    try:
        weekly_report = generate_safety_weekly_report(weekly_data)
        print()
        print("=" * 60)
        print("  校园消防安全周报")
        print("=" * 60)
        print()
        print(weekly_report)
        print()
        print("=" * 60)

        save_report(weekly_report, "安全周报_{}.txt".format(
            datetime.now().strftime("%Y%m%d")
        ))

    except Exception as e:
        print(f"\n[错误] 生成周报失败：{e}")

    print()
    print("程序执行完毕。")
