import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: ['volkovrun.avolkov.click'],
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})