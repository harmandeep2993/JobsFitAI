import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { saveToken } from '../lib/auth.js'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setErr('')
    if (mode === 'register' && password.length < 8) {
      setErr('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const res = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) { setErr(data.detail || 'Something went wrong.'); return }
      saveToken(data.token)
      navigate('/app', { replace: true })
    } catch {
      setErr('Network error. Is the server running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-[400px]">

        {/* Card */}
        <div className="bg-surface border border-border rounded-lg shadow-md p-8">

          {/* Brand */}
          <div className="flex items-center gap-2.5 mb-8">
            <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
              <svg width="15" height="15" viewBox="0 0 16 16" fill="white">
                <path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/>
              </svg>
            </div>
            <span className="text-[17px] font-bold tracking-tight">
              Jobs<span className="text-accent">Fit</span>AI
            </span>
          </div>

          {/* Heading */}
          <div className="mb-6">
            <h1 className="text-xl font-semibold text-t1 mb-1">
              {mode === 'login' ? 'Welcome back' : 'Create account'}
            </h1>
            <p className="text-[13.5px] text-t2">
              {mode === 'login'
                ? 'Sign in to continue to your dashboard.'
                : 'Start analyzing your resume against job listings.'}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-[12.5px] font-medium text-t2">
                Email address
              </label>
              <input
                type="email"
                required
                autoFocus
                autoComplete="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input-base"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-[12.5px] font-medium text-t2">
                Password
                {mode === 'register' && <span className="font-normal text-t3"> (min 8 characters)</span>}
              </label>
              <input
                type="password"
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="input-base"
              />
            </div>

            {err && (
              <div className="flex items-start gap-2 text-[12.5px] text-red bg-red-bg border border-red-bd rounded-sm px-3 py-2.5">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="flex-shrink-0 mt-px">
                  <circle cx="8" cy="8" r="6.5"/>
                  <path d="M8 5v3.5M8 11v.5"/>
                </svg>
                {err}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-2.5 text-[14px] mt-1"
            >
              {loading
                ? 'Please wait...'
                : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          {/* Toggle mode */}
          <div className="mt-5 pt-5 border-t border-border text-center text-[13px] text-t2">
            {mode === 'login' ? (
              <>
                Don&apos;t have an account?{' '}
                <button
                  onClick={() => { setMode('register'); setErr('') }}
                  className="text-accent font-medium hover:underline"
                >
                  Create one
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  onClick={() => { setMode('login'); setErr('') }}
                  className="text-accent font-medium hover:underline"
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>

        {/* Back to home */}
        <div className="mt-4 text-center">
          <Link to="/" className="text-[12.5px] text-t3 hover:text-t2 transition-colors">
            Back to home
          </Link>
        </div>
      </div>
    </div>
  )
}
