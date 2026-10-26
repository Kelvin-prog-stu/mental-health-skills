import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// BACKEND_URL lets a check run the frontend against a throwaway backend. Normally unset.
const backend = process.env.BACKEND_URL || 'http://localhost:8100'
const port = Number(process.env.FRONTEND_PORT) || 5180

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: { port, strictPort: true, proxy: { '/api': backend } },
})
