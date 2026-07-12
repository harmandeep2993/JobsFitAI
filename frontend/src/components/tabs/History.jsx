/**
 * History tab - past analyses (clickable to reopen the full result),
 * fetcher runs, and tracked applications, grouped by day.
 */
import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { apiFetch } from '../../lib/auth.js'
import { errMsg } from '../../lib/errors.js'
import { useToast } from '../Toast.jsx'
import { ResultsPanel } from '../AnalysisResults.jsx'
import { PageHeader, PageSpinner, EmptyState, ScorePill, ScoreLabel, Spinner } from '../ui.jsx'

function formatTime(str) {
  if (!str) return ''
  return str.slice(11, 16)
}

function dayKey(str) {
  return (str || '').slice(0, 10)
}

function dayLabel(key) {
  if (!key) return 'Unknown date'
  const today = new Date().toISOString().slice(0, 10)
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  if (key === today) return 'Today'
  if (key === yesterday) return 'Yesterday'
  const d = new Date(key)
  if (isNaN(d.getTime())) return key
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

// Group rows into [{ key, label, rows }] by calendar day of dateField.
function groupByDay(rows, dateField) {
  const groups = []
  const index = {}
  for (const row of rows) {
    const key = dayKey(row[dateField])
    if (!(key in index)) {
      index[key] = groups.length
      groups.push({ key, label: dayLabel(key), rows: [] })
    }
    groups[index[key]].rows.push(row)
  }
  return groups
}

const listVariants = { show: { transition: { staggerChildren: 0.03 } } }
const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.16, ease: [0.25, 0.1, 0.25, 1] } },
}

function DayHeader({ label }) {
  return (
    <div className="flex items-center gap-3 pt-2">
      <span className="text-[11px] font-semibold text-t3 uppercase tracking-[0.07em] flex-shrink-0">{label}</span>
      <span className="flex-1 h-px" style={{ background: 'rgba(var(--border) / 0.08)' }} />
    </div>
  )
}

function Row({ children, onClick, title }) {
  return (
    <div
      onClick={onClick}
      title={title}
      className={`bg-surface border rounded-lg px-4 py-3 flex items-center gap-3.5 transition-shadow ${
        onClick ? 'cursor-pointer hover:shadow-md' : ''
      }`}
      style={{ borderColor: 'rgba(var(--border) / 0.08)' }}
    >
      {children}
    </div>
  )
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
  const failed = Boolean(d?.error)
  const dotColor = !d
    ? 'rgb(var(--accent))'
    : failed
      ? 'rgb(var(--red))'
      : d.stopped ? 'rgb(var(--amber))' : 'rgb(var(--green))'

  const sources = d
    ? [
        d.adzuna ? `adzuna ${d.adzuna}` : '',
        d.arbeitnow ? `arbeitnow ${d.arbeitnow}` : '',
        d.bundesagentur ? `bundesagentur ${d.bundesagentur}` : '',
      ].filter(Boolean).join(' · ')
    : ''

  return (
    <div className="flex gap-3.5">
      {/* Timeline rail */}
      <div className="flex flex-col items-center flex-shrink-0 pt-4">
        <span className="w-2.5 h-2.5 rounded-full border-2 flex-shrink-0"
          style={{ borderColor: dotColor, background: 'rgb(var(--surface))' }} />
        <span className="w-px flex-1 mt-1" style={{ background: 'rgba(var(--border) / 0.1)' }} />
      </div>

      <div className="flex-1 min-w-0 pb-2.5">
        <Row>
          <div className="flex-1 min-w-0">
            <div className="text-[13.5px] text-t1">
              {!d && (run.detail || 'Fetch run completed')}
              {d && failed && <>Run failed<span className="text-t3"> - {d.error}</span></>}
              {d && !failed && (
                <>
                  <span className="font-semibold">{d.scored || 0} scored</span>
                  <span className="text-t2"> · {d.new || 0} new of {d.fetched || 0} fetched</span>
                </>
              )}
            </div>
            {d && (
              <div className="text-[12px] text-t3 mt-0.5">
                {d.manual ? 'Manual run' : 'Auto-fetch'}
                {d.stopped ? ' · stopped early' : ''}
                {sources ? ` · ${sources}` : ''}
              </div>
            )}
          </div>
          <div className="text-[12px] text-t3 flex-shrink-0">{formatTime(run.created_at)}</div>
        </Row>
      </div>
    </div>
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
            <div className="text-[12px] text-t3 mt-0.5">
              {row.resume_label || 'Resume'} · {dayLabel(dayKey(row.scored_at))} {formatTime(row.scored_at)}
            </div>
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
    { id: 'runs',         label: 'Fetch runs',    count: data?.fetcher_runs?.length || 0 },
    { id: 'applications', label: 'Applications',  count: data?.applications?.length || 0 },
  ]

  const analysisGroups = data ? groupByDay(data.analyses || [], 'scored_at') : []
  const runGroups      = data ? groupByDay(data.fetcher_runs || [], 'created_at') : []
  const appGroups      = data ? groupByDay(data.applications || [], 'applied_at') : []

  return (
    <div className="space-y-5 max-w-3xl">
      <PageHeader
        title="History"
        description="Your past analyses, job fetch runs, and applications in one place."
        action={
          <button onClick={load} className="btn-secondary h-8 px-3 text-[12.5px]">
            Refresh
          </button>
        }
      />

      {/* Segmented tab control */}
      <div className="inline-flex p-1 rounded-lg gap-0.5" style={{ background: 'rgb(var(--surface-2))' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 h-8 text-[12.5px] font-medium rounded-md transition-all ${
              tab === t.id ? 'bg-surface text-t1 shadow-sm' : 'text-t2 hover:text-t1'
            }`}
          >
            {t.label}
            {t.count > 0 && (
              <span className={`px-1.5 py-px text-[11px] rounded-sm font-semibold ${
                tab === t.id ? 'text-accent' : 'text-t3'
              }`} style={tab === t.id ? { background: 'rgba(var(--accent) / 0.1)' } : {}}>
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

      <AnimatePresence mode="wait">
        {data && (
          <motion.div key={tab} variants={listVariants} initial="hidden" animate="show" className="space-y-3">

            {/* Analyses */}
            {tab === 'analyses' && (
              analysisGroups.length
                ? analysisGroups.map(g => (
                    <div key={g.key} className="space-y-2">
                      <DayHeader label={g.label} />
                      {g.rows.map((a, i) => {
                        const clickable = Boolean(a.cache_hash)
                        return (
                          <motion.div key={a.cache_hash || i} variants={itemVariants}>
                            <Row
                              onClick={clickable ? () => setOpened(a) : undefined}
                              title={clickable ? 'Click to reopen the full result' : ''}
                            >
                              <ScorePill score={a.score || 0} />
                              <div className="flex-1 min-w-0">
                                <div className="text-[13.5px] font-medium text-t1 truncate">{a.jd_snippet || 'Job description'}</div>
                                <div className="text-[12px] text-t3 mt-0.5">
                                  {a.resume_label ? `${a.resume_label} · ` : ''}{formatTime(a.scored_at)}
                                </div>
                              </div>
                              <ScoreLabel score={a.score || 0} />
                              {clickable && (
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="rgb(var(--t3))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0">
                                  <path d="M6 4l4 4-4 4"/>
                                </svg>
                              )}
                            </Row>
                          </motion.div>
                        )
                      })}
                    </div>
                  ))
                : <EmptyState
                    title="No analyses yet"
                    description="Go to Resume Analyser to run your first analysis."
                  />
            )}

            {/* Fetch runs - timeline */}
            {tab === 'runs' && (
              runGroups.length
                ? runGroups.map(g => (
                    <div key={g.key} className="space-y-1">
                      <DayHeader label={g.label} />
                      <div className="pt-1.5">
                        {g.rows.map((r, i) => (
                          <motion.div key={i} variants={itemVariants}>
                            <RunRow run={r} />
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  ))
                : <EmptyState
                    title="No fetch runs yet"
                    description="Go to Job Matches and click Fetch Jobs to start pulling listings."
                  />
            )}

            {/* Applications */}
            {tab === 'applications' && (
              appGroups.length
                ? appGroups.map(g => (
                    <div key={g.key} className="space-y-2">
                      <DayHeader label={g.label} />
                      {g.rows.map((a, i) => (
                        <motion.div key={i} variants={itemVariants}>
                          <Row>
                            <ScorePill score={a.score || 0} />
                            <div className="flex-1 min-w-0">
                              <div className="text-[13.5px] font-medium text-t1 truncate">
                                {a.title || 'Job application'}
                                {a.company ? <span className="text-t2 font-normal"> · {a.company}</span> : ''}
                              </div>
                              <div className="text-[12px] text-t3 mt-0.5">Applied at {formatTime(a.applied_at)}</div>
                            </div>
                            <AppStatusBadge status={(a.app_status || '').trim()} />
                            {a.url && (
                              <a href={a.url} target="_blank" rel="noreferrer"
                                onClick={e => e.stopPropagation()}
                                className="text-[12px] font-medium flex-shrink-0 hover:underline" style={{ color: 'rgb(var(--accent))' }}>
                                View posting
                              </a>
                            )}
                          </Row>
                        </motion.div>
                      ))}
                    </div>
                  ))
                : <EmptyState
                    title="No applications tracked yet"
                    description="Mark jobs as applied in the Job Matches tab to track them here."
                  />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {opened && <AnalysisModal row={opened} onClose={() => setOpened(null)} />}
    </div>
  )
}
