/**
 * Job Matches tab - live listings scored against the active resume, with
 * run progress, sorting, score filter, and manual JD scoring for jobs
 * whose description could not be fetched.
 */
import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { apiFetch } from '../../lib/auth.js'
import { errMsg } from '../../lib/errors.js'
import { useToast } from '../Toast.jsx'
import { PageHeader, EmptyState, ScoreBadge, Card, CardBody, CardSection, FieldLabel, Spinner } from '../ui.jsx'

const listVariants = {
  show: { transition: { staggerChildren: 0.045 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.18, ease: [0.25, 0.1, 0.25, 1] } },
}

// Jobs posted within this many days get the "New" badge and count as fresh.
const NEW_JOB_DAYS = 3

function parsePostedAt(postedAt) {
  if (!postedAt) return null
  const d = /^\d+$/.test(String(postedAt))
    ? new Date(Number(postedAt) * 1000)
    : new Date(postedAt)
  return isNaN(d.getTime()) ? null : d
}

function relTime(postedAt) {
  const d = parsePostedAt(postedAt)
  if (!d) return ''
  const days = Math.floor((Date.now() - d.getTime()) / 86400000)
  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

function isNewJob(postedAt) {
  const d = parsePostedAt(postedAt)
  return d ? (Date.now() - d.getTime()) / 86400000 <= NEW_JOB_DAYS : false
}

// Accessible on/off switch - off state uses a soft neutral track, not a
// solid fill, so both states read clearly.
function Switch({ on, onClick }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      onClick={onClick}
      className="relative w-10 h-6 rounded-full transition-colors flex-shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
      style={{ background: on ? 'rgb(var(--accent))' : 'rgba(var(--t3) / 0.35)' }}
    >
      <span
        className="absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"
        style={{ transform: on ? 'translateX(20px)' : 'translateX(4px)' }}
      />
    </button>
  )
}

// Toolbar filter chip - active state is accent-tinted, inactive is neutral.
function Chip({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="h-8 px-3 text-[12.5px] font-medium rounded-full border transition-colors"
      style={active
        ? { background: 'rgba(var(--accent) / 0.1)', borderColor: 'rgba(var(--accent) / 0.35)', color: 'rgb(var(--accent))' }
        : { background: 'rgb(var(--surface))', borderColor: 'rgba(var(--border) / 0.12)', color: 'rgb(var(--t2))' }}
    >
      {children}
    </button>
  )
}

// === Paste-JD modal for jobs whose description could not be fetched ===
function ScoreJdModal({ job, onClose, onScored }) {
  const toast = useToast()
  const [jdText, setJdText] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit() {
    if (jdText.trim().length < 50) { toast('Paste the full job description first', 'warn'); return }
    setBusy(true)
    try {
      const res = await apiFetch('/api/match/score-jd', {
        method: 'POST',
        body: JSON.stringify({ id: job.id, jd_text: jdText }),
      })
      const data = await res?.json().catch(() => ({}))
      if (!res?.ok || !data.ok) { toast(errMsg(data, 'Could not score this JD'), 'error'); return }
      toast(`Scored: ${Math.round(data.score)} / 100`, 'success')
      onScored()
      onClose()
    } finally { setBusy(false) }
  }

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }} onClick={onClose}>
      <div className="w-full max-w-lg rounded-xl p-5 space-y-4" style={{ background: 'rgb(var(--surface))' }}
        onClick={e => e.stopPropagation()}>
        <div>
          <div className="text-[14px] font-semibold text-t1">{job.title}</div>
          <div className="text-[12.5px] text-t2 mt-0.5">
            We could not fetch this job's description automatically. Open the posting, copy the description, and paste it here to score it.
          </div>
        </div>
        <textarea
          value={jdText}
          onChange={e => setJdText(e.target.value)}
          rows={8}
          placeholder="Paste the job description here..."
          className="input-base resize-none w-full"
        />
        <div className="flex justify-end gap-2">
          {job.url && (
            <a href={job.url} target="_blank" rel="noreferrer" className="btn-secondary px-4 flex items-center">Open posting</a>
          )}
          <button onClick={submit} disabled={busy} className="btn-primary px-5">
            {busy ? <><Spinner size={13} /> Scoring...</> : 'Score'}
          </button>
        </div>
      </div>
    </div>
  )
}

function JobCard({ job, onApply, onDelete, onPasteJd }) {
  const chips = (job.matched_required || []).slice(0, 5)
  const extra = (job.matched_required || []).length - chips.length
  const jdUnavailable = job.status === 'jd_unavailable'
  const posted = relTime(job.posted_at)
  const fresh = isNewJob(job.posted_at)

  return (
    <div className={`bg-surface border rounded-lg p-4 flex items-start gap-4 transition-shadow hover:shadow-md ${
      job.applied ? 'border-green-bd' : 'border-border'
    }`}>
      <ScoreBadge score={job.score || 0} />

      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 min-w-0">
              <div className="text-[14px] font-semibold text-t1 truncate">{job.title}</div>
              {fresh && (
                <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide rounded-sm"
                  style={{ background: 'rgba(var(--accent) / 0.1)', color: 'rgb(var(--accent))' }}>
                  New
                </span>
              )}
            </div>
            <div className="text-[12.5px] text-t2 mt-0.5">
              {job.company}
              {job.location && <span className="text-t3"> · {job.location}</span>}
              {posted && <span className="text-t3"> · {posted}</span>}
            </div>
          </div>
          {jdUnavailable && (
            <span className="flex-shrink-0 px-2 py-0.5 text-[11px] font-medium rounded-sm border"
              style={{ background: 'rgba(217,119,6,0.08)', borderColor: 'rgba(217,119,6,0.25)', color: '#d97706' }}>
              Needs manual JD
            </span>
          )}
          {job.applied ? (
            <span className="flex-shrink-0 px-2 py-0.5 text-[11px] font-medium rounded-sm bg-green-bg border border-green-bd text-green">
              Applied
            </span>
          ) : null}
        </div>

        {chips.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2.5">
            {chips.map(k => (
              <span key={k} className="px-2 py-0.5 text-[11px] font-medium rounded-sm bg-green-bg border border-green-bd text-green">{k}</span>
            ))}
            {extra > 0 && <span className="text-[11px] text-t3 self-center">+{extra}</span>}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1.5 flex-shrink-0">
        {jdUnavailable && (
          <button onClick={() => onPasteJd(job)}
            className="h-7 px-2.5 text-[12px] font-medium rounded-sm border transition-colors flex items-center"
            style={{ borderColor: 'rgba(217,119,6,0.35)', color: '#d97706' }}>
            Paste JD
          </button>
        )}
        {job.url && (
          <a href={job.url} target="_blank" rel="noreferrer"
            className="h-7 px-2.5 text-[12px] font-medium border border-border text-t2 hover:text-t1 hover:bg-hover rounded-sm transition-colors flex items-center">
            View
          </a>
        )}
        <button
          onClick={() => onApply(job)}
          className={`h-7 px-2.5 text-[12px] font-medium rounded-sm border transition-colors flex items-center ${
            job.applied ? 'bg-green-bg border-green-bd text-green' : 'border-border text-t2 hover:text-t1 hover:bg-hover'
          }`}
        >
          {job.applied ? 'Applied' : 'Mark applied'}
        </button>
        <button
          onClick={() => onDelete(job.id)}
          className="w-7 h-7 flex items-center justify-center text-t3 hover:text-red hover:bg-red-bg rounded-sm transition-colors"
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

// === Search settings panel (titles, location, countries, scheduler) ===
const SCHEDULER_INTERVALS = [
  { value: 30,   label: 'Every 30 minutes' },
  { value: 60,   label: 'Every hour' },
  { value: 180,  label: 'Every 3 hours' },
  { value: 360,  label: 'Every 6 hours' },
  { value: 720,  label: 'Every 12 hours' },
  { value: 1440, label: 'Once a day' },
]

function SearchCriteriaPanel({ state, onSaved, onSchedulerChange, onToggleScheduler }) {
  const toast = useToast()
  const [saving, setSaving] = useState(false)

  async function saveFilters(e) {
    e.preventDefault()
    setSaving(true)
    const fd = new FormData(e.target)
    const target_titles = (fd.get('titles') || '').split('\n').map(t => t.trim()).filter(Boolean)
    const location  = (fd.get('location') || '').trim()
    const countries = (fd.get('countries') || '').split(',').map(c => c.trim()).filter(Boolean)
    const res = await apiFetch('/api/match/filters', {
      method: 'POST',
      body: JSON.stringify({ target_titles, location, countries }),
    })
    const data = await res?.json().catch(() => ({}))
    setSaving(false)
    if (res?.ok && data.ok) { toast('Search criteria saved', 'success'); onSaved() }
    else toast(errMsg(data, 'Save failed'), 'error')
  }

  async function changeInterval(e) {
    const interval = Number(e.target.value)
    const res = await apiFetch('/api/match/scheduler', { method: 'POST', body: JSON.stringify({ interval }) })
    const data = await res?.json().catch(() => ({}))
    if (res?.ok && data.ok) onSchedulerChange({ interval: data.interval })
    else toast('Could not update the interval', 'error')
  }

  return (
    <div className="space-y-4">
      <form onSubmit={saveFilters}>
        <CardSection
          title="Search Criteria"
          action={
            <button type="submit" disabled={saving} className="btn-primary h-7 px-3.5 text-[12.5px]">
              {saving ? 'Saving...' : 'Save'}
            </button>
          }
        >
          <div className="space-y-4">
            <div>
              <FieldLabel hint="(one per line)">Job titles</FieldLabel>
              <textarea
                name="titles"
                defaultValue={(state.filters?.target_titles || []).join('\n')}
                rows={4}
                placeholder={"Software Engineer\nBackend Developer\nPython Developer"}
                className="input-base resize-none"
              />
            </div>
            <div>
              <FieldLabel>Location</FieldLabel>
              <input type="text" name="location" defaultValue={state.filters?.location || ''} placeholder="Berlin, Munich, Remote..." className="input-base" />
            </div>
            <div>
              <FieldLabel hint="(comma separated)">Countries</FieldLabel>
              <input type="text" name="countries" defaultValue={(state.filters?.countries || []).join(', ')} placeholder="de, at, ch" className="input-base" />
            </div>
          </div>
        </CardSection>
      </form>

      <CardSection title="Auto-fetch">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Switch on={Boolean(state.scheduler?.enabled)} onClick={onToggleScheduler} />
            <div>
              <div className="text-[13.5px] font-medium text-t1">
                {state.scheduler?.enabled ? 'Auto-fetch is on' : 'Auto-fetch is off'}
              </div>
              <div className="text-[12px] text-t3 mt-0.5">
                Fetch and score new jobs in the background while you are away.
              </div>
            </div>
          </div>
          {state.scheduler?.enabled && (
            <select
              value={state.scheduler?.interval || 60}
              onChange={changeInterval}
              className="h-8 px-3 bg-surface border rounded-sm text-[12.5px] text-t1 focus:outline-none focus:border-accent"
              style={{ borderColor: 'rgba(var(--border) / 0.12)' }}
            >
              {SCHEDULER_INTERVALS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
              {!SCHEDULER_INTERVALS.some(o => o.value === (state.scheduler?.interval || 60)) && (
                <option value={state.scheduler.interval}>Every {state.scheduler.interval} min</option>
              )}
            </select>
          )}
        </div>
      </CardSection>
    </div>
  )
}


// === First-run setup guidance ===
function FirstRunSetup({ hasResume }) {
  const steps = [
    {
      done: hasResume,
      title: 'Activate a resume',
      desc: 'Go to Resumes and click "Use for matching" on the resume you want jobs scored against.',
    },
    {
      done: false,
      title: 'Set your search targets',
      desc: 'Click "Search criteria" above and enter the job titles and location you want to search for.',
    },
    {
      done: false,
      title: 'Fetch jobs',
      desc: 'Click Fetch Jobs above - listings are pulled from three sources and scored automatically.',
    },
  ]
  return (
    <Card>
      <CardBody className="py-5 space-y-4">
        <div className="text-[14px] font-semibold text-t1">Set up job matching</div>
        {steps.map((s, i) => (
          <div key={i} className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full flex items-center justify-center text-[12px] font-bold flex-shrink-0"
              style={s.done
                ? { background: 'rgba(22,163,74,0.1)', color: '#16a34a' }
                : { background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
              {s.done
                ? <svg width="11" height="11" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M2.5 7l3 3 6-6"/></svg>
                : i + 1}
            </span>
            <div>
              <div className="text-[13px] font-semibold text-t1">{s.title}</div>
              <div className="text-[12.5px] text-t2 mt-0.5">{s.desc}</div>
            </div>
          </div>
        ))}
      </CardBody>
    </Card>
  )
}

export default function JobMatches() {
  const toast = useToast()
  const [state, setState] = useState(null)
  const [running, setRunning] = useState(false)
  const [minScore, setMinScore] = useState(0)
  const [sortBy, setSortBy] = useState('score')
  const [hideApplied, setHideApplied] = useState(false)
  const [pasteJob, setPasteJob] = useState(null)
  const [showSettings, setShowSettings] = useState(false)

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
      if (!d.run_status?.running) {
        setRunning(false)
        toast('Job fetch complete', 'success')
      }
    }, 3000)
    return () => clearInterval(iv)
  }, [running, toast])

  async function toggleAutoFetch() {
    const enabled = !state?.scheduler?.enabled
    const res = await apiFetch('/api/match/scheduler', { method: 'POST', body: JSON.stringify({ enabled }) })
    if (res?.ok) {
      setState(s => s ? { ...s, scheduler: { ...s.scheduler, enabled } } : s)
      toast(enabled ? 'Auto-fetch enabled' : 'Auto-fetch disabled', 'success')
    } else {
      toast('Could not update scheduler', 'error')
    }
  }

  async function runFetch() {
    const res = await apiFetch('/api/match/run')
    const data = await res?.json().catch(() => ({}))
    if (res?.ok && data.ok) { setRunning(true); toast('Fetching and scoring jobs...', 'info') }
    else toast(errMsg(data, 'Could not start fetch'), 'error')
  }

  async function toggleApplied(job) {
    const next = !job.applied
    const res = await apiFetch('/api/match/applied', {
      method: 'POST',
      body: JSON.stringify({ id: job.id, applied: next }),
    })
    if (!res?.ok) { toast('Could not update applied status', 'error'); return }
    setState(s => s ? { ...s, results: s.results.map(r => r.id === job.id ? { ...r, applied: next } : r) } : s)
  }

  async function deleteJob(id) {
    await apiFetch('/api/match/delete', { method: 'POST', body: JSON.stringify({ id }) })
    setState(s => s ? { ...s, results: s.results.filter(r => r.id !== id) } : s)
  }

  async function exportCsv() {
    const res = await apiFetch('/api/match/export')
    if (!res?.ok) { toast('Export failed', 'error'); return }
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob); a.download = 'job_matches.csv'; a.click()
    toast('Exported', 'success')
  }

  const allResults = state?.results || []
  const newCount = allResults.filter(r => isNewJob(r.posted_at)).length
  const results = allResults
    .filter(r => (r.score || 0) >= minScore)
    .filter(r => !hideApplied || !r.applied)
    .sort((a, b) => {
      if (sortBy === 'score') return (b.score || 0) - (a.score || 0)
      // Newest first: compare parsed dates so ISO strings and unix
      // timestamps from different sources sort together correctly
      const da = parsePostedAt(a.posted_at)?.getTime() || 0
      const db = parsePostedAt(b.posted_at)?.getTime() || 0
      return db - da
    })

  const hasResume = state?.has_resume
  const showSetup = state && !hasResume && allResults.length === 0
  const runStatus = state?.run_status || {}

  return (
    <div className="space-y-5">
      <PageHeader
        title="Job Matches"
        description="Fetch live job listings from Adzuna, Arbeitnow, and Bundesagentur - automatically scored against your active resume."
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(v => !v)}
              className={`btn-secondary h-8 px-3 text-[12.5px] ${showSettings ? 'text-accent' : ''}`}
            >
              {showSettings ? 'Hide criteria' : 'Search criteria'}
            </button>
            <button onClick={exportCsv} className="btn-secondary h-8 px-3 text-[12.5px]">Export CSV</button>
            <button onClick={runFetch} disabled={running || !hasResume} className="btn-primary h-8 px-4 text-[12.5px]"
              title={!hasResume ? 'Activate a resume in the Resumes tab first' : ''}>
              {running
                ? <><span className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />Running...</>
                : 'Fetch Jobs'}
            </button>
          </div>
        }
      />

      {/* Context strip: active resume + auto-fetch status */}
      {hasResume && state?.resume_name && (
        <div className="flex items-center gap-3 flex-wrap text-[12.5px] text-t3">
          <span>
            Scoring against: <span className="font-medium text-t2">{state.resume_name}</span>
          </span>
          <button
            type="button"
            onClick={toggleAutoFetch}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-full border transition-colors hover:bg-hover"
            style={{ borderColor: 'rgba(var(--border) / 0.12)' }}
            title="Toggle auto-fetch"
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: state.scheduler?.enabled ? 'rgb(var(--green))' : 'rgba(var(--t3) / 0.5)' }}
            />
            {state.scheduler?.enabled
              ? `Auto-fetch on · every ${state.scheduler?.interval || 60} min`
              : 'Auto-fetch off'}
          </button>
        </div>
      )}

      {/* Search criteria */}
      {showSettings && state && (
        <SearchCriteriaPanel
          state={state}
          onSaved={load}
          onToggleScheduler={toggleAutoFetch}
          onSchedulerChange={patch =>
            setState(s => s ? { ...s, scheduler: { ...s.scheduler, ...patch } } : s)}
        />
      )}

      {/* First-run setup */}
      {showSetup && <FirstRunSetup hasResume={Boolean(hasResume)} />}

      {/* Stats */}
      {allResults.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Total scored',                    value: allResults.length },
            { label: `New (last ${NEW_JOB_DAYS} days)`, value: newCount, accent: true },
            { label: 'Good matches (60+)',              value: allResults.filter(r => r.score >= 60).length },
            { label: 'Applied',                         value: allResults.filter(r => r.applied).length },
          ].map(s => (
            <div key={s.label} className="bg-surface border rounded-lg px-4 py-3"
              style={{ borderColor: 'rgba(var(--border) / 0.08)' }}>
              <div className="text-xl font-bold" style={{ color: s.accent && s.value > 0 ? 'rgb(var(--accent))' : 'rgb(var(--t1))' }}>
                {s.value}
              </div>
              <div className="text-[12px] text-t2 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter + sort + running progress */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1.5">
          {[
            { v: 0,  label: 'All' },
            { v: 40, label: '40+' },
            { v: 60, label: '60+' },
            { v: 80, label: '80+' },
          ].map(o => (
            <Chip key={o.v} active={minScore === o.v} onClick={() => setMinScore(o.v)}>{o.label}</Chip>
          ))}
        </div>

        <span className="w-px h-5 mx-1" style={{ background: 'rgba(var(--border) / 0.12)' }} />

        <Chip active={sortBy === 'score'} onClick={() => setSortBy('score')}>Top score</Chip>
        <Chip active={sortBy === 'date'} onClick={() => setSortBy('date')}>Newest</Chip>

        <span className="w-px h-5 mx-1" style={{ background: 'rgba(var(--border) / 0.12)' }} />

        <Chip active={hideApplied} onClick={() => setHideApplied(v => !v)}>Hide applied</Chip>

        {running && (
          <div className="flex items-center gap-2 text-[13px] font-medium text-blue">
            <span className="w-2 h-2 rounded-full bg-blue animate-pulse" />
            {runStatus.phase === 'fetching' && 'Fetching listings from job boards...'}
            {runStatus.phase !== 'fetching' && (
              runStatus.total > 0
                ? `Scoring jobs: ${runStatus.checked || 0} of ${runStatus.total} checked, ${runStatus.scored || 0} scored`
                : 'Scoring jobs...'
            )}
          </div>
        )}

        {results.length > 0 && (
          <span className="ml-auto text-[12px] text-t3">
            {results.length} of {allResults.length} job{allResults.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Empty */}
      {!results.length && !running && !showSetup && (
        <EmptyState
          icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>}
          title="No job matches yet"
          description={allResults.length > 0
            ? 'No jobs match the current filters. Try lowering the minimum score or including applied jobs.'
            : 'Click Fetch Jobs to pull live listings scored against your resume.'}
          action={allResults.length === 0
            ? <button onClick={runFetch} disabled={running} className="btn-primary px-5 py-2 text-[13.5px]">Fetch Jobs</button>
            : null}
        />
      )}

      {/* List */}
      {results.length > 0 && (
        <motion.div className="space-y-2.5" variants={listVariants} initial="hidden" animate="show">
          {results.map(r => (
            <motion.div key={r.id} variants={itemVariants}>
              <JobCard job={r} onApply={toggleApplied} onDelete={deleteJob} onPasteJd={setPasteJob} />
            </motion.div>
          ))}
        </motion.div>
      )}

      {pasteJob && (
        <ScoreJdModal job={pasteJob} onClose={() => setPasteJob(null)} onScored={load} />
      )}
    </div>
  )
}
