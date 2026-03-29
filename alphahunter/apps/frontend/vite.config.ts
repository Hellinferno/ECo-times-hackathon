/**
 * Vite + Vitest configuration.
 *
 * Dev server: proxies /api → VITE_PROXY_TARGET (default http://localhost:8000)
 *             so the frontend makes same-origin API calls in development.
 *
 * Build:      Tailwind CSS is loaded as a Vite plugin (not a PostCSS plugin).
 *             In test mode Tailwind is skipped to avoid CSS processing overhead
 *             in jsdom — handled by the `mode !== "test"` guard.
 *
 * Tests:      jsdom environment, ./tests/setup.ts for @testing-library setup.
 */
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const proxyTarget = process.env.VITE_PROXY_TARGET || "http://localhost:8000";

export default defineConfig(async ({ mode }) => {
  const plugins = [react()];

  if (mode !== "test") {
    const tailwindcss = (await import("@tailwindcss/vite")).default;
    plugins.push(tailwindcss());
  }

  return {
    plugins,
    server: {
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: "./tests/setup.ts",
      css: true,
    },
  };
});
