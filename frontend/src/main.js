/**
 * 文件作用：
 * - 作为前端入口脚本，负责创建 Vue 应用并注册插件。
 * - 阅读这个文件时，建议先看整体结构，再看关键状态和交互逻辑。
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import './assets/main.css'

// 定义 app，负责当前文件中的一个主要状态、函数或导出能力。
const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
