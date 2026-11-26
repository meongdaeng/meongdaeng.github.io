import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// meongdaengtoon.com (GitHub Pages 사용자 도메인, public/CNAME)이라 base는 '/'
export default defineConfig({
  plugins: [vue()],
  base: '/',
})
