/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_N8N_URL: process.env.NEXT_PUBLIC_N8N_URL || 'http://localhost:5678',
  },
}

module.exports = nextConfig
