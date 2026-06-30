import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import basicSsl from "@vitejs/plugin-basic-ssl";

export default defineConfig(({ command }) => ({
  base: command === "build" && process.env.GITHUB_PAGES === "true" ? "/excel-plugin/" : "/",
  plugins: [react(), basicSsl()],
  server: {
    host: "localhost",
    port: 3000,
    https: true,
  },
  build: {
    rollupOptions: {
      input: {
        index: "index.html",
        taskpane: "taskpane.html",
      },
    },
  },
}));
