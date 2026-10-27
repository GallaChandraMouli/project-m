/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eefcf6',
          100: '#d5f8e7',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
        },
        dark: {
          bg: '#0A0D14',
          card: '#111726',
          border: '#1F293D',
          hover: '#192238'
        }
      }
    },
  },
  plugins: [],
}
