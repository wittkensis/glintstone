/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "celestial": {
          "navy": "#0a0e14",
          "surface": "#151a23",
          "border": "#2d3748",
          "text": "#e2e8f0",
        },
        "accent": {
          "gold": "#f6ad55",
          "violet": "#9f7aea",
        }
      },
      fontFamily: {
        "serif": ["Eczar", "Spectral", "serif"],
        "sans": ["Inter", "system-ui", "sans-serif"],
        "mono": ["Menlo", "Monaco", "monospace"],
        "cuneiform": ["Noto Sans Cuneiform", "serif"],
      },
      spacing: {
        "xs": "0.5rem",
        "s": "1rem",
        "m": "1.5rem",
        "l": "2rem",
        "xl": "3rem",
      },
    },
  },
  plugins: [],
}
