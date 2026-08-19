/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : Forbidden.vue
 * @Project : intelligent-jet
 */
 *
 * 403 禁止访问页 - 无权限提示
 */

<template>
  <div class="forbidden-page">
    <h1>403</h1>
    <p>你没有权限访问此页面</p>
    <el-button type="primary" @click="router.push('/dashboard')">返回仪表盘</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<style scoped>
.forbidden-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #0b0b0b;
  color: #ffffff;
}
.forbidden-page h1 {
  font-size: 72px;
  margin: 0;
  letter-spacing: -2.88px;
  color: #f36458;
}
.forbidden-page p {
  color: #b9b9b9;
  font-size: 16px;
  margin: 16px 0 32px;
}
</style>
