<!--
文件作用：
- 负责展示用户和 Agent 的聊天消息及附带图表。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

<template>
  <!-- 模板区域：负责当前页面或组件的界面结构和展示顺序 -->
  <div :class="['msg-row', msg.role]">
    <div v-if="msg.role === 'assistant'" class="avatar-wrap">
      <div class="avatar ai-avatar">
        <el-icon size="16"><Cpu /></el-icon>
      </div>
    </div>

    <div :class="['bubble-col', { 'has-chart': chartArtifacts.length > 0 || msg.chartOption }]">
      <div :class="['bubble', msg.role, { error: msg.status === 'error' }]">
        <div
          v-if="msg.role === 'assistant' && msg.status === 'streaming' && msg.streamStatus && !msg.content"
          class="stream-status"
        >
          <el-icon class="stream-status-icon" size="14"><Loading /></el-icon>
          <span>{{ msg.streamStatus }}</span>
        </div>

        <div v-else-if="msg.role === 'assistant' && msg.status === 'streaming' && !msg.content" class="typing-dots">
          <span></span><span></span><span></span>
        </div>

        <div v-if="msg.content" :class="msg.role === 'user' ? 'user-bubble' : ''">
          <div v-if="msg.role === 'assistant'" class="md-content" v-html="renderedContent"></div>
          <span v-else>{{ msg.content }}</span>
        </div>

        <span v-if="msg.role === 'assistant' && msg.status === 'streaming' && msg.content" class="cursor"></span>
      </div>

      <ChartRenderer
        v-for="(artifact, index) in chartArtifacts"
        :key="`${artifact.slot || 'chart'}-${index}`"
        :option="artifact.option"
      />
      <ChartRenderer v-if="!chartArtifacts.length && msg.chartOption" :option="msg.chartOption" />

      <div v-if="msg.role === 'assistant' && msg.status === 'done' && msg.content" class="msg-actions">
        <button class="action-btn" @click="copyContent" :title="copied ? '已复制' : '复制'">
          <el-icon size="13"><DocumentCopy /></el-icon>
          {{ copied ? '已复制' : '复制' }}
        </button>
      </div>
    </div>

    <div v-if="msg.role === 'user'" class="avatar-wrap">
      <div class="avatar user-avatar">
        {{ userInitial }}
      </div>
    </div>
  </div>
</template>

<script setup>
// 脚本区域：负责当前组件的状态管理、事件响应和接口交互。
import { computed, ref } from 'vue'
import MarkdownIt from 'markdown-it'
import { Cpu, DocumentCopy, Loading } from '@element-plus/icons-vue'

import ChartRenderer from './ChartRenderer.vue'
import { useAuthStore } from '@/stores/auth'

// 定义 props，负责当前文件中的一个主要状态、函数或导出能力。
const props = defineProps({
  msg: { type: Object, required: true },
})

// 定义 auth，负责当前文件中的一个主要状态、函数或导出能力。
const auth = useAuthStore()
// 定义 copied，负责当前文件中的一个主要状态、函数或导出能力。
const copied = ref(false)

// 定义 md，负责当前文件中的一个主要状态、函数或导出能力。
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
})

// 定义 renderedContent，负责当前文件中的一个主要状态、函数或导出能力。
const renderedContent = computed(() => md.render(props.msg.content || ''))
// 定义 chartArtifacts，负责当前文件中的一个主要状态、函数或导出能力。
const chartArtifacts = computed(() =>
  (props.msg.artifacts || []).filter((artifact) => artifact?.kind === 'echarts' && artifact?.option)
)

// 定义 userInitial，作为当前页面或模块共享状态的核心入口。
const userInitial = computed(() => {
  const name = auth.userInfo?.username || '我'
  return name.slice(-1)
})

// 定义 copyContent，负责当前文件中的一个主要状态、函数或导出能力。
async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.msg.content)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    // 忽略剪贴板失败
  }
}
</script>

<style scoped>
/* 样式区域：负责当前页面或组件的视觉呈现。 */
.msg-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 4px 0;
  animation: msgIn 0.2s ease;
}

.msg-row.user {
  flex-direction: row-reverse;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.avatar-wrap {
  flex-shrink: 0;
  padding-top: 2px;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: #fff;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.user-avatar {
  background: linear-gradient(135deg, #06B6D4, #0891B2);
  color: #fff;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.35);
}

.bubble-col {
  max-width: 74%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.bubble-col.has-chart {
  max-width: 92%;
  width: 92%;
}

.msg-row.user .bubble-col {
  align-items: flex-end;
}

.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
  position: relative;
}

.bubble.assistant {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top-left-radius: 4px;
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.bubble.user {
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: #fff;
  border-top-right-radius: 4px;
  box-shadow: 0 2px 12px rgba(79, 70, 229, 0.3);
}

.bubble.error {
  background: #FFF5F5;
  border-color: #FED7D7;
  color: #C53030;
}

.typing-dots {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: 4px 2px;
}

.stream-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-secondary);
  font-size: 13px;
}

.stream-status-icon {
  color: var(--primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.typing-dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: dot-bounce 1.3s ease infinite;
}

.typing-dots span:nth-child(2) { animation-delay: 0.18s; }
.typing-dots span:nth-child(3) { animation-delay: 0.36s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.msg-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.15s;
}

.msg-row:hover .msg-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  font-size: 12px;
  color: var(--text-muted);
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.action-btn:hover {
  color: var(--primary);
  border-color: var(--primary);
  background: var(--primary-light);
}
</style>
