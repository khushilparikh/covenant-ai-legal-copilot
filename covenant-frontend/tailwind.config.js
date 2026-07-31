/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14213D",
        ink2: "#1E2E52",
        paper: "#F7F7F4",
        panel: "#FFFFFF",
        line: "#E4E2DB",
        slate: "#5B6478",
        slateLight: "#8891A0",
        redline: "#B3271E",
        redlineBg: "#FBEBEA",
        greenln: "#2F7A52",
        greenlnBg: "#EAF4EF",
        amber: "#B8862E",
        amberBg: "#FBF3E6",
        brass: "#A9822E",
      },
      fontFamily: {
        serif: ["'Source Serif 4'", "Georgia", "serif"],
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
