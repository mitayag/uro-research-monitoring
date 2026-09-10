import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        maron: "#5A0E16",
        maroon: {
          DEFAULT: "#5A0E16",
          900: "#5A0E16",
          800: "#6E101C",
          700: "#7E1320",
          600: "#941A29",
          500: "#A92A38",
        },
        rose: {
          100: "#F8EAEC",
        },
        cream: {
          50: "#FCFAF7",
        },
        charcoal: "#1E1E24",
        "gray-700": "#525866",
        "gray-500": "#8B919E",
        "gray-300": "#D9DDE4",
        "gray-100": "#F2F4F7",
        status: {
          success: "#1F8F5F",
          warning: "#D99A22",
          danger: "#C1434D",
          info: "#3E7CC4",
          purple: "#7D57B8",
          neutral: "#8C96A3",
        },
      },
      fontFamily: {
        heading: ['"Playfair Display"', "Georgia", "serif"],
        sans: ["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      borderRadius: {
        control: "9px",
        card: "12px",
        modal: "14px",
      },
      boxShadow: {
        card: "0 2px 8px rgba(24, 24, 27, 0.04)",
        hover: "0 6px 20px rgba(24, 24, 27, 0.08)",
        modal: "0 24px 64px rgba(0,0,0,0.18)",
      },
    },
  },
  plugins: [],
};

export default config;
