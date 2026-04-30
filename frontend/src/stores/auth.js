/**
 * 文件作用：
 * - 管理前端登录状态、用户信息和访客模式。
 * - 阅读这个文件时，建议先看整体结构，再看关键状态和交互逻辑。
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '@/api'

// 定义常量 TOKEN_KEY，让后续代码共享同一份固定配置。
const TOKEN_KEY = 'sales-agent-token'
// 定义 USER_KEY，作为当前页面或模块共享状态的核心入口。
const USER_KEY = 'sales-agent-user'
// 定义常量 GUEST_KEY，让后续代码共享同一份固定配置。
const GUEST_KEY = 'sales-agent-guest'

// 定义 loadJson，负责当前文件中的一个主要状态、函数或导出能力。
function loadJson(key) {
  try {
    const raw = localStorage.getItem(key)
    return raw && raw !== 'undefined' ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

// 定义 useAuthStore，作为当前页面或模块共享状态的核心入口。
export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(loadJson(USER_KEY))
  const guestMode = ref(localStorage.getItem(GUEST_KEY) === '1')

  const isLoggedIn = computed(() => guestMode.value || (!!token.value && !!userInfo.value))

  async function login(repId) {
    const res = await authApi.login({ repId })
    const data = res.data
    token.value = data.token
    userInfo.value = {
      username: data.username,
      role: data.role,
    }
    guestMode.value = false
    localStorage.setItem(TOKEN_KEY, token.value)
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo.value))
    localStorage.removeItem(GUEST_KEY)
    return data
  }

  function enterGuestMode() {
    token.value = ''
    userInfo.value = {
      username: '本地体验',
      role: 'LOCAL_DEV',
    }
    guestMode.value = true
    localStorage.removeItem(TOKEN_KEY)
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo.value))
    localStorage.setItem(GUEST_KEY, '1')
  }

  function clearAuth() {
    token.value = ''
    userInfo.value = null
    guestMode.value = false
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(GUEST_KEY)
  }

  async function logout() {
    try {
      if (!guestMode.value) {
        await authApi.logout()
      }
    } finally {
      clearAuth()
      const { default: router } = await import('@/router')
      router.push('/login')
    }
  }

  return {
    token,
    userInfo,
    guestMode,
    isLoggedIn,
    login,
    logout,
    clearAuth,
    enterGuestMode,
  }
})
