const target = process.env.API_PROXY_TARGET || "http://localhost:8000";
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy API calls through Next so the browser never hits CORS issues.
  async rewrites() {
    return [
      { source: "/api/v1/:path*", destination: `${target}/api/v1/:path*` },
    ];
  },
};
export default nextConfig;
