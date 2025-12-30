/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Skip ESLint during build (run separately)
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  
  // Optimize images (using remotePatterns instead of deprecated domains)
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
    ],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  
  // Output configuration for Docker
  output: 'standalone',
  
  // Redirects
  async redirects() {
    return [
      {
        source: '/',
        destination: '/pos',
        permanent: false,
      },
    ];
  },
  
  // Headers for security
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
