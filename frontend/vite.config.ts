/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// API: python -m backend CATALOGUE_DIR (default port 8765)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8765' },
  },
  test: { environment: 'node' },
})
