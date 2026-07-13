/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  runtimeCaching: [
    {
      // Static assets (JS, CSS)
      urlPattern: /\.(js|css|woff2?|ttf|eot)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'platelink-static-v1',
        expiration: { maxEntries: 100, maxAgeSeconds: 30 * 24 * 60 * 60 }
      }
    },
    {
      // Images (food photos, logos)
      urlPattern: /\.(png|jpg|jpeg|webp|svg)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'platelink-images-v1',
        expiration: { maxEntries: 200, maxAgeSeconds: 30 * 24 * 60 * 60 }
      }
    },
    {
      // Menu API - Network First (check for updates, fallback to cache)
      urlPattern: /\/api\/customer\/menu\/.*/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'platelink-menu-v1',
        networkTimeoutSeconds: 5,
        expiration: { maxEntries: 50, maxAgeSeconds: 24 * 60 * 60 }
      }
    },
    {
      // Other API - Network Only (no caching for orders)
      urlPattern: /\/api\/(?!customer\/menu).*/,
      handler: 'NetworkOnly'
    }
  ]
});

module.exports = withPWA({
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['res.cloudinary.com', 'cdn.platelink.com']
  },
  output: 'standalone',
  transpilePackages: ['@platelink/ui', '@platelink/utils', '@platelink/types']
});
