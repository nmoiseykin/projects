/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'matrix-green': '#32ff79',
        'matrix-cyan': '#00d4ff',
        'dark-bg': '#0a0a0a',
        'dark-card': '#1a1a1a',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      boxShadow: {
        'matrix': '0 0 20px rgba(50, 255, 121, 0.08)',
        'matrix-glow': '0 0 30px rgba(50, 255, 121, 0.2)',
      },
    },
  },
  plugins: [],
}


