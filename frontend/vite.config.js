import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发服务器通过代理把 /api 转发到后端 8001，避免跨域，前端代码中统一用相对路径请求
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
