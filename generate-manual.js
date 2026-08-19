/**
 * 使用手册与安装文档生成脚本（含配图）
 * Jason Huan - 2026/8/19
 */
const fs = require('fs');
const path = require('path');
const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    ImageRun, Header, Footer, AlignmentType, HeadingLevel,
    BorderStyle, WidthType, ShadingType, PageBreak, PageOrientation
} = require('docx');

const PROJECT_DIR = 'C:\\Temp\\IntelligentJet';
const IMG_DIR = path.join(PROJECT_DIR, 'docs', 'images');
const OUT_PATH = path.join(PROJECT_DIR, 'docs', '智安联控-使用手册与安装文档.docx');

const cjkFont = { ascii: "Arial", eastAsia: "Microsoft YaHei" };

function readImage(filename) {
    // Prefer PNG, fallback to JPG
    const pngPath = path.join(IMG_DIR, filename.replace(/\.(jpg|jpeg)$/i, '.png'));
    if (fs.existsSync(pngPath)) {
        return fs.readFileSync(pngPath);
    }
    const jpgPath = path.join(IMG_DIR, filename);
    if (fs.existsSync(jpgPath)) {
        return fs.readFileSync(jpgPath);
    }
    return null;
}

function heading(text, level = HeadingLevel.HEADING_1) {
    return new Paragraph({
        heading: level,
        children: [new TextRun({ text, font: cjkFont, bold: true })],
        spacing: { before: 300, after: 150 }
    });
}

function para(text, opts = {}) {
    return new Paragraph({
        children: [new TextRun({ text, font: cjkFont, size: 22, ...opts })],
        spacing: { after: 100 }
    });
}

function bullet(text) {
    return new Paragraph({
        children: [new TextRun({ text, font: cjkFont, size: 22 })],
        bullet: { level: 0 },
        spacing: { after: 60 }
    });
}

function codeBlock(code) {
    // Consolas: monospace, supports box-drawing chars
    // SimSun: CJK monospace, each char = 2x ASCII width
    const codeFont = { ascii: "Consolas", eastAsia: "SimSun", hAnsi: "Consolas", cs: "Consolas" };
    return new Paragraph({
        children: code.split('\n').map((line, i) =>
            new TextRun({
                text: line,
                font: codeFont,
                size: 18,
                break: i > 0 ? 1 : undefined
            })
        ),
        shading: { type: ShadingType.SOLID, color: "F2F2F2" },
        spacing: { before: 80, after: 80, line: 276 },
        indent: { left: 240 },
        border: {
            left: { style: BorderStyle.SINGLE, size: 6, color: "CCCCCC", space: 8 }
        }
    });
}

function image(filename, width = 600, height = 338, caption = '') {
    const imgData = readImage(filename);
    if (!imgData) return para(`[图片未找到: ${filename}]`);

    const children = [
        new ImageRun({
            data: imgData,
            transformation: { width, height },
        })
    ];

    const result = [
        new Paragraph({
            children,
            alignment: AlignmentType.CENTER,
            spacing: { before: 200, after: 60 }
        })
    ];

    if (caption) {
        result.push(new Paragraph({
            children: [new TextRun({ text: caption, font: cjkFont, size: 20, italics: true, color: "666666" })],
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 }
        }));
    }

    return result;
}

function makeTable(headers, rows) {
    const headerCells = headers.map(h => new TableCell({
        children: [new Paragraph({
            children: [new TextRun({ text: h, font: cjkFont, bold: true, size: 22 })],
            alignment: AlignmentType.CENTER
        })],
        shading: { type: ShadingType.SOLID, color: "212121" },
        verticalAlign: "center"
    }));

    const headerRow = new TableRow({ children: headerCells, tableHeader: true });

    const dataRows = rows.map(row => new TableRow({
        children: row.map(cell => new TableCell({
            children: [new Paragraph({
                children: [new TextRun({ text: String(cell), font: cjkFont, size: 22 })],
                alignment: AlignmentType.CENTER
            })],
            verticalAlign: "center"
        }))
    }));

    return new Table({
        rows: [headerRow, ...dataRows],
        width: { size: 100, type: WidthType.PERCENTAGE },
        borders: {
            top: { style: BorderStyle.SINGLE, size: 1, color: "353535" },
            bottom: { style: BorderStyle.SINGLE, size: 1, color: "353535" },
            left: { style: BorderStyle.SINGLE, size: 1, color: "353535" },
            right: { style: BorderStyle.SINGLE, size: 1, color: "353535" },
            insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "353535" },
            insideVertical: { style: BorderStyle.SINGLE, size: 1, color: "353535" },
        }
    });
}

// Build document content
const children = [];

// === Cover Page ===
children.push(new Paragraph({ children: [], spacing: { before: 3000 } }));
children.push(new Paragraph({
    children: [new TextRun({ text: "智安联控", font: cjkFont, size: 96, bold: true })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 }
}));
children.push(new Paragraph({
    children: [new TextRun({ text: "基于AI视觉的校园消防联动应用软件", font: cjkFont, size: 32 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 600 }
}));
children.push(new Paragraph({
    children: [new TextRun({ text: "使用手册与安装文档", font: cjkFont, size: 48, bold: true, color: "0052ef" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 800 }
}));
children.push(new Paragraph({
    children: [
        new TextRun({ text: "作者: Jason Huan", font: cjkFont, size: 24, break: 1 }),
        new TextRun({ text: "邮箱: 549473121@qq.com", font: cjkFont, size: 24, break: 1 }),
        new TextRun({ text: "版本: v2.0", font: cjkFont, size: 24, break: 1 }),
        new TextRun({ text: "日期: 2026/8/19", font: cjkFont, size: 24, break: 1 }),
    ],
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 }
}));
children.push(new Paragraph({ children: [new PageBreak()] }));

// === Table of Contents ===
children.push(heading("目 录"));
const tocItems = [
    "第一章 系统概述",
    "  1.1 项目简介",
    "  1.2 技术栈",
    "  1.3 系统架构",
    "第二章 安装指南",
    "  2.1 环境要求",
    "  2.2 后端安装",
    "  2.3 前端安装",
    "  2.4 WebSocket服务安装",
    "  2.5 边缘端安装",
    "第三章 使用手册",
    "  3.1 系统登录",
    "  3.2 仪表盘",
    "  3.3 用户管理",
    "  3.4 角色管理",
    "  3.5 权限管理",
    "  3.6 3D可视化操作",
    "  3.7 云台控制面板",
    "  3.8 消防炮监控",
    "第四章 系统设计",
    "  4.1 数据库设计",
    "  4.2 RBAC权限模型",
    "  4.3 WebSocket通信架构",
    "  4.4 火焰检测与联动流程",
    "第五章 代码工程",
    "  5.1 工程结构",
    "  5.2 代码注释规范",
    "  5.3 核心模块说明",
    "第六章 API文档",
    "  6.1 认证API",
    "  6.2 用户管理API",
    "  6.3 角色管理API",
    "  6.4 权限管理API",
    "  6.5 WebSocket API",
];
tocItems.forEach(item => children.push(para(item, { size: 22 })));
children.push(new Paragraph({ children: [new PageBreak()] }));

// === Chapter 1: System Overview ===
children.push(heading("第一章 系统概述"));
children.push(heading("1.1 项目简介", HeadingLevel.HEADING_2));
children.push(para("智安联控（Intelligent Jet）是一套基于AI视觉的校园消防联动应用软件，系统集成了YOLOv5火焰识别、双目视觉定位、消防炮自动联动控制、RBAC权限管理和3D可视化操作等核心功能。"));
children.push(para("系统采用四层技术架构：平台管理层、控制执行层、边缘计算层和感知层，实现了从火焰检测到消防炮瞄准喷射的全自动联动。"));

children.push(heading("1.2 技术栈", HeadingLevel.HEADING_2));
children.push(...image('tech_stack_overview.png', 580, 326, '图1-1 技术栈总览'));
children.push(makeTable(
    ["层级", "技术", "版本"],
    [
        ["前端", "Vue.js 3 + Element Plus + Three.js + Pinia", "Vue 3.x"],
        ["后端", "Flask + SQLAlchemy + JWT + bcrypt", "Flask 3.x"],
        ["WebSocket", "aiohttp + Pelco-D + GCAN-212", "Python 3.10+"],
        ["边缘端", "OpenCV + YOLOv5 + NVIDIA Jetson", "Jetson Nano/Orin"],
        ["AI模型", "YOLOv5火焰识别 + 通义千问(qwen-plus)", "YOLOv5s"],
        ["数据库", "MySQL", "8.0+"],
        ["开发工具", "Trae AI辅助开发", "最新版"],
    ]
));

children.push(heading("1.3 系统架构", HeadingLevel.HEADING_2));
children.push(...image('system_architecture.png', 580, 326, '图1-2 系统四层架构图'));
children.push(para("系统采用四层架构设计："));
children.push(bullet("平台管理层：Vue.js前端，提供RBAC权限管理、3D可视化操作、实时监控界面"));
children.push(bullet("控制执行层：WebSocket服务端，处理三路WS连接(YOLO/PTZ/SLM)，转发控制指令"));
children.push(bullet("边缘计算层：NVIDIA Jetson运行YOLOv5火焰检测，通过GCAN-212协议控制消防炮"));
children.push(bullet("感知层：PTZ云台摄像头、消防炮设备、GCAN-212通信模块"));
children.push(new Paragraph({ children: [new PageBreak()] }));

// === Chapter 2: Installation Guide ===
children.push(heading("第二章 安装指南"));
children.push(heading("2.1 环境要求", HeadingLevel.HEADING_2));
children.push(makeTable(
    ["组件", "最低版本", "推荐版本", "说明"],
    [
        ["Python", "3.8", "3.10+", "后端+边缘端运行环境"],
        ["Node.js", "16", "18+", "前端构建环境"],
        ["MySQL", "8.0", "8.0", "数据库"],
        ["NVIDIA Jetson", "Nano", "Orin", "边缘AI推理(可选)"],
        ["Git", "2.30", "2.45+", "版本控制"],
    ]
));

children.push(heading("2.2 后端安装", HeadingLevel.HEADING_2));
children.push(para("1. 创建并激活Python虚拟环境："));
children.push(codeBlock("cd backend\npython -m venv venv\n# Windows\nvenv\\Scripts\\activate\n# Linux\nsource venv/bin/activate"));
children.push(para("2. 安装Python依赖："));
children.push(codeBlock("pip install -r requirements.txt"));
children.push(para("3. 初始化数据库："));
children.push(codeBlock("# 创建数据库并执行SQL脚本\nmysql -u root -p < init.sql\nmysql -u root -p rbac_db < rbac_db.sql"));
children.push(para("4. 配置环境变量（可选，创建 .env 文件）："));
children.push(codeBlock("SECRET_KEY=your-secret-key\nJWT_SECRET_KEY=your-jwt-secret\nDATABASE_URL=mysql+pymysql://root:root@localhost:3306/rbac_db"));
children.push(para("5. 启动后端服务："));
children.push(codeBlock("python run.py\n# 服务运行在 http://localhost:5000"));
children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(heading("2.3 前端安装", HeadingLevel.HEADING_2));
children.push(para("1. 安装Node.js依赖："));
children.push(codeBlock("cd frontend\nnpm install"));
children.push(para("2. 启动开发服务器："));
children.push(codeBlock("npm run dev\n# 开发服务器运行在 http://localhost:5173\n# API请求自动代理到 http://localhost:5000"));
children.push(para("3. 构建生产版本："));
children.push(codeBlock("npm run build"));
children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(heading("2.4 WebSocket服务安装", HeadingLevel.HEADING_2));
children.push(para("1. 安装依赖："));
children.push(codeBlock("cd websocket\npip install aiohttp"));
children.push(para("2. 启动WebSocket服务："));
children.push(codeBlock("python server.py\n# WebSocket服务运行在 ws://localhost:8765"));
children.push(para("3. 验证服务："));
children.push(para("浏览器访问 http://localhost:8765 查看服务状态页面。"));

children.push(heading("2.5 边缘端安装", HeadingLevel.HEADING_2));
children.push(para("1. 安装依赖（在NVIDIA Jetson上）："));
children.push(codeBlock("cd edge\npip install opencv-python torch torchvision\n# 安装YOLOv5\ngit clone https://github.com/ultralytics/yolov5.git"));
children.push(para("2. 配置GCAN-212设备："));
children.push(para("确保GCAN-212设备通过网线连接到Jetson，并配置同一网段的IP地址。"));
children.push(para("3. 启动边缘端联动服务："));
children.push(codeBlock("python watch_dog6.py"));
children.push(para("4. 启动大模型火情报告服务（可选）："));
children.push(codeBlock("cd scripts\nexport DASHSCOPE_API_KEY=your-api-key\npython fire_report_qwen.py"));
children.push(new Paragraph({ children: [new PageBreak()] }));

// === Chapter 3: User Manual ===
children.push(heading("第三章 使用手册"));
children.push(heading("3.1 系统登录", HeadingLevel.HEADING_2));
children.push(para("默认管理员账户："));
children.push(makeTable(
    ["字段", "值"],
    [["用户名", "admin"], ["密码", "admin123"], ["角色", "admin（管理员）"]]
));
children.push(para("登录后系统将自动获取JWT双令牌（access_token 15分钟有效，refresh_token 7天有效），并加载用户权限列表。"));

children.push(heading("3.2 仪表盘", HeadingLevel.HEADING_2));
children.push(para("仪表盘页面展示系统概览信息，包括用户总数、角色总数、权限总数等统计数据。管理员可快速查看系统状态。"));

children.push(heading("3.3 用户管理", HeadingLevel.HEADING_2));
children.push(para("用户管理页面提供用户CRUD操作和角色分配功能。需要 user:read 权限查看，user:write 权限操作。"));
children.push(bullet("创建用户：填写用户名、邮箱、密码（至少6位）"));
children.push(bullet("编辑用户：修改邮箱和启用/禁用状态"));
children.push(bullet("分配角色：为用户分配一个或多个角色"));
children.push(bullet("删除用户：软删除，可恢复"));

children.push(heading("3.4 角色管理", HeadingLevel.HEADING_2));
children.push(para("角色管理页面提供角色CRUD操作和权限分配功能。需要 role:read 权限查看，role:write 权限操作。"));
children.push(bullet("创建角色：填写角色名称和描述"));
children.push(bullet("分配权限：为角色分配权限编码（如 user:read, user:write）"));

children.push(heading("3.5 权限管理", HeadingLevel.HEADING_2));
children.push(para("权限管理页面提供权限列表查询和创建/删除操作。权限编码格式为 资源:操作（如 user:read）。"));

children.push(heading("3.6 3D可视化操作", HeadingLevel.HEADING_2));
children.push(para("3D操作页面使用Three.js渲染消防炮3D模型，支持："));
children.push(bullet("实时角度同步：通过WebSocket接收PTZ和SLM角度数据"));
children.push(bullet("方向控制：上下左右方向键控制消防炮"));
children.push(bullet("喷水模拟：基于抛体物理模型的水柱粒子特效"));
children.push(bullet("YOLO视频叠加：实时显示火焰检测画面"));
children.push(bullet("压力调节：滑块控制水柱喷射压力"));

children.push(heading("3.7 云台控制面板", HeadingLevel.HEADING_2));
children.push(para("云台控制面板提供PTZ云台的实时控制功能："));
children.push(bullet("WebSocket连接管理：支持自定义WS地址"));
children.push(bullet("角度显示：实时显示水平和垂直角度"));
children.push(bullet("角度旋转：输入目标角度进行绝对定位"));
children.push(bullet("快捷操作：右转搜索、急停"));

children.push(heading("3.8 消防炮监控", HeadingLevel.HEADING_2));
children.push(para("消防炮监控页面实时显示SLM消防炮的运行状态，包括当前角度、运动状态和告警信息。"));
children.push(new Paragraph({ children: [new PageBreak()] }));

// === Chapter 4: System Design ===
children.push(heading("第四章 系统设计"));
children.push(heading("4.1 数据库设计", HeadingLevel.HEADING_2));
children.push(...image('database_er_diagram.png', 580, 326, '图4-1 数据库ER关系图'));
children.push(para("系统采用经典RBAC五表模型：users、user_roles、roles、role_permissions、permissions。"));
children.push(makeTable(
    ["表名", "说明", "主要字段"],
    [
        ["users", "用户表", "id, username, password_hash, email, is_active"],
        ["user_roles", "用户-角色关联表", "user_id, role_id"],
        ["roles", "角色表", "id, name, description"],
        ["role_permissions", "角色-权限关联表", "role_id, permission_id"],
        ["permissions", "权限表", "id, code, name, description"],
    ]
));

children.push(heading("4.2 RBAC权限模型", HeadingLevel.HEADING_2));
children.push(...image('rbac_permission_model.png', 580, 326, '图4-2 RBAC权限模型层次图'));
children.push(para("系统采用基于角色的访问控制（RBAC）模型，权限校验流程："));
children.push(bullet("用户登录获取JWT access_token"));
children.push(bullet("请求API时携带 Authorization: Bearer <token>"));
children.push(bullet("后端解码Token获取用户ID，查询用户角色和权限"));
children.push(bullet("校验用户是否拥有所需权限编码"));
children.push(bullet("通过则执行业务逻辑，否则返回403"));
children.push(para("预置权限编码："));
children.push(makeTable(
    ["权限编码", "说明"],
    [
        ["user:read", "查看用户列表"],
        ["user:write", "创建/编辑/删除用户"],
        ["role:read", "查看角色列表"],
        ["role:write", "创建/编辑/删除角色"],
        ["permission:read", "查看权限列表"],
        ["permission:write", "创建/删除权限"],
    ]
));

children.push(heading("4.3 WebSocket通信架构", HeadingLevel.HEADING_2));
children.push(...image('websocket_architecture.png', 580, 326, '图4-3 三路WebSocket连接架构图'));
children.push(para("WebSocket服务端基于aiohttp实现，提供三路独立WS通道："));
children.push(makeTable(
    ["通道", "路径", "功能", "数据格式"],
    [
        ["/ws/yolo", "火焰检测通道", "推送YOLOv5检测帧和状态", "JPEG二进制+JSON"],
        ["/ws/ptz", "云台控制通道", "PTZ方向控制和角度查询", "JSON"],
        ["/ws/slm", "消防炮控制通道", "SLM方向控制和状态查询", "JSON"],
    ]
));

children.push(heading("4.4 火焰检测与联动流程", HeadingLevel.HEADING_2));
children.push(...image('fire_detection_flow(1).png', 435, 580, '图4-4 火焰检测与联动流程图'));
children.push(para("全自动联动流程："));
children.push(bullet("1. YOLOv5实时检测火焰目标"));
children.push(bullet("2. 连续3帧确认（防误报算法）"));
children.push(bullet("3. 双目摄像头测距定位"));
children.push(bullet("4. 画面坐标转换为云台角度"));
children.push(bullet("5. PTZ云台和SLM消防炮同步瞄准"));
children.push(bullet("6. 消防炮启动喷射"));
children.push(bullet("7. 通义千问大模型生成火情报告"));
children.push(new Paragraph({ children: [new PageBreak()] }));

// === Chapter 5: Code Engineering ===
children.push(heading("第五章 代码工程"));
children.push(heading("5.1 工程结构", HeadingLevel.HEADING_2));
children.push(codeBlock(
`智安联控-完整代码工程/
├── backend/          # 后端 Flask API + RBAC权限管理
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
├── frontend/         # 前端 Vue.js + Element UI
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
├── websocket/        # WebSocket实时通信服务
│   ├── drivers/      # 设备驱动
│   ├── services/     # 三路WS服务 (yolo/ptz/slm)
│   ├── utils/        # 工具 (PTZ控制/角度转换)
│   ├── static/       # 静态测试页面
│   ├── server.py     # WS服务端
│   └── API.md        # API文档
│
├── edge/             # 边缘端智能联动代码
│   ├── watch_dog6.py     # 主控联动(最新版)
│   ├── fire_yolo.py      # 火焰YOLO检测
│   ├── camera_control.py # 摄像头控制
│   ├── protocol_parser.py # GCAN协议解析
│   └── slm_driver.py     # 消防炮驱动
│
├── scripts/          # 独立脚本
│   └── fire_report_qwen.py  # 通义千问大模型火情报告
│
└── docs/             # 文档
    ├── DESIGN.md     # 系统设计文档
    ├── images/       # 手册配图
    └── diagrams/     # 架构图(25+张)`
));

children.push(heading("5.2 代码注释规范", HeadingLevel.HEADING_2));
children.push(para("所有核心代码文件头部均包含统一格式的注释信息，按文件类型适配："));
children.push(para("Python 文件："));
children.push(codeBlock(
"# -*- coding: utf-8 -*-\n# @Time    : 2026/8/19 10:00\n# @Author  : Jason Huan\n# @Email   : 549473121@qq.com\n# @File    : example.py\n# @Project : intelligent-jet\n\"\"\"\n模块功能描述\n============\"\"\""
));
children.push(para("JavaScript/Vue 文件："));
children.push(codeBlock(
`/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : example.js
 * @Project : intelligent-jet
 */`
));
children.push(para("SQL 文件："));
children.push(codeBlock(
`-- @Time    : 2026/8/19 10:00
-- @Author  : Jason Huan
-- @Email   : 549473121@qq.com
-- @File    : example.sql
-- @Project : intelligent-jet`));

children.push(heading("5.3 核心模块说明", HeadingLevel.HEADING_2));
children.push(makeTable(
    ["模块", "文件", "功能说明"],
    [
        ["Flask应用工厂", "backend/app/__init__.py", "创建Flask实例，初始化数据库和蓝图"],
        ["JWT认证工具", "backend/app/utils/auth.py", "Token生成/解码/权限装饰器"],
        ["用户模型", "backend/app/models/user.py", "用户CRUD、密码哈希、权限查询"],
        ["WebSocket服务", "websocket/server.py", "三路WS服务(yolo/ptz/slm)"],
        ["PTZ云台控制", "websocket/utils/ptz/ptz_control.py", "Pelco-D协议云台控制"],
        ["角度转换", "websocket/utils/slm/angle_conversion.py", "画面坐标→云台角度转换"],
        ["火焰检测", "edge/fire_yolo.py", "YOLOv5实时火焰检测+连续帧判稳"],
        ["智能联动", "edge/watch_dog6.py", "检测→定位→瞄准→喷射全自动"],
        ["GCAN协议", "edge/protocol_parser.py", "解析GCAN-212控制帧"],
        ["火情报告", "scripts/fire_report_qwen.py", "通义千问API五段式报告"],
        ["3D可视化", "frontend/src/views/ThreeDOperation.vue", "Three.js消防炮3D模型"],
        ["水柱特效", "frontend/src/utils/WaterSpray.js", "抛体物理模拟水柱粒子"],
        ["权限指令", "frontend/src/components/PermissionDirective.js", "v-permission按钮级控制"],
        ["Pinia状态", "frontend/src/stores/auth.js", "Token/用户信息/权限管理"],
    ]
));
children.push(new Paragraph({ children: [new PageBreak()] }));

// === Chapter 6: API Documentation ===
children.push(heading("第六章 API文档"));
children.push(heading("6.1 认证API", HeadingLevel.HEADING_2));
children.push(makeTable(
    ["方法", "路径", "说明", "权限"],
    [
        ["POST", "/api/auth/register", "用户注册", "公开"],
        ["POST", "/api/auth/login", "用户登录", "公开"],
        ["POST", "/api/auth/refresh", "刷新Token", "需登录"],
        ["GET", "/api/auth/me", "获取当前用户", "需登录"],
    ]
));

children.push(heading("6.2 用户管理API", HeadingLevel.HEADING_2));
children.push(makeTable(
    ["方法", "路径", "说明", "权限"],
    [
        ["GET", "/api/users", "用户列表(分页)", "user:read"],
        ["GET", "/api/users/:id", "用户详情", "user:read"],
        ["POST", "/api/users", "创建用户", "user:write"],
        ["PUT", "/api/users/:id", "更新用户", "user:write"],
        ["DELETE", "/api/users/:id", "删除用户", "user:write"],
        ["PUT", "/api/users/:id/roles", "分配角色", "user:write"],
    ]
));

children.push(heading("6.3 角色管理API", HeadingLevel.HEADING_2));
children.push(makeTable(
    ["方法", "路径", "说明", "权限"],
    [
        ["GET", "/api/roles", "角色列表", "role:read"],
        ["GET", "/api/roles/:id", "角色详情", "role:read"],
        ["POST", "/api/roles", "创建角色", "role:write"],
        ["PUT", "/api/roles/:id", "更新角色", "role:write"],
        ["DELETE", "/api/roles/:id", "删除角色", "role:write"],
        ["PUT", "/api/roles/:id/permissions", "分配权限", "role:write"],
    ]
));

children.push(heading("6.4 权限管理API", HeadingLevel.HEADING_2));
children.push(makeTable(
    ["方法", "路径", "说明", "权限"],
    [
        ["GET", "/api/permissions", "权限列表", "permission:read"],
        ["POST", "/api/permissions", "创建权限", "permission:write"],
        ["DELETE", "/api/permissions/:id", "删除权限", "permission:write"],
    ]
));

children.push(heading("6.5 WebSocket API", HeadingLevel.HEADING_2));
children.push(para("WebSocket服务地址：ws://localhost:8765"));
children.push(makeTable(
    ["通道", "路径", "消息类型", "说明"],
    [
        ["YOLO", "/ws/yolo", "status / JPEG帧", "火焰检测结果推送"],
        ["PTZ", "/ws/ptz", "angle_data / status", "云台角度和控制"],
        ["SLM", "/ws/slm", "angle_data / move_state", "消防炮角度和状态"],
    ]
));

// === Author Info ===
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading("作者信息"));
children.push(makeTable(
    ["字段", "内容"],
    [
        ["作者", "Jason Huan"],
        ["邮箱", "549473121@qq.com"],
        ["项目名称", "intelligent-jet"],
        ["GitHub仓库", "https://github.com/huanzs/IntelligentJet"],
        ["开发工具", "Trae AI辅助开发工具"],
        ["开发时间", "2026.07 - 2026.08"],
        ["版本", "v2.0"],
    ]
));

// Build document
const doc = new Document({
    styles: {
        default: {
            document: { run: { font: cjkFont, size: 22 } }
        },
        paragraphStyles: [
            {
                id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
                run: { size: 36, bold: true, font: cjkFont, color: "0052ef" },
                paragraph: { spacing: { before: 400, after: 200 } }
            },
            {
                id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
                run: { size: 28, bold: true, font: cjkFont },
                paragraph: { spacing: { before: 300, after: 150 } }
            },
        ]
    },
    sections: [{
        properties: {
            page: {
                size: { width: 11906, height: 16838 }, // A4
                margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
            }
        },
        children
    }]
});

Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync(OUT_PATH, buffer);
    console.log(`Manual generated: ${OUT_PATH}`);
    console.log(`File size: ${(buffer.length / 1024).toFixed(2)} KB`);
}).catch(err => {
    console.error('Error:', err);
    process.exit(1);
});
