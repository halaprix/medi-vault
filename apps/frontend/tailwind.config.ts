import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: ["class", "class"],
  theme: {
  	extend: {
  		colors: {
  			primary: {
  				DEFAULT: '#1a4f8c',
  				light: '#2563eb',
  				dark: '#1e3a5f'
  			},
  			accent: {
  				DEFAULT: '#0d9488',
  				light: '#14b8a6'
  			},
  			warning: '#f59e0b',
  			danger: '#ef4444',
  			success: '#22c55e'
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [],
};

export default config;
