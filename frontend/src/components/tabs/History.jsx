/**
 * History tab - past analyses (clickable to reopen the full result),
 * fetcher runs, and tracked applications.
 */
import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { errMsg } from '../../lib/errors.js'
import { useToast } from '../Toast.jsx'
import { ResultsPanel } from '../AnalysisResults.jsx'
import { PageHeader, PageSpinner, EmptyState, ListRow, ScorePill, ScoreLabel, Spinner } from '../ui.jsx'

function formatDate(str) {
  if (!str) return ''
  return str.slice(0, 16).replace('T', ' ')
}

// Application status -> badge styling. Empty status means plain "applied".
const APP_STATUS_STYLES = {
  applied:   { label: 'Applied',   background: 'rgba(var(--blue) / 0.08)',  borderColor: 'rgba(var(--blue) / 0.25)',  color: 'rgb(var(--blue))' },
  interview: { label: 'Interview', background: 'rgba(var(--amber) / 0.08)', borderColor: 'rgba(var(--amber) / 0.25)', color: 'rgb(var(--amber))' },
  offer:     { label: 'Offer',     background: 'rgba(var(--green) / 0.08)', borderColor: 'rgba(var(--green) / 0.25)', color: 'rgb(var(--green))' },
  rejected:  { label: 'Rejected',  background: 'rgba(var(--red) / 0.08)',   borderColor: 'rgba(var(--red) / 0.25)',   color: 'rgb(var(--red))' },
}

function AppStatusBadge({ status }) {
  const s = APP_STATUS_STYLES[status] || APP_STATUS_STYLES.applied
  return (
    <span className="px-2 py-0.5 text-[11px] font-medium rounded-sm border flex-shrink-0"
      style={{ background: s.background, borderColor: s.borderColor, color: s.color }}>
      {s.label}
    </span>
  )
}

// Fetcher run details are stored as a JSON blob - parse defensively and
// render a readable summary instead of the raw string.
function parseRun(detail) {
  try {
    const d = JSON.parse(detail)
    if (!d || typeof d !== 'object') return null
    return d
  } catch {
    return null
  }
}

function RunRow({ run }) {
  const d = parseRun(run.detail)
  if (!d) {
    return (
      <ListRow>
        <span className="w-2 h-2 rounded-full bg-accent flex-shrink-0" />
        <div className="flex-1 text-[13.5px] text-t1">{run.detail || 'Fetch run completed'}</div>
        <div className="text-[12px] text-t3 flex-shrink-0">{formatDate(run.created_at)}</div>
      </ListRow>
    )
  }

  const failed = Boolean(d.error)
  const dotColor = failed
    ? 'rgb(var(--red))'
    : d.stopped ? 'rgb(var(--amber))' : 'rgb(var(--green))'
  const sources = [
    d.adzuna ? `adzuna ${d.adzuna}` : '',
    d.arbeitnow ? `arbeitnow ${d.arbeitnow}` : '',
    d.bundesagentur ? `bundesagentur ${d.bundesagentur}` : '',
  ].filter(Boolean).join(' · ')

  return (
    <ListRow>
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: dotColor }} />
      <div className="flex-1 min-w-0">
        <div className="text-[13.5px] text-t1">
          {failed
            ? <>Run failed<span className="text-t3"> - {d.error}</span></>
            : <>{d.fetched || 0} fetched · {d.new || 0} new · <span className="font-semibold">{d.scored || 0} scored</span></>}
        </div>
        <div className="text-[12px] text-t3 mt-0.5">
          {d.manual ? 'Manual run' : 'Auto-fetch'}
          {d.stopped ? ' · stopped early' : ''}
          {sources ? ` · ${sources}` : ''}
        </div>
      </div>
      <div className="text-[12px] text-t3 flex-shrink-0">{formatDate(run.created_at)}</div>
    </ListRow>
  )
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
      .catch(() => { toast('Network error loading the analysis', 'error'); onClose() })
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
  const [failed, setFailed] = useState(false)
  const [tab, setTab] = useState('analyses')
  const [opened, setOpened] = useState(null)

  const load = useCallback(async () => {
    setFailed(false)
    setData(null)
    try {
      const res = await apiFetch('/api/history')
      const d = await res?.json().catch(() => ({}))
      if (!res?.ok || !d.ok) { setFailed(true); return }
      setData(d)
    } catch {
      setFailed(true)
    }
  }, [])

  useEffect(() => { load() }, [load])

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
        action={
          <button onClick={load} className="btn-secondary h-8 px-3 text-[12.5px]">
            Refresh
          </button>
        }
      />

      {/* Tab bar */}
      <div className="flex border-b border-border/10 gap-0.5">
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

      {!data && !failed && <PageSpinner />}

      {failed && (
        <EmptyState
          title="Could not load your history"
          description="The server did not respond - check your connection and try again."
          action={<button onClick={load} className="btn-primary px-5 py-2 text-[13.5px]">Retry</button>}
        />
      )}

      {/* Analyses */}
      {data && tab === 'analyses' && (
        data.analyses?.length
          ? <div className="space-y-2">
              {data.analyses.map((a, i) => {
                const clickable = Boolean(a.cache_hash)
                return (
                  <div key={a.cache_hash || i}
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
              {data.fetcher_runs.map((r, i) => <RunRow key={i} run={r} />)}
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
                  <AppStatusBadge status={(a.app_status || '').trim()} />
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
