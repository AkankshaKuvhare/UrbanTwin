/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
          950: '#042f2e',
        },
        traffic: {
          low: '#10b981',
          moderate: '#f59e0b',
          heavy: '#f97316',
          severe: '#ef4444',
          gridlock: '#991b1b',
        },
        aqi: {
          good: '#10b981',
          satisfactory: '#84cc16',
          moderate: '#f59e0b',
          poor: '#f97316',
          veryPoor: '#ef4444',
          severe: '#7f1d1d',
        },
        navy: {
          850: '#0f172a',
          900: '#0a0f1d',
          950: '#060a15',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}
