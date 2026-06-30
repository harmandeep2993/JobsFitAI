import { useState, useEffect } from 'react'
import { apiFetch } from '../../lib/auth.js'

function ScorePill({ score }) {
  const cls =
    score >= 80 ? 'bg-green-bg border-green-bd text-green' :
    score >= 60 ? 'bg-blue-bg border-blue-bd text-blue' :
    score >= 40 ? 'bg-amber-bg border-amber-bd text-amber' :
                  'bg-red-bg border-red-bd text-red'
  return (
    <span className={`px-2 py-0.5 rounded-xs text-xs font-bold border ${cls}`}>
      {Math.round(score)}
    </span>
  )
}

export default function History() {
  const [data, setData] = useState(null)
  const [tab, setTab] = useState('analyses')

  useEffect(() => {
    apiFetch('/api/history').then(r => r?.json()).then(d => setData(d))
  }, [])

  if (!data) return <div className="text-sm text-t3">Loading...</div>

  const tabs = [
    { id: 'analyses', label: 'Analyses', count: data.analyses?.length },
    { id: 'runs', label: 'Fetcher runs', count: data.fetcher_runs?.length },
    { id: 'applications', label: 'Applications', count: data.applications?.length },
  ]

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">History</h1>

      <div className="flex gap-1 border-b border-border">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
              tab === t.id
                ? 'border-accent text-accent'
                : 'border-transparent text-t2 hover:text-t1'
            }`}
          >
            {t.label}
            {t.count > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 bg-hover rounded-xs text-t3">{t.count}</span>
            )}
          </button>
        ))}
      </div>

      {tab === 'analyses' && (
        <div className="space-y-2">
          {!data.analyses?.length && <p className="text-sm text-t3">No analyses yet.</p>}
          {data.analyses?.map(a => (
            <div key={a.id} className="bg-surface border border-border rounded px-4 py-3 flex items-center gap-4">
              <ScorePill score={a.score || 0} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{a.jd_snippet || 'Job description'}</div>
                <div className="text-xs text-t3 mt-0.5">{a.scored_at?.slice(0, 16).replace('T', ' ')}</div>
              </div>
              <div className={`text-xs font-semibold ${
                a.label === 'Excellent' ? 'text-green' :
                a.label === 'Good' ? 'text-blue' :
                a.label === 'Partial' ? 'text-amber' : 'text-red'
              }`}>{a.label}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'runs' && (
        <div className="space-y-2">
          {!data.fetcher_runs?.length && <p className="text-sm text-t3">No fetcher runs yet.</p>}
          {data.fetcher_runs?.map((r, i) => (
            <div key={i} className="bg-surface border border-border rounded px-4 py-3 flex items-center gap-4">
              <span className="w-2 h-2 rounded-full bg-accent flex-shrink-0" />
              <div className="flex-1 text-sm text-t1">
                {r.detail || 'Fetch run completed'}
              </div>
              <div className="text-xs text-t3">{r.created_at?.slice(0, 16).replace('T', ' ')}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'applications' && (
        <div className="space-y-2">
          {!data.applications?.length && <p className="text-sm text-t3">No applications tracked yet.</p>}
          {data.applications?.map((a, i) => (
            <div key={i} className="bg-surface border border-border rounded px-4 py-3 flex items-center gap-3">
              <span className="text-xs text-t3">{a.created_at?.slice(0, 16).replace('T', ' ')}</span>
              <span className="text-sm">{a.job_id || a.detail || 'Job application'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
