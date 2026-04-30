/**
 * 文件作用：
 * - 管理聊天会话、消息列表和流式返回解析过程。
 * - 阅读这个文件时，建议先看整体结构，再看关键状态和交互逻辑。
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { agentApi } from '@/api'
import { ElMessage } from 'element-plus'

// 定义常量 SESSION_KEY，让后续代码共享同一份固定配置。
const SESSION_KEY = 'sales-agent-chat-sessions'
// 定义常量 STREAM_CHUNK_SIZE，控制前端打字机每次显示的字符数。
const STREAM_CHUNK_SIZE = 4
// 定义常量 STREAM_FRAME_MS，控制前端打字机刷新间隔。
const STREAM_FRAME_MS = 28

// 定义 deriveChartOption，负责当前文件中的一个主要状态、函数或导出能力。
function deriveChartOption(artifacts = []) {
  const artifact = artifacts.find((item) => item?.kind === 'echarts' && item?.option)
  return artifact?.option || null
}

// 定义 normalizeMessage，负责当前文件中的一个主要状态、函数或导出能力。
function normalizeMessage(message) {
  const artifacts = Array.isArray(message.artifacts)
    ? message.artifacts
    : message.chartOption
      ? [{ kind: 'echarts', slot: 'main_chart', option: message.chartOption }]
      : []

  return {
    ...message,
    artifacts,
    chartOption: deriveChartOption(artifacts),
    status: message.status === 'streaming' ? 'done' : message.status || 'done',
    streamStatus: '',
  }
}

// 定义 loadSessions，负责当前文件中的一个主要状态、函数或导出能力。
function loadSessions() {
  try {
    const sessions = JSON.parse(localStorage.getItem(SESSION_KEY) || '[]')
    return sessions.map((session) => ({
      ...session,
      messages: (session.messages || []).map(normalizeMessage),
    }))
  } catch {
    return []
  }
}

// 定义 saveSessions，负责当前文件中的一个主要状态、函数或导出能力。
function saveSessions(sessions) {
  try {
    const payload = sessions.map((session) => ({
      id: session.id,
      title: session.title,
      createdAt: session.createdAt,
      messages: session.messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        artifacts: msg.artifacts || [],
        status: msg.status === 'streaming' ? 'done' : msg.status,
      })),
    }))
    localStorage.setItem(SESSION_KEY, JSON.stringify(payload))
  } catch {
    // localStorage 不可写时静默处理
  }
}

// 定义 buildAuthHeaders，负责当前文件中的一个主要状态、函数或导出能力。
function buildAuthHeaders() {
  const token = localStorage.getItem('sales-agent-token') || ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 定义 parseArtifacts，负责当前文件中的一个主要状态、函数或导出能力。
function parseArtifacts(data) {
  try {
    const parsed = JSON.parse(data)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// 定义 parseSseBlock，负责把一个完整 SSE 事件块解析成 event/data。
function parseSseBlock(block) {
  const lines = block.split('\n')
  let event = 'message'
  const dataLines = []

  for (const rawLine of lines) {
    const line = rawLine.replace(/\r$/, '')
    if (!line || line.startsWith(':')) continue

    if (line.startsWith('event:')) {
      const value = line.slice(6)
      event = (value.startsWith(' ') ? value.slice(1) : value).trim() || 'message'
      continue
    }

    if (line.startsWith('data:')) {
      const value = line.slice(5)
      dataLines.push(value.startsWith(' ') ? value.slice(1) : value)
    }
  }

  return { event, data: dataLines.join('\n') }
}

// 定义 sleep，负责给前端打字机节奏提供轻量等待。
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// 定义 useChatStore，作为当前页面或模块共享状态的核心入口。
export const useChatStore = defineStore('chat', () => {
  const sessions = ref(loadSessions())
  const activeSessionId = ref(sessions.value[0]?.id || null)
  const isStreaming = ref(false)
  let abortController = null

  const activeSession = computed(
    () => sessions.value.find((session) => session.id === activeSessionId.value) || null
  )

  function createSession() {
    const id = `session-${Date.now()}`
    const session = {
      id,
      title: '新对话',
      createdAt: new Date().toISOString(),
      messages: [],
    }
    sessions.value.unshift(session)
    activeSessionId.value = id
    saveSessions(sessions.value)
    return session
  }

  function deleteSession(sessionId) {
    agentApi.clearSession(sessionId).catch(() => {})
    const index = sessions.value.findIndex((session) => session.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
    }
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = sessions.value[0]?.id || null
    }
    saveSessions(sessions.value)
  }

  function switchSession(sessionId) {
    activeSessionId.value = sessionId
  }

  function patchLastAssistant(sessionId, patch) {
    const session = sessions.value.find((item) => item.id === sessionId)
    if (!session) return
    for (let index = session.messages.length - 1; index >= 0; index -= 1) {
      const message = session.messages[index]
      if (message.role !== 'assistant') continue
      if (patch.content !== undefined) message.content = patch.content
      if (patch.artifacts !== undefined) {
        message.artifacts = patch.artifacts
        message.chartOption = deriveChartOption(patch.artifacts)
      }
      if (patch.status !== undefined) message.status = patch.status
      if (patch.streamStatus !== undefined) message.streamStatus = patch.streamStatus
      break
    }
  }

  async function sendMessage(text) {
    if (!text.trim() || isStreaming.value) return

    let session = activeSession.value
    if (!session) {
      session = createSession()
    }

    const sessionId = session.id
    const isFirstMessage = session.messages.length === 0

    session.messages.push({
      id: Date.now(),
      role: 'user',
      content: text,
      artifacts: [],
      chartOption: null,
      status: 'done',
    })
    if (isFirstMessage) {
      session.title = text.slice(0, 20)
    }

    session.messages.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      artifacts: [],
      chartOption: null,
      status: 'streaming',
      streamStatus: '正在分析问题...',
    })

    isStreaming.value = true
    abortController = new AbortController()

    let fullContent = ''
    let buffer = ''
    let pendingText = ''
    let flushPromise = null

    const flushTokenQueue = () => {
      if (flushPromise) return flushPromise
      flushPromise = (async () => {
        while (pendingText) {
          const nextText = pendingText.slice(0, STREAM_CHUNK_SIZE)
          pendingText = pendingText.slice(STREAM_CHUNK_SIZE)
          fullContent += nextText
          patchLastAssistant(sessionId, { content: fullContent, streamStatus: '' })
          await sleep(STREAM_FRAME_MS)
        }
        flushPromise = null
      })()
      return flushPromise
    }

    const enqueueToken = (data) => {
      if (!data) return
      pendingText += data
      flushTokenQueue()
    }

    try {
      const response = await fetch('/agent/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...buildAuthHeaders(),
        },
        body: JSON.stringify({ sessionId, message: text }),
        signal: abortController.signal,
      })

      if (response.status === 401) {
        const { useAuthStore } = await import('@/stores/auth')
        useAuthStore().clearAuth()
        const { default: router } = await import('@/router')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
        return
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      const handleSseEvent = ({ event, data }) => {
        if (event === 'token') {
          enqueueToken(data)
        } else if (event === 'status') {
          patchLastAssistant(sessionId, { streamStatus: data })
        } else if (event === 'artifacts') {
          patchLastAssistant(sessionId, { artifacts: parseArtifacts(data), streamStatus: '' })
        } else if (event === 'error') {
          ElMessage.error(data || '服务暂时不可用，请稍后重试')
          patchLastAssistant(sessionId, {
            content: data || '服务暂时不可用，请稍后重试。',
            status: 'error',
            streamStatus: '',
          })
        } else if (event === 'done') {
          patchLastAssistant(sessionId, { status: 'done', streamStatus: '' })
        }
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const blocks = buffer.split(/\n\n/)
        buffer = blocks.pop() ?? ''

        for (const block of blocks) {
          if (!block.trim()) continue
          handleSseEvent(parseSseBlock(block))
        }
      }

      if (buffer.trim()) {
        handleSseEvent(parseSseBlock(buffer))
      }

      if (flushPromise) {
        await flushPromise
      }
      patchLastAssistant(sessionId, { content: fullContent, status: 'done', streamStatus: '' })
    } catch (err) {
      if (err.name === 'AbortError') {
        patchLastAssistant(sessionId, { status: 'done', streamStatus: '' })
      } else {
        ElMessage.error('请求失败，请检查 Python 后端服务是否正常运行')
        patchLastAssistant(sessionId, {
          content: '请求失败，请检查 Python 后端服务是否正常运行。',
          status: 'error',
          streamStatus: '',
        })
      }
    } finally {
      isStreaming.value = false
      abortController = null
      saveSessions(sessions.value)
    }
  }

  function stopStreaming() {
    abortController?.abort()
  }

  return {
    sessions,
    activeSessionId,
    activeSession,
    isStreaming,
    createSession,
    deleteSession,
    switchSession,
    sendMessage,
    stopStreaming,
  }
})
