/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        pastel: {
          lavender: {
            DEFAULT: '#A78BFA',
            light: '#F5F2FD',
            border: '#DDD6FE',
            hover: '#906EE8',
            dark: '#6D28D9',
          },
          blue: {
            DEFAULT: '#93C5FD',
            light: '#EFF6FF',
            border: '#BFDBFE',
            hover: '#60A5FA',
            dark: '#1D4ED8',
          },
          peach: {
            DEFAULT: '#FDBA9A',
            light: '#FFF7ED',
            border: '#FED7AA',
            dark: '#C2410C',
          },
          mint: {
            DEFAULT: '#A7E8D0',
            light: '#ECFDF5',
            border: '#6EE7B7',
            dark: '#065F46',
          },
          rose: {
            DEFAULT: '#F5B5C8',
            light: '#FFF1F2',
            border: '#FECDD3',
            dark: '#9F1239',
          },
          bg: {
            DEFAULT: '#FAFAF7',
            dark: '#181724',
          },
          surface: {
            DEFAULT: '#FFFFFF',
            dark: '#221F33',
            elevated: '#2B2740',
          },
          charcoal: {
            DEFAULT: '#252334',
            light: '#F4F2FA',
          },
          slate: {
            DEFAULT: '#666477',
            light: '#A4A0BD',
          },
          border: {
            DEFAULT: '#E7E2F0',
            dark: '#363252',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        'lg': '12px',
        'xl': '14px',
        '2xl': '16px',
        '3xl': '24px',
      },
      boxShadow: {
        'pastel': '0 4px 20px -2px rgba(167, 139, 250, 0.08), 0 2px 6px -1px rgba(37, 35, 52, 0.03)',
        'pastel-hover': '0 8px 30px -4px rgba(167, 139, 250, 0.16), 0 4px 10px -2px rgba(37, 35, 52, 0.05)',
        'pastel-card': '0 2px 10px -2px rgba(37, 35, 52, 0.04)',
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        floatSlow: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'float-slow': 'floatSlow 8s ease-in-out infinite',
        'pulse-subtle': 'pulseSubtle 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
