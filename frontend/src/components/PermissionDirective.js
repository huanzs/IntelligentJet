/**
 * @Time    : 2026/8/19 10:00
 * @Author  : Jason Huan
 * @Email   : 549473121@qq.com
 * @File    : PermissionDirective.js
 * @Project : intelligent-jet
 */

import { useAuthStore } from '../stores/auth'

export const vPermission = {
  mounted(el, binding) {
    const authStore = useAuthStore()
    const required = binding.value
    if (required && !authStore.hasPermission(required)) {
      el.parentNode && el.parentNode.removeChild(el)
    }
  },
}
