import { createContext, useContext, useState, useCallback } from 'react'

const ToastCtx = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const toast = useCallback((msg, type = 'info', duration = 3500) => {
    const id = Date.now()
    setToasts(t => [...t, { id, msg, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), duration)
  }, [])

  const colors = {
    info:    'bg-surface border-border text-t1',
    success: 'bg-green-bg border-green-bd text-green',
    error:   'bg-red-bg border-red-bd text-red',
    warn:    'bg-amber-bg border-amber-bd text-amber',
  }

  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div className="fixed bottom-5 right-5 flex flex-col gap-2 z-50 pointer-events-none">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`border rounded-s px-4 py-2.5 text-sm font-medium shadow-m max-w-xs animate-in ${colors[t.type] || colors.info}`}
          >
            {t.msg}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() {
  return useContext(ToastCtx)
}
