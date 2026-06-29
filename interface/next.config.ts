import type { NextConfig } from "next";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Trailing slash is required: Django (APPEND_SLASH) 500s on POST to a
        // slashless URL, and Next strips the slash from the matched :path*.
        source: "/backend/:path*",
        destination: `${apiBaseUrl}/:path*/`,
      },
    ];
  },
};

export default nextConfig;
