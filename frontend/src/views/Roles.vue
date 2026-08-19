/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : Roles.vue
 * @Project : intelligent-jet
 */

<template>
  <div class="roles-page">
    <div class="page-header">
      <h2 class="page-title">角色管理</h2>
      <el-button v-if="authStore.hasPermission('role:write')" type="primary" @click="showCreateDialog">
        创建角色
      </el-button>
    </div>

    <div class="table-card">
      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="操作" width="260" v-if="authStore.hasPermission('role:write')">
          <template #default="{ row }">
            <el-button size="small" text @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" text @click="showPermissionDialog(row)">权限</el-button>
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
          @current-change="fetchRoles"
        />
      </div>
    </div>

    <!-- 创建/编辑角色对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑角色' : '创建角色'" width="480px" class="dark-dialog">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 权限分配对话框 -->
    <el-dialog v-model="permDialogVisible" title="分配权限" width="480px" class="dark-dialog">
      <el-checkbox-group v-model="selectedPermIds">
        <el-checkbox v-for="perm in allPermissions" :key="perm.id" :value="perm.id" :label="perm.name + ' (' + perm.code + ')'" />
      </el-checkbox-group>
      <template #footer>
        <el-button @click="permDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleAssignPermissions">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getRole, getRoles, createRole, updateRole, deleteRole, assignRolePermissions } from '../api/roles'
import { getPermissions } from '../api/permissions'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(false)
const roles = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const permDialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const editingId = ref(null)
const formRef = ref()

const form = reactive({
  name: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
}

const allPermissions = ref([])
const selectedPermIds = ref([])

async function fetchRoles() {
  loading.value = true
  try {
    const res = await getRoles({ page: page.value, per_page: perPage.value })
    roles.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, { name: '', description: '' })
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, { name: row.name, description: row.description || '' })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await updateRole(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createRole(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchRoles()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除角色 ${row.name}？`, '确认', { type: 'warning' })
    await deleteRole(row.id)
    ElMessage.success('删除成功')
    fetchRoles()
  } catch {
    // cancelled or error
  }
}

async function showPermissionDialog(row) {
  editingId.value = row.id
  try {
    const [permRes, roleRes] = await Promise.all([
      getPermissions({ page: 1, per_page: 100 }),
      getRole(row.id),
    ])
    allPermissions.value = permRes.data.items
    selectedPermIds.value = (roleRes.data.permissions || []).map(p => p.id)
    permDialogVisible.value = true
  } catch (e) {
    console.log(e.message)
    ElMessage.error('获取权限信息失败')
  }
}

async function handleAssignPermissions() {
  submitLoading.value = true
  try {
    await assignRolePermissions(editingId.value, selectedPermIds.value)
    ElMessage.success('权限分配成功')
    permDialogVisible.value = false
    fetchRoles()
  } catch (err) {
    ElMessage.error(err.message || '分配失败')
  } finally {
    submitLoading.value = false
  }
}

onMounted(fetchRoles)
</script>

<style scoped>
.roles-page {
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
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
