# WebSocket 前端联调文档

## 服务基本信息

| 项目 | 值 |
|------|------|
| HTTP/WebSocket 端口 | `8765`（环境变量 `WS_PORT` 可覆盖） |
| 首页 | `GET /` → `index.html` |
| 静态资源 | `GET /static/{filename}` |

---

## WebSocket 连接路径

| 设备 | WS 路径 | 默认地址 |
|------|---------|----------|
| SLM 消防炮 | `/ws/slm` | `ws://localhost:8765/ws/slm` |
| PTZ 云台 | `/ws/ptz` | `ws://localhost:8765/ws/ptz` |

---

## 一、SLM 消防炮（`/ws/slm`）

### 1.1 客户端 → 服务端：发送消息

SLM 使用**纯文本**协议，直接发送方向字符串。

| 消息内容 | 说明 |
|----------|------|
| `left` | 向左移动（水平角 -4°） |
| `right` | 向右移动（水平角 +4°） |
| `up` | 向上移动（垂直角 +4°） |
| `down` | 向下移动（垂直角 -4°） |
| `stop` | 停止移动 |
| `home` | 回归原点（0°, 0°） |

> **切换逻辑**：若当前已在某方向移动，再次发送相同方向会自动停止（toggle）。例如当前 `left`，再发 `left` → 变为 `stop`。

**示例**：
```javascript
ws.send("left");   // 开始左移
ws.send("left");   // 再次发送 → 停止
ws.send("home");   // 回归原点
ws.send("stop");   // 停止
```

### 1.2 服务端 → 客户端：推送消息

所有服务端消息均为 JSON 格式，通过 `type` 字段区分。

#### ① `angle_data` — 角度数据广播（轮询间隔 0.1s）

```json
{
  "type": "angle_data",
  "data": {
    "control_type": 2,
    "status_type": 1,
    "horizontal_angle": 12.5,
    "vertical_angle": 45.0,
    "x_positive_status": "有效",
    "x_negative_status": "无效",
    "y_positive_status": "有效",
    "y_negative_status": "无效",
    "pressure_mpa": 0.85,
    "x_pos_limit": "无效",
    "x_neg_limit": "无效",
    "y_pos_limit": "无效",
    "y_neg_limit": "无效"
  },
  "move_state": "left"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.horizontal_angle` | `float` | 水平角度（°），保留1位小数 |
| `data.vertical_angle` | `float` | 垂直角度（°），范围 0.0~90.0，保留1位小数 |
| `data.pressure_mpa` | `float` | 管道压力（MPa），保留2位小数 |
| `data.control_type` | `int` | 控制类型（2=正常） |
| `data.status_type` | `int` | 状态类型 |
| `data.x_positive_status` | `string` | X正向状态：`无效` / `有效` / `错误` / `不使用` |
| `data.x_negative_status` | `string` | X负向状态 |
| `data.y_positive_status` | `string` | Y正向状态 |
| `data.y_negative_status` | `string` | Y负向状态 |
| `data.x_pos_limit` | `string` | X正限位：`无效` / `有效` / `错误` / `不使用` |
| `data.x_neg_limit` | `string` | X负限位 |
| `data.y_pos_limit` | `string` | Y正限位 |
| `data.y_neg_limit` | `string` | Y负限位 |
| `move_state` | `string` | 当前移动状态：`stop` / `left` / `right` / `up` / `down` |

#### ② `move_state` — 移动状态变更通知

```json
{
  "type": "move_state",
  "move_state": "left"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `move_state` | `string` | `stop` / `left` / `right` / `up` / `down` |

#### ③ `status` — 状态通知

```json
{
  "type": "status",
  "message": "GCAN 设备已连接"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `message` | `string` | 状态描述文本 |

常见 `message` 值：
- `"GCAN 设备已连接"`
- `"客户端已连接，当前 N 个连接"`
- `"已回归原点 (0, 0)"`

#### ④ `warning` — 警告通知

```json
{
  "type": "warning",
  "message": "俯仰角到达边界，已停止移动"
}
```

常见 `message` 值：
- `"GCAN 设备未连接，等待重连..."`
- `"未获取到角度数据"`
- `"俯仰角到达边界，已停止移动"`

#### ⑤ `error` — 错误通知

```json
{
  "type": "error",
  "message": "GCAN 连接失败，3.0s 后重试..."
}
```

常见 `message` 值：
- `"GCAN 连接失败，3.0s 后重试..."`
- `"获取角度异常: ..."`
- `"控制执行异常: ..."`
- `"GCAN 设备未连接，无法回归原点"`

### 1.3 连接生命周期事件

| 时机 | 服务端行为 |
|------|-----------|
| 连接建立 | 广播 `status`（客户端已连接）；单播当前 GCAN 连接状态 + 当前 `move_state` |
| 客户端断开且无剩余客户端 | 自动将 `move_state` 重置为 `stop` |

### 1.4 业务约束

| 约束 | 值 |
|------|------|
| 俯仰角范围 | 0.0° ~ 90.0°（到达边界自动停止） |
| 每次偏转步长 | 4°（固定值） |
| 轮询间隔 | 0.1s |
| GCAN 重连间隔 | 3.0s |

---

## 二、PTZ 云台（`/ws/ptz`）

### 2.1 客户端 → 服务端：发送消息

PTZ 使用 **JSON** 协议，消息必须为合法 JSON 字符串。

#### ① 绝对角度旋转

```json
{
  "action": "rotate_absolute",
  "h": 180.0,
  "v": 45.0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | `string` | 是 | 固定值 `"rotate_absolute"` |
| `h` | `float` | 否 | 水平角度，默认 0，范围 0.0~360.0（服务端裁剪） |
| `v` | `float` | 否 | 垂直角度，默认 0，范围 -90.0~90.0（服务端裁剪） |

#### ② 右转搜索

```json
{
  "action": "search"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | `string` | 是 | 固定值 `"search"` |

#### ③ 急停

```json
{
  "action": "emergency_stop"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | `string` | 是 | 固定值 `"emergency_stop"` |

**示例**：
```javascript
ws.send(JSON.stringify({ action: "rotate_absolute", h: 180, v: 45 }));
ws.send(JSON.stringify({ action: "search" }));
ws.send(JSON.stringify({ action: "emergency_stop" }));
```

### 2.2 服务端 → 客户端：推送消息

#### ① `angle_data` — 角度数据广播（轮询间隔 0.2s）

```json
{
  "type": "angle_data",
  "data": {
    "horizontal_angle": 180.0,
    "vertical_angle": 45.0
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.horizontal_angle` | `float` | 水平角度（°），保留2位小数，范围 0.0~360.0 |
| `data.vertical_angle` | `float` | 垂直角度（°），保留2位小数，范围 -90.0~90.0 |

#### ② `status` — 状态通知

```json
{
  "type": "status",
  "message": "云台设备已连接"
}
```

常见 `message` 值：
- `"云台设备已连接"`
- `"客户端已连接，当前 N 个连接"`
- `"旋转到 水平:180.0° 垂直:45.0°"`
- `"云台开始右转搜索"`
- `"云台已急停"`

#### ③ `warning` — 警告通知

```json
{
  "type": "warning",
  "message": "未获取到角度数据"
}
```

#### ④ `error` — 错误通知

```json
{
  "type": "error",
  "message": "云台连接已断开，等待重连..."
}
```

常见 `message` 值：
- `"云台连接失败，3.0s 后重试..."`
- `"云台连接已断开，等待重连..."`
- `"查询角度异常: ..."`
- `"云台未连接"`
- `"旋转失败: ..."`
- `"搜索失败: ..."`
- `"急停失败: ..."`

### 2.3 连接生命周期事件

| 时机 | 服务端行为 |
|------|-----------|
| 连接建立 | 广播 `status`（客户端已连接）；单播当前 PTZ 连接状态 |
| 连接失败 | 若连续 3 次查询失败，自动判定断线并重连 |

### 2.4 业务约束

| 约束 | 值 |
|------|------|
| 水平角度范围 | 0.0° ~ 360.0° |
| 垂直角度范围 | -90.0° ~ 90.0° |
| 轮询间隔 | 0.2s |
| PTZ 重连间隔 | 3.0s |
| 连续失败上限 | 3 次（超过判定断线） |

---

## 三、消息类型速查表

| `type` 值 | 方向 | SLM | PTZ | 含义 |
|-----------|------|:---:|:---:|------|
| `angle_data` | 服务端→客户端 | ✅ | ✅ | 角度实时数据 |
| `move_state` | 服务端→客户端 | ✅ | — | 移动状态变更 |
| `status` | 服务端→客户端 | ✅ | ✅ | 一般状态通知 |
| `warning` | 服务端→客户端 | ✅ | ✅ | 警告通知 |
| `error` | 服务端→客户端 | ✅ | ✅ | 错误通知 |

---

## 四、环境变量配置（`.env`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WS_PORT` | `8765` | HTTP/WebSocket 服务端口 |
| `PTZ_IP` | `10.1.1.81` | 云台控制器 IP |
| `PTZ_PORT` | `10123` | 云台控制器端口 |
