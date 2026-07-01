/**
 * Toast notification system - slide-in from bottom-right with framer-motion.
 */
import { createContext, useContext, useState, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

const ToastCtx = createContext(null)

const ICONS = {
  success: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 8l3.5 3.5L13 5"/>
    </svg>
  ),
  error: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4l8 8M12 4l-8 8"/>
    </svg>
  ),
  warn: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8 3v5M8 11v1"/>
    </svg>
  ),
  info: (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="6.5"/>
      <path d="M8 7v4M8 5v.5"/>
    </svg>
  ),
}

const TYPE_STYLES = {
  success: { background: 'rgba(22,163,74,0.08)',   borderColor: 'rgba(22,163,74,0.25)',  color: '#16a34a' },
  error:   { background: 'rgba(220,38,38,0.08)',  borderColor: 'rgba(220,38,38,0.25)', color: '#dc2626' },
  warn:    { background: 'rgba(217,119,6,0.08)',  borderColor: 'rgba(217,119,6,0.25)', color: '#d97706' },
  info:    { background: 'rgb(var(--surface))',   borderColor: 'rgba(0,0,0,0.08)',      color: 'rgb(var(--t1))' },
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
      <div
        className="fixed bottom-5 right-5 flex flex-col gap-2 z-[200] pointer-events-none"
        style={{ maxWidth: '340px', width: 'calc(100vw - 40px)' }}
      >
        <AnimatePresence>
          {toasts.map(t => {
            const s = TYPE_STYLES[t.type] || TYPE_STYLES.info
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 12, scale: 0.96 }}
                animate={{ opacity: 1, y: 0,  scale: 1 }}
                exit={{    opacity: 0, y: 6,  scale: 0.96, transition: { duration: 0.15 } }}
                transition={{ duration: 0.18, ease: [0.25, 0.1, 0.25, 1] }}
                className="flex items-start gap-2.5 border rounded-lg px-3.5 py-2.5 text-[13px] font-medium shadow-md pointer-events-auto"
                style={{
                  background: s.background,
                  borderColor: s.borderColor,
                  color: s.color,
                  backdropFilter: 'blur(8px)',
                  WebkitBackdropFilter: 'blur(8px)',
                }}
              >
                <span className="flex-shrink-0 mt-px">{ICONS[t.type] || ICONS.info}</span>
                <span style={{ color: 'rgb(var(--t1))' }}>{t.msg}</span>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() {
  return useContext(ToastCtx)
}
