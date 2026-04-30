<!--
文件作用：
- 组合聊天页面的主要布局、交互和快捷入口。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

<template>
  <!-- 模板区域：负责当前页面或组件的界面结构和展示顺序 -->
  <div class="chat-layout">
    <aside :class="['sidebar', { collapsed: sidebarCollapsed }]">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <el-icon size="18" color="#fff"><TrendCharts /></el-icon>
        </div>
        <transition name="slide-fade">
          <span v-if="!sidebarCollapsed" class="brand-text">Python Agent</span>
        </transition>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon size="14">
            <component :is="sidebarCollapsed ? 'Expand' : 'Fold'" />
          </el-icon>
        </button>
      </div>

      <div class="sidebar-new">
        <button class="new-chat-btn" @click="newChat" :title="sidebarCollapsed ? '新对话' : ''">
          <el-icon size="15"><Plus /></el-icon>
          <span v-if="!sidebarCollapsed">新对话</span>
        </button>
      </div>

      <div class="session-list" v-if="!sidebarCollapsed">
        <p class="list-label">历史对话</p>
        <div
          v-for="session in chat.sessions"
          :key="session.id"
          :class="['session-item', { active: session.id === chat.activeSessionId }]"
          @click="chat.switchSession(session.id)"
        >
          <el-icon size="13" class="session-icon"><ChatLineRound /></el-icon>
          <span class="session-title">{{ session.title }}</span>
          <button class="del-btn" @click.stop="confirmDelete(session.id)" title="删除">
            <el-icon size="12"><Delete /></el-icon>
          </button>
        </div>
        <div v-if="chat.sessions.length === 0" class="empty-sessions">
          暂无对话记录
        </div>
      </div>

      <div class="quick-section" v-if="!sidebarCollapsed">
        <p class="list-label">快捷提问</p>
        <div
          v-for="question in quickQuestions"
          :key="question.text"
          class="quick-item"
          @click="sendQuick(question.text)"
        >
          <span class="quick-emoji">{{ question.icon }}</span>
          <span class="quick-text">{{ question.text }}</span>
        </div>
      </div>

      <div :class="['sidebar-user', { collapsed: sidebarCollapsed }]">
        <div class="user-avatar">{{ userInitial }}</div>
        <div v-if="!sidebarCollapsed" class="user-meta">
          <p class="user-name">{{ auth.userInfo?.username }}</p>
          <p class="user-role">{{ roleLabel }}</p>
        </div>
        <button v-if="!sidebarCollapsed" class="logout-btn" @click="auth.logout()" title="退出">
          <el-icon size="14"><SwitchButton /></el-icon>
        </button>
      </div>
    </aside>

    <main class="chat-main">
      <header class="chat-header">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="16" color="#4F46E5"><Cpu /></el-icon>
          </div>
          <div>
            <h2 class="header-title">销售数据分析助手</h2>
            <p class="header-sub">FastAPI · OpenAI SDK · 通义千问</p>
          </div>
        </div>
        <div class="header-right">
          <el-tag v-if="auth.guestMode" size="small" effect="plain">本地体验模式</el-tag>
          <el-tag v-if="chat.isStreaming" type="success" size="small" class="streaming-tag">
            <el-icon class="spinning"><Loading /></el-icon>
            AI 思考中
          </el-tag>
          <el-button size="small" plain :icon="DataBoard" @click="metricsVisible = true">运行指标</el-button>
          <el-button
            v-if="chat.activeSession"
            size="small"
            plain
            :icon="Delete"
            @click="clearCurrentSession"
            class="clear-btn"
          >
            清空记忆
          </el-button>
        </div>
      </header>

      <div class="messages-container" ref="messagesEl" @scroll="handleMessagesScroll">
        <div v-if="!chat.activeSession || chat.activeSession.messages.length === 0" class="welcome">
          <div class="welcome-icon">
            <el-icon size="36" color="#4F46E5"><TrendCharts /></el-icon>
          </div>
          <h3 class="welcome-title">你好，{{ auth.userInfo?.username || '朋友' }} 👋</h3>
          <p class="welcome-desc">
            我是 Python 版 AI 销售数据分析助手，可以帮你查询销售数据、生成图表、发现异常，还能查看运行时指标。
          </p>
          <div class="welcome-cards">
            <div
              v-for="card in welcomeCards"
              :key="card.text"
              class="welcome-card"
              @click="sendQuick(card.text)"
            >
              <div class="wc-icon">{{ card.icon }}</div>
              <div class="wc-text">{{ card.text }}</div>
            </div>
          </div>
        </div>

        <div v-else class="message-list">
          <MessageBubble
            v-for="msg in chat.activeSession.messages"
            :key="msg.id"
            :msg="msg"
          />
        </div>

        <button
          v-if="showJumpToBottom"
          class="jump-bottom-btn"
          @click="jumpToBottom"
        >
          <el-icon size="14"><ArrowDown /></el-icon>
          <span>回到底部</span>
        </button>
      </div>

      <div class="input-area">
        <div class="input-row">
          <el-input
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 5 }"
            placeholder="问我关于销售数据的任何问题… (Enter 发送，Shift+Enter 换行)"
            resize="none"
            class="chat-input"
            :disabled="chat.isStreaming"
            @keydown.enter.exact.prevent="handleSend"
          />
          <div class="send-btns">
            <el-button
              v-if="chat.isStreaming"
              type="danger"
              :icon="VideoPause"
              circle
              @click="chat.stopStreaming()"
              title="停止生成"
              class="stop-btn"
            />
            <el-button
              v-else
              type="primary"
              :icon="Promotion"
              circle
              :disabled="!inputText.trim()"
              @click="handleSend"
              class="send-btn-circle"
            />
          </div>
        </div>
        <p class="input-hint">AI 可能产生错误，重要决策请以实际数据为准</p>
      </div>
    </main>

    <MetricsDrawer v-model="metricsVisible" />
  </div>
</template>

<script setup>
// 脚本区域：负责当前组件的状态管理、事件响应和接口交互。
import { computed, nextTick, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  ChatLineRound,
  Cpu,
  DataBoard,
  Delete,
  Expand,
  Fold,
  Loading,
  Plus,
  Promotion,
  SwitchButton,
  TrendCharts,
  VideoPause,
} from '@element-plus/icons-vue'

import { agentApi } from '@/api'
import MessageBubble from '@/components/MessageBubble.vue'
import MetricsDrawer from '@/components/MetricsDrawer.vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

// 定义 auth，负责当前文件中的一个主要状态、函数或导出能力。
const auth = useAuthStore()
// 定义 chat，负责当前文件中的一个主要状态、函数或导出能力。
const chat = useChatStore()

// 定义 inputText，负责当前文件中的一个主要状态、函数或导出能力。
const inputText = ref('')
// 定义 messagesEl，负责当前文件中的一个主要状态、函数或导出能力。
const messagesEl = ref(null)
// 定义 sidebarCollapsed，负责当前文件中的一个主要状态、函数或导出能力。
const sidebarCollapsed = ref(false)
// 定义 metricsVisible，负责当前文件中的一个主要状态、函数或导出能力。
const metricsVisible = ref(false)
const autoScrollEnabled = ref(true)
const showJumpToBottom = ref(false)
const BOTTOM_THRESHOLD = 80

// 定义 userInitial，作为当前页面或模块共享状态的核心入口。
const userInitial = computed(() => {
  const name = auth.userInfo?.username || '我'
  return name.slice(-1)
})

// 定义 roleLabel，负责当前文件中的一个主要状态、函数或导出能力。
const roleLabel = computed(() => {
  const role = auth.userInfo?.role
  const map = {
    SALES_DIRECTOR: '销售总监',
    SALES_MANAGER: '大区经理',
    SALES_REP: '销售代表',
    LOCAL_DEV: '开发体验',
  }
  return map[role] || role || '销售代表'
})

// 定义 quickQuestions，负责当前文件中的一个主要状态、函数或导出能力。
const quickQuestions = [
  { icon: '📈', text: '近6个月销售趋势' },
  { icon: '🏆', text: '本季度Top5销售员' },
  { icon: '🗺️', text: '各大区销售排名' },
  { icon: '⚠️', text: '有没有销售异常' },
  { icon: '📦', text: '最畅销产品Top10' },
  { icon: '💰', text: '本月华东区销售额是多少？' },
]

// 定义 welcomeCards，负责当前文件中的一个主要状态、函数或导出能力。
const welcomeCards = [
  { icon: '📊', text: '近6个月销售趋势，生成折线图' },
  { icon: '🏆', text: '第四季度各大区销售排名' },
  { icon: '⚠️', text: '最近销售数据有没有异常' },
  { icon: '🧭', text: '本月华东区销售额是多少？' },
]

function isNearBottom() {
  if (!messagesEl.value) return true
  const { scrollHeight, scrollTop, clientHeight } = messagesEl.value
  return scrollHeight - scrollTop - clientHeight <= BOTTOM_THRESHOLD
}

function handleMessagesScroll() {
  const nearBottom = isNearBottom()
  autoScrollEnabled.value = nearBottom
  showJumpToBottom.value = !nearBottom && !!chat.activeSession?.messages?.length
}

// 定义 scrollToBottom，负责当前文件中的一个主要状态、函数或导出能力。
function scrollToBottom(smooth = true, force = false) {
  nextTick(() => {
    if (!messagesEl.value) return
    if (!force && !autoScrollEnabled.value) return
    messagesEl.value.scrollTo({
      top: messagesEl.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    })
    showJumpToBottom.value = false
  })
}

function jumpToBottom() {
  autoScrollEnabled.value = true
  scrollToBottom(true, true)
}

watch(
  () => chat.activeSession?.messages?.length,
  () => scrollToBottom()
)

watch(
  () => {
    const messages = chat.activeSession?.messages
    if (!messages?.length) return ''
    const last = messages[messages.length - 1]
    return last?.role === 'assistant' ? last.content : ''
  },
  () => scrollToBottom(false)
)

// 定义 handleSend，负责当前文件中的一个主要状态、函数或导出能力。
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || chat.isStreaming) return
  inputText.value = ''
  if (!chat.activeSession) {
    chat.createSession()
  }
  autoScrollEnabled.value = true
  showJumpToBottom.value = false
  await chat.sendMessage(text)
}

// 定义 sendQuick，负责当前文件中的一个主要状态、函数或导出能力。
function sendQuick(text) {
  if (chat.isStreaming) return
  if (!chat.activeSession) {
    chat.createSession()
  }
  autoScrollEnabled.value = true
  showJumpToBottom.value = false
  chat.sendMessage(text)
}

// 定义 newChat，负责当前文件中的一个主要状态、函数或导出能力。
function newChat() {
  chat.createSession()
}

watch(
  () => chat.activeSessionId,
  () => {
    autoScrollEnabled.value = true
    showJumpToBottom.value = false
    scrollToBottom(false, true)
  }
)

// 定义 confirmDelete，负责当前文件中的一个主要状态、函数或导出能力。
function confirmDelete(sessionId) {
  ElMessageBox.confirm('确认删除这条对话记录？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger',
  }).then(() => {
    chat.deleteSession(sessionId)
  }).catch(() => {})
}

// 定义 clearCurrentSession，负责当前文件中的一个主要状态、函数或导出能力。
async function clearCurrentSession() {
  if (!chat.activeSession) return
  const confirmed = await ElMessageBox.confirm(
    '清空后 AI 将忘记本次对话上下文，是否继续？',
    '清空记忆',
    {
      confirmButtonText: '确认清空',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).catch(() => null)

  if (!confirmed) return

  try {
    await agentApi.clearSession(chat.activeSession.id)
    ElMessage.success('对话记忆已清空')
  } catch {
    ElMessage.error('清空失败')
  }
}
</script>

<style scoped>
/* 样式区域：负责当前页面或组件的视觉呈现。 */
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-page);
}

.sidebar {
  width: 260px;
  min-width: 260px;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, min-width 0.25s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
  min-width: 64px;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  position: relative;
}

.sidebar.collapsed .sidebar-brand {
  justify-content: center;
}

.sidebar.collapsed .collapse-btn {
  position: absolute;
  right: 8px;
  top: 20px;
  margin-left: 0;
}

.brand-logo {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  flex: 1;
  white-space: nowrap;
}

.collapse-btn {
  margin-left: auto;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(255,255,255,0.1);
  color: #fff;
}

.sidebar-new {
  padding: 12px 12px 6px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 9px 12px;
  background: rgba(79, 70, 229, 0.2);
  border: 1px solid rgba(79, 70, 229, 0.35);
  border-radius: 9px;
  color: #A5B4FC;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.new-chat-btn:hover {
  background: rgba(79, 70, 229, 0.35);
  color: #fff;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}

.list-label {
  font-size: 11px;
  color: rgba(255,255,255,0.25);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 10px 6px 4px;
  font-weight: 600;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  color: rgba(255,255,255,0.55);
  font-size: 13px;
}

.session-item:hover {
  background: var(--sidebar-hover);
  color: rgba(255,255,255,0.85);
}

.session-item.active {
  background: var(--sidebar-active);
  color: #fff;
  border: 1px solid rgba(79,70,229,0.3);
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.del-btn {
  display: none;
  width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: 4px;
  color: rgba(255,255,255,0.35);
  cursor: pointer;
  padding: 0;
}

.session-item:hover .del-btn {
  display: flex;
}

.del-btn:hover {
  background: rgba(239,68,68,0.2);
  color: #F87171;
}

.empty-sessions {
  font-size: 12px;
  color: rgba(255,255,255,0.2);
  text-align: center;
  padding: 20px 0;
}

.quick-section {
  padding: 0 8px;
  border-top: 1px solid rgba(255,255,255,0.06);
  padding-top: 4px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 7px;
  cursor: pointer;
  transition: background 0.15s;
  color: rgba(255,255,255,0.45);
  font-size: 12px;
}

.quick-item:hover {
  background: var(--sidebar-hover);
  color: rgba(255,255,255,0.75);
}

.quick-emoji {
  font-size: 14px;
  flex-shrink: 0;
}

.quick-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 14px;
  border-top: 1px solid rgba(255,255,255,0.06);
}

.sidebar-user.collapsed {
  justify-content: center;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06B6D4, #0891B2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-meta {
  flex: 1;
  overflow: hidden;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
}

.logout-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 7px;
  color: rgba(255,255,255,0.35);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}

.logout-btn:hover {
  background: rgba(239,68,68,0.15);
  border-color: rgba(239,68,68,0.3);
  color: #F87171;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 38px;
  height: 38px;
  background: var(--primary-light);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.header-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.streaming-tag {
  animation: pulse 1.5s ease infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  position: relative;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 860px;
  margin: 0 auto;
}

.jump-bottom-btn {
  position: sticky;
  bottom: 14px;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 6px;
  width: max-content;
  margin: 12px auto 0;
  padding: 7px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--primary);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
}

.jump-bottom-btn:hover {
  border-color: var(--primary);
  background: var(--primary-light);
}

.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 200px);
  text-align: center;
  padding: 40px 20px;
}

.welcome-icon {
  width: 72px;
  height: 72px;
  background: var(--primary-light);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(79, 70, 229, 0.15);
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.welcome-desc {
  font-size: 14px;
  color: var(--text-secondary);
  max-width: 560px;
  line-height: 1.7;
  margin-bottom: 32px;
}

.welcome-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 560px;
  width: 100%;
}

.welcome-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.welcome-card:hover {
  border-color: var(--primary);
  background: var(--primary-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.wc-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.wc-text {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  line-height: 1.4;
}

.welcome-card:hover .wc-text {
  color: var(--primary);
}

.input-area {
  padding: 16px 24px 20px;
  background: var(--bg-card);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  max-width: 860px;
  margin: 0 auto;
}

:deep(.chat-input .el-textarea__inner) {
  border-radius: 12px;
  border-color: var(--border);
  padding: 12px 16px;
  font-size: 14px;
  resize: none;
  font-family: var(--font-sans);
  line-height: 1.6;
  transition: border-color 0.15s, box-shadow 0.15s;
}

:deep(.chat-input .el-textarea__inner:focus) {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
}

.send-btns {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  padding-bottom: 2px;
}

.send-btn-circle,
.stop-btn {
  width: 40px;
  height: 40px;
}

.input-hint {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 8px;
  max-width: 860px;
  margin-left: auto;
  margin-right: auto;
}

.slide-fade-enter-active {
  transition: all 0.2s ease;
}

.slide-fade-leave-active {
  transition: all 0.15s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}

@media (max-width: 980px) {
  .welcome-cards {
    grid-template-columns: 1fr;
  }

  .header-right {
    gap: 6px;
  }
}

@media (max-width: 760px) {
  .sidebar {
    display: none;
  }

  .chat-header,
  .messages-container,
  .input-area {
    padding-left: 14px;
    padding-right: 14px;
  }
}
</style>
