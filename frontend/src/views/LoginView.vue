<!--
文件作用：
- 提供登录页和访客模式入口，作为前端第一屏。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

<template>
  <!-- 模板区域：负责当前页面或组件的界面结构和展示顺序 -->
  <div class="login-page">
    <div class="login-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <div class="login-card">
      <div class="logo-area">
        <div class="logo-icon">
          <el-icon size="28" color="#fff"><TrendCharts /></el-icon>
        </div>
        <div>
          <h1 class="brand">JiChi AI</h1>
          <p class="brand-sub">销售数据分析平台 · Python Edition</p>
        </div>
      </div>

      <div class="card-body">
        <h2 class="card-title">欢迎回来</h2>
        <p class="card-desc">登录您的账号以继续使用 Python 版 AI 分析助手</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="销售代表 ID" prop="repId">
            <el-input
              v-model="form.repId"
              type="number"
              placeholder="请输入您的销售代表 ID（如：1、2、13）"
              size="large"
              :prefix-icon="User"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>

          <el-button
            plain
            size="large"
            class="guest-btn"
            @click="enterGuest"
          >
            本地直达
          </el-button>
        </el-form>

        <div class="quick-logins">
          <p class="quick-label">快速体验账号</p>
          <div class="quick-btns">
            <el-tag
              v-for="demo in demoAccounts"
              :key="demo.repId"
              class="demo-tag"
              @click="quickLogin(demo)"
            >
              {{ demo.label }}
            </el-tag>
          </div>
          <p class="quick-tip">如果后端 `AUTH_ENABLED=false`，也可以直接点“本地直达”。</p>
        </div>
      </div>
    </div>

    <p class="footer-tip">Powered by FastAPI · OpenAI SDK · Vue 3</p>
  </div>
</template>

<script setup>
// 脚本区域：负责当前组件的状态管理、事件响应和接口交互。
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, TrendCharts } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'

// 定义 auth，负责当前文件中的一个主要状态、函数或导出能力。
const auth = useAuthStore()
// 定义 router，负责当前文件中的一个主要状态、函数或导出能力。
const router = useRouter()
// 定义 formRef，负责当前文件中的一个主要状态、函数或导出能力。
const formRef = ref(null)
// 定义 loading，负责当前文件中的一个主要状态、函数或导出能力。
const loading = ref(false)

// 定义 form，负责当前文件中的一个主要状态、函数或导出能力。
const form = reactive({ repId: '' })

// 定义 rules，负责当前文件中的一个主要状态、函数或导出能力。
const rules = {
  repId: [{ required: true, message: '请输入销售代表 ID', trigger: 'blur' }],
}

// 定义 demoAccounts，负责当前文件中的一个主要状态、函数或导出能力。
const demoAccounts = [
  { label: '大区经理 - 王芳', repId: 1 },
  { label: '销售代表 - 张三', repId: 2 },
  { label: '销售总监 - 赵六', repId: 13 },
]

// 定义 quickLogin，负责当前文件中的一个主要状态、函数或导出能力。
function quickLogin(demo) {
  form.repId = demo.repId
  handleLogin()
}

// 定义 enterGuest，负责当前文件中的一个主要状态、函数或导出能力。
function enterGuest() {
  auth.enterGuestMode()
  ElMessage.success('已进入本地体验模式')
  router.push('/')
}

// 定义 handleLogin，负责当前文件中的一个主要状态、函数或导出能力。
async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(Number(form.repId))
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 样式区域：负责当前页面或组件的视觉呈现。 */
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #0F172A;
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.25;
}

.orb-1 {
  width: 480px;
  height: 480px;
  background: #4F46E5;
  top: -120px;
  right: -80px;
  animation: float 8s ease-in-out infinite;
}

.orb-2 {
  width: 360px;
  height: 360px;
  background: #7C3AED;
  bottom: -60px;
  left: -60px;
  animation: float 10s ease-in-out infinite reverse;
}

.orb-3 {
  width: 240px;
  height: 240px;
  background: #06B6D4;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: float3 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

@keyframes float3 {
  0%, 100% { transform: translate(-50%, -50%) translateY(0); }
  50% { transform: translate(-50%, -50%) translateY(-20px); }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 440px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.4);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 28px 32px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(79, 70, 229, 0.4);
}

.brand {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.brand-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.card-body {
  padding: 28px 32px 32px;
}

.card-title {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
}

.card-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 24px;
}

:deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.7) !important;
  font-size: 13px;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  box-shadow: none !important;
  border-radius: 10px;
}

:deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.25) !important;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #4F46E5 !important;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2) !important;
}

:deep(.el-input__inner) {
  color: #fff !important;
  background: transparent !important;
}

:deep(.el-input__prefix-inner .el-icon) {
  color: rgba(255, 255, 255, 0.35);
}

.login-btn,
.guest-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  margin-top: 10px;
  border-radius: 10px;
}

.login-btn {
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  border: none;
  letter-spacing: 2px;
  box-shadow: 0 4px 20px rgba(79, 70, 229, 0.4);
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 24px rgba(79, 70, 229, 0.5);
}

.guest-btn {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.85);
}

.guest-btn:hover {
  border-color: rgba(255, 255, 255, 0.35);
  color: #fff;
}

.quick-logins {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.quick-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  margin-bottom: 10px;
}

.quick-btns {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.demo-tag {
  cursor: pointer;
  background: rgba(79, 70, 229, 0.15);
  border-color: rgba(79, 70, 229, 0.3);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
  font-size: 12px;
  transition: all 0.2s;
}

.demo-tag:hover {
  background: rgba(79, 70, 229, 0.3);
  border-color: rgba(79, 70, 229, 0.6);
  color: #fff;
}

.quick-tip {
  margin-top: 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.28);
}

.footer-tip {
  position: relative;
  z-index: 1;
  margin-top: 24px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.2);
}

@media (max-width: 540px) {
  .login-card {
    width: calc(100vw - 32px);
  }
}
</style>
