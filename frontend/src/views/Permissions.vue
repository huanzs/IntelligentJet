/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : Permissions.vue
 * @Project : intelligent-jet
 */
 *
 * 权限管理页 - 权限列表和创建/删除
 */

<template>
  <div class="permissions-page">
    <div class="page-header">
      <h2 class="page-title">权限管理</h2>
      <el-button v-if="authStore.hasPermission('permission:write')" type="primary" @click="showCreateDialog">
        创建权限
      </el-button>
    </div>

    <div class="table-card">
      <el-table :data="permissions" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="权限编码">
          <template #default="{ row }">
            <el-tag size="small" class="code-tag">{{ row.code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="权限名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="操作" width="120" v-if="authStore.hasPermission('permission:write')">
          <template #default="{ row }">
            <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          :page-size="perPage"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchPermissions"
        />
      </div>
    </div>

    <!-- 创建权限对话框 -->
    <el-dialog v-model="dialogVisible" title="创建权限" width="480px" class="dark-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="权限编码" prop="code">
          <el-input v-model="form.code" placeholder="如 user:read" />
        </el-form-item>
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="form.name" placeholder="如 查看用户" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getPermissions, createPermission, deletePermission } from '../api/permissions'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(false)
const permissions = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref()

const form = reactive({
  code: '',
  name: '',
  description: '',
})

const rules = {
  code: [{ required: true, message: '请输入权限编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入权限名称', trigger: 'blur' }],
}

async function fetchPermissions() {
  loading.value = true
  try {
    const res = await getPermissions({ page: page.value, per_page: perPage.value })
    permissions.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('获取权限列表失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  Object.assign(form, { code: '', name: '', description: '' })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    await createPermission(form)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    fetchPermissions()
  } catch (err) {
    ElMessage.error(err.message || '创建失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除权限 ${row.name}？`, '确认', { type: 'warning' })
    await deletePermission(row.id)
    ElMessage.success('删除成功')
    fetchPermissions()
  } catch {
    // cancelled or error
  }
}

onMounted(fetchPermissions)
</script>

<style scoped>
.permissions-page {
  color: #ffffff;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-title {
  font-size: 24px;
  font-weight: 425;
  letter-spacing: -0.24px;
  margin: 0;
}
.table-card {
  background: #212121;
  border: 1px solid #353535;
  border-radius: 6px;
  padding: 16px;
}
.code-tag {
  background: #353535 !important;
  color: #b9b9b9 !important;
  border: none !important;
  border-radius: 99999px !important;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px !important;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
