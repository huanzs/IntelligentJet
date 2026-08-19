/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : SlmMonitor.vue
 * @Project : intelligent-jet
 */

<template>
  <div class="slm-page">
    <!-- 顶栏 -->
    <div class="header">
      <h1>消防炮角度监控</h1>
      <div class="connection-panel">
        <div :class="['status-dot', statusClass]"></div>
        <span class="status-text">{{ statusText }}</span>
        <input
          type="text"
          class="ws-url-input"
          v-model="wsUrl"
          placeholder="WebSocket 地址"
        />
        <button class="btn btn-connect" :disabled="connected" @click="connectWS">连接</button>
        <button class="btn btn-disconnect" :disabled="!connected" @click="disconnectWS">断开</button>
      </div>
    </div>

    <div class="main-content">
      <!-- 核心数据卡片 -->
      <div class="data-cards">
        <div class="data-card card-h">
          <div class="label">水平角度</div>
          <div class="value">{{ hAngleDisplay }}<span class="unit">°</span></div>
        </div>
        <div class="data-card card-v">
          <div class="label">垂直角度</div>
          <div class="value">{{ vAngleDisplay }}<span class="unit">°</span></div>
        </div>
        <div class="data-card card-p">
          <div class="label">管道压力</div>
          <div class="value">{{ pressureDisplay }}<span class="unit">MPa</span></div>
        </div>
      </div>

      <!-- 方向控制 -->
      <div class="control-section">
        <h3>方向控制</h3>
        <div class="control-panel">
          <div class="control-row">
            <button
              :class="['ctrl-btn', { active: moveState === 'up' }]"
              @click="sendMove('up')"
            >上</button>
          </div>
          <div class="control-row">
            <button
              :class="['ctrl-btn', { active: moveState === 'left' }]"
              @click="sendMove('left')"
            >左</button>
            <button class="ctrl-btn stop-btn" @click="sendMove('stop')">停止</button>
            <button
              :class="['ctrl-btn', { active: moveState === 'right' }]"
              @click="sendMove('right')"
            >右</button>
          </div>
          <div class="control-row">
            <button
              :class="['ctrl-btn', { active: moveState === 'down' }]"
              @click="sendMove('down')"
            >下</button>
            <button class="ctrl-btn stop-btn" @click="sendMove('home')">归位</button>
          </div>
          <div class="move-state-display">
            当前状态: <span class="state-value">{{ moveState }}</span>
          </div>
        </div>
      </div>

      <!-- 详细状态 -->
      <div class="detail-section">
        <h3>设备状态</h3>
        <div class="detail-grid">
          <div class="detail-item"><div class="key">控制类型</div><div class="val">{{ detail.control_type }}</div></div>
          <div class="detail-item"><div class="key">状态类型</div><div class="val">{{ detail.status_type }}</div></div>
          <div class="detail-item"><div class="key">X 正向状态</div><div class="val">{{ detail.x_positive_status }}</div></div>
          <div class="detail-item"><div class="key">X 负向状态</div><div class="val">{{ detail.x_negative_status }}</div></div>
          <div class="detail-item"><div class="key">Y 正向状态</div><div class="val">{{ detail.y_positive_status }}</div></div>
          <div class="detail-item"><div class="key">Y 负向状态</div><div class="val">{{ detail.y_negative_status }}</div></div>
          <div class="detail-item"><div class="key">X 正限位</div><div class="val">{{ detail.x_pos_limit }}</div></div>
          <div class="detail-item"><div class="key">X 负限位</div><div class="val">{{ detail.x_neg_limit }}</div></div>
          <div class="detail-item"><div class="key">Y 正限位</div><div class="val">{{ detail.y_pos_limit }}</div></div>
          <div class="detail-item"><div class="key">Y 负限位</div><div class="val">{{ detail.y_neg_limit }}</div></div>
        </div>
      </div>

      <!-- 日志 -->
      <div class="log-section">
        <h3>消息日志</h3>
        <div class="log-container" ref="logContainer">
          <div
            v-for="(entry, idx) in logs"
            :key="idx"
            :class="['log-entry', entry.type]"
          >
            <span class="time">[{{ entry.time }}]</span> {{ entry.message }}
            <span v-if="entry.count > 1" class="log-count">×{{ entry.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onBeforeUnmount } from 'vue'

let ws = null

const connected = ref(false)
const connecting = ref(false)
const statusText = ref('未连接')
const statusClass = ref('')
const wsUrl = ref('ws://localhost:8765/ws/slm')

const hAngle = ref(0)
const vAngle = ref(0)
const pressure = ref(0)
const moveState = ref('stop')

const detail = reactive({
  control_type: '--',
  status_type: '--',
  x_positive_status: '--',
  x_negative_status: '--',
  y_positive_status: '--',
  y_negative_status: '--',
  x_pos_limit: '--',
  x_neg_limit: '--',
  y_pos_limit: '--',
  y_neg_limit: '--',
})

const logs = ref([])
const logContainer = ref(null)

// 角度日志合并相关
let lastAngleKey = null
let lastAngleCount = 0

// 计算属性
const hAngleDisplay = computed(() => {
  if (hAngle.value == null) return '--'
  return (hAngle.value >= 0 ? '+' : '') + hAngle.value.toFixed(1)
})

const vAngleDisplay = computed(() => {
  if (vAngle.value == null) return '--'
  return (vAngle.value >= 0 ? '+' : '') + vAngle.value.toFixed(1)
})

const pressureDisplay = computed(() => {
  if (pressure.value == null) return '--'
  return pressure.value.toFixed(2)
})

// 工具函数
function pad2(n) {
  return String(n).padStart(2, '0')
}

function nowTime() {
  const d = new Date()
  return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`
}

function addLog(type, message) {
  logs.value.push({ type, message, time: nowTime(), count: 1 })
  if (logs.value.length > 200) {
    logs.value.splice(0, logs.value.length - 200)
  }
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

function updateLastLog(type, message, count) {
  const last = logs.value[logs.value.length - 1]
  if (last) {
    last.message = message
    last.time = nowTime()
    last.count = count
  }
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

function setStatus(state, text) {
  statusClass.value = state
  statusText.value = text
}

function updateDetail(data) {
  detail.control_type = data.control_type ?? '--'
  detail.status_type = data.status_type ?? '--'
  detail.x_positive_status = data.x_positive_status ?? '--'
  detail.x_negative_status = data.x_negative_status ?? '--'
  detail.y_positive_status = data.y_positive_status ?? '--'
  detail.y_negative_status = data.y_negative_status ?? '--'
  detail.x_pos_limit = data.x_pos_limit ?? '--'
  detail.x_neg_limit = data.x_neg_limit ?? '--'
  detail.y_pos_limit = data.y_pos_limit ?? '--'
  detail.y_neg_limit = data.y_neg_limit ?? '--'
}

// WebSocket 发送
function sendMove(direction) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(direction)
  }
}

// WebSocket 连接
function connectWS() {
  const url = wsUrl.value.trim()
  if (!url) return

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close()
  }

  connecting.value = true
  setStatus('connecting', '连接中...')
  addLog('status', '正在连接 ' + url)

  ws = new WebSocket(url)

  ws.onopen = () => {
    connected.value = true
    connecting.value = false
    setStatus('connected', '已连接')
    addLog('status', 'WebSocket 连接成功')
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)

      switch (msg.type) {
        case 'angle_data': {
          hAngle.value = msg.data.horizontal_angle
          vAngle.value = msg.data.vertical_angle
          pressure.value = msg.data.pressure_mpa
          updateDetail(msg.data)
          if (msg.move_state) {
            moveState.value = msg.move_state
          }

          const hStr = (msg.data.horizontal_angle >= 0 ? '+' : '') + msg.data.horizontal_angle.toFixed(1)
          const vStr = (msg.data.vertical_angle >= 0 ? '+' : '') + msg.data.vertical_angle.toFixed(1)
          const pStr = msg.data.pressure_mpa.toFixed(2)
          const moveTag = msg.move_state && msg.move_state !== 'stop' ? `  [${msg.move_state}]` : ''
          const logKey = hStr + '|' + vStr + '|' + pStr + '|' + moveTag

          if (logKey === lastAngleKey) {
            lastAngleCount++
            updateLastLog('data', `水平: ${hStr}°  垂直: ${vStr}°  压力: ${pStr} MPa${moveTag}`, lastAngleCount)
          } else {
            lastAngleKey = logKey
            lastAngleCount = 1
            addLog('data', `水平: ${hStr}°  垂直: ${vStr}°  压力: ${pStr} MPa${moveTag}`)
          }
          break
        }
        case 'move_state':
          moveState.value = msg.move_state
          addLog('status', `移动状态: ${msg.move_state}`)
          lastAngleKey = null
          lastAngleCount = 0
          break
        case 'status':
          addLog('status', msg.message)
          lastAngleKey = null
          lastAngleCount = 0
          break
        case 'warning':
          addLog('warning', msg.message)
          lastAngleKey = null
          lastAngleCount = 0
          break
        case 'error':
          addLog('error', msg.message)
          lastAngleKey = null
          lastAngleCount = 0
          break
      }
    } catch (e) {
      addLog('warning', '收到非 JSON 消息: ' + event.data)
    }
  }

  ws.onclose = () => {
    connected.value = false
    connecting.value = false
    setStatus('', '已断开')
    addLog('error', 'WebSocket 连接已关闭')
  }

  ws.onerror = () => {
    connected.value = false
    connecting.value = false
    setStatus('error', '连接失败')
    addLog('error', 'WebSocket 连接出错')
  }
}

function disconnectWS() {
  if (ws) {
    ws.close()
    ws = null
  }
  connected.value = false
  connecting.value = false
  setStatus('', '未连接')
  addLog('status', '已手动断开连接')
}

onBeforeUnmount(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.slm-page {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #e0e6ed;
  min-height: 100%;
}

/* ── 顶栏 ── */
.header {
  background: linear-gradient(135deg, #1a2a3a 0%, #0f1923 100%);
  padding: 20px 32px;
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.header h1 {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 1px;
}

.connection-panel {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #555;
  transition: background 0.3s;
}

.status-dot.connected {
  background: #00e676;
  box-shadow: 0 0 8px #00e67688;
}
.status-dot.connecting {
  background: #ffc107;
  animation: pulse 1s infinite;
}
.status-dot.error {
  background: #ff5252;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.status-text {
  font-size: 14px;
  color: #8899aa;
  min-width: 100px;
}

.ws-url-input {
  background: #1a2a3a;
  border: 1px solid #2a4a6a;
  border-radius: 6px;
  color: #e0e6ed;
  padding: 8px 14px;
  font-size: 14px;
  width: 260px;
  outline: none;
  transition: border-color 0.3s;
}

.ws-url-input:focus {
  border-color: #4fc3f7;
}

.btn {
  padding: 8px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-connect {
  background: #1565c0;
  color: #fff;
}

.btn-connect:hover {
  background: #1976d2;
}

.btn-disconnect {
  background: #c62828;
  color: #fff;
}

.btn-disconnect:hover {
  background: #d32f2f;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── 数据卡片 ── */
.data-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.data-card {
  background: linear-gradient(180deg, #1a2a3a 0%, #152232 100%);
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: border-color 0.3s;
}

.data-card:hover {
  border-color: #4fc3f7;
}

.data-card .label {
  font-size: 13px;
  color: #6b8299;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 12px;
}

.data-card .value {
  font-size: 48px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  transition: color 0.3s;
}

.data-card .unit {
  font-size: 18px;
  font-weight: 400;
  color: #6b8299;
  margin-left: 4px;
}

.card-h .value {
  color: #4fc3f7;
}
.card-v .value {
  color: #66bb6a;
}
.card-p .value {
  color: #ffa726;
}

/* ── 方向控制 ── */
.control-section,
.detail-section,
.log-section {
  background: #1a2a3a;
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  padding: 20px 24px;
}

.control-section h3,
.detail-section h3,
.log-section h3 {
  font-size: 14px;
  color: #6b8299;
  letter-spacing: 1px;
  margin-bottom: 16px;
  text-transform: uppercase;
}

.control-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.control-row {
  display: flex;
  gap: 8px;
}

.ctrl-btn {
  width: 72px;
  height: 48px;
  border: 1px solid #2a4a6a;
  border-radius: 8px;
  background: #0f1923;
  color: #b0c4d8;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}

.ctrl-btn:hover {
  border-color: #4fc3f7;
  color: #4fc3f7;
}
.ctrl-btn:active {
  background: #1a3a5a;
  transform: scale(0.95);
}

.ctrl-btn.active {
  background: #1565c0;
  border-color: #4fc3f7;
  color: #fff;
  box-shadow: 0 0 10px #1565c088;
}

.ctrl-btn.stop-btn {
  width: auto;
  padding: 0 20px;
}

.move-state-display {
  margin-top: 12px;
  font-size: 14px;
  color: #6b8299;
}

.move-state-display .state-value {
  color: #4fc3f7;
  font-weight: 600;
}

/* ── 设备状态详情 ── */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.detail-item {
  background: #0f1923;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.detail-item .key {
  font-size: 12px;
  color: #556677;
  margin-bottom: 6px;
}

.detail-item .val {
  font-size: 14px;
  font-weight: 500;
  color: #b0c4d8;
}

/* ── 日志 ── */
.log-container {
  background: #0a1018;
  border-radius: 8px;
  padding: 12px 16px;
  height: 180px;
  overflow-y: auto;
  font-family: "Cascadia Code", "Fira Code", monospace;
  font-size: 13px;
  line-height: 1.8;
}

.log-entry {
  opacity: 0.9;
}
.log-entry .time {
  color: #556677;
}
.log-entry.status {
  color: #4fc3f7;
}
.log-entry.data {
  color: #66bb6a;
}
.log-entry.warning {
  color: #ffa726;
}
.log-entry.error {
  color: #ff5252;
}

.log-count {
  color: #ffa726;
  margin-left: 8px;
}

/* ── 响应式 ── */
@media (max-width: 700px) {
  .data-cards {
    grid-template-columns: 1fr;
  }
  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  .connection-panel {
    flex-wrap: wrap;
  }
}
</style>