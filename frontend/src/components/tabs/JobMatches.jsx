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
import { PageHeader, EmptyState, ScoreBadge, Card, CardBody, Spinner } from '../ui.jsx'

const listVariants = {
  show: { transition: { staggerChildren: 0.045 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.18, ease: [0.25, 0.1, 0.25, 1] } },
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

  return (
    <div className={`bg-surface border rounded-lg p-4 flex items-start gap-4 transition-shadow hover:shadow-md ${
      job.applied ? 'border-green-bd' : 'border-border'
    }`}>
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
      desc: 'In Settings, enter the job titles and location you want to search for.',
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
  const [pasteJob, setPasteJob] = useState(null)

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
  const results = allResults
    .filter(r => (r.score || 0) >= minScore)
    .sort((a, b) => {
      if (sortBy === 'score') return (b.score || 0) - (a.score || 0)
      // Newest first: posted_at may be an ISO string or unix timestamp
      return String(b.posted_at || '').localeCompare(String(a.posted_at || ''))
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

      {/* Active resume banner */}
      {hasResume && state?.resume_name && (
        <div className="text-[12.5px] text-t3">
          Scoring against: <span className="font-medium text-t2">{state.resume_name}</span>
        </div>
      )}

      {/* First-run setup */}
      {showSetup && <FirstRunSetup hasResume={Boolean(hasResume)} />}

      {/* Stats */}
      {allResults.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Total scored', value: allResults.length },
            { label: '60+ score',    value: allResults.filter(r => r.score >= 60).length },
            { label: 'Applied',      value: allResults.filter(r => r.applied).length },
          ].map(s => (
            <div key={s.label} className="bg-surface border border-border rounded-lg px-4 py-3">
              <div className="text-xl font-bold text-t1">{s.value}</div>
              <div className="text-[12px] text-t2 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter + sort + running progress */}
      <div className="flex items-center gap-3 flex-wrap">
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

        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          className="h-8 px-3 bg-surface border border-border rounded-sm text-[12.5px] text-t1 focus:outline-none focus:border-accent"
        >
          <option value="score">Highest score</option>
          <option value="date">Newest first</option>
        </select>

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
            ? 'No jobs match the current score filter. Try lowering the minimum score.'
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
