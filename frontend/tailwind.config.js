/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        stark: {
          darkest: '#030712',
          darker: '#060d1a',
          dark: '#0a1628',
          card: '#0c1b33',
          border: 'rgba(0, 240, 255, 0.22)',
          borderHover: 'rgba(0, 240, 255, 0.5)',
          cyan: '#00f0ff',
          ice: '#e0f2fe',
          cyanMuted: 'rgba(0, 240, 255, 0.12)',
          amber: '#f59e0b',
        }
      },
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        mono: ['Consolas', 'Courier New', 'monospace'],
        sans: ['Rajdhani', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan': '0 0 15px rgba(0, 240, 255, 0.35)',
        'glow-cyan-lg': '0 0 30px rgba(0, 240, 255, 0.5)',
      }
    },
  },
  plugins: [],
}
