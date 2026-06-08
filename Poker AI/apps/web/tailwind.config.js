/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        felt: "#1a4d3a",
        rail: "#0f172a",
      },
    },
  },
  plugins: [],
};
