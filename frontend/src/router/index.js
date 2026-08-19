/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : index.js
 * @Project : intelligent-jet
 */
 * 
 * Vue Router 路由配置 - 含路由守卫和权限拦截
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { permission: 'user:read' },
      },
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('../views/Roles.vue'),
        meta: { permission: 'role:read' },
      },
      {
        path: 'permissions',
        name: 'Permissions',
        component: () => import('../views/Permissions.vue'),
        meta: { permission: 'permission:read' },
      },
      {
        path: 'three-d-operation',
        name: 'ThreeDOperation',
        component: () => import('../views/ThreeDOperation.vue'),
        meta: { permission: 'operation:read' },
      },
      {
        path: 'ptz-control',
        name: 'PtzControl',
        component: () => import('../views/PtzControl.vue'),
        meta: { permission: 'operation:read' },
      },
      {
        path: 'slm-monitor',
        name: 'SlmMonitor',
        component: () => import('../views/SlmMonitor.vue'),
        meta: { permission: 'operation:read' },
      },
    ],
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('../views/Forbidden.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.public) {
    return next()
  }

  if (!authStore.isLoggedIn) {
    return next('/login')
  }

  if (!authStore.user) {
    try {
      await authStore.fetchUser()
    } catch {
      return next('/login')
    }
  }

  if (to.meta.permission && !authStore.hasPermission(to.meta.permission)) {
    return next('/403')
  }

  next()
})

export default router
