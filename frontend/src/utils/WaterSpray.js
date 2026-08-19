/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : WaterSpray.js
 * @Project : intelligent-jet
 */
 * 
 * Three.js 水柱粒子特效 - 基于抛体物理模拟的水柱可视化
 */

import * as THREE from 'three'

export default class WaterSpray {
  constructor(scene, barrelGroup) {
    this.scene = scene
    this.barrelGroup = barrelGroup
    this.isSpraying = false
    this.pressure = 0.7 // 喷射力度 0-1

    // 粒子配置
    this.maxParticles = 1500
    this.particlesPerFrame = 20
    this.gravity = 9.8
    this.baseSpeed = 12
    this.particleLife = 2.5 // 秒

    // 粒子数据
    this.positions = new Float32Array(this.maxParticles * 3)
    this.velocities = new Float32Array(this.maxParticles * 3)
    this.lives = new Float32Array(this.maxParticles)
    this.maxLives = new Float32Array(this.maxParticles)
    this.sizes = new Float32Array(this.maxParticles)

    // 粒子状态：false = 死亡/可用，true = 存活
    this.active = new Array(this.maxParticles).fill(false)

    // 当前存活粒子数
    this.activeCount = 0

    // 下一个可用的粒子索引
    this.nextIndex = 0

    // 创建几何体
    this.geometry = new THREE.BufferGeometry()
    this.geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3))
    this.geometry.setAttribute('size', new THREE.BufferAttribute(this.sizes, 1))

    // 创建材质
    this.material = new THREE.PointsMaterial({
      color: 0x64b4ff,
      size: 0.1,
      transparent: true,
      opacity: 0.7,
      sizeAttenuation: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    })

    // 创建粒子系统
    this.points = new THREE.Points(this.geometry, this.material)
    this.scene.add(this.points)

    // 辅助变量
    this._muzzlePos = new THREE.Vector3()
    this._direction = new THREE.Vector3()
    this._quaternion = new THREE.Quaternion()
  }

  start() {
    this.isSpraying = true
  }

  stop() {
    this.isSpraying = false
  }

  setPressure(value) {
    this.pressure = Math.max(0, Math.min(1, value))
  }

  /**
   * 计算当前角度和力度下水流的落点位置（忽略随机散射的理想弹道）
   * @returns {THREE.Vector3|null} 落点位置，若无法到达地面则返回 null
   */
  getLandingPosition() {
    // 获取炮口位置
    this.barrelGroup.getWorldPosition(this._muzzlePos)
    this.barrelGroup.getWorldQuaternion(this._quaternion)
    this._direction.set(0, 0, 1).applyQuaternion(this._quaternion)
    this._muzzlePos.addScaledVector(this._direction, 2.65)

    // 获取发射方向（无散射）
    this._direction.set(0, 0, 1).applyQuaternion(this._quaternion)

    const speed = this.baseSpeed * this.pressure
    const vx = this._direction.x * speed
    const vy = this._direction.y * speed
    const vz = this._direction.z * speed

    const y0 = this._muzzlePos.y
    // 解二次方程: y0 + vy*t - 0.5*g*t^2 = 0
    // -0.5*g*t^2 + vy*t + y0 = 0
    const a = -0.5 * this.gravity
    const b = vy
    const c = y0

    const discriminant = b * b - 4 * a * c
    if (discriminant < 0) return null

    const sqrtD = Math.sqrt(discriminant)
    const t1 = (-b + sqrtD) / (2 * a)
    const t2 = (-b - sqrtD) / (2 * a)

    // 取正数且较大的时间（落地时刻）
    let t = -1
    if (t1 > 0 && t2 > 0) t = Math.max(t1, t2)
    else if (t1 > 0) t = t1
    else if (t2 > 0) t = t2

    if (t <= 0) return null

    return new THREE.Vector3(
      this._muzzlePos.x + vx * t,
      0,
      this._muzzlePos.z + vz * t
    )
  }

  update(deltaTime) {
    // 发射新粒子
    if (this.isSpraying && this.activeCount < this.maxParticles) {
      const emitCount = Math.floor(this.particlesPerFrame * this.pressure)
      for (let i = 0; i < emitCount && this.activeCount < this.maxParticles; i++) {
        this._emitParticle()
      }
    }

    // 更新所有存活粒子
    for (let i = 0; i < this.maxParticles; i++) {
      if (!this.active[i]) continue

      // 更新生命值
      this.lives[i] -= deltaTime

      // 检查是否死亡
      const idx = i * 3
      const y = this.positions[idx + 1]

      if (this.lives[i] <= 0 || y < 0) {
        this.active[i] = false
        this.activeCount--
        continue
      }

      // 应用重力
      this.velocities[idx + 1] -= this.gravity * deltaTime

      // 更新位置
      this.positions[idx] += this.velocities[idx] * deltaTime
      this.positions[idx + 1] += this.velocities[idx + 1] * deltaTime
      this.positions[idx + 2] += this.velocities[idx + 2] * deltaTime

      // 更新粒子大小（生命值衰减时变小）
      const lifeRatio = this.lives[i] / this.maxLives[i]
      this.sizes[i] = 0.1 * lifeRatio
    }

    // 更新几何体
    this.geometry.attributes.position.needsUpdate = true
    this.geometry.attributes.size.needsUpdate = true
  }

  _emitParticle() {
    // 找到一个死亡的粒子索引
    let index = -1
    for (let i = 0; i < this.maxParticles; i++) {
      const checkIdx = (this.nextIndex + i) % this.maxParticles
      if (!this.active[checkIdx]) {
        index = checkIdx
        this.nextIndex = (checkIdx + 1) % this.maxParticles
        break
      }
    }

    if (index === -1) return // 没有可用粒子

    // 获取炮口位置
    this.barrelGroup.getWorldPosition(this._muzzlePos)
    // 炮口在炮管末端，需要沿炮管方向偏移
    this.barrelGroup.getWorldQuaternion(this._quaternion)
    this._direction.set(0, 0, 1).applyQuaternion(this._quaternion)
    this._muzzlePos.addScaledVector(this._direction, 2.65) // 炮口位置

    // 获取发射方向（炮管朝向 + 随机散射）
    this._direction.set(0, 0, 1)
    this._direction.applyQuaternion(this._quaternion)
    // 添加随机散射
    const scatter = 0.08
    this._direction.x += (Math.random() - 0.5) * scatter
    this._direction.y += (Math.random() - 0.5) * scatter
    this._direction.z += (Math.random() - 0.5) * scatter
    this._direction.normalize()

    // 计算初始速度
    const speed = this.baseSpeed * this.pressure * (0.9 + Math.random() * 0.2)

    // 设置粒子属性
    const idx = index * 3
    this.positions[idx] = this._muzzlePos.x
    this.positions[idx + 1] = this._muzzlePos.y
    this.positions[idx + 2] = this._muzzlePos.z

    this.velocities[idx] = this._direction.x * speed
    this.velocities[idx + 1] = this._direction.y * speed
    this.velocities[idx + 2] = this._direction.z * speed

    // 随机生命值
    const life = this.particleLife * (0.7 + Math.random() * 0.6)
    this.lives[index] = life
    this.maxLives[index] = life

    // 随机大小
    this.sizes[index] = 0.08 + Math.random() * 0.04

    // 标记为存活
    this.active[index] = true
    this.activeCount++
  }

  dispose() {
    this.geometry.dispose()
    this.material.dispose()
    this.scene.remove(this.points)
  }
}
