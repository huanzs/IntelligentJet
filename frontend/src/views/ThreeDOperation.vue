/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : ThreeDOperation.vue
 * @Project : intelligent-jet
 */

<template>
  <div class="three-d-container">
    <div ref="canvasContainer" class="canvas-area">
      <div class="overlay-cards">
        <div class="monitor-card">
          <span class="card-label">实时视频</span>
          <iframe :src="rtspUrl" frameborder="0" allowfullscreen></iframe>
        </div>
        <button class="toggle-card-btn" @click="toggleRightCard" :title="showRightCard ? '隐藏监控画面' : '显示监控画面'">
          <svg viewBox="0 0 24 24" width="14" height="14" class="toggle-arrow" :class="{ expanded: showRightCard }">
            <path d="M8 5l8 7-8 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <transition name="card-expand">
          <div class="monitor-card" v-if="showRightCard">
            <span class="card-label">YOLO检测</span>
            <div class="yolo-status-bar">
              <span :class="['yolo-status-dot', yoloConnected ? 'online' : 'offline']"></span>
              <span class="yolo-status-text">{{ yoloConnected ? '直播中' : '未连接' }}</span>
              <span class="yolo-status-info">FPS: {{ yoloFps }}</span>
              <span class="yolo-status-info">{{ yoloDetection }}</span>
            </div>
            <img
              v-if="yoloStreamSrc"
              :src="yoloStreamSrc"
              alt="YOLO检测画面"
            />
            <div v-else class="yolo-placeholder">
              点击连接YOLO
            </div>
            <button class="yolo-connect-btn" @click="connectYolo" :title="yoloConnected ? '重新连接' : '连接YOLO'">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 1l22 22M16.72 11.06A10.94 10.94 0 0 1 19 12.55M5 12.55a10.94 10.94 0 0 1 5.68-3.66M8.53 6.86a7 7 0 0 1 6.95 0M12 20a8 8 0 0 1-6.46-3.34M1 1l22 22"/>
                <path v-if="!yoloConnected" d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01"/>
              </svg>
            </button>
          </div>
        </transition>
      </div>
    </div>
    <div class="control-panel">
      <!-- <h2 class="panel-title">消防炮控制台</h2> -->

      <!-- WebSocket 状态 -->
      <div class="status-bar">
        <span :class="['ws-indicator', wsConnected ? 'connected' : 'disconnected']"></span>
        <span class="status-text">{{ wsConnected ? 'SLM+PTZ 已连接' : 'WebSocket 未连接' }}</span>
      </div>

      <!-- 角度显示 -->
      <div class="section-label">角度信息</div>
      <div class="angle-display">
        <div class="angle-item">
          <label>炮水平角度</label>
          <span class="angle-value">{{ cannonYaw.toFixed(1) }}°</span>
        </div>
        <div class="angle-item">
          <label>炮俯仰角度</label>
          <span class="angle-value">{{ cannonPitch.toFixed(1) }}°</span>
        </div>
        <div class="angle-item">
          <label>摄像头水平角度</label>
          <span class="angle-value">{{ cameraYaw.toFixed(1) }}°</span>
        </div>
        <div class="angle-item">
          <label>摄像头俯仰角度</label>
          <span class="angle-value">{{ cameraPitch.toFixed(1) }}°</span>
        </div>
      </div>

      <!-- 同步控制 -->
      <div class="sync-status">
        <span :class="{ active: syncing, connecting: connecting }">
          {{ connecting ? '连接中...' : syncing ? '角度同步中...' : '角度未同步' }}
        </span>
      </div>
      <div class="btn-group">
        <el-button
          :type="syncing ? 'danger' : 'primary'"
          :disabled="connecting"
          @click="toggleSync"
          class="full-btn"
        >
          {{ connecting ? '连接中...' : syncing ? '停止同步' : '同步角度' }}
        </el-button>
      </div>

      <!-- 寻火与联动 -->
      <div class="btn-group">
        <el-button
          :type="autoMode ? 'warning' : 'primary'"
          :disabled="!syncing"
          @click="toggleAutoMode"
          class="full-btn"
        >
          {{ autoMode ? '开启手动' : '开启联动' }}
        </el-button>
        <el-button
          :type="searching ? 'danger' : 'primary'"
          :disabled="!syncing"
          @click="toggleSearch"
          class="full-btn outline-btn"
        >
          {{ searching ? '停止搜索' : '开始寻火' }}
        </el-button>
      </div>

      <!-- 操作面板 -->
      <div class="operation-section">
        <div class="section-label">操作面板</div>
        <div class="dpad-grid">
          <button class="dpad-btn dpad-up" :class="{ active: syncing && slmMoveState === 'up' }" @click="operateCannon('up')" title="上">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
          </button>
          <button class="dpad-btn dpad-left" :class="{ active: syncing && slmMoveState === 'left' }" @click="operateCannon('left')" title="左">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
          </button>
          <button class="dpad-btn dpad-center" @click="operateCannon('home')" title="归位">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12l9-9 9 9"/><path d="M5 10v9a1 1 0 001 1h3v-5h6v5h3a1 1 0 001-1v-9"/></svg>
          </button>
          <button class="dpad-btn dpad-right" :class="{ active: syncing && slmMoveState === 'right' }" @click="operateCannon('right')" title="右">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
          </button>
          <button class="dpad-btn dpad-down" :class="{ active: syncing && slmMoveState === 'down' }" @click="operateCannon('down')" title="下">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
          </button>
        </div>
      </div>

      <!-- 喷水控制 -->
      <div class="spray-section">
        <div class="section-label">喷水控制</div>
        <div class="spray-status">
          <span :class="{ active: isSpraying }">{{ isSpraying ? '喷水中' : '未喷水' }}</span>
        </div>
        <el-button
          :type="isSpraying ? 'success' : 'primary'"
          @click="toggleSpray"
          class="full-btn"
        >
          {{ isSpraying ? '停止喷水' : '开始喷水' }}
        </el-button>
        <div class="pressure-control">
          <label>喷射力度: {{ pressure }}%</label>
          <el-slider
            v-model="pressure"
            :min="0"
            :max="100"
            @input="updatePressure"
            class="pressure-slider"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import WaterSpray from '../utils/WaterSpray.js'

const canvasContainer = ref(null)

// RTSP 视频流地址（从环境变量读取）
const rtspUrl = ref(import.meta.env.VITE_RTSP_URL || '')

// 角度状态（度数）
const cannonYaw = ref(0)
const cannonPitch = ref(0)
const cameraYaw = ref(0)
const cameraPitch = ref(0)

const wsConnected = ref(false)
const syncing = ref(false)
const connecting = ref(false)

// 喷水状态
const isSpraying = ref(false)
const searching = ref(false)
const autoMode = ref(false)
const pressure = ref(70)
const showRightCard = ref(false)

// YOLO 视频流状态（WebSocket）
const yoloWsUrl = import.meta.env.VITE_YOLO_WS_URL || 'ws://localhost:8765/ws/yolo'
const yoloStreamSrc = ref('')
const yoloConnected = ref(false)
const yoloFps = ref('--')
const yoloDetection = ref('检测: 等待中...')
let wsYolo = null
let yoloLastBlobUrl = null
let yoloFrameCount = 0
let yoloClientFpsFrames = 0
let yoloClientFpsStart = performance.now()

// WebSocket 连接（SLM 消防炮 + PTZ 云台）
let wsSlm = null
let wsPtz = null
let slmReady = false
let ptzReady = false
const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8765'

let scene, camera3d, renderer, controls
let cannonGroup, cameraModelGroup, waterSpray
let landingIndicator
let animationId = null
let lastTime = performance.now()

// SLM 移动状态（用于按钮激活态）
const slmMoveState = ref('stop')

// 过渡动画时长（ms）
const TRANSITION_DURATION = 200

// 消防炮角度过渡
let cannonAnimating = false
let cannonTransStart = 0
let cannonFromYaw = 0
let cannonFromPitch = 0
let cannonToYaw = 0
let cannonToPitch = 0

// 摄像头角度过渡
let cameraAnimating = false
let cameraTransStart = 0
let cameraFromYaw = 0
let cameraFromPitch = 0
let cameraToYaw = 0
let cameraToPitch = 0

function createScene() {
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0b0b0b)
  scene.fog = new THREE.Fog(0x0b0b0b, 30, 60)

  // 相机
  const w = canvasContainer.value.clientWidth
  const h = canvasContainer.value.clientHeight
  camera3d = new THREE.PerspectiveCamera(50, w / h, 0.1, 100)
  camera3d.position.set(8, 6, 8)
  camera3d.lookAt(0, 1.5, 0)

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  canvasContainer.value.appendChild(renderer.domElement)

  // 轨道控制
  controls = new OrbitControls(camera3d, renderer.domElement)
  controls.target.set(0, 1.5, 0)
  controls.enableDamping = true
  controls.dampingFactor = 0.05

  // 灯光
  const ambient = new THREE.AmbientLight(0xffffff, 0.5)
  scene.add(ambient)

  const dirLight = new THREE.DirectionalLight(0xffffff, 1.2)
  dirLight.position.set(5, 10, 5)
  dirLight.castShadow = true
  dirLight.shadow.mapSize.set(1024, 1024)
  scene.add(dirLight)

  const pointLight = new THREE.PointLight(0xff6600, 0.4, 20)
  pointLight.position.set(-3, 5, -3)
  scene.add(pointLight)

  // 地面
  const groundGeo = new THREE.PlaneGeometry(40, 40)
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0x212121,
    roughness: 0.8,
    metalness: 0.2
  })
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.receiveShadow = true
  scene.add(ground)

  // 网格辅助线
  const grid = new THREE.GridHelper(40, 40, 0x353535, 0x212121)
  scene.add(grid)

  // 创建落点指示器
  createLandingIndicator()

  // 创建消防炮
  createCannon()

  // 创建摄像头
  createCameraModel()
}

function createLandingIndicator() {
  // 外圈 - 绿色发光环
  const ringGeo = new THREE.RingGeometry(0.4, 0.5, 64)
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x00ff66,
    transparent: true,
    opacity: 0.8,
    side: THREE.DoubleSide,
    depthWrite: false
  })
  landingIndicator = new THREE.Mesh(ringGeo, ringMat)
  landingIndicator.rotation.x = -Math.PI / 2
  landingIndicator.position.y = 0.01
  landingIndicator.visible = true
  scene.add(landingIndicator)

  // 内部填充 - 半透明绿色圆面
  const fillGeo = new THREE.CircleGeometry(0.4, 64)
  const fillMat = new THREE.MeshBasicMaterial({
    color: 0x00ff66,
    transparent: true,
    opacity: 0.15,
    side: THREE.DoubleSide,
    depthWrite: false
  })
  const fill = new THREE.Mesh(fillGeo, fillMat)
  fill.rotation.x = -Math.PI / 2
  fill.position.y = 0.0
  landingIndicator.add(fill)

  // 十字准星线
  const crossMat = new THREE.LineBasicMaterial({
    color: 0x00ff66,
    transparent: true,
    opacity: 0.6
  })
  const crossSize = 0.3
  // 横线
  const hPoints = [new THREE.Vector3(-crossSize, 0, 0), new THREE.Vector3(crossSize, 0, 0)]
  const hGeo = new THREE.BufferGeometry().setFromPoints(hPoints)
  const hLine = new THREE.Line(hGeo, crossMat)
  landingIndicator.add(hLine)
  // 竖线
  const vPoints = [new THREE.Vector3(0, 0, -crossSize), new THREE.Vector3(0, 0, crossSize)]
  const vGeo = new THREE.BufferGeometry().setFromPoints(vPoints)
  const vLine = new THREE.Line(vGeo, crossMat)
  landingIndicator.add(vLine)
}

function createCannon() {
  cannonGroup = new THREE.Group()

  const redMat = new THREE.MeshStandardMaterial({ color: 0xcc2222, roughness: 0.4, metalness: 0.6 })
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.3, metalness: 0.8 })
  const grayMat = new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.3, metalness: 0.7 })
  const yellowMat = new THREE.MeshStandardMaterial({ color: 0xffcc00, roughness: 0.5, metalness: 0.3 })

  // === 固定底座 ===
  // 底板
  const basePlate = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.4, 0.2, 32), darkMat)
  basePlate.position.y = 0.1
  basePlate.castShadow = true
  cannonGroup.add(basePlate)

  // 底座柱体
  const basePillar = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.8, 0.6, 32), grayMat)
  basePillar.position.y = 0.5
  basePillar.castShadow = true
  cannonGroup.add(basePillar)

  // 警示条纹
  const stripe = new THREE.Mesh(new THREE.CylinderGeometry(0.82, 0.82, 0.05, 32), yellowMat)
  stripe.position.y = 0.7
  cannonGroup.add(stripe)

  // === 水平旋转部分（绕 Y 轴旋转）===
  const yawGroup = new THREE.Group()
  yawGroup.position.y = 0.8
  yawGroup.name = 'yawGroup'

  // 旋转平台
  const turntable = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.65, 0.25, 32), redMat)
  turntable.position.y = 0.125
  turntable.castShadow = true
  yawGroup.add(turntable)

  // 旋转平台装饰环
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.03, 8, 32), grayMat)
  ring.rotation.x = Math.PI / 2
  ring.position.y = 0.25
  yawGroup.add(ring)

  // === 俯仰旋转部分（绕 X 轴旋转）===
  const pitchGroup = new THREE.Group()
  pitchGroup.position.y = 0.4
  pitchGroup.name = 'pitchGroup'

  // 支撑臂 左
  const armGeo = new THREE.BoxGeometry(0.12, 0.6, 0.12)
  const armL = new THREE.Mesh(armGeo, redMat)
  armL.position.set(-0.35, 0.3, 0)
  armL.castShadow = true
  pitchGroup.add(armL)

  // 支撑臂 右
  const armR = new THREE.Mesh(armGeo, redMat)
  armR.position.set(0.35, 0.3, 0)
  armR.castShadow = true
  pitchGroup.add(armR)

  // 俯仰轴
  const pivot = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.8, 16), grayMat)
  pivot.rotation.z = Math.PI / 2
  pivot.position.y = 0.6
  pitchGroup.add(pivot)

  // === 炮管组 ===
  const barrelGroup = new THREE.Group()
  barrelGroup.position.y = 0.6
  barrelGroup.name = 'barrelGroup'

  // 炮管主体
  const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.15, 2.5, 16), redMat)
  barrel.rotation.x = Math.PI / 2
  barrel.position.z = 1.25
  barrel.castShadow = true
  barrelGroup.add(barrel)

  // 炮口
  const muzzle = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.12, 0.2, 16), darkMat)
  muzzle.rotation.x = Math.PI / 2
  muzzle.position.z = 2.55
  muzzle.castShadow = true
  barrelGroup.add(muzzle)

  // 炮口装饰环
  const muzzleRing = new THREE.Mesh(new THREE.TorusGeometry(0.19, 0.02, 8, 16), grayMat)
  muzzleRing.position.z = 2.65
  barrelGroup.add(muzzleRing)

  // 水管接口
  const pipeJoint = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 0.3, 12), grayMat)
  pipeJoint.rotation.x = Math.PI / 2
  pipeJoint.position.set(0, -0.15, 0.3)
  barrelGroup.add(pipeJoint)

  // 水管弯头
  const pipeElbow = new THREE.Mesh(new THREE.SphereGeometry(0.1, 12, 12), grayMat)
  pipeElbow.position.set(0, -0.15, 0.15)
  barrelGroup.add(pipeElbow)

  // 控制手柄
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.3, 8), yellowMat)
  handle.position.set(0.25, 0.1, 0.5)
  handle.rotation.z = Math.PI / 4
  barrelGroup.add(handle)

  pitchGroup.add(barrelGroup)
  yawGroup.add(pitchGroup)
  cannonGroup.add(yawGroup)

  // 指示灯
  const indicatorGeo = new THREE.SphereGeometry(0.05, 8, 8)
  const indicatorMat = new THREE.MeshStandardMaterial({
    color: 0x00ff00,
    emissive: 0x00ff00,
    emissiveIntensity: 0.8
  })
  const indicator = new THREE.Mesh(indicatorGeo, indicatorMat)
  indicator.position.set(0, 0.26, 0.65)
  yawGroup.add(indicator)

  scene.add(cannonGroup)
}

function createCameraModel() {
  cameraModelGroup = new THREE.Group()

  const whiteMat = new THREE.MeshStandardMaterial({ color: 0xeeeeee, roughness: 0.3, metalness: 0.5 })
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.2, metalness: 0.8 })
  const lensMat = new THREE.MeshStandardMaterial({ color: 0x111133, roughness: 0.1, metalness: 0.9 })
  const grayMat = new THREE.MeshStandardMaterial({ color: 0x666666, roughness: 0.3, metalness: 0.7 })
  const blueMat = new THREE.MeshStandardMaterial({ color: 0x0088ff, emissive: 0x0044aa, emissiveIntensity: 0.5, roughness: 0.2, metalness: 0.8 })

  // 位置偏移到正前方（+Z 方向，与消防炮朝向一致）
  cameraModelGroup.position.set(0, 0, 3.5)

  // === 固定底座 ===
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.6, 0.15, 24), grayMat)
  base.position.y = 0.075
  base.castShadow = true
  cameraModelGroup.add(base)

  // 底座柱
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.15, 1.5, 16), grayMat)
  pole.position.y = 0.9
  pole.castShadow = true
  cameraModelGroup.add(pole)

  // === 水平旋转部分 ===
  const yawGroup = new THREE.Group()
  yawGroup.position.y = 1.65
  yawGroup.name = 'cameraYawGroup'

  // 旋转连接件
  const joint = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.15, 16), darkMat)
  joint.position.y = 0.075
  yawGroup.add(joint)

  // === 俯仰旋转部分 ===
  const pitchGroup = new THREE.Group()
  pitchGroup.position.y = 0.2
  pitchGroup.name = 'cameraPitchGroup'

  // 摄像头主体
  const camBody = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.35, 0.6), whiteMat)
  camBody.position.set(0, 0, -0.15)
  camBody.castShadow = true
  pitchGroup.add(camBody)

  // 镜头
  const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 0.2, 16), lensMat)
  lens.rotation.x = Math.PI / 2
  lens.position.set(0, 0, -0.5)
  lens.castShadow = true
  pitchGroup.add(lens)

  // 镜头外圈
  const lensRing = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.02, 8, 16), darkMat)
  lensRing.position.set(0, 0, -0.6)
  pitchGroup.add(lensRing)

  // LED 指示灯
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 8), blueMat)
  led.position.set(0.2, 0.12, -0.1)
  pitchGroup.add(led)

  // 遮阳罩
  const hoodGeo = new THREE.BoxGeometry(0.55, 0.08, 0.3)
  const hood = new THREE.Mesh(hoodGeo, darkMat)
  hood.position.set(0, 0.22, -0.2)
  hood.castShadow = true
  pitchGroup.add(hood)

  yawGroup.add(pitchGroup)

  // 添加雷达 FOV 视野指示器
  const radarFOV = createCameraRadarFOV()
  yawGroup.add(radarFOV)

  cameraModelGroup.add(yawGroup)

  scene.add(cameraModelGroup)
}

function createCameraRadarFOV() {
  const radarGroup = new THREE.Group()
  radarGroup.name = 'cameraRadarFOV'

  const R = 3 // 扇形半径
  const fovAngle = Math.PI / 2.5 // 约72度视野角
  const halfFov = fovAngle / 2

  const mainColor = 0x0088ff
  const brightColor = 0x00ccff

  // --- FOV 扇形区域 ---
  const sectorShape = new THREE.Shape()
  sectorShape.moveTo(0, 0)
  const segs = 48
  for (let i = 0; i <= segs; i++) {
    const angle = -halfFov + fovAngle * (i / segs)
    sectorShape.lineTo(Math.sin(angle) * R, Math.cos(angle) * R)
  }
  sectorShape.lineTo(0, 0)
  const sectorGeo = new THREE.ShapeGeometry(sectorShape)
  const sectorMat = new THREE.MeshBasicMaterial({
    color: mainColor, transparent: true, opacity: 0.1,
    side: THREE.DoubleSide, depthWrite: false
  })
  const sector = new THREE.Mesh(sectorGeo, sectorMat)
  sector.rotation.x = -Math.PI / 2
  radarGroup.add(sector)

  // --- FOV 弧线 ---
  const arcGeo = new THREE.RingGeometry(R - 0.04, R + 0.02, 48, 1, Math.PI / 2 - halfFov, fovAngle)
  const arcMat = new THREE.MeshBasicMaterial({
    color: brightColor, transparent: true, opacity: 0.6,
    side: THREE.DoubleSide, depthWrite: false
  })
  const arc = new THREE.Mesh(arcGeo, arcMat)
  arc.rotation.x = -Math.PI / 2
  radarGroup.add(arc)

  // --- FOV 边界线 ---
  const fovLineMat = new THREE.LineBasicMaterial({
    color: brightColor, transparent: true, opacity: 0.5
  })
  const leftEnd = new THREE.Vector3(Math.sin(-halfFov) * R, 0, -Math.cos(-halfFov) * R)
  const rightEnd = new THREE.Vector3(Math.sin(halfFov) * R, 0, -Math.cos(halfFov) * R)
  radarGroup.add(new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), leftEnd]), fovLineMat
  ))
  radarGroup.add(new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), rightEnd]), fovLineMat
  ))

  // --- 中心方向线 ---
  const dirMat = new THREE.LineBasicMaterial({
    color: brightColor, transparent: true, opacity: 0.7
  })
  radarGroup.add(new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, -R)]),
    dirMat
  ))

  // 定位到地面（yawGroup.y=1.65，偏移-1.63 使扇形位于 y=0.02）
  radarGroup.position.y = -1.63

  return radarGroup
}

function applyAngles(cYawDeg, cPitchDeg, camYawDeg, camPitchDeg) {
  const cYaw = THREE.MathUtils.degToRad(cYawDeg)
  const cPitch = THREE.MathUtils.degToRad(cPitchDeg)
  const camYaw = THREE.MathUtils.degToRad(camYawDeg)
  const camPitch = THREE.MathUtils.degToRad(camPitchDeg)

  // 消防炮 — yaw 取反修正左右方向
  const yawGroup = cannonGroup.getObjectByName('yawGroup')
  const barrelGroup = cannonGroup.getObjectByName('barrelGroup')
  if (yawGroup) yawGroup.rotation.y = -cYaw
  if (barrelGroup) barrelGroup.rotation.x = -cPitch

  // 摄像头 — 基础旋转 π 使面向 +Z（与消防炮同向），pitch 取反保持一致
  const camYawGrp = cameraModelGroup.getObjectByName('cameraYawGroup')
  const camPitchGrp = cameraModelGroup.getObjectByName('cameraPitchGroup')
  if (camYawGrp) camYawGrp.rotation.y = Math.PI - camYaw
  if (camPitchGrp) camPitchGrp.rotation.x = -camPitch
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

function startCannonTransition(toYawDeg, toPitchDeg) {
  cannonFromYaw = THREE.MathUtils.degToRad(cannonYaw.value)
  cannonFromPitch = THREE.MathUtils.degToRad(cannonPitch.value)
  cannonToYaw = THREE.MathUtils.degToRad(toYawDeg)
  cannonToPitch = THREE.MathUtils.degToRad(toPitchDeg)
  cannonTransStart = performance.now()
  cannonAnimating = true
}

function startCameraTransition(toYawDeg, toPitchDeg) {
  cameraFromYaw = THREE.MathUtils.degToRad(cameraYaw.value)
  cameraFromPitch = THREE.MathUtils.degToRad(cameraPitch.value)
  cameraToYaw = THREE.MathUtils.degToRad(toYawDeg)
  cameraToPitch = THREE.MathUtils.degToRad(toPitchDeg)
  cameraTransStart = performance.now()
  cameraAnimating = true
}

function animate() {
  animationId = requestAnimationFrame(animate)

  const now = performance.now()
  const deltaTime = Math.min((now - lastTime) / 1000, 0.1)
  lastTime = now

  // 消防炮角度过渡
  if (cannonAnimating) {
    const elapsed = now - cannonTransStart
    let t = Math.min(elapsed / TRANSITION_DURATION, 1)
    t = easeInOutCubic(t)
    const cy = cannonFromYaw + (cannonToYaw - cannonFromYaw) * t
    const cp = cannonFromPitch + (cannonToPitch - cannonFromPitch) * t
    cannonYaw.value = THREE.MathUtils.radToDeg(cy)
    cannonPitch.value = THREE.MathUtils.radToDeg(cp)
    if (t >= 1) cannonAnimating = false
  }

  // 摄像头角度过渡
  if (cameraAnimating) {
    const elapsed = now - cameraTransStart
    let t = Math.min(elapsed / TRANSITION_DURATION, 1)
    t = easeInOutCubic(t)
    const cy = cameraFromYaw + (cameraToYaw - cameraFromYaw) * t
    const cp = cameraFromPitch + (cameraToPitch - cameraFromPitch) * t
    cameraYaw.value = THREE.MathUtils.radToDeg(cy)
    cameraPitch.value = THREE.MathUtils.radToDeg(cp)
    if (t >= 1) cameraAnimating = false
  }

  // 应用角度到3D模型
  if (cannonAnimating || cameraAnimating) {
    applyAngles(cannonYaw.value, cannonPitch.value, cameraYaw.value, cameraPitch.value)
  }

  // 更新喷水粒子系统
  if (waterSpray) {
    waterSpray.update(deltaTime)

    // 更新落点指示器位置
    if (landingIndicator) {
      const landingPos = waterSpray.getLandingPosition()
      if (landingPos) {
        landingIndicator.position.x = landingPos.x
        landingIndicator.position.z = landingPos.z
        landingIndicator.visible = true
      } else {
        landingIndicator.visible = false
      }
    }
  }

  controls.update()
  renderer.render(scene, camera3d)
}

function connectYolo() {
  // 关闭已有连接
  if (wsYolo) {
    wsYolo.onclose = null
    wsYolo.close()
    wsYolo = null
  }

  yoloConnected.value = false
  yoloFps.value = '--'
  yoloDetection.value = '检测: 连接中...'

  wsYolo = new WebSocket(yoloWsUrl)
  wsYolo.binaryType = 'arraybuffer'

  wsYolo.onopen = () => {
    yoloConnected.value = true
    yoloFrameCount = 0
    yoloClientFpsFrames = 0
    yoloClientFpsStart = performance.now()
  }

  wsYolo.onmessage = (event) => {
    if (typeof event.data === 'string') {
      // JSON 状态消息
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'status') {
          if (msg.fps !== undefined) yoloFps.value = msg.fps
          if (msg.detection_count !== undefined) {
            yoloDetection.value = msg.detection_count > 0
              ? `检测: ${msg.detection_count} 个目标`
              : '检测: 无检测'
          }
        }
      } catch (e) {
        console.warn('[YOLO] 解析JSON失败:', e)
      }
    } else {
      // 二进制 JPEG 帧
      yoloFrameCount++
      yoloClientFpsFrames++

      // 释放上一帧 Blob URL
      if (yoloLastBlobUrl) URL.revokeObjectURL(yoloLastBlobUrl)

      // ArrayBuffer → Blob → Object URL
      const blob = new Blob([event.data], { type: 'image/jpeg' })
      yoloLastBlobUrl = URL.createObjectURL(blob)
      yoloStreamSrc.value = yoloLastBlobUrl

      // 计算客户端 FPS（每秒更新一次）
      const now = performance.now()
      const elapsed = (now - yoloClientFpsStart) / 1000
      if (elapsed >= 1.0) {
        yoloFps.value = Math.round(yoloClientFpsFrames / elapsed)
        yoloClientFpsFrames = 0
        yoloClientFpsStart = now
      }
    }
  }

  wsYolo.onclose = () => {
    yoloConnected.value = false
    yoloFps.value = '--'
    yoloDetection.value = '检测: 已断开'
    wsYolo = null
  }

  wsYolo.onerror = () => {
    yoloConnected.value = false
    yoloFps.value = '--'
    yoloDetection.value = '检测: 连接失败'
  }
}

function disconnectYolo() {
  // 关闭 WebSocket
  if (wsYolo) {
    wsYolo.onclose = null
    wsYolo.close()
    wsYolo = null
  }
  // 释放 Blob URL
  if (yoloLastBlobUrl) {
    URL.revokeObjectURL(yoloLastBlobUrl)
    yoloLastBlobUrl = null
  }
  yoloStreamSrc.value = ''
  yoloConnected.value = false
  yoloFps.value = '--'
  yoloDetection.value = '检测: 等待中...'
}

function toggleRightCard() {
  showRightCard.value = !showRightCard.value
  if (showRightCard.value) {
    connectYolo()
  } else {
    disconnectYolo()
  }
}

function connectWebSocket() {
  slmReady = false
  ptzReady = false

  // === SLM 消防炮 WebSocket ===
  wsSlm = new WebSocket(`${wsBaseUrl}/ws/slm`)

  wsSlm.onopen = () => {
    slmReady = true
    console.log('[SLM] WebSocket 已连接')
    if (slmReady && ptzReady) onBothConnected()
  }

  wsSlm.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      switch (msg.type) {
        case 'angle_data':
          if (!syncing.value) return
          startCannonTransition(msg.data.horizontal_angle, msg.data.vertical_angle)
          if (msg.move_state) slmMoveState.value = msg.move_state
          break
        case 'move_state':
          slmMoveState.value = msg.move_state
          break
        case 'status':
          console.log('[SLM]', msg.message)
          break
        case 'warning':
          console.warn('[SLM]', msg.message)
          break
        case 'error':
          console.error('[SLM]', msg.message)
          break
      }
    } catch (e) {
      console.error('解析 SLM WebSocket 数据失败:', e)
    }
  }

  wsSlm.onclose = () => {
    console.log('[SLM] WebSocket 已断开')
    slmReady = false
    onAnyDisconnected()
  }

  wsSlm.onerror = (err) => {
    console.error('[SLM] WebSocket 错误:', err)
    slmReady = false
    onAnyDisconnected()
  }

  // === PTZ 云台 WebSocket ===
  wsPtz = new WebSocket(`${wsBaseUrl}/ws/ptz`)

  wsPtz.onopen = () => {
    ptzReady = true
    console.log('[PTZ] WebSocket 已连接')
    if (slmReady && ptzReady) onBothConnected()
  }

  wsPtz.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      switch (msg.type) {
        case 'angle_data':
          if (!syncing.value) return
          startCameraTransition(msg.data.horizontal_angle, msg.data.vertical_angle)
          break
        case 'status':
          console.log('[PTZ]', msg.message)
          break
        case 'warning':
          console.warn('[PTZ]', msg.message)
          break
        case 'error':
          console.error('[PTZ]', msg.message)
          break
      }
    } catch (e) {
      console.error('解析 PTZ WebSocket 数据失败:', e)
    }
  }

  wsPtz.onclose = () => {
    console.log('[PTZ] WebSocket 已断开')
    ptzReady = false
    onAnyDisconnected()
  }

  wsPtz.onerror = (err) => {
    console.error('[PTZ] WebSocket 错误:', err)
    ptzReady = false
    onAnyDisconnected()
  }
}

function onBothConnected() {
  // 确保仍在连接中状态（防止断开后 onopen 延迟触发）
  if (!connecting.value) return
  wsConnected.value = true
  connecting.value = false
  syncing.value = true
}

function onAnyDisconnected() {
  // 防止重入
  if (wsSlm === null && wsPtz === null) return
  const slm = wsSlm
  const ptz = wsPtz
  wsSlm = null
  wsPtz = null
  slmReady = false
  ptzReady = false
  if (slm) { slm.onclose = null; try { slm.close() } catch (e) { /* ignore */ } }
  if (ptz) { ptz.onclose = null; try { ptz.close() } catch (e) { /* ignore */ } }
  wsConnected.value = false
  connecting.value = false
  syncing.value = false
  searching.value = false
  autoMode.value = false
  slmMoveState.value = 'stop'
}

function toggleSync() {
  if (syncing.value) {
    // 停止同步 → 断开双连接
    syncing.value = false
    if (wsSlm) { wsSlm.onclose = null; wsSlm.close(); wsSlm = null }
    if (wsPtz) { wsPtz.onclose = null; wsPtz.close(); wsPtz = null }
    slmReady = false
    ptzReady = false
    wsConnected.value = false
    searching.value = false
    autoMode.value = false
    slmMoveState.value = 'stop'
  } else if (!connecting.value) {
    // 开始同步 → 进入连接中状态
    connecting.value = true
    connectWebSocket()
  }
}

function toggleAutoMode() {
  if (!wsPtz || wsPtz.readyState !== WebSocket.OPEN) return
  autoMode.value = !autoMode.value
  wsPtz.send(JSON.stringify({ action: 'set_auto', value: autoMode.value }))
}

function toggleSearch() {
  if (!wsPtz || wsPtz.readyState !== WebSocket.OPEN) return
  if (searching.value) {
    wsPtz.send(JSON.stringify({ action: 'emergency_stop' }))
    searching.value = false
  } else {
    wsPtz.send(JSON.stringify({ action: 'search' }))
    searching.value = true
  }
}

function operateCannon(direction) {
  if (syncing.value) {
    // 同步模式：通过 SLM WebSocket 发送方向命令
    if (wsSlm && wsSlm.readyState === WebSocket.OPEN) {
      wsSlm.send(direction)
    }
    // 角度更新由 WebSocket 推送的 angle_data 处理
    return
  }

  // 离线模式：本地调整角度
  const step = 5 // 每次调整5度
  let newCYaw = cannonYaw.value
  let newCPitch = cannonPitch.value

  switch (direction) {
    case 'up':
      newCPitch = Math.max(newCPitch - step, -90)
      break
    case 'down':
      newCPitch = Math.min(newCPitch + step, 45)
      break
    case 'left':
      newCYaw = newCYaw - step
      break
    case 'right':
      newCYaw = newCYaw + step
      break
    case 'home':
      newCYaw = 0
      newCPitch = 0
      break
  }

  startCannonTransition(newCYaw, newCPitch)
  startCameraTransition(newCYaw, newCPitch)
}

function toggleSpray() {
  isSpraying.value = !isSpraying.value
  if (waterSpray) {
    if (isSpraying.value) {
      waterSpray.start()
    } else {
      waterSpray.stop()
    }
  }
}

function updatePressure() {
  if (waterSpray) {
    waterSpray.setPressure(pressure.value / 100)
  }
}

function onResize() {
  if (!canvasContainer.value) return
  const w = canvasContainer.value.clientWidth
  const h = canvasContainer.value.clientHeight
  if (w === 0 || h === 0) return
  camera3d.aspect = w / h
  camera3d.updateProjectionMatrix()
  renderer.setSize(w, h)
}

onMounted(() => {
  createScene()
  animate()
  window.addEventListener('resize', onResize)

  // 设置默认角度（摄像头与消防炮朝向一致）
  cannonYaw.value = 15
  cannonPitch.value = -10
  cameraYaw.value = 15
  cameraPitch.value = -10
  applyAngles(15, -10, 15, -10)

  // 初始化喷水系统
  const barrelGroup = cannonGroup.getObjectByName('barrelGroup')
  waterSpray = new WaterSpray(scene, barrelGroup)
  waterSpray.setPressure(pressure.value / 100)

  // 使用 ResizeObserver 监听容器尺寸变化
  const resizeObserver = new ResizeObserver(() => {
    onResize()
  })
  resizeObserver.observe(canvasContainer.value)
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (wsSlm) { wsSlm.onclose = null; wsSlm.close(); wsSlm = null }
  if (wsPtz) { wsPtz.onclose = null; wsPtz.close(); wsPtz = null }
  disconnectYolo()
  window.removeEventListener('resize', onResize)
  if (waterSpray) waterSpray.dispose()
  if (renderer) renderer.dispose()
})
</script>

<style scoped>
.three-d-container {
  width: calc(100% + 48px);
  height: calc(100% + 48px);
  display: flex;
  overflow: hidden;
  margin: -24px;
  font-family: Inter, 'Microsoft YaHei', ui-sans-serif, system-ui, sans-serif;
}

.canvas-area {
  flex: 1;
  height: 100%;
  min-width: 0;
  position: relative;
}

.control-panel {
  width: 280px;
  height: 100%;
  background: #212121;
  padding: 20px 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-left: 1px solid #353535;
  color: #e0e0e0;
  overflow-y: auto;
  flex-shrink: 0;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  text-align: center;
  letter-spacing: 2px;
}

/* WebSocket 状态 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.ws-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.ws-indicator.connected {
  background: #19d600;
  box-shadow: 0 0 6px #19d600;
}

.ws-indicator.disconnected {
  background: #dd0000;
  box-shadow: 0 0 6px #dd0000;
}

.status-text {
  color: #b9b9b9;
}

/* 角度显示 */
.section-label {
  font-size: 12px;
  color: #797979;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding-top: 4px;
}

.angle-display {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.angle-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  font-size: 13px;
}

.angle-item label {
  color: #797979;
}

.angle-item .angle-value {
  color: #0052ef;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* 同步状态 */
.sync-status {
  text-align: center;
  font-size: 13px;
  color: #797979;
}

.sync-status .active {
  color: #19d600;
}

.sync-status .connecting {
  color: #e6a700;
}

/* 按钮组 */
.btn-group {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.full-btn {
  flex: 1;
}

.outline-btn {
  border-color: #353535;
  color: #ffffff;
}

.outline-btn:hover {
  border-color: #0052ef;
  color: #ffffff;
}

/* 操作面板 */
.operation-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #353535;
}

.dpad-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 4px;
  width: 100%;
  aspect-ratio: 3 / 3;
  max-width: 180px;
  margin: 0 auto;
}

.dpad-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  padding: 0;
}

.dpad-btn:hover {
  background: rgba(0, 82, 239, 0.3);
  border-color: rgba(0, 82, 239, 0.6);
  color: #fff;
}

.dpad-btn:active {
  background: rgba(0, 82, 239, 0.5);
  transform: scale(0.95);
}

.dpad-up    { grid-column: 2; grid-row: 1; }
.dpad-left  { grid-column: 1; grid-row: 2; }
.dpad-center{ grid-column: 2; grid-row: 2; }
.dpad-right { grid-column: 3; grid-row: 2; }
.dpad-down  { grid-column: 2; grid-row: 3; }

.dpad-center {
  border-color: rgba(0, 82, 239, 0.4);
  background: rgba(0, 82, 239, 0.15);
}

.dpad-center:hover {
  background: rgba(0, 82, 239, 0.4);
}

.dpad-btn.active {
  background: rgba(0, 82, 239, 0.45);
  border-color: rgba(0, 82, 239, 0.8);
  color: #fff;
  box-shadow: 0 0 8px rgba(0, 82, 239, 0.4);
}

/* 喷水控制 */
.spray-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid #353535;
}

.spray-status {
  text-align: center;
  font-size: 13px;
  color: #797979;
}

.spray-status .active {
  color: #0052ef;
  font-weight: 600;
}

/* 压力控制 */
.pressure-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pressure-control label {
  font-size: 13px;
  color: #b9b9b9;
  text-align: center;
}

.pressure-slider {
  padding: 0 8px;
}

/* Overlay monitor cards */
.overlay-cards {
  position: absolute;
  top: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 10;
  pointer-events: none;
}

.monitor-card {
  position: relative;
  height: calc(100vh / 3 * 0.7);  /* 调整视频大小 */
  aspect-ratio: 16 / 9;
  background: rgba(0, 0, 0, 0.75);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  pointer-events: auto;
}

.card-label {
  position: absolute;
  top: 8px;
  left: 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 8px;
  border-radius: 4px;
  z-index: 1;
  pointer-events: none;
}

.monitor-card iframe,
.monitor-card img {
  width: 100%;
  height: 100%;
  display: block;
}

.monitor-card img {
  object-fit: cover;
}

/* YOLO status bar */
.yolo-status-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.7);
  font-size: 11px;
  color: #ccc;
  z-index: 1;
  pointer-events: none;
}

.yolo-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.yolo-status-dot.online {
  background: #00ff88;
  box-shadow: 0 0 4px #00ff88;
  animation: yolo-pulse 1.5s infinite;
}

.yolo-status-dot.offline {
  background: #ff4444;
}

@keyframes yolo-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.yolo-status-text {
  flex-shrink: 0;
}

.yolo-status-info {
  margin-left: auto;
  color: #aaa;
}

.yolo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 14px;
}

.yolo-connect-btn {
  position: absolute;
  top: 8px;
  right: 10px;
  width: 26px;
  height: 26px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.5);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  transition: all 0.2s;
}

.yolo-connect-btn:hover {
  background: rgba(0, 82, 239, 0.6);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.4);
}

.toggle-card-btn {
  width: 24px;
  height: 48px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(0, 0, 0, 0.6);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  flex-shrink: 0;
  pointer-events: auto;
}

.toggle-card-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}

.toggle-arrow {
  transition: transform 0.3s;
}

.toggle-arrow.expanded {
  transform: rotate(180deg);
}

.card-expand-enter-active {
  transition: all 0.3s ease-out;
}

.card-expand-leave-active {
  transition: all 0.2s ease-in;
}

.card-expand-enter-from,
.card-expand-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}
</style>
