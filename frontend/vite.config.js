import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
    // Removed manual process.env define as it breaks Vite HMR Websockets
})