import type { NextConfig } from "next";

const isStandalone = process.env.NEXT_OUTPUT_STANDALONE === "true" || process.platform !== "win32";

const nextConfig: NextConfig = {
  // Use standalone output in Linux Docker containers / CI; disable locally on Windows to prevent symlink EPERM
  output: isStandalone ? "standalone" : undefined,
  reactStrictMode: true,
};

export default nextConfig;
