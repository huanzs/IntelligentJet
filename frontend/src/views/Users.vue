/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : Users.vue
 * @Project : intelligent-jet
 */

<template>
  <div class="users-page">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button v-if="authStore.hasPermission('user:write')" type="primary" @click="showCreateDialog">
        创建用户
      </el-button>
    </div>

    <div class="table-card">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="角色">
          <template #default="{ row }">
            <el-tag v-for="role in row.roles" :key="role" size="small" class="dark-tag">{{ role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" v-if="authStore.hasPermission('user:write')">
          <template #default="{ row }">
            <el-button size="small" text @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" text @click="showRoleDialog(row)">角色</el-button>
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
          @current-change="fetchUsers"
        />
      </div>
    </div>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '创建用户'" width="480px" class="dark-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码" :prop="isEdit ? '' : 'password'">
          <el-input v-model="form.password" type="password" :placeholder="isEdit ? '留空则不修改' : '至少6位'" show-password />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 角色分配对话框 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="480px" class="dark-dialog">
      <el-checkbox-group v-model="selectedRoleIds">
        <el-checkbox v-for="role in allRoles" :key="role.id" :value="role.id" :label="role.name" />
      </el-checkbox-group>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleAssignRoles">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getUsers, createUser, updateUser, deleteUser, assignUserRoles } from '../api/users'
import { getRoles } from '../api/roles'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(false)
const users = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const roleDialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const editingId = ref(null)
const formRef = ref()

const form = reactive({
  username: '',
  email: '',
  password: '',
  is_active: true,
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

const allRoles = ref([])
const selectedRoleIds = ref([])

async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUsers({ page: page.value, per_page: perPage.value })
    users.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { username: '', email: '', password: '', is_active: true })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, { username: row.username, email: row.email, password: '', is_active: row.is_active })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (isEdit.value) {
      const data = { email: form.email, is_active: form.is_active }
      if (form.password) data.password = form.password
      await updateUser(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createUser(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '确认', { type: 'warning' })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch {
    // cancelled or error
  }
}

async function showRoleDialog(row) {
  editingId.value = row.id
  try {
    const res = await getRoles({ page: 1, per_page: 100 })
    allRoles.value = res.data.items
    selectedRoleIds.value = []
    // Fetch user details to get current roles
    const userRes = await getUsers({ page: 1, per_page: 1000 })
    const currentUser = userRes.data.items.find(u => u.id === row.id)
    if (currentUser) {
      const roleNames = currentUser.roles || []
      selectedRoleIds.value = allRoles.value.filter(r => roleNames.includes(r.name)).map(r => r.id)
    }
    roleDialogVisible.value = true
  } catch {
    ElMessage.error('获取角色信息失败')
  }
}

async function handleAssignRoles() {
  submitLoading.value = true
  try {
    await assignUserRoles(editingId.value, selectedRoleIds.value)
    ElMessage.success('角色分配成功')
    roleDialogVisible.value = false
    fetchUsers()
  } catch (err) {
    ElMessage.error(err.message || '分配失败')
  } finally {
    submitLoading.value = false
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.users-page {
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
.dark-tag {
  background: #353535 !important;
  color: #b9b9b9 !important;
  border: none !important;
  border-radius: 99999px !important;
  margin-right: 4px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
