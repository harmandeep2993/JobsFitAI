import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { saveToken } from '../lib/auth.js'

export default function Login() {
  const [tab, setTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setErr('')
    if (tab === 'register' && password.length < 8) {
      setErr('Password must be at least 8 characters')
      return
    }
    setLoading(true)
    try {
      const path = tab === 'login' ? '/api/auth/login' : '/api/auth/register'
      const res = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) { setErr(data.detail || 'Something went wrong'); return }
      saveToken(data.token)
      navigate('/app', { replace: true })
    } catch {
      setErr('Network error - is the server running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-[360px] bg-surface border border-border rounded shadow-lg p-8">
        {/* Brand */}
        <div className="flex items-center gap-2 mb-7">
          <div className="w-7 h-7 rounded-[7px] bg-accent flex items-center justify-center text-white text-[11px] font-black">JF</div>
          <span className="text-[17px] font-black tracking-tight">Jobs<em className="text-accent not-italic">Fit</em>AI</span>
        </div>

        {/* Tabs */}
        <div className="flex border border-border rounded-s overflow-hidden mb-6">
          {['login', 'register'].map(t => (
            <button
              key={t}
              type="button"
              onClick={() => { setTab(t); setErr('') }}
              className={`flex-1 py-2 text-[13px] font-semibold transition-colors ${
                tab === t ? 'bg-accent text-white' : 'text-t2 hover:text-t1 hover:bg-hover'
              }`}
            >
              {t === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-t2 mb-1.5">Email</label>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-3 py-2 bg-bg border border-border rounded-xs text-[13.5px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-t2 mb-1.5">
              Password{tab === 'register' && ' (min 8 characters)'}
            </label>
            <input
              type="password"
              required
              autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 bg-bg border border-border rounded-xs text-[13.5px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          {err && (
            <div className="text-xs text-red bg-red-bg border border-red-bd rounded-xs px-3 py-2">
              {err}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-accent text-white rounded-xs text-sm font-semibold hover:bg-accent-h disabled:opacity-60 transition-colors mt-1"
          >
            {loading ? 'Please wait...' : tab === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
