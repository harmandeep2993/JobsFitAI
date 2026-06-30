import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

const SCORE_CFG = {
  excellent: { min: 80, color: '#16a34a', bg: 'var(--green-bg)', border: 'var(--green-bd)', label: 'Excellent' },
  good:      { min: 60, color: '#4f46e5', bg: 'var(--blue-bg)',  border: 'var(--blue-bd)',  label: 'Good' },
  partial:   { min: 40, color: '#d97706', bg: 'var(--amber-bg)', border: 'var(--amber-bd)', label: 'Partial' },
  poor:      { min: 0,  color: '#dc2626', bg: 'var(--red-bg)',   border: 'var(--red-bd)',   label: 'Poor' },
}

function scoreCfg(score) {
  if (score >= 80) return SCORE_CFG.excellent
  if (score >= 60) return SCORE_CFG.good
  if (score >= 40) return SCORE_CFG.partial
  return SCORE_CFG.poor
}

function ScoreBadge({ score }) {
  const cfg = scoreCfg(score)
  return (
    <div
      className="flex items-center justify-center w-11 h-11 rounded-sm text-sm font-bold flex-shrink-0 border"
      style={{ background: cfg.bg, borderColor: cfg.border, color: cfg.color }}
    >
      {Math.round(score)}
    </div>
  )
}

function JobCard({ job, onApply, onDelete }) {
  const chips = (job.matched_required || []).slice(0, 5)
  const extra = (job.matched_required || []).length - chips.length

  return (
    <div
      className={`card p-4 flex items-start gap-4 hover:shadow-md transition-shadow ${
        job.applied ? 'ring-1 ring-green-bd' : ''
      }`}
    >
      <ScoreBadge score={job.score || 0} />

      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <div className="text-[14px] font-semibold text-t1 truncate">{job.title}</div>
            <div className="text-[12.5px] text-t2 mt-0.5">
              {job.company}
              {job.location && <span className="text-t3"> · {job.location}</span>}
            </div>
          </div>
          {job.applied && (
            <span className="flex-shrink-0 px-2 py-0.5 text-[11px] font-medium rounded-xs bg-green-bg border border-green-bd text-green">
              Applied
            </span>
          )}
        </div>

        {chips.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2.5">
            {chips.map(k => (
              <span key={k} className="px-2 py-0.5 text-[11px] font-medium rounded-xs bg-green-bg border border-green-bd text-green">
                {k}
              </span>
            ))}
            {extra > 0 && <span className="text-[11px] text-t3 self-center">+{extra}</span>}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noreferrer"
            className="h-7 px-2.5 text-[12px] font-medium border border-border text-t2 hover:text-t1 hover:bg-hover rounded-xs transition-colors flex items-center"
          >
            View
          </a>
        )}
        <button
          onClick={() => onApply(job.id)}
          className={`h-7 px-2.5 text-[12px] font-medium rounded-xs border transition-colors flex items-center ${
            job.applied
              ? 'bg-green-bg border-green-bd text-green hover:opacity-80'
              : 'border-border text-t2 hover:text-t1 hover:bg-hover'
          }`}
        >
          {job.applied ? 'Applied' : 'Mark applied'}
        </button>
        <button
          onClick={() => onDelete(job.id)}
          className="w-7 h-7 flex items-center justify-center text-t3 hover:text-red hover:bg-red-bg rounded-xs transition-colors"
          title="Remove"
        >
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 4h10M5 4V2h6v2M4 4l.7 9.3h6.6L12 4"/>
          </svg>
        </button>
      </div>
    </div>
  )
}

export default function JobMatches() {
  const toast = useToast()
  const [state, setState] = useState(null)
  const [running, setRunning] = useState(false)
  const [minScore, setMinScore] = useState(0)

  const load = useCallback(async () => {
    const res = await apiFetch('/api/match/state')
    if (res?.ok) {
      const d = await res.json()
      setState(d)
      setRunning(d.run_status?.running || false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!running) return
    const iv = setInterval(async () => {
      const res = await apiFetch('/api/match/state')
      if (!res?.ok) return
      const d = await res.json()
      setState(d)
      if (!d.run_status?.running) setRunning(false)
    }, 3000)
    return () => clearInterval(iv)
  }, [running])

  async function runFetch() {
    const res = await apiFetch('/api/match/run')
    if (res?.ok) {
      setRunning(true)
      toast('Fetching and scoring jobs...', 'info')
    } else {
      toast('Could not start fetch - is a resume loaded?', 'error')
    }
  }

  async function toggleApplied(id) {
    await apiFetch('/api/match/applied', { method: 'POST', body: JSON.stringify({ id }) })
    setState(s => s ? {
      ...s,
      results: s.results.map(r => r.id === id ? { ...r, applied: !r.applied } : r)
    } : s)
  }

  async function deleteJob(id) {
    await apiFetch('/api/match/delete', { method: 'POST', body: JSON.stringify({ id }) })
    setState(s => s ? { ...s, results: s.results.filter(r => r.id !== id) } : s)
    toast('Job removed', 'info')
  }

  async function exportCsv() {
    const res = await apiFetch('/api/match/export')
    if (!res?.ok) { toast('Export failed', 'error'); return }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'job_matches.csv'; a.click()
    URL.revokeObjectURL(url)
    toast('Exported', 'success')
  }

  const allResults = state?.results || []
  const results = allResults.filter(r => (r.score || 0) >= minScore)

  const stats = {
    total:   allResults.length,
    good:    allResults.filter(r => r.score >= 60).length,
    applied: allResults.filter(r => r.applied).length,
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-t1">Job Matches</h1>
        <p className="text-sm text-t2 mt-1">Fetch and score job listings automatically against your active resume.</p>
      </div>

      {/* Stats row */}
      {allResults.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Total scored', value: stats.total },
            { label: '60+ score',    value: stats.good },
            { label: 'Applied',      value: stats.applied },
          ].map(s => (
            <div key={s.label} className="card px-4 py-3">
              <div className="text-xl font-bold text-t1">{s.value}</div>
              <div className="text-[12px] text-t2 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-2.5 flex-wrap">
        <select
          value={minScore}
          onChange={e => setMinScore(Number(e.target.value))}
          className="h-8 px-3 bg-surface border border-border rounded-sm text-[12.5px] text-t1 focus:outline-none focus:border-accent"
        >
          <option value={0}>All scores</option>
          <option value={40}>40+ Partial</option>
          <option value={60}>60+ Good</option>
          <option value={80}>80+ Excellent</option>
        </select>

        <div className="flex-1" />

        <button onClick={exportCsv} className="btn-secondary h-8 px-3 text-[12.5px]">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 2v8M5 7l3 3 3-3M2 13h12"/>
          </svg>
          Export CSV
        </button>

        <button
          onClick={runFetch}
          disabled={running}
          className="btn-primary h-8 px-4 text-[12.5px]"
        >
          {running ? (
            <>
              <span className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />
              Running...
            </>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13.5 4A7 7 0 102 10.5"/>
                <path d="M14 1v4h-4"/>
              </svg>
              Fetch Jobs
            </>
          )}
        </button>
      </div>

      {/* Running banner */}
      {running && (
        <div className="flex items-center gap-3 card px-4 py-3 border-blue-bd bg-blue-bg text-blue">
          <span className="w-2 h-2 rounded-full bg-blue animate-pulse flex-shrink-0" />
          <span className="text-[13px] font-medium">Fetching and scoring jobs in background...</span>
        </div>
      )}

      {/* Empty state */}
      {!results.length && !running && (
        <div className="card p-12 text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 rounded-full bg-surface-2 flex items-center justify-center">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--t3)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
            </div>
          </div>
          <div className="text-sm font-medium text-t1 mb-1">No job matches yet</div>
          <div className="text-xs text-t3 mb-5">
            {allResults.length > 0
              ? 'No jobs match the current score filter.'
              : 'Upload a resume in Resumes tab, then click "Fetch Jobs".'}
          </div>
          {allResults.length === 0 && (
            <button onClick={runFetch} disabled={running} className="btn-primary px-5 py-2">
              Fetch Jobs
            </button>
          )}
        </div>
      )}

      {/* Job list */}
      {results.length > 0 && (
        <div className="space-y-2.5">
          {results.map(r => (
            <JobCard
              key={r.id}
              job={r}
              onApply={toggleApplied}
              onDelete={deleteJob}
            />
          ))}
        </div>
      )}

      {results.length > 0 && (
        <div className="text-[12px] text-t3">
          Showing {results.length} of {allResults.length} job{allResults.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}
