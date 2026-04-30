/**
 * 文件作用：
 * - 统一封装前端请求逻辑，管理 token 注入和接口调用方法。
 * - 阅读这个文件时，建议先看整体结构，再看关键状态和交互逻辑。
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

// 定义 http，负责当前文件中的一个主要状态、函数或导出能力。
const http = axios.create({
  baseURL: '/',
  timeout: 90000,
})

// 定义 getToken，负责当前文件中的一个主要状态、函数或导出能力。
function getToken() {
  return localStorage.getItem('sales-agent-token') || ''
}

// 定义 extractErrorMessage，负责当前文件中的一个主要状态、函数或导出能力。
function extractErrorMessage(err) {
  return (
    err.response?.data?.error ||
    err.response?.data?.detail ||
    err.response?.data?.message ||
    ''
  )
}

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err.response?.status
    const message = extractErrorMessage(err)

    if (status === 401) {
      const { useAuthStore } = await import('@/stores/auth')
      useAuthStore().clearAuth()
      const { default: router } = await import('@/router')
      router.push('/login')
      ElMessage.error(message || '登录已过期，请重新登录')
    } else if (status === 403) {
      ElMessage.error(message || '权限不足')
    } else {
      ElMessage.error(message || '网络请求失败')
    }
    return Promise.reject(err)
  }
)

// 定义 authApi，负责当前文件中的一个主要状态、函数或导出能力。
export const authApi = {
  login: (data) => http.post('/auth/login', data),
  logout: () => http.post('/auth/logout'),
}

// 定义 agentApi，负责当前文件中的一个主要状态、函数或导出能力。
export const agentApi = {
  chat: (data) => http.post('/agent/chat', data),
  clearSession: (sessionId) => http.delete(`/agent/session/${sessionId}`),
  metrics: () => http.get('/ops/metrics'),
  health: () => http.get('/health'),
}

export default http
