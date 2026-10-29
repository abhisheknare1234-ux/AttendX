/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    if (process.env.API_BACKEND_URL) {
      return [
        {
          source: '/api/v1/:path*',
          destination: `${process.env.API_BACKEND_URL}/api/v1/:path*`,
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
