/**
 * Analyzer tab - two upload boxes side by side, staged progress, results,
 * and a follow-up "Improve my resume" flow fed by the identified gaps.
 */
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { apiFetch } from '../../lib/auth.js'
import { errMsg } from '../../lib/errors.js'
import { useToast } from '../Toast.jsx'
import { ResumePicker } from '../ResumePicker.jsx'
import { ResultsPanel } from '../AnalysisResults.jsx'
import {
  PageHeader, Card, CardBody, SectionLabel, Spinner,
} from '../ui.jsx'

// Soft indigo tint - same for upload zone and textarea
const INNER_BG = 'rgba(99,102,241,0.04)'
const INNER_BORDER = 'rgba(99,102,241,0.18)'
const BOX_HEIGHT = '218px'

// Staged progress labels shown while the pipeline runs. Times are rough
// estimates of when each phase typically starts (seconds).
const STAGES = [
  { at: 0,  label: 'Reading your resume...' },
  { at: 4,  label: 'Extracting resume and job description with AI...' },
  { at: 14, label: 'Scoring your match...' },
  { at: 20, label: 'Writing your personalised summary...' },
]

// === Clear button - accent coloured ===
function ClearBtn({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-6 h-6 flex items-center justify-center rounded-sm transition-colors flex-shrink-0"
      title="Clear"
      style={{ color: 'rgb(var(--accent))', background: 'rgba(99,102,241,0.08)' }}
      onMouseEnter={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.16)' }}
      onMouseLeave={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.08)' }}
    >
      <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 2l10 10M12 2L2 12"/>
      </svg>
    </button>
  )
}

// === First-run onboarding banner ===
function OnboardingBanner({ hasResumes, hasJd, hasResult }) {
  const steps = [
    { done: hasResumes, label: 'Select or upload a resume' },
    { done: hasJd,      label: 'Paste a job description' },
    { done: hasResult,  label: 'Click Analyse to get your match score' },
  ]
  return (
    <Card>
      <CardBody className="py-4">
        <div className="text-[13.5px] font-semibold text-t1 mb-3">Welcome! Get your first match score in 3 steps:</div>
        <div className="flex flex-col sm:flex-row gap-3">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center gap-2 flex-1">
              <span className="w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0"
                style={s.done
                  ? { background: 'rgba(22,163,74,0.1)', color: '#16a34a' }
                  : { background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
                {s.done
                  ? <svg width="10" height="10" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M2.5 7l3 3 6-6"/></svg>
                  : i + 1}
              </span>
              <span className={`text-[12.5px] ${s.done ? 'text-t3 line-through' : 'text-t2'}`}>{s.label}</span>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  )
}

// === Improve resume panel (post-analysis flow) ===
function ImprovePanel({ result, jd }) {
  const toast = useToast()
  const [loading, setLoading] = useState(false)
  const [improve, setImprove] = useState(null)

  async function run() {
    setLoading(true)
    try {
      const res = await apiFetch('/api/improve-resume', {
        method: 'POST',
        body: JSON.stringify({
          jd,
          gaps: result.summary?.gaps || [],
          strengths: result.summary?.strengths || [],
        }),
      })
      const data = await res?.json().catch(() => ({}))
      if (!res?.ok || !data.ok) { toast(errMsg(data), 'error'); return }
      setImprove(data)
    } catch (e) {
      toast(errMsg(e.message), 'error')
    } finally {
      setLoading(false)
    }
  }

  if (!improve) {
    return (
      <Card>
        <CardBody className="flex flex-col sm:flex-row items-start sm:items-center gap-3 py-4">
          <div className="flex-1">
            <div className="text-[13.5px] font-semibold text-t1">Close the gaps</div>
            <div className="text-[12.5px] text-t2 mt-0.5">
              Generate improved, JD-aligned bullet points from your stored resumes - targeting the gaps found above.
            </div>
          </div>
          <button onClick={run} disabled={loading} className="btn-primary px-5 flex-shrink-0">
            {loading ? <><Spinner size={13} /> Generating...</> : 'Improve my resume'}
          </button>
        </CardBody>
      </Card>
    )
  }

  return (
    <Card>
      <CardBody className="space-y-5">
        <SectionLabel>Suggested improvements</SectionLabel>
        {improve.sections.map(sec => (
          <div key={sec.group}>
            <div className="text-[12.5px] font-semibold text-t1 mb-2">{sec.group}</div>
            <div className="space-y-2.5">
              {sec.items.filter(it => it.after).map((it, i) => (
                <div key={i} className="rounded-lg p-3 space-y-1.5" style={{ background: 'rgb(var(--surface-2))' }}>
                  {it.before && it.changed && (
                    <div className="text-[12px] text-t3 line-through leading-relaxed">{it.before}</div>
                  )}
                  <div className="flex items-start gap-2">
                    <span className="flex-shrink-0 mt-0.5 px-1.5 py-px text-[10.5px] font-semibold rounded-sm"
                      style={{ background: 'rgba(22,163,74,0.1)', color: '#16a34a' }}>{it.badge}</span>
                    <div className="text-[13px] text-t1 leading-relaxed flex-1">{it.after}</div>
                    <button
                      onClick={() => { navigator.clipboard.writeText(it.after) }}
                      className="flex-shrink-0 text-[11px] font-medium px-2 py-0.5 rounded-sm transition-colors"
                      style={{ color: 'rgb(var(--accent))', background: 'rgba(99,102,241,0.08)' }}
                      title="Copy bullet"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </CardBody>
    </Card>
  )
}

// === Main ===
export default function Analyzer() {
  const toast = useToast()
  const [resumeSrc, setResumeSrc] = useState(null)   // {file, resumeId, name}
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [stage, setStage] = useState(0)
  const [result, setResult] = useState(null)
  const [hasResumes, setHasResumes] = useState(true) // assume true until checked
  // Last score per resume+JD input pair, so a re-run shows the delta
  const lastScoreRef = useRef({})

  useEffect(() => {
    apiFetch('/api/resumes').then(r => r?.json()).then(d => {
      setHasResumes((d?.resumes || []).length > 0)
    }).catch(() => {})
  }, [])

  // Advance the staged progress label while an analysis runs
  useEffect(() => {
    if (!loading) { setStage(0); return }
    const t0 = Date.now()
    const iv = setInterval(() => {
      const elapsed = (Date.now() - t0) / 1000
      const idx = STAGES.reduce((acc, s, i) => (elapsed >= s.at ? i : acc), 0)
      setStage(idx)
    }, 1000)
    return () => clearInterval(iv)
  }, [loading])

  const canAnalyze = resumeSrc && jd.trim().length >= 50

  async function analyze() {
    if (!resumeSrc) { toast('Select or upload a resume first', 'warn'); return }
    if (jd.trim().length < 50) { toast('Job description is too short', 'warn'); return }
    setLoading(true); setResult(null)
    try {
      let body = { jd }
      if (resumeSrc.file) {
        const fd = new FormData()
        fd.append('file', resumeSrc.file)
        const up = await apiFetch('/api/upload', { method: 'POST', body: fd })
        if (!up?.ok) { toast('Upload failed', 'error'); return }
        const upData = await up.json()
        if (!upData.ok) { toast(errMsg(upData, 'Upload failed'), 'error'); return }
        body.tmp = upData.tmp
      } else {
        body.resume_id = resumeSrc.resumeId
      }

      const res = await apiFetch('/api/analyze', { method: 'POST', body: JSON.stringify(body) })
      const data = await res?.json().catch(() => ({}))
      if (!res?.ok || !data.ok) { toast(errMsg(data, 'Analysis failed'), 'error'); return }

      // Delta vs the previous run of the same resume+JD input pair
      const key = `${resumeSrc.resumeId || resumeSrc.name}::${jd.trim().slice(0, 200)}`
      const prev = lastScoreRef.current[key]
      data._delta = prev !== undefined ? Math.round(data.score) - prev : null
      lastScoreRef.current[key] = Math.round(data.score)

      setResult(data)
    } catch (e) {
      toast(errMsg(e.message), 'error')
    } finally {
      setLoading(false)
    }
  }

  const showOnboarding = !hasResumes && !result

  return (
    <div className="space-y-5">
      <PageHeader
        title="Resume Analyser"
        description="Choose a stored resume or upload a new one, then paste a job description to get an AI-powered match score."
      />

      {showOnboarding && (
        <OnboardingBanner hasResumes={Boolean(resumeSrc)} hasJd={jd.trim().length >= 50} hasResult={Boolean(result)} />
      )}

      {/* Input boxes + action row */}
      <div className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Resume box */}
          <Card>
            <div className="px-5 py-3 border-b flex items-center justify-between" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
              <span className="text-[13px] font-semibold text-t1">Resume</span>
              {resumeSrc && <ClearBtn onClick={() => { setResumeSrc(null); setResult(null) }} />}
            </div>
            <CardBody className="p-4">
              <ResumePicker
                selected={resumeSrc}
                onSelect={src => { setResumeSrc(src); setResult(null) }}
                onClear={() => { setResumeSrc(null); setResult(null) }}
                height={BOX_HEIGHT}
              />
            </CardBody>
          </Card>

          {/* JD box */}
          <Card>
            <div className="px-5 py-3 border-b flex items-center justify-between" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
              <span className="text-[13px] font-semibold text-t1">Job Description</span>
              <div className="flex items-center gap-2">
                <span className={`text-[11px] font-medium ${jd.length >= 50 ? 'text-green' : 'text-t3'}`}>
                  {jd.length < 50 ? `${50 - jd.length} more chars` : `${jd.length} chars`}
                </span>
                {jd && <ClearBtn onClick={() => { setJd(''); setResult(null) }} />}
              </div>
            </div>
            <CardBody className="p-4">
              <div className="relative" style={{ height: BOX_HEIGHT }}>
                {!jd && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 pointer-events-none select-none rounded-lg"
                    style={{ background: INNER_BG, border: `2px dashed ${INNER_BORDER}` }}>
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.1)' }}>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/><line x1="8" y1="9" x2="10" y2="9"/>
                      </svg>
                    </div>
                    <div className="text-[13px] font-semibold text-t2">Paste job description</div>
                    <div className="text-[12px] text-t3 text-center px-6">Paste the full job description here...</div>
                  </div>
                )}
                <textarea
                  value={jd}
                  onChange={e => setJd(e.target.value)}
                  className="input-base resize-none w-full h-full"
                  style={{
                    background: jd ? INNER_BG : 'transparent',
                    border: jd ? `2px dashed ${INNER_BORDER}` : '2px dashed transparent',
                    color: 'rgb(var(--t1))',
                    position: 'relative',
                    zIndex: 1,
                  }}
                />
              </div>
            </CardBody>
          </Card>
        </div>

        <div className="flex justify-end">
          <button onClick={analyze} disabled={loading || !canAnalyze} className="btn-primary px-6">
            {loading ? <><Spinner size={14} /> Analysing...</> : (result ? 'Re-analyse' : 'Analyse Resume')}
          </button>
        </div>
      </div>

      {/* Loading with staged progress */}
      <AnimatePresence>
        {loading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            <Card>
              <CardBody className="py-14 flex flex-col items-center gap-4 text-center">
                <div className="w-12 h-12 rounded-full"
                  style={{ border: '3px solid rgba(0,0,0,0.06)', borderTopColor: 'rgb(var(--accent))', animation: 'spin 0.9s linear infinite' }}
                />
                <div>
                  <div className="text-[14px] font-semibold text-t1">{STAGES[stage].label}</div>
                  <div className="text-[13px] text-t2 mt-1">Usually takes 15-30 seconds</div>
                </div>
                <div className="flex gap-1.5">
                  {STAGES.map((_, i) => (
                    <span key={i} className="w-1.5 h-1.5 rounded-full transition-colors"
                      style={{ background: i <= stage ? 'rgb(var(--accent))' : 'rgba(0,0,0,0.1)' }} />
                  ))}
                </div>
              </CardBody>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results + improve flow */}
      {result && !loading && (
        <ResultsPanel
          result={result}
          delta={result._delta}
          footer={<ImprovePanel result={result} jd={jd} />}
        />
      )}
    </div>
  )
}
