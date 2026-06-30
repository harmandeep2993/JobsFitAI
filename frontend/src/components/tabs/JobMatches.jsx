import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

function ScorePill({ score }) {
  const cls =
    score >= 80 ? 'bg-green-bg border-green-bd text-green' :
    score >= 60 ? 'bg-blue-bg border-blue-bd text-blue' :
    score >= 40 ? 'bg-amber-bg border-amber-bd text-amber' :
                  'bg-red-bg border-red-bd text-red'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-xs text-xs font-bold border ${cls}`}>
      {Math.round(score)}
    </span>
  )
}

export default function JobMatches() {
  const toast = useToast()
  const [state, setState] = useState(null)
  const [running, setRunning] = useState(false)
  const [minScore, setMinScore] = useState(0)

  const load = useCallback(async () => {
    const res = await apiFetch('/api/match/state')
    if (res?.ok) setState(await res.json())
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!running) return
    const iv = setInterval(async () => {
      const res = await apiFetch('/api/match/state')
      if (!res?.ok) return
      const data = await res.json()
      setState(data)
      if (!data.run_status?.running) setRunning(false)
    }, 3000)
    return () => clearInterval(iv)
  }, [running])

  async function runFetch() {
    setRunning(true)
    await apiFetch('/api/match/run')
    toast('Fetch started', 'info')
  }

  async function toggleApplied(id) {
    await apiFetch('/api/match/applied', { method: 'POST', body: JSON.stringify({ id }) })
    load()
  }

  async function deleteJob(id) {
    await apiFetch('/api/match/delete', { method: 'POST', body: JSON.stringify({ id }) })
    setState(s => s ? { ...s, results: s.results.filter(r => r.id !== id) } : s)
  }

  async function exportCsv() {
    const res = await apiFetch('/api/match/export')
    if (!res?.ok) { toast('Export failed', 'error'); return }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'job_matches.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  const results = (state?.results || []).filter(r => (r.score || 0) >= minScore)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-lg font-bold flex-1">Job Matches</h1>
        <div className="flex items-center gap-2">
          <label className="text-xs text-t2">Min score</label>
          <select
            value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
            className="px-2 py-1 bg-surface border border-border rounded-xs text-xs text-t1 focus:outline-none"
          >
            {[0,40,60,80].map(v => <option key={v} value={v}>{v}+</option>)}
          </select>
        </div>
        <button onClick={exportCsv} className="px-3 py-1.5 bg-surface border border-border rounded-s text-xs font-medium text-t2 hover:text-t1 hover:bg-hover transition-colors">
          Export CSV
        </button>
        <button
          onClick={runFetch}
          disabled={running}
          className="px-4 py-1.5 bg-accent text-white rounded-s text-xs font-semibold hover:bg-accent-h disabled:opacity-60 transition-colors"
        >
          {running ? 'Running...' : 'Fetch Jobs'}
        </button>
      </div>

      {state?.run_status?.running && (
        <div className="flex items-center gap-2 text-xs text-t2 bg-surface border border-border rounded-s px-3 py-2">
          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          Fetching and scoring jobs...
        </div>
      )}

      {!results.length && (
        <div className="bg-surface border border-border rounded p-8 text-center text-sm text-t3">
          No job matches yet. Click "Fetch Jobs" to start.
        </div>
      )}

      <div className="space-y-2">
        {results.map(r => (
          <div
            key={r.id}
            className={`bg-surface border rounded p-4 flex items-start gap-4 transition-colors ${
              r.applied ? 'border-green-bd bg-green-bg/30' : 'border-border'
            }`}
          >
            <div className="flex-shrink-0 pt-0.5">
              <ScorePill score={r.score || 0} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm truncate">{r.title}</div>
              <div className="text-xs text-t2 mt-0.5">{r.company} {r.location ? `· ${r.location}` : ''}</div>
              {r.matched_required?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {r.matched_required.slice(0, 6).map(k => (
                    <span key={k} className="px-1.5 py-0.5 bg-green-bg border border-green-bd text-green text-[10px] rounded-xs">{k}</span>
                  ))}
                  {r.matched_required.length > 6 && (
                    <span className="text-[10px] text-t3">+{r.matched_required.length - 6}</span>
                  )}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {r.url && (
                <a href={r.url} target="_blank" rel="noreferrer" className="text-xs text-accent hover:underline">View</a>
              )}
              <button
                onClick={() => toggleApplied(r.id)}
                className={`text-xs px-2 py-1 rounded-xs border transition-colors ${
                  r.applied
                    ? 'bg-green-bg border-green-bd text-green'
                    : 'border-border text-t2 hover:text-t1 hover:bg-hover'
                }`}
              >
                {r.applied ? 'Applied' : 'Mark applied'}
              </button>
              <button
                onClick={() => deleteJob(r.id)}
                className="text-xs text-t3 hover:text-red transition-colors p-1"
                title="Delete"
              >
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                  <path d="M3 4h10M5 4V2h6v2M6 7v5M10 7v5M4 4l.6 9h6.8L12 4"/>
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>

      {state && (
        <div className="text-xs text-t3 pt-2">
          {results.length} job{results.length !== 1 ? 's' : ''} shown
          {state.results?.length !== results.length ? ` (${state.results.length} total)` : ''}
        </div>
      )}
    </div>
  )
}
