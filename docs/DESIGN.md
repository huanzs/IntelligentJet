# RBAC 权限管理系统 - 系统设计文档

## 1. 项目概述

### 1.1 目标
构建一个最小可用的 RBAC（基于角色的访问控制）系统原型，实现用户认证、角色管理和权限控制的核心功能。

### 1.2 技术选型

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 + Vite + Pinia + Vue Router | Vue 3.x |
| UI 框架 | Element Plus (暗色主题) | 最新稳定版 |
| 后端 | Flask + Flask-SQLAlchemy + Flask-Migrate | Flask 3.x |
| 认证 | PyJWT + bcrypt | - |
| 数据库 | MySQL | 8.x |
| 部署 | 前后端双服务独立运行 | - |

### 1.3 权限模型
经典三表模型：**用户 -> 角色 -> 权限**

- 用户可拥有多个角色（多对多）
- 角色可拥有多个权限（多对多）
- 权限编码格式：`资源:操作`（如 `user:read`, `user:write`）

---

## 2. 项目结构

```
d:\workspace\final\
├── DESIGN.md                     # 设计文档（本文件）
├── backend/                      # Flask API 服务
│   ├── app/
│   │   ├── __init__.py          # Flask app 工厂
│   │   ├── config.py            # 配置（数据库、JWT 密钥等）
│   │   ├── extensions.py        # 扩展初始化（SQLAlchemy 等）
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # 用户模型
│   │   │   ├── role.py          # 角色模型
│   │   │   └── permission.py    # 权限模型
│   │   ├── api/
│   │   │   ├── __init__.py      # Blueprint 注册
│   │   │   ├── auth.py          # 登录/注册/刷新
│   │   │   ├── users.py         # 用户 CRUD
│   │   │   ├── roles.py         # 角色 CRUD
│   │   │   └── permissions.py   # 权限 CRUD
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── auth.py          # JWT 工具、权限装饰器
│   │       └── response.py      # 统一响应格式
│   ├── migrations/              # Flask-Migrate 迁移文件
│   ├── requirements.txt
│   ├── .env                     # 环境变量（不提交）
│   └── run.py                   # 入口文件
├── frontend/                     # Vue 3 SPA
│   ├── src/
│   │   ├── api/                 # API 请求封装
│   │   │   ├── index.js         # axios 实例与拦截器
│   │   │   ├── auth.js          # 认证 API
│   │   │   ├── users.js         # 用户 API
│   │   │   ├── roles.js         # 角色 API
│   │   │   └── permissions.js   # 权限 API
│   │   ├── assets/              # 静态资源
│   │   │   └── styles/
│   │   │       └── dark-theme.css # 暗色主题覆盖
│   │   ├── components/          # 公共组件
│   │   │   └── PermissionDirective.js # v-permission 指令
│   │   ├── layouts/
│   │   │   └── MainLayout.vue   # 主布局（侧边栏+顶栏+内容区）
│   │   ├── router/
│   │   │   └── index.js         # 路由配置 + 权限守卫
│   │   ├── stores/
│   │   │   └── auth.js          # 认证状态管理
│   │   ├── views/
│   │   │   ├── Login.vue        # 登录页
│   │   │   ├── Register.vue     # 注册页
│   │   │   ├── Dashboard.vue    # 仪表盘
│   │   │   ├── Users.vue        # 用户管理
│   │   │   ├── Roles.vue        # 角色管理
│   │   │   ├── Permissions.vue  # 权限管理
│   │   │   └── Forbidden.vue    # 403 页面
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
```

---

## 3. 数据库设计

### 3.1 ER 关系图

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    users     │     │  user_roles      │     │      roles       │
├──────────────┤     ├──────────────────┤     ├──────────────────┤
│ id (PK, AI)  │────>│ user_id (FK)     │<────│ id (PK, AI)      │
│ username     │     │ role_id (FK)     │     │ name             │
│ password_hash│     └──────────────────┘     │ description      │
│ email        │                               │ created_at       │
│ is_active    │     ┌──────────────────┐     └──────────────────┘
│ created_at   │     │ role_permissions │           │
│ updated_at   │     ├──────────────────┤     ┌──────────────────┐
└──────────────┘     │ role_id (FK)     │────>│   permissions    │
                     │ permission_id(FK)│     ├──────────────────┤
                     └──────────────────┘     │ id (PK, AI)      │
                                              │ code             │
                                              │ name             │
                                              │ description      │
                                              │ created_at       │
                                              └──────────────────┘
```

### 3.2 表结构详细设计

#### users 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(64) | UNIQUE, NOT NULL | 用户名 |
| password_hash | VARCHAR(256) | NOT NULL | bcrypt 密码哈希 |
| email | VARCHAR(120) | UNIQUE, NOT NULL | 邮箱 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否启用 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |
| updated_at | DATETIME | ON UPDATE NOW | 更新时间 |

#### roles 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| name | VARCHAR(64) | UNIQUE, NOT NULL | 角色名称 |
| description | VARCHAR(256) | | 角色描述 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

#### permissions 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| code | VARCHAR(64) | UNIQUE, NOT NULL | 权限编码，如 `user:read` |
| name | VARCHAR(64) | NOT NULL | 权限名称，如 "查看用户" |
| description | VARCHAR(256) | | 权限描述 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

#### user_roles 关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| user_id | INT | FK -> users.id, NOT NULL | 用户 ID |
| role_id | INT | FK -> roles.id, NOT NULL | 角色 ID |

联合主键: `(user_id, role_id)`

#### role_permissions 关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| role_id | INT | FK -> roles.id, NOT NULL | 角色 ID |
| permission_id | INT | FK -> permissions.id, NOT NULL | 权限 ID |

联合主键: `(role_id, permission_id)`

### 3.3 预置数据

系统初始化时创建：

| 角色 | 权限 |
|------|------|
| admin | user:read, user:write, role:read, role:write, permission:read, permission:write |
| viewer | user:read, role:read, permission:read |

预置管理员账户: `admin / admin123`

---

## 4. 后端 API 设计

### 4.1 统一响应格式

```json
// 成功
{
  "code": 200,
  "message": "success",
  "data": { ... }
}

// 分页
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}

// 错误
{
  "code": 401,
  "message": "认证失败",
  "data": null
}
```

### 4.2 认证 API (`/api/auth`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/auth/register` | 用户注册 | 公开 |
| POST | `/api/auth/login` | 用户登录，返回 access_token + refresh_token | 公开 |
| POST | `/api/auth/refresh` | 刷新 access_token | 需登录 |
| GET | `/api/auth/me` | 获取当前用户信息及权限列表 | 需登录 |

**注册请求体:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**登录响应体:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "roles": ["admin"],
      "permissions": ["user:read", "user:write", ...]
    }
  }
}
```

### 4.3 用户管理 API (`/api/users`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/users` | 用户列表（分页） | `user:read` |
| GET | `/api/users/:id` | 用户详情 | `user:read` |
| POST | `/api/users` | 创建用户 | `user:write` |
| PUT | `/api/users/:id` | 更新用户 | `user:write` |
| DELETE | `/api/users/:id` | 删除用户 | `user:write` |
| PUT | `/api/users/:id/roles` | 分配角色 | `user:write` |

### 4.4 角色管理 API (`/api/roles`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/roles` | 角色列表 | `role:read` |
| GET | `/api/roles/:id` | 角色详情（含权限列表） | `role:read` |
| POST | `/api/roles` | 创建角色 | `role:write` |
| PUT | `/api/roles/:id` | 更新角色 | `role:write` |
| DELETE | `/api/roles/:id` | 删除角色 | `role:write` |
| PUT | `/api/roles/:id/permissions` | 分配权限 | `role:write` |

### 4.5 权限管理 API (`/api/permissions`)

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/permissions` | 权限列表 | `permission:read` |
| POST | `/api/permissions` | 创建权限 | `permission:write` |
| DELETE | `/api/permissions/:id` | 删除权限 | `permission:write` |

### 4.6 后端核心机制

#### JWT 双 Token
- **access_token**: 有效期 15 分钟，用于 API 请求认证
- **refresh_token**: 有效期 7 天，用于刷新 access_token
- 请求头: `Authorization: Bearer <access_token>`

#### 权限装饰器
```python
@require_permission("user:write")
def create_user():
    ...
```
装饰器从 JWT 中提取用户 ID，查询该用户所有角色下的权限，判断是否包含所需权限码。

#### 密码安全
- 使用 bcrypt 哈希存储密码
- 密码最小长度 6 位

---

## 5. 前端设计

### 5.1 页面列表

| 页面 | 路径 | 说明 | 权限要求 |
|------|------|------|---------|
| 登录 | `/login` | 用户登录 | 公开 |
| 注册 | `/register` | 用户注册 | 公开 |
| 仪表盘 | `/dashboard` | 系统概览（用户数、角色数、权限数统计） | 需登录 |
| 用户管理 | `/users` | 用户列表、增删改查、角色分配 | `user:read` / `user:write` |
| 角色管理 | `/roles` | 角色列表、增删改查、权限分配 | `role:read` / `role:write` |
| 权限管理 | `/permissions` | 权限列表、增删 | `permission:read` / `permission:write` |
| 403 | `/403` | 无权限提示 | - |

### 5.2 前端权限控制

#### 路由守卫
```javascript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  // 1. 公开页面直接放行
  // 2. 需登录页面检查 token
  // 3. 需权限页面检查 permission meta
  // 4. 无权限跳转 /403
})
```

#### 按钮级控制 - 自定义指令
```html
<el-button v-permission="'user:write'">创建用户</el-button>
```
无权限时，按钮不渲染。

#### Pinia Auth Store
```javascript
// stores/auth.js
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    user: null,
    permissions: []
  }),
  actions: {
    login(credentials) { ... },
    logout() { ... },
    fetchUser() { ... }
  },
  getters: {
    hasPermission: (state) => (code) => state.permissions.includes(code)
  }
})
```

### 5.3 主布局

```
┌─────────────────────────────────────────────┐
│  顶栏 (#0b0b0b)  Logo    用户名 | 退出      │
├──────────┬──────────────────────────────────┤
│          │                                  │
│  侧边栏   │       内容区                     │
│ (#212121) │    (#0b0b0b)                    │
│          │                                  │
│ 用户管理   │                                  │
│ 角色管理   │                                  │
│ 权限管理   │                                  │
│          │                                  │
└──────────┴──────────────────────────────────┘
```

侧边栏菜单项根据用户权限动态显示：
- 有 `user:read` -> 显示"用户管理"
- 有 `role:read` -> 显示"角色管理"
- 有 `permission:read` -> 显示"权限管理"

---

## 6. 视觉设计规范

> 以下规范为前端 UI 实现的视觉标准，基于 Sanity 暗色设计系统。

### 6.1 核心色值

```
Background:      #0b0b0b (近黑画布)
Surface:         #212121 (卡片/容器/侧边栏)
Border:          #353535 (可见) / #212121 (隐约)
Text Primary:    #ffffff (白色主文字)
Text Secondary:  #b9b9b9 (银色次要文字)
Text Tertiary:   #797979 (灰色辅助文字)
CTA:             #f36458 (珊瑚红主按钮)
Interactive:     #0052ef (电光蓝，所有悬停态)
Success:         #19d600 (绿色)
Error:           #dd0000 (纯红)
```

### 6.2 组件适配规则

| Element Plus 组件 | 暗色适配 |
|------------------|---------|
| El-Button (primary) | 背景 `#f36458`，悬停 `#0052ef`，文字 `#ffffff`，圆角 99999px |
| El-Button (default) | 背景 `#212121`，边框 `#353535`，文字 `#b9b9b9`，悬停 `#0052ef` |
| El-Table | 表头背景 `#212121`，行背景 `#0b0b0b`，边框 `#353535` |
| El-Input | 背景 `#0b0b0b`，边框 `#212121`，圆角 3px，聚焦边框 `#0052ef` |
| El-Dialog | 背景 `#212121`，边框 `#353535`，圆角 6px |
| El-Menu (侧边栏) | 背景 `#212121`，文字 `#b9b9b9`，激活 `#0052ef` |
| El-Tag | 背景 `#353535`，文字 `#b9b9b9`，圆角 99999px |

### 6.3 字体

- 主字体: Inter (替代 waldenburgNormal)
- 代码/标签: IBM Plex Mono
- CJK 回退: Microsoft YaHei

### 6.4 间距

基础单位 8px，内部间距 12-16px，卡片间距 24px，区域间距 32px。

---

## 7. 开发与部署

### 7.1 本地开发

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
flask db init && flask db migrate && flask db upgrade
python run.py               # 默认 5000 端口

# 前端
cd frontend
npm install
npm run dev                 # 默认 5173 端口，代理 /api -> localhost:5000
```

### 7.2 前端 Vite 代理配置

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true
    }
  }
}
```

### 7.3 环境变量

```env
# backend/.env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/rbac_db
```

---

# 附录：完整视觉设计系统参考

> 以下为原始 Sanity 风格视觉设计系统规范，供实现时详细参考。

## A1. Visual Theme & Atmosphere

Sanity's website is a developer-content platform rendered as a nocturnal command center -- dark, precise, and deeply structured. The entire experience sits on a near-black canvas (`#0b0b0b`) that reads less like a "dark mode toggle" and more like the natural state of a tool built for people who live in terminals. Where most CMS marketing pages reach for friendly pastels and soft illustration, Sanity leans into the gravity of its own product: structured content deserves a structured stage.

The signature typographic voice is waldenburgNormal -- a distinctive, slightly geometric sans-serif with tight negative letter-spacing (-0.32px to -4.48px at display sizes) that gives headlines a compressed, engineered quality. At 112px hero scale with -4.48px tracking, the type feels almost machined -- like precision-cut steel letterforms. This is paired with IBM Plex Mono for code and technical labels, creating a dual-register voice: editorial authority meets developer credibility.

What makes Sanity distinctive is the interplay between its monochromatic dark palette and vivid, saturated accent punctuation. The neutral scale runs from pure black through a tightly controlled gray ramp (`#0b0b0b` -> `#212121` -> `#353535` -> `#797979` -> `#b9b9b9` -> `#ededed` -> `#ffffff`) with no warm or cool bias -- just pure, achromatic precision. Against this disciplined backdrop, a neon green accent (display-p3 green) and electric blue (`#0052ef`) land with the impact of signal lights in a dark control room. The orange-red CTA (`#f36458`) provides the only warm touch in an otherwise cool system.

**Key Characteristics:**
- Near-black canvas (`#0b0b0b`) as the default, natural environment -- not a dark "mode" but the primary identity
- waldenburgNormal with extreme negative tracking at display sizes, creating a precision-engineered typographic voice
- Pure achromatic gray scale -- no warm or cool undertones, pure neutral discipline
- Vivid accent punctuation: neon green, electric blue (`#0052ef`), and coral-red (`#f36458`) against the dark field
- Pill-shaped primary buttons (99999px radius) contrasting with subtle rounded rectangles (3-6px) for secondary actions
- IBM Plex Mono as the technical counterweight to the editorial display face
- Full-bleed dark sections with content contained in measured max-width containers
- Hover states that shift to electric blue (`#0052ef`) across all interactive elements -- a consistent "activation" signal

## A2. Color Palette & Roles

### Primary Brand
- **Sanity Black** (`#0b0b0b`): The primary canvas and dominant surface color.
- **Pure Black** (`#000000`): Used for maximum-contrast moments, deep overlays.
- **Sanity Red** (`#f36458`): The primary CTA and brand accent.

### Accent & Interactive
- **Electric Blue** (`#0052ef`): The universal hover/active state color.
- **Light Blue** (`#55beff` / `#afe3ff`): Secondary blue variants.
- **Neon Green** (`color(display-p3 .270588 1 0)`): Success states. Falls back to `#19d600` in sRGB.

### Surface & Background
- **Near Black** (`#0b0b0b`): Default page background.
- **Dark Gray** (`#212121`): Elevated surface color for cards, containers.
- **Medium Dark** (`#353535`): Tertiary surface and border color.
- **Pure White** (`#ffffff`): Inverted sections, text on dark.
- **Light Gray** (`#ededed`): Light surface for inverted sections.

### Neutrals & Text
- **White** (`#ffffff`): Primary text on dark surfaces.
- **Silver** (`#b9b9b9`): Secondary text.
- **Medium Gray** (`#797979`): Tertiary text, metadata.

### Semantic
- **Error Red** (`#dd0000`): Destructive actions, validation errors.
- **Focus Ring Blue** (`#0052ef`): Focus ring color for accessibility.

### Border System
- **Subtle Border** (`#212121`): Standard border for inputs, cards.
- **Medium Border** (`#353535`): More visible borders, dividers.

## A3. Typography Rules

### Font Family
- **Display / Headline**: Inter (替代 waldenburgNormal)
- **Body / UI**: Inter
- **Code / Technical**: IBM Plex Mono
- **Fallback / CJK**: Microsoft YaHei

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| Section Heading | Inter | 48px | 400 | 1.08 | -1.68px |
| Heading Medium | Inter | 32px | 425 | 1.24 | -0.32px |
| Heading Small | Inter | 24px | 425 | 1.24 | -0.24px |
| Subheading | Inter | 20px | 425 | 1.13 | -0.2px |
| Body | Inter | 16px | 400 | 1.50 | normal |
| Body Small | Inter | 15px | 400 | 1.50 | -0.15px |
| Caption | Inter | 13px | 400-500 | 1.30-1.50 | -0.13px |
| Code Body | IBM Plex Mono | 15px | 400 | 1.50 | normal |

## A4. Component Stylings

### Buttons

**Primary CTA (Pill)**
- Background: `#f36458`, Text: `#ffffff`
- Border Radius: 99999px
- Hover: `#0052ef` background

**Ghost / Subtle**
- Background: `#212121`, Text: `#b9b9b9`
- Border: 1px solid `#212121`, Border Radius: 5px
- Hover: `#0052ef` background

### Cards
- Background: `#212121`, Border: 1px solid `#353535`
- Border Radius: 6px, Padding: 24px
- Titles: `#ffffff`, Body: `#b9b9b9`

### Inputs
- Background: `#0b0b0b`, Border: 1px solid `#212121`
- Border Radius: 3px, Padding: 8px 12px
- Focus: 2px solid `#0052ef`

### Navigation
- Top Nav: `#0b0b0b` with backdrop blur
- Sidebar: `#212121`, text `#b9b9b9`, active `#0052ef`
- Border bottom: 1px solid `#212121`

## A5. Layout Principles

### Spacing System
Base unit: **8px**

| Token | Value | Usage |
|-------|-------|-------|
| space-5 | 8px | Base unit -- button padding, input padding |
| space-6 | 12px | Standard component gap |
| space-7 | 16px | Section internal padding |
| space-8 | 24px | Large component padding |
| space-9 | 32px | Section padding |

### Border Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| radius-xs | 3px | Inputs, textareas |
| radius-sm | 5px | Secondary buttons, tags |
| radius-md | 6px | Standard cards |
| radius-lg | 12px | Large containers |
| radius-pill | 99999px | Primary buttons, badges |

## A6. Depth & Elevation

Depth is communicated through surface color shifts, not shadows:
- `#0b0b0b` (ground) -> `#212121` (elevated) -> `#353535` (prominent)
- Border-based containment (1px solid `#212121` or `#353535`)
- Focus rings only: 0 0 0 2px `#0052ef`
