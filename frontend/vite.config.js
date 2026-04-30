/**
 * 文件作用：
 * - 配置前端开发服务器、别名和后端接口代理规则。
 * - 阅读这个文件时，建议先看整体结构，再看关键状态和交互逻辑。
 */

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devPort = Number(env.VITE_DEV_PORT || 5174)
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8088'

  return {
    plugins: [
      vue(),
      AutoImport({
        resolvers: [ElementPlusResolver()],
        imports: ['vue', 'vue-router', 'pinia'],
      }),
      Components({
        resolvers: [ElementPlusResolver()],
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: devPort,
      proxy: {
        '/auth': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/agent': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/ops': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/test': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return
            if (id.includes('echarts')) return 'echarts'
            if (id.includes('element-plus')) return 'element-plus'
            if (id.includes('vue')) return 'vue-vendor'
          },
        },
      },
    },
  }
})
