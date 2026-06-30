import { useState, useEffect } from 'react'
import { apiFetch } from '../../lib/auth.js'

function ScorePill({ score }) {
  const { color, bg, border } =
    score >= 80 ? { color: '#16a34a', bg: 'var(--green-bg)', border: 'var(--green-bd)' } :
    score >= 60 ? { color: '#4f46e5', bg: 'var(--blue-bg)',  border: 'var(--blue-bd)' } :
    score >= 40 ? { color: '#d97706', bg: 'var(--amber-bg)', border: 'var(--amber-bd)' } :
                  { color: '#dc2626', bg: 'var(--red-bg)',   border: 'var(--red-bd)' }
  return (
    <span
      className="px-2 py-0.5 rounded-xs text-[12px] font-bold border flex-shrink-0"
      style={{ color, background: bg, borderColor: border }}
    >
      {Math.round(score)}
    </span>
  )
}

function EmptyState({ label }) {
  return (
    <div className="text-center py-12 text-[13px] text-t3">{label}</div>
  )
}

function formatDate(str) {
  if (!str) return ''
  return str.slice(0, 16).replace('T', ' ')
}

export default function History() {
  const [data, setData] = useState(null)
  const [tab, setTab] = useState('analyses')

  useEffect(() => {
    apiFetch('/api/history').then(r => r?.json()).then(d => setData(d))
  }, [])

  if (!data) {
    return (
      <div className="space-y-5">
        <div>
          <h1 className="text-xl font-semibold text-t1">History</h1>
        </div>
        <div className="card p-8 text-center text-sm text-t3">Loading...</div>
      </div>
    )
  }

  const tabs = [
    { id: 'analyses',     label: 'Analyses',     count: data.analyses?.length || 0 },
    { id: 'runs',         label: 'Fetcher runs',  count: data.fetcher_runs?.length || 0 },
    { id: 'applications', label: 'Applications',  count: data.applications?.length || 0 },
  ]

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-t1">History</h1>
        <p className="text-sm text-t2 mt-1">Your analysis history, job fetch runs, and tracked applications.</p>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-border gap-1">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-[13px] font-medium border-b-2 transition-colors -mb-px ${
              tab === t.id
                ? 'border-accent text-accent'
                : 'border-transparent text-t2 hover:text-t1'
            }`}
          >
            {t.label}
            {t.count > 0 && (
              <span className={`px-1.5 py-px text-[11px] rounded-xs ${
                tab === t.id ? 'bg-accent/10 text-accent' : 'bg-surface-2 text-t3'
              }`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Analyses */}
      {tab === 'analyses' && (
        <div className="space-y-2">
          {!data.analyses?.length
            ? <EmptyState label="No analyses yet. Go to Analyzer to run your first analysis." />
            : data.analyses.map(a => (
              <div key={a.id} className="card px-4 py-3 flex items-center gap-4">
                <ScorePill score={a.score || 0} />
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px] font-medium text-t1 truncate">
                    {a.jd_snippet || 'Job description'}
                  </div>
                  <div className="text-[12px] text-t3 mt-0.5">{formatDate(a.scored_at)}</div>
                </div>
                <div className={`text-[12.5px] font-semibold flex-shrink-0 ${
                  a.label === 'Excellent' ? 'text-green' :
                  a.label === 'Good' ? 'text-blue' :
                  a.label === 'Partial' ? 'text-amber' : 'text-red'
                }`}>{a.label}</div>
              </div>
            ))
          }
        </div>
      )}

      {/* Fetcher runs */}
      {tab === 'runs' && (
        <div className="space-y-2">
          {!data.fetcher_runs?.length
            ? <EmptyState label="No fetcher runs yet. Go to Job Matches and click Fetch Jobs." />
            : data.fetcher_runs.map((r, i) => (
              <div key={i} className="card px-4 py-3 flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-accent flex-shrink-0" />
                <div className="flex-1 text-[13px] text-t1">{r.detail || 'Fetch run completed'}</div>
                <div className="text-[12px] text-t3 flex-shrink-0">{formatDate(r.created_at)}</div>
              </div>
            ))
          }
        </div>
      )}

      {/* Applications */}
      {tab === 'applications' && (
        <div className="space-y-2">
          {!data.applications?.length
            ? <EmptyState label="No applications tracked yet. Mark jobs as applied in Job Matches." />
            : data.applications.map((a, i) => (
              <div key={i} className="card px-4 py-3 flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-green flex-shrink-0" />
                <div className="flex-1 text-[13px] text-t1">{a.job_id || a.detail || 'Job application'}</div>
                <div className="text-[12px] text-t3 flex-shrink-0">{formatDate(a.created_at)}</div>
              </div>
            ))
          }
        </div>
      )}
    </div>
  )
}
