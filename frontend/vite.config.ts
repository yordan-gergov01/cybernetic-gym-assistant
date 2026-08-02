import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// Phone-first PWA. The dev server proxies /api to the FastAPI backend so the app
// always talks to a same-origin path, in dev and in production alike.
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Cybernetic Gym Assistant',
        short_name: 'Gym AI',
        description: 'Персонален AI треньор по методологията на Menno Henselmans',
        lang: 'bg',
        theme_color: '#0B0B0D',
        background_color: '#0B0B0D',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // API responses are user-specific and change constantly — never serve them from cache.
        navigateFallbackDenylist: [/^\/api/],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  // Only the pure logic in src/utils is covered. Components are verified by typecheck,
  // build and use — a DOM test runner is not worth its weight for this app yet.
  test: {
    include: ['src/**/*.test.ts'],
  },
})
