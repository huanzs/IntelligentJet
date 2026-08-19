/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : users.js
 * @Project : intelligent-jet
 */

import http from './index'

export function getUsers(params) {
  return http.get('/api/users', { params })
}

export function getUser(id) {
  return http.get(`/api/users/${id}`)
}

export function createUser(data) {
  return http.post('/api/users', data)
}

export function updateUser(id, data) {
  return http.put(`/api/users/${id}`, data)
}

export function deleteUser(id) {
  return http.delete(`/api/users/${id}`)
}

export function assignUserRoles(id, role_ids) {
  return http.put(`/api/users/${id}/roles`, { role_ids })
}
