import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiPort = process.env.VITE_API_PORT || process.env.POKER_AI_API_PORT || "8000";
const apiOrigin = `http://127.0.0.1:${apiPort}`;
const wsOrigin = `ws://127.0.0.1:${apiPort}`;

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          if (
            id.includes("react-markdown") ||
            id.includes("micromark") ||
            id.includes("mdast-") ||
            id.includes("unist-")
          ) {
            return "vendor-markdown";
          }
          if (id.includes("@tanstack")) {
            return "vendor-query";
          }
          if (
            id.includes("react-dom") ||
            id.includes("react-router") ||
            id.includes("/react/")
          ) {
            return "vendor-react";
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: apiOrigin,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      // Prefer VITE_WS_BASE_URL (direct to API) — proxy only for manual npm run dev
      "/ws": {
        target: wsOrigin,
        ws: true,
        rewrite: (path) => path,
        configure: (proxy) => {
          proxy.on("error", () => {
            /* client navigated away / StrictMode remount — harmless */
          });
        },
      },
    },
  },
});
