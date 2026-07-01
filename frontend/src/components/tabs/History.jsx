import { useState, useEffect } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { PageHeader, PageSpinner, EmptyState, ListRow, ScorePill, ScoreLabel } from '../ui.jsx'

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

  const tabs = [
    { id: 'analyses',     label: 'Analyses',     count: data?.analyses?.length || 0 },
    { id: 'runs',         label: 'Fetcher runs',  count: data?.fetcher_runs?.length || 0 },
    { id: 'applications', label: 'Applications',  count: data?.applications?.length || 0 },
  ]

  return (
    <div className="space-y-5">
      <PageHeader
        title="History"
        description="Your past analyses, job fetch runs, and applications in one place."
      />

      {/* Tab bar */}
      <div className="flex border-b border-border gap-0.5">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-[13px] font-medium border-b-2 -mb-px transition-colors ${
              tab === t.id ? 'border-accent text-accent' : 'border-transparent text-t2 hover:text-t1'
            }`}
          >
            {t.label}
            {t.count > 0 && (
              <span className={`px-1.5 py-px text-[11px] rounded-sm ${
                tab === t.id ? 'bg-accent/10 text-accent' : 'bg-surface-2 text-t3'
              }`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {!data && <PageSpinner />}

      {/* Analyses */}
      {data && tab === 'analyses' && (
        data.analyses?.length
          ? <div className="space-y-2">
              {data.analyses.map(a => (
                <ListRow key={a.id}>
                  <ScorePill score={a.score || 0} />
                  <div className="flex-1 min-w-0">
                    <div className="text-[13.5px] font-medium text-t1 truncate">{a.jd_snippet || 'Job description'}</div>
                    <div className="text-[12px] text-t3 mt-0.5">{formatDate(a.scored_at)}</div>
                  </div>
                  <ScoreLabel score={a.score || 0} />
                </ListRow>
              ))}
            </div>
          : <EmptyState
              title="No analyses yet"
              description="Go to Resume Analyser to run your first analysis."
            />
      )}

      {/* Fetcher runs */}
      {data && tab === 'runs' && (
        data.fetcher_runs?.length
          ? <div className="space-y-2">
              {data.fetcher_runs.map((r, i) => (
                <ListRow key={i}>
                  <span className="w-2 h-2 rounded-full bg-accent flex-shrink-0" />
                  <div className="flex-1 text-[13.5px] text-t1">{r.detail || 'Fetch run completed'}</div>
                  <div className="text-[12px] text-t3 flex-shrink-0">{formatDate(r.created_at)}</div>
                </ListRow>
              ))}
            </div>
          : <EmptyState
              title="No fetcher runs yet"
              description="Go to Job Matches and click Fetch Jobs to start pulling listings."
            />
      )}

      {/* Applications */}
      {data && tab === 'applications' && (
        data.applications?.length
          ? <div className="space-y-2">
              {data.applications.map((a, i) => (
                <ListRow key={i}>
                  <span className="w-2 h-2 rounded-full bg-green flex-shrink-0" />
                  <div className="flex-1 text-[13.5px] text-t1">{a.job_id || a.detail || 'Job application'}</div>
                  <div className="text-[12px] text-t3 flex-shrink-0">{formatDate(a.created_at)}</div>
                </ListRow>
              ))}
            </div>
          : <EmptyState
              title="No applications tracked yet"
              description="Mark jobs as applied in the Job Matches tab to track them here."
            />
      )}
    </div>
  )
}
