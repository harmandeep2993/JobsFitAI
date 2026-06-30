/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // RGB-channel variables enable opacity modifiers: bg-accent/10, text-accent/60 etc.
        accent:      'rgb(var(--accent) / <alpha-value>)',
        'accent-h':  'rgb(var(--accent-h) / <alpha-value>)',
        bg:          'rgb(var(--bg) / <alpha-value>)',
        surface:     'rgb(var(--surface) / <alpha-value>)',
        'surface-2': 'rgb(var(--surface-2) / <alpha-value>)',
        hover:       'rgb(var(--hover) / <alpha-value>)',
        border:      'rgb(var(--border) / <alpha-value>)',
        t1:          'rgb(var(--t1) / <alpha-value>)',
        t2:          'rgb(var(--t2) / <alpha-value>)',
        t3:          'rgb(var(--t3) / <alpha-value>)',
        green:       'rgb(var(--green) / <alpha-value>)',
        'green-bg':  'rgb(var(--green-bg) / <alpha-value>)',
        'green-bd':  'rgb(var(--green-bd) / <alpha-value>)',
        blue:        'rgb(var(--blue) / <alpha-value>)',
        'blue-bg':   'rgb(var(--blue-bg) / <alpha-value>)',
        'blue-bd':   'rgb(var(--blue-bd) / <alpha-value>)',
        amber:       'rgb(var(--amber) / <alpha-value>)',
        'amber-bg':  'rgb(var(--amber-bg) / <alpha-value>)',
        'amber-bd':  'rgb(var(--amber-bd) / <alpha-value>)',
        red:         'rgb(var(--red) / <alpha-value>)',
        'red-bg':    'rgb(var(--red-bg) / <alpha-value>)',
        'red-bd':    'rgb(var(--red-bd) / <alpha-value>)',
      },
      borderRadius: {
        DEFAULT: '10px',
        lg: '14px',
        sm: '7px',
        xs: '5px',
        full: '9999px',
      },
      spacing: {
        topbar:  'var(--topbar-h)',
        sidebar: 'var(--sidebar-w)',
      },
      width:  { sidebar: 'var(--sidebar-w)' },
      height: { topbar:  'var(--topbar-h)' },
      boxShadow: {
        sm:      '0 1px 2px rgba(0,0,0,0.06)',
        DEFAULT: '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.05)',
        md:      '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.05)',
        lg:      '0 12px 32px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.06)',
        accent:  '0 4px 20px rgb(var(--accent) / 0.25)',
      },
      fontFamily: {
        sans:     ['Inter', 'system-ui', 'sans-serif'],
        display:  ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
