import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    'process.env': {},           // shims process.env so it doesn't throw
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
})