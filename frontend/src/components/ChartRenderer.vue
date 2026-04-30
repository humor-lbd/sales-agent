<!--
文件作用：
- 负责接收后端图表产物并渲染为 ECharts 图表。
- 阅读这个文件时，可以先看整体结构，再逐节理解细节。
-->

<template>
  <!-- 模板区域：负责当前页面或组件的界面结构和展示顺序 -->
  <div class="chart-wrapper">
    <div ref="chartEl" class="chart-canvas"></div>
    <div v-if="renderError" class="chart-error">{{ renderError }}</div>
  </div>
</template>

<script setup>
// 脚本区域：负责当前组件的状态管理、事件响应和接口交互。
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

// 定义 props，负责当前文件中的一个主要状态、函数或导出能力。
const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
})

// 定义 chartEl，负责当前文件中的一个主要状态、函数或导出能力。
const chartEl = ref(null)
// 定义 renderError，负责当前文件中的一个主要状态、函数或导出能力。
const renderError = ref('')
let chart = null

// 定义 defaultOption，负责当前文件中的一个主要状态、函数或导出能力。
const defaultOption = {
  backgroundColor: 'transparent',
  textStyle: { fontFamily: 'inherit', color: '#334155' },
  grid: { top: 40, right: 20, bottom: 40, left: 50, containLabel: true },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(15,23,42,0.9)',
    borderColor: 'rgba(255,255,255,0.1)',
    textStyle: { color: '#e2e8f0', fontSize: 13 },
    extraCssText: 'border-radius:10px;padding:10px 14px;box-shadow:0 8px 32px rgba(0,0,0,0.3)',
  },
  color: ['#4F46E5', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
}

// 定义 mergeOption，负责当前文件中的一个主要状态、函数或导出能力。
function mergeOption(base, override) {
  const result = { ...base, ...override }
  if (base.textStyle && override.textStyle) {
    result.textStyle = { ...base.textStyle, ...override.textStyle }
  }
  if (base.tooltip && override.tooltip) {
    result.tooltip = { ...base.tooltip, ...override.tooltip }
  }
  if (!override.grid) {
    result.grid = base.grid
  }
  return result
}

// 定义 buildSafeOption，负责当前文件中的一个主要状态、函数或导出能力。
function buildSafeOption(option) {
  if (!option || typeof option !== 'object') {
    return null
  }

  const nextOption = {
    ...option,
  }

  if (nextOption.series && !Array.isArray(nextOption.series)) {
    nextOption.series = [nextOption.series]
  }

  if (Array.isArray(nextOption.series)) {
    nextOption.series = nextOption.series.filter(
      (seriesItem) => seriesItem && typeof seriesItem === 'object'
    )
  }

  return mergeOption(defaultOption, nextOption)
}

// 定义 ensureChart，负责当前文件中的一个主要状态、函数或导出能力。
function ensureChart() {
  if (!chartEl.value) return
  if (!chart) {
    chart = echarts.init(chartEl.value, null, { renderer: 'canvas' })
  }
}

// 定义 applyOption，负责当前文件中的一个主要状态、函数或导出能力。
function applyOption(option) {
  const safeOption = buildSafeOption(option)
  if (!safeOption) {
    renderError.value = '图表配置为空，暂时无法渲染。'
    chart?.clear()
    return
  }

  try {
    ensureChart()
    renderError.value = ''
    chart?.clear()
    chart?.setOption(safeOption, true)
    chart?.resize()
  } catch (error) {
    renderError.value = '图表配置异常，已跳过渲染。'
    chart?.clear()
    console.error('Chart render failed:', error)
  }
}

// 定义 resizeObserver，负责当前文件中的一个主要状态、函数或导出能力。
const resizeObserver = new ResizeObserver(() => chart?.resize())

onMounted(() => {
  applyOption(props.option)
  if (chartEl.value) {
    resizeObserver.observe(chartEl.value)
  }
})

onUnmounted(() => {
  resizeObserver.disconnect()
  chart?.dispose()
})

watch(
  () => props.option,
  (newOption) => {
    applyOption(newOption)
  },
  { deep: true }
)
</script>

<style scoped>
/* 样式区域：负责当前页面或组件的视觉呈现。 */
.chart-wrapper {
  width: 100%;
  margin-top: 12px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.chart-canvas {
  width: 100%;
  height: 380px;
}

.chart-error {
  padding: 12px 16px 16px;
  color: #b45309;
  font-size: 13px;
}
</style>
