import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/pet/',
  plugins: [react()],
  server: {
    proxy: {
      '/pet-api': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/pet-api/, ''),
      },
    },
  },
})
