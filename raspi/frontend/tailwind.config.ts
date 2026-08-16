import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0f1117",
          raised: "#1a1d27",
          overlay: "#242736",
        },
        accent: {
          DEFAULT: "#3b82f6",
          dim: "#2563eb",
          glow: "#60a5fa",
        },
        danger: {
          DEFAULT: "#ef4444",
          dim: "#dc2626",
        },
        success: "#22c55e",
        warning: "#f59e0b",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
