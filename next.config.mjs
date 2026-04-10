/** @type {import('next').NextConfig} */
const nextConfig = {
  // Required for Docker multi-stage builds: produces .next/standalone with a
  // self-contained server.js that can run without the full node_modules tree.
  // See frontend/Dockerfile and the Deployment section in README.md.
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
