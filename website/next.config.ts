import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The auto-deploy (scripts/deploy.sh) builds into a staging dir
  // (NEXT_DIST_DIR=.next.new) and swaps it in only after the whole build
  // succeeded, so a failed or killed build can never leave the live .next --
  // the one moss-ao-web is serving from -- half-written. Everywhere else
  // (dev, `next start`, local builds) the variable is unset and this stays
  // the default .next.
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
