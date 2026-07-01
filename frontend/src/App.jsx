import { Routes, Route, Navigate } from 'react-router-dom'
import { isAuthed } from './lib/auth.js'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import About from './pages/About.jsx'
import Pricing from './pages/Pricing.jsx'
import Privacy from './pages/Privacy.jsx'
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
  return (
    <Routes>
      <Route path="/"        element={<RedirectIfAuthed><Landing /></RedirectIfAuthed>} />
      <Route path="/login"   element={<RedirectIfAuthed><Login /></RedirectIfAuthed>} />
      <Route path="/about"   element={<About />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/app"     element={<RequireAuth><AppShell /></RequireAuth>} />
      <Route path="*"        element={<Navigate to="/" replace />} />
    </Routes>
  )
}
