/**
 * History tab - past analyses (clickable to reopen the full result),
 * fetcher runs, and tracked applications.
 */
import { useState, useEffect } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { errMsg } from '../../lib/errors.js'
import { useToast } from '../Toast.jsx'
import { ResultsPanel } from '../AnalysisResults.jsx'
import { PageHeader, PageSpinner, EmptyState, ListRow, ScorePill, ScoreLabel, Spinner } from '../ui.jsx'

function formatDate(str) {
  if (!str) return ''
  return str.slice(0, 16).replace('T', ' ')
}

// === Modal reopening the full cached result of a past analysis ===
function AnalysisModal({ row, onClose }) {
  const toast = useToast()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch(`/api/history/analysis?hash=${encodeURIComponent(row.cache_hash)}`)
      .then(async res => {
        const data = await res?.json().catch(() => ({}))
        if (!res?.ok || !data.ok) { toast(errMsg(data), 'warn'); onClose(); return }
        setResult(data)
        setLoading(false)
      })
  }, [row.cache_hash, onClose, toast])

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }} onClick={onClose}>
      <div className="w-full max-w-3xl max-h-[90vh] overflow-auto rounded-xl p-5"
        style={{ background: 'rgb(var(--bg))' }} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-[14px] font-semibold text-t1">Past analysis</div>
            <div className="text-[12px] text-t3 mt-0.5">{row.resume_label || 'Resume'} · {formatDate(row.scored_at)}</div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg text-t2 hover:bg-surface-2 transition-colors">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 2l10 10M12 2L2 12"/>
            </svg>
          </button>
        </div>
        {loading && <div className="py-16 flex justify-center"><Spinner size={22} /></div>}
        {result && <ResultsPanel result={result} />}
      </div>
    </div>
  )
}

export default function History() {
  const [data, setData] = useState(null)
  const [tab, setTab] = useState('analyses')
  const [opened, setOpened] = useState(null)

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
              {data.analyses.map((a, i) => {
                const clickable = Boolean(a.cache_hash)
                return (
                  <div key={i}
                    onClick={clickable ? () => setOpened(a) : undefined}
                    className={clickable ? 'cursor-pointer' : ''}
                    title={clickable ? 'Click to reopen the full result' : ''}>
                    <ListRow>
                      <ScorePill score={a.score || 0} />
                      <div className="flex-1 min-w-0">
                        <div className="text-[13.5px] font-medium text-t1 truncate">{a.jd_snippet || 'Job description'}</div>
                        <div className="text-[12px] text-t3 mt-0.5">
                          {a.resume_label ? `${a.resume_label} · ` : ''}{formatDate(a.scored_at)}
                        </div>
                      </div>
                      <ScoreLabel score={a.score || 0} />
                      {clickable && (
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="rgb(var(--t3))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                          <path d="M6 4l4 4-4 4"/>
                        </svg>
                      )}
                    </ListRow>
                  </div>
                )
              })}
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
                  <ScorePill score={a.score || 0} />
                  <div className="flex-1 min-w-0">
                    <div className="text-[13.5px] font-medium text-t1 truncate">
                      {a.title || 'Job application'}{a.company ? ` - ${a.company}` : ''}
                    </div>
                    <div className="text-[12px] text-t3 mt-0.5">Applied {formatDate(a.applied_at)}</div>
                  </div>
                  {a.url && (
                    <a href={a.url} target="_blank" rel="noreferrer"
                      className="text-[12px] font-medium flex-shrink-0" style={{ color: 'rgb(var(--accent))' }}>
                      View posting
                    </a>
                  )}
                </ListRow>
              ))}
            </div>
          : <EmptyState
              title="No applications tracked yet"
              description="Mark jobs as applied in the Job Matches tab to track them here."
            />
      )}

      {opened && <AnalysisModal row={opened} onClose={() => setOpened(null)} />}
    </div>
  )
}
