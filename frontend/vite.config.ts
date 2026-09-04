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
      includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
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
        // Rendered from favicon.svg onto the app's own background: a transparent mark
        // is drawn by each launcher on a background of its choosing, usually white.
        // The maskable icon is a separate file rather than the same one declared twice -
        // a launcher crops it to its own shape, so the mark needs the wider safe zone
        // that would look like a mistake on the normal icon.
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: 'icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
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
