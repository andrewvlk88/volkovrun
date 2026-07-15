/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Heebo','system-ui','sans-serif'],
        mono: ['JetBrains Mono','monospace'],
      },
      colors: {
        action: '#ef4444',
        positive: '#22c55e',
        amber: {DEFAULT:'#f59e0b'},
        info: '#3b82f6',
        paper: '#f8f7f5',
      },
      borderRadius: {pill: '9999px'}
    },
  },
  plugins: [],
}
