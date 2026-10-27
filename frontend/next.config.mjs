const backend = (process.env.FLASK_API_URL || 'http://127.0.0.1:5000').replace(/\/$/, '');
const backendUrl = new URL(backend);
if (!['http:', 'https:'].includes(backendUrl.protocol) || backendUrl.username || backendUrl.password || backendUrl.search || backendUrl.hash || backendUrl.pathname !== '/') {
  throw new Error('FLASK_API_URL harus berupa origin HTTP atau HTTPS tanpa path atau kredensial.');
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  poweredByHeader: false,
  devIndicators: false,
  experimental: { useTypeScriptCli: false, agentUpgrade: 'security' },
  async headers() {
    return [{
      source: '/:path*',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'Referrer-Policy', value: 'no-referrer' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      ],
    }];
  },
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
