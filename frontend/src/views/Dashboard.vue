/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : Dashboard.vue
 * @Project : intelligent-jet
 */

<template>
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.users || '--' }}</div>
        <div class="stat-label">用户数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.roles || '--' }}</div>
        <div class="stat-label">角色数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.permissions || '--' }}</div>
        <div class="stat-label">权限数</div>
      </div>
    </div>
    <div class="info-section">
      <h3 class="section-title">当前用户信息</h3>
      <div class="info-card">
        <div class="info-row">
          <span class="info-label">用户名</span>
          <span class="info-value">{{ authStore.user?.username }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">邮箱</span>
          <span class="info-value">{{ authStore.user?.email }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">角色</span>
          <div class="info-tags">
            <el-tag v-for="role in (authStore.user?.roles || [])" :key="role" size="small" class="dark-tag">
              {{ role }}
            </el-tag>
          </div>
        </div>
        <div class="info-row">
          <span class="info-label">权限</span>
          <div class="info-tags">
            <el-tag v-for="perm in (authStore.permissions || [])" :key="perm" size="small" class="dark-tag">
              {{ perm }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getUsers } from '../api/users'
import { getRoles } from '../api/roles'
import { getPermissions } from '../api/permissions'

const authStore = useAuthStore()

const stats = ref({
  users: 0,
  roles: 0,
  permissions: 0,
})

onMounted(async () => {
  try {
    const promises = []
    if (authStore.hasPermission('user:read')) {
      promises.push(getUsers({ page: 1, per_page: 1 }).then(r => { stats.value.users = r.data.total }))
    }
    if (authStore.hasPermission('role:read')) {
      promises.push(getRoles({ page: 1, per_page: 1 }).then(r => { stats.value.roles = r.data.total }))
    }
    if (authStore.hasPermission('permission:read')) {
      promises.push(getPermissions({ page: 1, per_page: 1 }).then(r => { stats.value.permissions = r.data.total }))
    }
    await Promise.all(promises)
  } catch {
    // silently ignore
  }
})
</script>

<style scoped>
.dashboard {
  color: #ffffff;
}
.page-title {
  font-size: 24px;
  font-weight: 425;
  letter-spacing: -0.24px;
  margin: 0 0 24px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.stat-card {
  background: #212121;
  border: 1px solid #353535;
  border-radius: 6px;
  padding: 24px;
  text-align: center;
}
.stat-value {
  font-size: 36px;
  font-weight: 425;
  color: #ffffff;
  letter-spacing: -0.36px;
}
.stat-label {
  font-size: 13px;
  color: #797979;
  margin-top: 4px;
}
.section-title {
  font-size: 18px;
  font-weight: 425;
  color: #ffffff;
  letter-spacing: -0.18px;
  margin: 0 0 16px;
}
.info-card {
  background: #212121;
  border: 1px solid #353535;
  border-radius: 6px;
  padding: 24px;
}
.info-row {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid #353535;
}
.info-row:last-child {
  border-bottom: none;
}
.info-label {
  width: 80px;
  flex-shrink: 0;
  color: #797979;
  font-size: 14px;
}
.info-value {
  color: #ffffff;
  font-size: 14px;
}
.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.dark-tag {
  background: #353535 !important;
  color: #b9b9b9 !important;
  border: none !important;
  border-radius: 99999px !important;
}
</style>
