/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : permissions.js
 * @Project : intelligent-jet
 */
 * 
 * 权限管理 API 封装 - 列表查询和增删
 */

import http from './index'

export function getPermissions(params) {
  return http.get('/api/permissions', { params })
}

export function createPermission(data) {
  return http.post('/api/permissions', data)
}

export function deletePermission(id) {
  return http.delete(`/api/permissions/${id}`)
}
