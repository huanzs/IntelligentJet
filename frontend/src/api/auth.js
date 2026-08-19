/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : auth.js
 * @Project : intelligent-jet
 */

import http from './index'

export function login(data) {
  return http.post('/api/auth/login', data)
}

export function register(data) {
  return http.post('/api/auth/register', data)
}

export function refreshToken(refresh_token) {
  return http.post('/api/auth/refresh', { refresh_token })
}

export function getMe() {
  return http.get('/api/auth/me')
}
