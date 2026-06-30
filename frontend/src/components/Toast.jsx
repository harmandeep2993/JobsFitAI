import { createContext, useContext, useState, useCallback } from 'react'

const ToastCtx = createContext(null)

const ICONS = {
  success: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 8l3.5 3.5L13 5"/>
    </svg>
  ),
  error: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4l8 8M12 4l-8 8"/>
    </svg>
  ),
  warn: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 3v5M8 11v1"/>
    </svg>
  ),
  info: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="6.5"/>
      <path d="M8 7v4M8 5v.5"/>
    </svg>
  ),
}

const TYPE_STYLES = {
  success: 'bg-green-bg border-green-bd text-green',
  error:   'bg-red-bg border-red-bd text-red',
  warn:    'bg-amber-bg border-amber-bd text-amber',
  info:    'bg-surface border-border text-t1',
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const toast = useCallback((msg, type = 'info', duration = 3500) => {
    const id = Date.now()
    setToasts(t => [...t, { id, msg, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), duration)
  }, [])

  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div className="fixed bottom-5 right-5 flex flex-col gap-2 z-[100] pointer-events-none" style={{ maxWidth: '340px', width: 'calc(100vw - 40px)' }}>
        {toasts.map(t => (
          <div
            key={t.id}
            className={`flex items-start gap-2.5 border rounded-sm px-3.5 py-2.5 text-[13px] font-medium shadow-md pointer-events-auto ${TYPE_STYLES[t.type] || TYPE_STYLES.info}`}
          >
            <span className="flex-shrink-0 mt-px">{ICONS[t.type] || ICONS.info}</span>
            <span>{t.msg}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() {
  return useContext(ToastCtx)
}
