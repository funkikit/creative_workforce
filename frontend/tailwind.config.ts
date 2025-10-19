import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./tests/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f5f8ff",
          100: "#e2e8ff",
          200: "#c7d1ff",
          300: "#a8b6ff",
          400: "#8797ff",
          500: "#6777f7",
          600: "#4d5bd4",
          700: "#3844a9",
          800: "#262f7f",
          900: "#181f58",
        },
      },
    },
  },
  plugins: [],
};

export default config;
