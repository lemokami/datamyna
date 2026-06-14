/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface:  { DEFAULT: '#111118', card: '#18181f', border: '#26262f' },
        brand:    { DEFAULT: '#7c6ef8', dim: '#5b4fd4', glow: 'rgba(124,110,248,0.15)' },
        teal:     { DEFAULT: '#2dd4bf' },
        ink:      { DEFAULT: '#e2e2f0', muted: '#8282a0', faint: '#3a3a50' },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
