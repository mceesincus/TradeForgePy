// vite.config.ts
import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // ** ADD THESE NEW CONFIGURATION OPTIONS **
  server: {
    watch: {
      // Use polling which is more reliable in some environments (like Windows Subsystem for Linux or Docker)
      // but can use more CPU. It's a great debugging tool.
      usePolling: true,
    },
  },
  // Force a different cache directory
  cacheDir: 'node_modules/.vite-custom',
  // ** END OF NEW OPTIONS **
})