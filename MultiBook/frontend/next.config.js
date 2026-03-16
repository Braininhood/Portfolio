/** @type {import('next').NextConfig} */

// Build CSP connect-src: allow API and Supabase
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const apiOrigin = apiUrl ? new URL(apiUrl).origin : 'http://localhost:8000';

// Next 14 vs 16: only add version-specific options to avoid "Unrecognized key" warnings
const nextVersion = require('next/package.json').version || '';
const isNext16 = nextVersion.startsWith('16.');

const nextConfig = {
  reactStrictMode: true,

  // Production: standalone folder for deploy without npm run build on server (run node server.js)
  output: 'standalone',

  ...(isNext16
    ? { turbopack: {} }
    : { eslint: { ignoreDuringBuilds: false } }),

  // Allow 127.0.0.1 in dev so _next/* and webpack-hmr work when opening app at http://127.0.0.1:3000
  allowedDevOrigins: [
    '127.0.0.1', 'localhost',
    'http://127.0.0.1:3000', 'http://localhost:3000',
    '13.135.109.229', 'ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
    'https://13.135.109.229', 'https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
  ],

  // Content-Security-Policy and other security headers
  // In development we skip CSP to avoid blocking Next.js inline scripts and HMR
  async headers() {
    const isProd = process.env.NODE_ENV === 'production';
    const cspParts = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://maps.googleapis.com https://*.googleapis.com",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "img-src 'self' data: blob: https:",
      "font-src 'self' data: https://fonts.gstatic.com https://fonts.googleapis.com",
      `connect-src 'self' ${apiOrigin} https://*.supabase.co wss://*.supabase.co https://accounts.google.com https://*.googleapis.com blob:`,
      "frame-src 'self' https://accounts.google.com https://*.supabase.co",
      "frame-ancestors 'self'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
    ];
    if (isProd) {
      cspParts.push("upgrade-insecure-requests");
    }
    const csp = cspParts.join('; ');

    const securityHeaders = [
      { key: 'X-DNS-Prefetch-Control', value: 'on' },
      { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(self)' },
    ];
    // Only set CSP in production; in dev it blocks Next.js inline scripts and causes "Connection closed"
    // Note: CSP warnings in dev are expected and harmless - Next.js uses nonces that may not match
    if (isProd) {
      securityHeaders.push({ key: 'Content-Security-Policy', value: csp });
    }

    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ];
  },

  // WebSocket configuration for HMR (Hot Module Reload)
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Use polling for file watching (more reliable than WebSockets on some systems)
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
        ignored: /node_modules/,
      };
      // Optimize for faster rebuilds in development
      config.optimization = {
        ...config.optimization,
        removeAvailableModules: false,
        removeEmptyChunks: false,
        splitChunks: false,
      };
      // Do not override devtool: Next.js warns and reverts to eval-source-map in dev
    }
    return config;
  },
  
  // API proxy for development (optional - frontend and backend run separately)
  // Note: Frontend makes direct API calls, so rewrites are not needed
  // async rewrites() {
  //   const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: `${apiUrl}/:path*`,
  //     },
  //   ];
  // },
  
  // Image remotePatterns (Next 16: domains deprecated; use only remotePatterns)
  images: {
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost' },
      { protocol: 'https', hostname: 'localhost' },
      { protocol: 'https', hostname: 'yourdomain.com' },
      { protocol: 'https', hostname: '13.135.109.229' },
      { protocol: 'https', hostname: 'ec2-13-135-109-229.eu-west-2.compute.amazonaws.com' },
      { protocol: 'https', hostname: '**.googleusercontent.com' },
      { protocol: 'https', hostname: '**.googleapis.com' },
    ],
  },
  
  // Environment variables available on client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  },
  
  // PWA configuration
  // Note: Service worker and offline support can be added with next-pwa package if needed
  
  // Allow cross-origin requests in development (fixes blocked _next/* resource warnings)
  // Note: This is a Next.js 14+ feature
  // The warning about blocked cross-origin requests is usually harmless in development
};

module.exports = nextConfig;
