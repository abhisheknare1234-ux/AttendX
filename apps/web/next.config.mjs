/** @type {import('next').NextConfig} */
const apiBackendUrl = process.env.API_BACKEND_URL || 'http://127.0.0.1:8000';

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiBackendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

