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
          redSoft: "#fecaca",
          yellow: "#eab308",
          yellowBg: "#fefce8",
          yellowSoft: "#fde68a",
          green: "#16a34a",
          greenBg: "#f0fdf4",
          greenSoft: "#bbf7d0",
          gray: "#475569",
          grayBg: "#f1f5f9",
        },
        status: {
          live: "#10b981",
          warn: "#f59e0b",
          off: "#94a3b8",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glass: "0 8px 30px rgb(15 23 42 / 0.04)",
        glassLg: "0 20px 60px rgb(15 23 42 / 0.06)",
        ring: "0 0 0 1px rgb(255 255 255 / 0.6)",
      },
      backdropBlur: {
        xs: "2px",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      animation: {
        pulseRing: "pulseRing 2s ease-in-out infinite",
        statusGlow: "statusGlow 2.4s ease-in-out infinite",
      },
      keyframes: {
        pulseRing: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(220, 38, 38, 0.45)" },
          "50%": { boxShadow: "0 0 0 12px rgba(220, 38, 38, 0)" },
        },
        statusGlow: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(16, 185, 129, 0.45)" },
          "50%": { boxShadow: "0 0 0 6px rgba(16, 185, 129, 0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
