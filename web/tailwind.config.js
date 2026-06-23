/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14110E",
        paper: "#FCFBF8",
        surface: "#FFFFFF",
        line: "#EAE4D9",
        "line-soft": "#F1ECE3",
        muted: "#5A544B",
        amber: { DEFAULT: "#F5A623", press: "#DE9213" },
        ok: "#2E9E6B",
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ['"Space Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
