/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent:       'var(--accent)',
        'accent-s':   'var(--accent-s)',
        'accent-h':   'var(--accent-h)',
        bg:           'var(--bg)',
        surface:      'var(--surface)',
        'surface-2':  'var(--surface-2)',
        hover:        'var(--hover)',
        border:       'var(--border)',
        t1:           'var(--t1)',
        t2:           'var(--t2)',
        t3:           'var(--t3)',
        green:        'var(--green)',
        'green-bg':   'var(--green-bg)',
        'green-bd':   'var(--green-bd)',
        blue:         'var(--blue)',
        'blue-bg':    'var(--blue-bg)',
        'blue-bd':    'var(--blue-bd)',
        amber:        'var(--amber)',
        'amber-bg':   'var(--amber-bg)',
        'amber-bd':   'var(--amber-bd)',
        red:          'var(--red)',
        'red-bg':     'var(--red-bg)',
        'red-bd':     'var(--red-bd)',
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
      width: {
        sidebar: 'var(--sidebar-w)',
      },
      height: {
        topbar: 'var(--topbar-h)',
      },
      boxShadow: {
        sm:  'var(--shadow-sm)',
        DEFAULT: 'var(--shadow)',
        md:  'var(--shadow-md)',
        lg:  'var(--shadow-lg)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      transitionDuration: {
        DEFAULT: '150ms',
      },
    },
  },
  plugins: [],
}
