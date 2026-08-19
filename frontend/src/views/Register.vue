/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : Register.vue
 * @Project : intelligent-jet
 */
 *
 * 注册页 - 用户注册，含表单验证
 */

<template>
  <div class="register-page">
    <div class="register-card">
      <h1 class="register-title">注册</h1>
      <p class="register-subtitle">创建 系统账号</p>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleRegister">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码（至少6位）" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" class="register-btn" :loading="loading" native-type="submit">
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await register(form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (err) {
    ElMessage.error(err.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0b0b0b;
}
.register-card {
  width: 400px;
  padding: 48px 40px;
  background: #212121;
  border: 1px solid #353535;
  border-radius: 6px;
}
.register-title {
  font-size: 32px;
  font-weight: 425;
  color: #ffffff;
  letter-spacing: -0.32px;
  margin: 0 0 4px;
}
.register-subtitle {
  font-size: 14px;
  color: #797979;
  margin: 0 0 32px;
}
.register-btn {
  width: 100%;
  border-radius: 99999px;
}
.register-footer {
  text-align: center;
  color: #797979;
  font-size: 13px;
  margin-top: 16px;
}
.register-footer a {
  color: #0052ef;
  text-decoration: none;
}
.register-footer a:hover {
  text-decoration: underline;
}
</style>
