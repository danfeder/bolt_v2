/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable Edge Runtime for better performance
  experimental: {
    runtime: 'edge',
  },
  
  // Disable unnecessary features for API-only usage
  images: {
    unoptimized: true,
  },
  
  // Configure build output
  output: 'standalone',
  
  // Restrict API routes to /api directory
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination: '/:path*',
      },
    ];
  },
  
  // TypeScript configuration
  typescript: {
    // Enable type checking in production builds
    ignoreBuildErrors: false,
  },
};

module.exports = nextConfig;
