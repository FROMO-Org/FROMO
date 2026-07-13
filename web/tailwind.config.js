/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink:        "var(--color-ink)",
        paper:      "var(--color-paper)",
        surface:    "var(--color-surface)",
        line:       "var(--color-line)",
        "line-soft":"var(--color-line-soft)",
        muted:      "var(--color-muted)",
        amber: { DEFAULT: "#F5A623", press: "#DE9213" },
        ok: "#2E9E6B",
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "Inter", "system-ui", "sans-serif"],
        sans:    ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono:    ['"Space Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
