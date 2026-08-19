/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : PtzControl.vue
 * @Project : intelligent-jet
 */
 *
 * 云台控制面板 - WebSocket实时云台方向和角度控制
 */

<template>
  <div class="ptz-page">
    <!-- 顶栏 -->
    <div class="header">
      <h1>云台控制面板</h1>
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

    <!-- 主体 -->
    <div class="main-content">
      <!-- 角度 + 旋转同行 -->
      <div class="top-row">
        <!-- 角度显示 -->
        <div class="angle-card">
          <div class="angle-item angle-item-h">
            <div class="label">水平角度</div>
            <div class="value">{{ hAngleDisplay }}<span class="unit">°</span></div>
            <div class="limit-bar">
              <div class="fill" :style="hFillStyle"></div>
            </div>
            <div class="limit-labels"><span>0°</span><span>360°</span></div>
          </div>
          <div class="angle-item angle-item-v">
            <div class="label">垂直角度</div>
            <div class="value">{{ vAngleDisplay }}<span class="unit">°</span></div>
            <div class="limit-bar">
              <div class="fill" :style="vFillStyle"></div>
            </div>
            <div class="limit-labels"><span>-90°</span><span>+90°</span></div>
          </div>
        </div>

        <!-- 角度旋转 + 快捷操作 -->
        <div class="card">
          <div class="card-title">角度旋转</div>
          <div class="angle-input-group">
            <div class="input-row">
              <label>水平角度</label>
              <input
                type="number"
                class="angle-input"
                v-model.number="targetH"
                step="1"
                min="0"
                max="360"
              />
              <span class="input-unit">°</span>
            </div>
            <div class="input-row">
              <label>垂直角度</label>
              <input
                type="number"
                class="angle-input"
                v-model.number="targetV"
                step="1"
                min="-90"
                max="90"
              />
              <span class="input-unit">°</span>
            </div>
            <div class="action-buttons">
              <button class="btn-action btn-rotate" @click="rotateAbsolute">旋转到目标</button>
            </div>
          </div>

          <div class="card-title" style="margin-top:18px">快捷操作</div>
          <div class="action-buttons">
            <button class="btn-action btn-search" @click="sendAction('search')">右转搜索</button>
            <button class="btn-action btn-e-stop" @click="emergencyStop">急 停</button>
          </div>
        </div>
      </div>

      <!-- 日志 -->
      <div class="card">
        <div class="card-title">消息日志</div>
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
import { ref, computed, nextTick, onBeforeUnmount } from 'vue'

let ws = null

const connected = ref(false)
const connecting = ref(false)
const statusText = ref('未连接')
const statusClass = ref('')
const wsUrl = ref('ws://localhost:8765/ws/ptz')

const hAngle = ref(0)
const vAngle = ref(0)
const targetH = ref(0)
const targetV = ref(0)

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

const hFillStyle = computed(() => {
  const pct = Math.max(0, Math.min(100, (hAngle.value / 360) * 100))
  return { left: '0%', width: pct + '%' }
})

const vFillStyle = computed(() => {
  const pct = Math.max(0, Math.min(100, ((vAngle.value + 90) / 180) * 100))
  return { left: '0%', width: pct + '%' }
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
  // 限制日志数量
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

// WebSocket 发送
function sendJSON(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj))
  }
}

function emergencyStop() {
  sendJSON({ action: 'emergency_stop' })
}

function rotateAbsolute() {
  const h = parseFloat(targetH.value) || 0
  const v = parseFloat(targetV.value) || 0
  sendJSON({ action: 'rotate_absolute', h, v })
}

function sendAction(action) {
  sendJSON({ action })
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

          const hStr = (msg.data.horizontal_angle >= 0 ? '+' : '') + msg.data.horizontal_angle.toFixed(1)
          const vStr = (msg.data.vertical_angle >= 0 ? '+' : '') + msg.data.vertical_angle.toFixed(1)
          const logKey = hStr + '|' + vStr

          if (logKey === lastAngleKey) {
            lastAngleCount++
            updateLastLog('data', `水平: ${hStr}°  垂直: ${vStr}°`, lastAngleCount)
          } else {
            lastAngleKey = logKey
            lastAngleCount = 1
            addLog('data', `水平: ${hStr}°  垂直: ${vStr}°`)
          }
          break
        }
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

.ptz-page {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #e0e6ed;
  min-height: 100%;
}

/* ── 顶栏 ── */
.header {
  background: linear-gradient(135deg, #1a2a3a 0%, #0f1923 100%);
  padding: 16px 28px;
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #4fc3f7;
}

.connection-panel {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
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
  font-size: 13px;
  color: #8899aa;
  min-width: 80px;
}

.ws-url-input {
  background: #1a2a3a;
  border: 1px solid #2a4a6a;
  border-radius: 6px;
  color: #e0e6ed;
  padding: 7px 12px;
  font-size: 13px;
  width: 240px;
  outline: none;
  transition: border-color 0.3s;
}
.ws-url-input:focus {
  border-color: #4fc3f7;
}

.btn {
  padding: 7px 20px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-connect {
  background: #1565c0;
  color: #fff;
}
.btn-connect:hover:not(:disabled) {
  background: #1976d2;
}
.btn-disconnect {
  background: #c62828;
  color: #fff;
}
.btn-disconnect:hover:not(:disabled) {
  background: #d32f2f;
}

/* ── 主体布局 ── */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── 卡片通用 ── */
.card {
  background: linear-gradient(180deg, #1a2a3a 0%, #152232 100%);
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.3s;
}
.card:hover {
  border-color: #4fc3f7;
}

.card-title {
  font-size: 12px;
  color: #6b8299;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 14px;
}

/* ── 顶行布局 ── */
.top-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* ── 角度卡片 ── */
.angle-card {
  background: linear-gradient(180deg, #1a2a3a 0%, #152232 100%);
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.3s;
}
.angle-card:hover {
  border-color: #4fc3f7;
}

.angle-item {
  text-align: center;
}
.angle-item + .angle-item {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #1e3a5f;
}

.angle-item .label {
  font-size: 12px;
  color: #6b8299;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 6px;
}
.angle-item .value {
  font-size: 38px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  transition: color 0.3s;
}
.angle-item .unit {
  font-size: 14px;
  font-weight: 400;
  color: #6b8299;
  margin-left: 4px;
}

.angle-item-h .value {
  color: #4fc3f7;
}
.angle-item-v .value {
  color: #66bb6a;
}
.angle-item-h .fill {
  background: #4fc3f7;
}
.angle-item-v .fill {
  background: #66bb6a;
}

/* ── 限位指示条 ── */
.limit-bar {
  margin-top: 10px;
  position: relative;
  height: 8px;
  background: #0f1923;
  border-radius: 4px;
  overflow: visible;
}
.limit-bar .fill {
  position: absolute;
  height: 100%;
  border-radius: 4px;
  transition: left 0.3s, width 0.3s;
}

.limit-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #556677;
  margin-top: 4px;
}

/* ── 绝对角度输入 ── */
.angle-input-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-row label {
  font-size: 13px;
  color: #6b8299;
  min-width: 70px;
  text-align: right;
}

.angle-input {
  background: #0f1923;
  border: 1px solid #2a4a6a;
  border-radius: 6px;
  color: #e0e6ed;
  padding: 8px 12px;
  font-size: 14px;
  width: 100px;
  outline: none;
  transition: border-color 0.3s;
}
.angle-input:focus {
  border-color: #4fc3f7;
}

.input-unit {
  font-size: 13px;
  color: #556677;
}

.btn-action {
  padding: 8px 18px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 6px;
}

.btn-rotate {
  background: #1565c0;
  color: #fff;
}
.btn-rotate:hover:not(:disabled) {
  background: #1976d2;
}

.btn-search {
  background: #e65100;
  color: #fff;
}
.btn-search:hover:not(:disabled) {
  background: #ef6c00;
}

.btn-e-stop {
  background: #b71c1c;
  color: #fff;
  padding: 10px 28px;
  font-size: 14px;
  font-weight: 700;
}
.btn-e-stop:hover:not(:disabled) {
  background: #c62828;
}

/* ── 功能按钮区 ── */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

/* ── 日志区 ── */
.log-container {
  background: #0a1018;
  border-radius: 8px;
  padding: 12px 14px;
  height: 160px;
  overflow-y: auto;
  font-family: "Cascadia Code", "Fira Code", monospace;
  font-size: 12px;
  line-height: 1.7;
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
  .top-row {
    grid-template-columns: 1fr;
  }
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
