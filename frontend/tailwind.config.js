/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent:  'var(--accent)',
        'accent-s': 'var(--accent-s)',
        'accent-h': 'var(--accent-h)',
        bg:      'var(--bg)',
        surface: 'var(--bg-r)',
        'surface-c': 'var(--bg-c)',
        hover:   'var(--bg-hov)',
        border:  'var(--bd)',
        'border-s': 'var(--bd-s)',
        t1:      'var(--t1)',
        t2:      'var(--t2)',
        t3:      'var(--t3)',
        green:   'var(--green)',
        'green-bg': 'var(--green-bg)',
        'green-bd': 'var(--green-bd)',
        blue:    'var(--blue)',
        'blue-bg': 'var(--blue-bg)',
        'blue-bd': 'var(--blue-bd)',
        amber:   'var(--amber)',
        'amber-bg': 'var(--amber-bg)',
        'amber-bd': 'var(--amber-bd)',
        red:     'var(--red)',
        'red-bg': 'var(--red-bg)',
        'red-bd': 'var(--red-bd)',
      },
      borderRadius: {
        DEFAULT: 'var(--radius)',
        s: 'var(--radius-s)',
        xs: 'var(--radius-xs)',
      },
      boxShadow: {
        DEFAULT: 'var(--sha)',
        s:  'var(--sha-s)',
        m:  'var(--sha-m)',
        lg: 'var(--sha-lg)',
      },
      width: {
        sidebar: 'var(--sidebar-w)',
      },
      height: {
        topbar: 'var(--topbar-h)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
