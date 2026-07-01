/**
 * ATS Check tab - resume text and JD side by side, action buttons below aligned right.
 */
import { useState } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'
import {
  PageHeader, Card, CardBody, CardSection, SectionLabel,
  Spinner,
} from '../ui.jsx'

const INNER_BG = 'rgba(99,102,241,0.04)'
const INNER_BORDER = 'rgba(99,102,241,0.18)'
const BOX_HEIGHT = '218px'

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

function SectionFlag({ label, ok }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-sm border text-[12.5px] font-medium capitalize"
      style={ok
        ? { background: 'rgba(22,163,74,0.08)', borderColor: 'rgba(22,163,74,0.25)', color: '#16a34a' }
        : { background: 'rgba(220,38,38,0.08)', borderColor: 'rgba(220,38,38,0.25)', color: '#dc2626' }
      }
    >
      {ok
        ? <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M2.5 7l3 3 6-6"/></svg>
        : <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3l8 8M11 3L3 11"/></svg>
      }
      {label}
    </div>
  )
}

export default function ATS() {
  const toast = useToast()
  const [resumeText, setResumeText] = useState('')
  const [jd, setJd] = useState('')
  const [checkResult, setCheckResult] = useState(null)
  const [optimResult, setOptimResult] = useState(null)
  const [loading, setLoading] = useState('')

  async function check() {
    if (resumeText.trim().length < 50) { toast('Paste your resume text first', 'warn'); return }
    setLoading('check'); setCheckResult(null)
    try {
      const res = await apiFetch('/api/ats/check', { method: 'POST', body: JSON.stringify({ resume_text: resumeText }) })
      if (!res?.ok) { toast('Check failed', 'error'); return }
      setCheckResult(await res.json())
    } finally { setLoading('') }
  }

  async function optimise() {
    if (resumeText.trim().length < 50) { toast('Paste your resume text first', 'warn'); return }
    if (jd.trim().length < 100) { toast('Paste a job description to optimise against', 'warn'); return }
    setLoading('optimise'); setOptimResult(null)
    try {
      const res = await apiFetch('/api/ats/optimise', { method: 'POST', body: JSON.stringify({ resume_text: resumeText, jd_text: jd }) })
      if (!res?.ok) { toast('Optimise failed', 'error'); return }
      setOptimResult(await res.json())
    } finally { setLoading('') }
  }

  const scoreColor =
    checkResult?.score >= 80 ? '#16a34a' :
    checkResult?.score >= 60 ? '#6366f1' :
    checkResult?.score >= 40 ? '#d97706' : '#dc2626'

  return (
    <div className="space-y-5">
      <PageHeader
        title="ATS Check"
        description="Scan your resume for ATS compatibility issues and use AI-powered optimisation to improve your chances."
      />

      {/* Input boxes + actions */}
      <div className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Resume text box */}
          <Card>
            <div className="px-5 py-3 border-b flex items-center justify-between" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
              <span className="text-[13px] font-semibold text-t1">Resume text</span>
              {resumeText && <ClearBtn onClick={() => { setResumeText(''); setCheckResult(null); setOptimResult(null) }} />}
            </div>
            <CardBody className="p-4">
              <textarea
                value={resumeText}
                onChange={e => setResumeText(e.target.value)}
                placeholder="Paste your full resume text here..."
                className="input-base resize-none"
                style={{ height: BOX_HEIGHT, background: INNER_BG, border: `2px dashed ${INNER_BORDER}` }}
              />
            </CardBody>
          </Card>

          {/* JD box */}
          <Card>
            <div className="px-5 py-3 border-b flex items-center justify-between" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
              <span className="text-[13px] font-semibold text-t1">Job Description</span>
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-t3">Optional - needed for AI Optimise</span>
                {jd && <ClearBtn onClick={() => { setJd(''); setOptimResult(null) }} />}
              </div>
            </div>
            <CardBody className="p-4">
              <textarea
                value={jd}
                onChange={e => setJd(e.target.value)}
                placeholder="Paste the job description to optimise against..."
                className="input-base resize-none"
                style={{ height: BOX_HEIGHT, background: INNER_BG, border: `2px dashed ${INNER_BORDER}` }}
              />
            </CardBody>
          </Card>
        </div>

        {/* Action buttons - bottom right */}
        <div className="flex justify-end gap-2">
          <button onClick={check} disabled={!!loading} className="btn-secondary px-5">
            {loading === 'check' ? <><Spinner size={13} /> Checking...</> : 'ATS Check'}
          </button>
          <button onClick={optimise} disabled={!!loading} className="btn-primary px-5">
            {loading === 'optimise' ? <><Spinner size={13} /> Optimising...</> : 'AI Optimise'}
          </button>
        </div>
      </div>

      {/* ATS result */}
      {checkResult && (
        <Card>
          <CardBody className="space-y-5">
            <div className="flex items-center gap-3">
              <SectionLabel>ATS Score</SectionLabel>
              <span className="text-2xl font-bold" style={{ color: scoreColor }}>
                {Math.round(checkResult.score || 0)}
                <span className="text-[13px] font-normal text-t3 ml-1">/ 100</span>
              </span>
            </div>

            {checkResult.section_flags && Object.keys(checkResult.section_flags).length > 0 && (
              <div>
                <SectionLabel>Section presence</SectionLabel>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(checkResult.section_flags).map(([k, v]) => <SectionFlag key={k} label={k} ok={v} />)}
                </div>
              </div>
            )}

            {checkResult.formatting_flags?.length > 0 ? (
              <div>
                <SectionLabel>Formatting warnings</SectionLabel>
                <ul className="space-y-1.5">
                  {checkResult.formatting_flags.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-[13px]" style={{ color: '#d97706' }}>
                      <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="flex-shrink-0 mt-0.5">
                        <path d="M8 3v5M8 11v.5"/><path d="M8 1L1 13h14L8 1z"/>
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-[13px]" style={{ color: '#16a34a' }}>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 8l3.5 3.5L13 5"/></svg>
                No formatting issues detected
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* Optimise result */}
      {optimResult && (
        <Card>
          <CardBody className="space-y-4">
            <SectionLabel>Optimised Resume</SectionLabel>

            {optimResult.coverage_before !== undefined && optimResult.coverage_after !== undefined && (
              <div className="flex items-center gap-3 rounded-lg px-4 py-3" style={{ background: 'rgb(var(--surface-2))' }}>
                <span className="text-[12.5px] text-t2">Keyword coverage:</span>
                <span className="font-bold" style={{ color: '#dc2626' }}>{Math.round(optimResult.coverage_before)}%</span>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="rgb(var(--t3))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
                <span className="font-bold" style={{ color: '#16a34a' }}>{Math.round(optimResult.coverage_after)}%</span>
              </div>
            )}

            {optimResult.resume_text && (
              <pre className="rounded-lg p-4 text-[12px] text-t1 whitespace-pre-wrap overflow-auto max-h-96 leading-relaxed"
                style={{ background: 'rgb(var(--surface-2))', border: '1px solid rgba(0,0,0,0.06)' }}>
                {optimResult.resume_text}
              </pre>
            )}
          </CardBody>
        </Card>
      )}
    </div>
  )
}
