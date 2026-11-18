import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  experimental: {
    // The /api proxy cuts requests off after 30s by default. CV tailoring and interview prep
    // make several LLM calls (draft, review, up to two revisions) and can take minutes.
    proxyTimeout: 10 * 60 * 1000,
  },
  async rewrites() {
    // Trim: on Windows `set BACKEND_PORT=8005 && ...` stores "8005 " (with the space)
    const backendPort = (process.env.BACKEND_PORT || "8005").trim();
    return [
      {
        source: "/api/:path*",
        destination: `http://127.0.0.1:${backendPort}/api/:path*`,
      },
    ];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
