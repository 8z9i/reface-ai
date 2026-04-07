import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Grotesk'", "Inter", "system-ui", "sans-serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"]
      },
      colors: {
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81"
        },
        surface: "#0B1021",
        glass: "rgba(255, 255, 255, 0.08)"
      },
      boxShadow: {
        glass: "0 20px 80px rgba(0, 0, 0, 0.35)",
        brand: "0 10px 40px rgba(99, 102, 241, 0.35)"
      },
      backgroundImage: {
        "grid-glow":
          "radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.35), transparent 25%), radial-gradient(circle at 80% 0%, rgba(14, 165, 233, 0.35), transparent 25%), radial-gradient(circle at 50% 80%, rgba(236, 72, 153, 0.35), transparent 30%)"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

export default config;
