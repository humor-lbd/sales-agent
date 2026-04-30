<!--
文件作用：
- 展示后端运行指标，帮助观察性能和稳定性。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

<template>
  <!-- 模板区域：负责当前页面或组件的界面结构和展示顺序 -->
  <el-drawer
    :model-value="modelValue"
    title="运行时指标"
    size="480px"
    @close="emit('update:modelValue', false)"
  >
    <div class="metrics-layout">
      <div class="metrics-actions">
        <el-tag type="info" round>Python Backend</el-tag>
        <el-button size="small" :loading="loading" @click="refreshMetrics">刷新</el-button>
      </div>

      <div v-if="loading && !metrics" class="metrics-skeleton">
        <el-skeleton :rows="8" animated />
      </div>

      <div v-else-if="error" class="metrics-empty">
        <el-empty :description="error" />
      </div>

      <div v-else-if="metrics" class="metrics-body">
        <div class="summary-grid">
          <div class="summary-card">
            <p class="summary-label">服务运行时长</p>
            <p class="summary-value">{{ metrics.uptimeSeconds }}s</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">请求总数</p>
            <p class="summary-value">{{ metrics.requests.total }}</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">MySQL 查询</p>
            <p class="summary-value">{{ metrics.database.queryCount }}</p>
            <p class="summary-sub">avg {{ metrics.database.avgMs }}ms</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">Redis 命中率</p>
            <p class="summary-value">{{ formatPercent(metrics.cache.hitRate) }}</p>
            <p class="summary-sub">{{ metrics.cache.hits }} hit / {{ metrics.cache.misses }} miss</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">LLM 调用</p>
            <p class="summary-value">{{ metrics.llm.syncCalls + metrics.llm.streamCalls + metrics.llm.toolLoopCalls }}</p>
            <p class="summary-sub">avg {{ metrics.llm.avgMs }}ms</p>
          </div>
          <div class="summary-card">
            <p class="summary-label">首 Token</p>
            <p class="summary-value">{{ metrics.llm.avgFirstTokenMs }}ms</p>
            <p class="summary-sub">max {{ metrics.llm.maxFirstTokenMs }}ms</p>
          </div>
        </div>

        <section class="metrics-section">
          <div class="section-head">
            <h4>请求路径</h4>
            <el-tag size="small" type="success">实时快照</el-tag>
          </div>
          <div v-if="requestEntries.length" class="kv-list">
            <div v-for="[path, value] in requestEntries" :key="path" class="kv-item">
              <div>
                <p class="kv-title">{{ path }}</p>
                <p class="kv-sub">{{ value.count }} 次 · avg {{ value.avgMs }}ms · max {{ value.maxMs }}ms</p>
              </div>
              <el-tag size="small">{{ Object.keys(value.statuses).join(', ') }}</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无请求数据" :image-size="56" />
        </section>

        <section class="metrics-section">
          <div class="section-head">
            <h4>Tool 调用</h4>
            <el-tag size="small" type="warning">函数调用</el-tag>
          </div>
          <div v-if="toolEntries.length" class="kv-list">
            <div v-for="[tool, value] in toolEntries" :key="tool" class="kv-item">
              <div>
                <p class="kv-title">{{ tool }}</p>
                <p class="kv-sub">{{ value.count }} 次 · avg {{ value.avgMs }}ms · max {{ value.maxMs }}ms</p>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无工具调用" :image-size="56" />
        </section>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
// 脚本区域：负责当前组件的状态管理、事件响应和接口交互。
import { computed, ref, watch } from 'vue'

import { agentApi } from '@/api'

// 定义 props，负责当前文件中的一个主要状态、函数或导出能力。
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

// 定义 emit，负责当前文件中的一个主要状态、函数或导出能力。
const emit = defineEmits(['update:modelValue'])

// 定义 loading，负责当前文件中的一个主要状态、函数或导出能力。
const loading = ref(false)
// 定义 metrics，负责当前文件中的一个主要状态、函数或导出能力。
const metrics = ref(null)
// 定义 error，负责当前文件中的一个主要状态、函数或导出能力。
const error = ref('')

// 定义 requestEntries，负责当前文件中的一个主要状态、函数或导出能力。
const requestEntries = computed(() => Object.entries(metrics.value?.requests?.byPath || {}))
// 定义 toolEntries，负责当前文件中的一个主要状态、函数或导出能力。
const toolEntries = computed(() => Object.entries(metrics.value?.tools || {}))

// 定义 formatPercent，负责当前文件中的一个主要状态、函数或导出能力。
function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`
}

// 定义 refreshMetrics，负责当前文件中的一个主要状态、函数或导出能力。
async function refreshMetrics() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await agentApi.metrics()
    metrics.value = data
  } catch {
    error.value = '指标获取失败，请确认 Python 后端已启动'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      refreshMetrics()
    }
  }
)
</script>

<style scoped>
/* 样式区域：负责当前页面或组件的视觉呈现。 */
.metrics-layout {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.metrics-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metrics-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.summary-label {
  font-size: 12px;
  color: var(--text-muted);
}

.summary-value {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary-sub {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.metrics-section {
  padding: 14px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-head h4 {
  font-size: 14px;
}

.kv-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kv-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #F8FAFC;
  border: 1px solid #E5E7EB;
}

.kv-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-all;
}

.kv-sub {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.metrics-empty {
  padding-top: 20px;
}
</style>
