/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vmm-blue': '#1e40af',
        'vmm-green': '#059669',
        'vmm-orange': '#ea580c',
        'vmm-gray': '#6b7280',
      }
    },
  },
  plugins: [],
}

