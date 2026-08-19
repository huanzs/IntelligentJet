/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : roles.js
 * @Project : intelligent-jet
 */

import http from './index'

export function getRoles(params) {
  return http.get('/api/roles', { params })
}

export function getRole(id) {
  return http.get(`/api/roles/${id}`)
}

export function createRole(data) {
  return http.post('/api/roles', data)
}

export function updateRole(id, data) {
  return http.put(`/api/roles/${id}`, data)
}

export function deleteRole(id) {
  return http.delete(`/api/roles/${id}`)
}

export function assignRolePermissions(id, permission_ids) {
  return http.put(`/api/roles/${id}/permissions`, { permission_ids })
}
