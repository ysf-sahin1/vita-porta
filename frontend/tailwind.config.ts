import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        triage: {
          red: "#dc2626",
          redBg: "#fef2f2",
          yellow: "#eab308",
          yellowBg: "#fefce8",
          green: "#16a34a",
          greenBg: "#f0fdf4",
          gray: "#475569",
          grayBg: "#f1f5f9",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      animation: {
        pulseRing: "pulseRing 2s ease-in-out infinite",
      },
      keyframes: {
        pulseRing: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(220, 38, 38, 0.45)" },
          "50%": { boxShadow: "0 0 0 12px rgba(220, 38, 38, 0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
