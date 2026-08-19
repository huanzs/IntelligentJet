/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : ws-server.js
 * @Project : intelligent-jet
 */

/**
 * WebSocket 模拟服务器
 * 模拟消防炮和摄像头的旋转角度数据
 * 角度变化有规律，相邻数据跨度过小
 */

// const { WebSocketServer } = require('ws')
import { WebSocketServer } from 'ws'

const PORT = 8080
const SEND_INTERVAL = 200 // 发送间隔 200ms，与前端过渡动画时间一致

// 角度范围限制
const CANNON_YAW_RANGE = { min: 0, max: 360 }      // 消防炮水平角度范围
const CANNON_PITCH_RANGE = { min: 0, max: 90 }    // 消防炮俯仰角度范围
const CAMERA_YAW_RANGE = { min: -180, max: 180 }    // 摄像头水平角度范围
const CAMERA_PITCH_RANGE = { min: 0, max: 45 }    // 摄像头俯仰角度范围

// 当前角度状态
let currentAngles = {
  cannonYaw: 15,
  cannonPitch: -10,
  cameraYaw: -20,
  cameraPitch: 5
}

// 运动参数（正弦波运动）
const motionParams = {
  cannonYaw: { amplitude: 60, frequency: 0.15, phase: 0 },
  cannonPitch: { amplitude: 25, frequency: 0.08, phase: Math.PI / 3 },
  cameraYaw: { amplitude: 100, frequency: 0.1, phase: Math.PI / 2 },
  cameraPitch: { amplitude: 30, frequency: 0.12, phase: Math.PI / 4 }
}

let startTime = Date.now()

/**
 * 使用正弦波生成平滑变化的角度值
 * 正弦波确保相邻数据变化平滑，不会出现跳跃
 */
function generateAngles() {
  const elapsed = (Date.now() - startTime) / 1000 // 秒

  // 为每个角度生成基于正弦波的值
  const cannonYaw = motionParams.cannonYaw.amplitude * Math.sin(
    2 * Math.PI * motionParams.cannonYaw.frequency * elapsed + motionParams.cannonYaw.phase
  )

  const cannonPitch = motionParams.cannonPitch.amplitude * Math.sin(
    2 * Math.PI * motionParams.cannonPitch.frequency * elapsed + motionParams.cannonPitch.phase
  )

  const cameraYaw = motionParams.cameraYaw.amplitude * Math.sin(
    2 * Math.PI * motionParams.cameraYaw.frequency * elapsed + motionParams.cameraYaw.phase
  )

  const cameraPitch = motionParams.cameraPitch.amplitude * Math.sin(
    2 * Math.PI * motionParams.cameraPitch.frequency * elapsed + motionParams.cameraPitch.phase
  )

  // 限制在有效范围内
  currentAngles = {
    cannonYaw: Math.max(CANNON_YAW_RANGE.min, Math.min(CANNON_YAW_RANGE.max, cannonYaw)),
    cannonPitch: Math.max(CANNON_PITCH_RANGE.min, Math.min(CANNON_PITCH_RANGE.max, cannonPitch)),
    cameraYaw: Math.max(CAMERA_YAW_RANGE.min, Math.min(CAMERA_YAW_RANGE.max, cameraYaw)),
    cameraPitch: Math.max(CAMERA_PITCH_RANGE.min, Math.min(CAMERA_PITCH_RANGE.max, cameraPitch))
  }

  return currentAngles
}

/**
 * 创建 WebSocket 服务器
 */
const wss = new WebSocketServer({ port: PORT })

console.log(`WebSocket 服务器已启动，端口: ${PORT}`)
console.log(`数据发送间隔: ${SEND_INTERVAL}ms`)

wss.on('connection', (ws) => {
  console.log('客户端已连接')

  // 发送当前角度数据
  const sendAngleData = () => {
    const angles = generateAngles()
    const message = JSON.stringify({
      cannonYaw: parseFloat(angles.cannonYaw.toFixed(2)),
      cannonPitch: parseFloat(angles.cannonPitch.toFixed(2)),
      cameraYaw: parseFloat(angles.cameraYaw.toFixed(2)),
      cameraPitch: parseFloat(angles.cameraPitch.toFixed(2)),
      timestamp: Date.now()
    })

    if (ws.readyState === ws.OPEN) {
      ws.send(message)
    }
  }

  // 定时发送数据
  const intervalId = setInterval(sendAngleData, SEND_INTERVAL)

  // 立即发送一次
  sendAngleData()

  ws.on('close', () => {
    console.log('客户端已断开')
    clearInterval(intervalId)
  })

  ws.on('error', (err) => {
    console.error('WebSocket 错误:', err.message)
    clearInterval(intervalId)
  })
})

// 优雅关闭
process.on('SIGINT', () => {
  console.log('\n正在关闭服务器...')
  wss.close(() => {
    console.log('服务器已关闭')
    process.exit(0)
  })
})
