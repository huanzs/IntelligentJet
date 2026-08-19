/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : auth.js
 * @Project : intelligent-jet
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshTokenVal = ref(localStorage.getItem('refresh_token') || '')
  const user = ref(null)
  const permissions = ref([])

  const isLoggedIn = computed(() => !!token.value)

  function hasPermission(code) {
    return permissions.value.includes(code)
  }

  async function login(credentials) {
    const res = await loginApi(credentials)
    token.value = res.data.access_token
    refreshTokenVal.value = res.data.refresh_token
    user.value = res.data.user
    permissions.value = res.data.user.permissions || []
    localStorage.setItem('access_token', token.value)
    localStorage.setItem('refresh_token', refreshTokenVal.value)
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res.data
      permissions.value = res.data.permissions || []
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    refreshTokenVal.value = ''
    user.value = null
    permissions.value = []
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    token,
    refreshTokenVal,
    user,
    permissions,
    isLoggedIn,
    hasPermission,
    login,
    fetchUser,
    logout,
  }
})
