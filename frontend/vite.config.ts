import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "OI Pulse Fleet",
        short_name: "Fleet",
        start_url: "/",
        display: "standalone",
        background_color: "#f8fafc",
        theme_color: "#163a66",
      },
    }),
  ],
  server: { port: 5173, proxy: { "/api": "http://localhost:8000" } },
  resolve: { alias: { "@": "/src" } },
  test: { environment: "jsdom" },
});
