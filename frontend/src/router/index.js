/**
 * 文件作用：
 * - 定义页面路由和基础登录守卫逻辑。
 * - 阅读这个文件时，建议先看整体结构，再看关键状态和交互逻辑。
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 定义 routes，负责当前文件中的一个主要状态、函数或导出能力。
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

// 定义 router，负责当前文件中的一个主要状态、函数或导出能力。
const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'Login' }
  }
  if (to.name === 'Login' && auth.isLoggedIn) {
    return { name: 'Chat' }
  }
})

export default router
