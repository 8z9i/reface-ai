/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: true
  },
  images: {
    domains: ["images.unsplash.com", "replicate.delivery", "dummyimage.com"]
  }
};

export default nextConfig;
