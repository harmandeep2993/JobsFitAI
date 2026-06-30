import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { isAuthed } from './lib/auth.js'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import AppShell from './layouts/AppShell.jsx'

function RequireAuth({ children }) {
  if (!isAuthed()) return <Navigate to="/login" replace />
  return children
}

function RedirectIfAuthed({ children }) {
  if (isAuthed()) return <Navigate to="/app" replace />
  return children
}

export default function App() {
  const [dark, setDark] = useState(() => {
    return localStorage.getItem('theme') === 'dark'
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <Routes>
      <Route path="/" element={<RedirectIfAuthed><Landing onToggleDark={() => setDark(d => !d)} dark={dark} /></RedirectIfAuthed>} />
      <Route path="/login" element={<RedirectIfAuthed><Login /></RedirectIfAuthed>} />
      <Route path="/app" element={<RequireAuth><AppShell dark={dark} onToggleDark={() => setDark(d => !d)} /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
