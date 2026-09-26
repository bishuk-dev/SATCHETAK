import { defineConfig } from '@playwright/test'
import process from 'node:process'
import { resolve } from 'node:path'

export default defineConfig({
  testDir: './tests',
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:5174',
    channel: 'chrome',
    viewport: { width: 1440, height: 1100 },
    launchOptions: { args: ['--enable-unsafe-swiftshader'] },
    trace: 'retain-on-failure',
  },
  webServer: [{
    command: 'npm run dev -- --host 127.0.0.1 --port 5174 --strictPort',
    url: 'http://127.0.0.1:5174',
    reuseExistingServer: false,
    env: { SATCHETAK_API_URL: 'http://127.0.0.1:8001' },
  }, {
    command: `"${resolve('..', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')}" -m uvicorn satchetak.main:app --host 127.0.0.1 --port 8001`,
    cwd: '..',
    url: 'http://127.0.0.1:8001/api/v1/health',
    env: { SATCHETAK_DATA_DIR: resolve('.test-api-data') },
    reuseExistingServer: false,
  }],
})
