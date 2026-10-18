/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"DM Sans"', 'sans-serif'],
        heading: ['"Manrope"', '"DM Sans"', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
      },
      colors: {
        brand: {
          dark: '#080d12',
          surface: '#0d151c',
          panel: '#111b22',
          border: '#202f3a',
          emerald: '#6cdbb0',
          accent: '#83e0ba',
        },
      },
    },
  },
  plugins: [],
};
