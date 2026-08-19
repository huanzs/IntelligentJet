/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : MainLayout.vue
 * @Project : intelligent-jet
 */
 *
 * 主布局组件 - 侧边栏+顶栏+内容区的暗色主题布局
 */

<template>
  <div class="main-layout">
    <header class="top-bar">
      <div class="top-bar-left">
        <span class="logo">消防炮联动系统</span>
      </div>
      <div class="top-bar-right">
        <span class="username">{{ authStore.user?.username }}</span>
        <el-button text @click="handleLogout" class="logout-btn">退出</el-button>
      </div>
    </header>
    <div class="main-body">
      <aside class="sidebar" :class="{ 'is-collapsed': isCollapsed }">
        <el-menu
          :default-active="route.path"
          :collapse="isCollapsed"
          router
          background-color="#212121"
          text-color="#b9b9b9"
          active-text-color="#0052ef"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title><span>仪表盘</span></template>
          </el-menu-item>
          <el-menu-item v-if="authStore.hasPermission('user:read')" index="/users">
            <el-icon><User /></el-icon>
            <template #title><span>用户管理</span></template>
          </el-menu-item>
          <el-menu-item v-if="authStore.hasPermission('role:read')" index="/roles">
            <el-icon><Key /></el-icon>
            <template #title><span>角色管理</span></template>
          </el-menu-item>
          <el-menu-item v-if="authStore.hasPermission('permission:read')" index="/permissions">
            <el-icon><Lock /></el-icon>
            <template #title><span>权限管理</span></template>
          </el-menu-item>
          <el-menu-item v-if="authStore.hasPermission('operation:read')" index="/three-d-operation">
            <el-icon><Monitor /></el-icon>
            <template #title><span>三维操作</span></template>
          </el-menu-item>
          <el-menu-item v-if="authStore.hasPermission('operation:read')" index="/ptz-control">
            <el-icon><VideoCamera /></el-icon>
            <template #title><span>云台控制</span></template>
          </el-menu-item>
          <el-menu-item v-if="authStore.hasPermission('operation:read')" index="/slm-monitor">
            <el-icon><Aim /></el-icon>
            <template #title><span>消防炮监控</span></template>
          </el-menu-item>
        </el-menu>
        <div class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <el-icon :size="16">
            <DArrowLeft v-if="!isCollapsed" />
            <DArrowRight v-else />
          </el-icon>
        </div>
      </aside>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Odometer, User, Key, Lock, Monitor, VideoCamera, Aim, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'

const isCollapsed = ref(false)

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0b0b0b;
}
.top-bar {
  height: 56px;
  background: #0b0b0b;
  border-bottom: 1px solid #212121;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}
.top-bar-left {
  display: flex;
  align-items: center;
}
.logo {
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: -0.2px;
}
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.username {
  color: #b9b9b9;
  font-size: 14px;
}
.logout-btn {
  color: #b9b9b9 !important;
}
.logout-btn:hover {
  color: #0052ef !important;
}
.main-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.sidebar {
  width: 220px;
  background: #212121;
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid #353535;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
}
.sidebar.is-collapsed {
  width: 64px;
}
.sidebar .el-menu {
  border-right: none;
  flex: 1;
}
.sidebar.is-collapsed .el-menu {
  width: 64px;
}
.collapse-btn {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #797979;
  border-top: 1px solid #353535;
  transition: color 0.2s, background-color 0.2s;
  flex-shrink: 0;
}
.collapse-btn:hover {
  color: #0052ef;
  background-color: #1a1a1a;
}
.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}
</style>
