import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/ingest':   { target: 'http://backend:8000', changeOrigin: true },
      '/dau':      { target: 'http://backend:8000', changeOrigin: true },
      '/wau':      { target: 'http://backend:8000', changeOrigin: true },
      '/mau':      { target: 'http://backend:8000', changeOrigin: true },
      '/top-pages':{ target: 'http://backend:8000', changeOrigin: true },
      '/events':   { target: 'http://backend:8000', changeOrigin: true },
      '/stats':    { target: 'http://backend:8000', changeOrigin: true },
      '/sessions': { target: 'http://backend:8000', changeOrigin: true },
      '/tracker.js':{ target: 'http://backend:8000', changeOrigin: true },
    },
  },
})
