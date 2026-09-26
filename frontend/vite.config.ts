import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': loadEnv(mode, '.', 'SATCHETAK_').SATCHETAK_API_URL || 'http://127.0.0.1:8000' },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1300,
    rollupOptions: {
      output: { manualChunks: { maplibre: ['maplibre-gl'], react: ['react', 'react-dom'] } },
    },
  },
}))
