import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "#ffc700",
      },
    },
  },
  plugins: [],
} satisfies Config;

