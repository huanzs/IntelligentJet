# 智安联控-完整代码工程

> 基于AI视觉的校园消防联动应用软件
> 滁州学院第三届教职工人工智能应用创新比赛 - 教工组赛道五

## 工程结构

```
智安联控-完整代码工程/
├── backend/          # 后端 Flask API + RBAC权限管理 (42个文件)
│   ├── app/
│   │   ├── api/      # REST API (auth/users/roles/permissions)
│   │   ├── models/   # 数据模型 (user/role/permission)
│   │   ├── utils/    # 工具 (JWT认证/响应封装)
│   │   ├── config.py
│   │   └── __init__.py
│   ├── migrations/   # 数据库迁移
│   ├── run.py        # 启动脚本
│   ├── init.sql      # 数据库初始化
│   └── rbac_db.sql   # RBAC建表+种子数据
│
├── frontend/         # 前端 Vue.js + Element UI (33个文件)
│   ├── src/
│   │   ├── api/      # API调用层
│   │   ├── assets/   # 样式资源
│   │   ├── components/ # 公共组件
│   │   ├── layouts/  # 布局组件
│   │   ├── router/   # 路由配置
│   │   ├── stores/   # Pinia状态管理
│   │   ├── utils/    # 工具 (WaterSpray水柱特效)
│   │   └── views/    # 页面 (3D操作/监控/控制/仪表盘/登录)
│   ├── mock/         # Mock数据
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── websocket/        # WebSocket实时通信服务 (16个文件)
│   ├── drivers/      # 设备驱动
│   ├── services/     # 三路WS服务 (yolo/ptz/slm)
│   ├── utils/        # 工具 (PTZ控制/角度转换)
│   ├── static/       # 静态测试页面
│   ├── server.py     # WS服务端
│   └── API.md        # API文档
│
├── edge/             # 边缘端智能联动代码 (16个文件)
│   ├── watch_dog6.py     # 主控联动(最新版)
│   ├── watch_dog5.py     # 主控联动(历史版)
│   ├── fire_yolo.py      # 火焰YOLO检测
│   ├── camera_control.py # 摄像头控制
│   ├── protocol_parser.py # GCAN协议解析
│   ├── slm_driver.py     # 消防炮驱动
│   ├── detect.py         # 检测脚本
│   └── ...
│
├── scripts/          # 独立脚本
│   └── fire_report_qwen.py  # 通义千问大模型火情报告
│
└── docs/             # 文档 (35个文件)
    ├── DESIGN.md     # 系统设计文档
    └── diagrams/     # 架构图(25+张)
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python Flask + MySQL + JWT + RBAC |
| 前端 | Vue.js 3 + Element UI + Three.js + Pinia |
| WebSocket | Python websockets + Pelco-D + GCAN-212 |
| 边缘端 | Python + OpenCV + YOLOv5 + NVIDIA Jetson |
| AI模型 | YOLOv5火焰识别 + 通义千问(qwen-plus)API |
| 开发工具 | Trae AI辅助开发 |

## 核心功能模块

### 1. AI火焰识别 (yolo_service.py)
- YOLOv5实时火焰检测
- 连续帧判稳算法(防误报)
- 检测结果WebSocket推送

### 2. 双目视觉定位 (angle_conversion.py)
- 双目摄像头测距
- 画面坐标→云台角度转换
- 3D空间坐标计算

### 3. 消防炮联动控制 (watch_dog6.py)
- 检测→定位→瞄准→喷射全自动
- PID闭环控制
- GCAN-212协议通信

### 4. 大模型火情报告 (fire_report_qwen.py)
- 通义千问API调用
- 五段式结构化报告生成
- 火情数据→自然语言报告

### 5. RBAC权限管理 (backend/)
- JWT双令牌认证
- 角色-权限四级模型
- 前端按钮级权限控制

### 6. 3D可视化操作 (ThreeDOperation.vue)
- Three.js消防炮3D模型
- 实时角度同步
- 水柱粒子物理特效

## 文件统计

| 模块 | 文件数 | 大小 |
|------|--------|------|
| backend | 42 | 66.4KB |
| frontend | 33 | 195.5KB |
| websocket | 16 | 114.1KB |
| edge | 16 | 154.1KB |
| scripts | 1 | 8.3KB |
| docs | 35 | 115.5KB |
| **合计** | **143** | **653.9KB** |


## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- NVIDIA Jetson (边缘端)

### 后端启动
`ash
cd backend
python -m venv venv
source venv/bin/activate    # Linux
venv\Scripts\activate       # Windows
pip install -r requirements.txt
flask db upgrade
python run.py
`

### 前端启动
`ash
cd frontend
npm install
npm run dev
`

### WebSocket服务启动
`ash
cd websocket
python server.py
`

### 边缘端启动
`ash
cd edge
python watch_dog6.py
`

### 大模型报告服务
`ash
cd scripts
export DASHSCOPE_API_KEY=your-api-key
python fire_report_qwen.py
`

## 作者信息

| 字段 | 内容 |
|------|------|
| 作者 | Jason Huan |
| 邮箱 | 549473121@qq.com |
| 开发工具 | Trae AI辅助开发工具 |
| 开发时间 | 2026.07 - 2026.08 |
| 项目名称 | intelligent-jet |

## 代码注释规范

所有核心代码文件头部均包含统一格式的注释信息：

`python
# @Time    : 2026/8/19 10:00
# @Author  : Jason Huan
# @Email   : 549473121@qq.com
# @File    : example.py
# @Project : intelligent-jet
`

## License

本项目为滁州学院第三届教职工人工智能应用创新比赛参赛作品，版权归作者所有。

## 相关文档

- [系统设计文档](docs/DESIGN.md)
- [WebSocket API文档](websocket/API.md)
- [使用手册与安装文档](docs/智安联控-使用手册与安装文档.docx)
- [参赛作品登记表](../参赛作品登记表-智安联控.docx)