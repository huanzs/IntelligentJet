/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : Login.vue
 * @Project : intelligent-jet
 */

<template>
  <div class="login-page">
    <!-- 三维网格背景 -->
    <div class="grid-bg">
      <div class="grid-floor"></div>
      <div class="grid-wall-left"></div>
      <div class="grid-wall-right"></div>
      <div class="glow-horizon"></div>
    </div>
    <div class="login-card">
      <h1 class="login-title">消防炮联动系统</h1>
      <p class="login-subtitle">消防炮联动系统</p>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" native-type="submit">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (err) {
    ElMessage.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── 页面容器 ── */
.login-page {
  position: relative;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0b0b0b;
  overflow: hidden;
}

/* ── 三维网格背景容器 ── */
.grid-bg {
  position: absolute;
  inset: 0;
  perspective: 600px;
  pointer-events: none;
  z-index: 0;
}

/* 地面网格 */
.grid-floor {
  position: absolute;
  bottom: -10%;
  left: -50%;
  width: 200%;
  height: 70%;
  background:
    linear-gradient(90deg, rgba(0,82,239,0.12) 1px, transparent 1px),
    linear-gradient(0deg, rgba(0,82,239,0.12) 1px, transparent 1px);
  background-size: 60px 60px;
  transform: rotateX(60deg);
  transform-origin: center bottom;
  animation: gridScroll 12s linear infinite;
}

/* 左侧墙面网格 */
.grid-wall-left {
  position: absolute;
  top: -10%;
  left: -8%;
  width: 50%;
  height: 130%;
  background:
    linear-gradient(90deg, rgba(0,82,239,0.08) 1px, transparent 1px),
    linear-gradient(180deg, rgba(0,82,239,0.08) 1px, transparent 1px);
  background-size: 60px 60px;
  transform: rotateY(55deg);
  transform-origin: left center;
  animation: wallFlicker 8s ease-in-out infinite alternate;
}

/* 右侧墙面网格 */
.grid-wall-right {
  position: absolute;
  top: -10%;
  right: -8%;
  width: 50%;
  height: 130%;
  background:
    linear-gradient(90deg, rgba(0,82,239,0.08) 1px, transparent 1px),
    linear-gradient(180deg, rgba(0,82,239,0.08) 1px, transparent 1px);
  background-size: 60px 60px;
  transform: rotateY(-55deg);
  transform-origin: right center;
  animation: wallFlicker 8s ease-in-out infinite alternate-reverse;
}

/* 地平线发光 */
.glow-horizon {
  position: absolute;
  bottom: 28%;
  left: 0;
  width: 100%;
  height: 3px;
  background: rgba(0,82,239,0.5);
  box-shadow:
    0 0 30px 8px rgba(0,82,239,0.25),
    0 0 80px 20px rgba(0,82,239,0.1);
}

/* 地面网格滚动动画 */
@keyframes gridScroll {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 0 60px;
  }
}

/* 墙面微闪动画 */
@keyframes wallFlicker {
  0% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
}

/* ── 登录卡片 ── */
.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  padding: 48px 40px;
  background: rgba(33,33,33,0.85);
  border: 1px solid #353535;
  border-radius: 6px;
  backdrop-filter: blur(12px);
  box-shadow:
    0 0 40px rgba(0,82,239,0.08),
    0 8px 32px rgba(0,0,0,0.5);
}
.login-title {
  font-size: 32px;
  font-weight: 425;
  color: #ffffff;
  letter-spacing: -0.32px;
  margin: 0 0 4px;
}
.login-subtitle {
  font-size: 14px;
  color: #797979;
  margin: 0 0 32px;
}
.login-btn {
  width: 100%;
  border-radius: 99999px;
}
.login-footer {
  text-align: center;
  color: #797979;
  font-size: 13px;
  margin-top: 16px;
}
.login-footer a {
  color: #0052ef;
  text-decoration: none;
}
.login-footer a:hover {
  text-decoration: underline;
}
</style>
