import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // NOTE: The /api/video_stream/* rewrite has been REMOVED.
  // We now use a dedicated Next.js App Router API route at
  // app/api/video_stream/[...path]/route.ts which manually proxies all
  // request headers including Range: bytes=... to the FastAPI backend.
  // Next.js rewrites silently drop Range headers, breaking PIXI's 206
  // Partial Content video decode and causing blank canvas rendering.
};

export default nextConfig;
