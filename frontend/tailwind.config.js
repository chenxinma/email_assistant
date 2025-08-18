/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#165DFF',
        secondary: '#36CFC9',
        accent: '#722ED1',
        neutral: '#F5F7FA',
        'neutral-dark': '#1D2129',
        success: '#52C41A',
        warning: '#FAAD14',
        danger: '#FF4D4F',
      },
    },
  },
  plugins: [],
}