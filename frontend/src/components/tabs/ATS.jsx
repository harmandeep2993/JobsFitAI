import { useState } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'
import {
  PageHeader, Card, CardBody, CardSection, SectionLabel, FieldLabel,
  Spinner,
} from '../ui.jsx'

function SectionFlag({ label, ok }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-sm border text-[12.5px] font-medium capitalize ${
      ok ? 'bg-green-bg border-green-bd text-green' : 'bg-red-bg border-red-bd text-red'
    }`}>
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
    setLoading('check')
    try {
      const res = await apiFetch('/api/ats/check', { method: 'POST', body: JSON.stringify({ resume_text: resumeText }) })
      if (!res?.ok) { toast('Check failed', 'error'); return }
      setCheckResult(await res.json())
    } finally { setLoading('') }
  }

  async function optimise() {
    if (resumeText.trim().length < 50) { toast('Paste your resume text first', 'warn'); return }
    if (jd.trim().length < 100) { toast('Paste a job description to optimise against', 'warn'); return }
    setLoading('optimise')
    try {
      const res = await apiFetch('/api/ats/optimise', { method: 'POST', body: JSON.stringify({ resume_text: resumeText, jd_text: jd }) })
      if (!res?.ok) { toast('Optimise failed', 'error'); return }
      setOptimResult(await res.json())
    } finally { setLoading('') }
  }

  const scoreColor =
    checkResult?.score >= 80 ? '#16a34a' :
    checkResult?.score >= 60 ? '#4f46e5' :
    checkResult?.score >= 40 ? '#d97706' : '#dc2626'

  return (
    <div className="space-y-5">
      <PageHeader
        title="ATS Check"
        description="Scan your resume for ATS compatibility issues and use AI-powered keyword optimisation to improve your chances."
        action={
          <div className="flex gap-2">
            <button onClick={check} disabled={!!loading} className="btn-primary px-4 py-2 text-[13.5px]">
              {loading === 'check' ? <><Spinner size={13} /> Checking...</> : 'ATS Check'}
            </button>
            <button onClick={optimise} disabled={!!loading} className="btn-secondary px-4 py-2 text-[13.5px]">
              {loading === 'optimise' ? <><Spinner size={13} /> Optimising...</> : 'AI Optimise'}
            </button>
          </div>
        }
      />

      {/* Inputs */}
      <CardSection title="Resume text">
        <FieldLabel>Paste your full resume content</FieldLabel>
        <textarea
          value={resumeText}
          onChange={e => setResumeText(e.target.value)}
          placeholder="Paste your full resume text here..."
          className="input-base resize-none"
          style={{ height: '160px' }}
        />
      </CardSection>

      <CardSection title="Job description" action={<span className="text-[11px] text-t3">Optional - needed for AI Optimise</span>}>
        <textarea
          value={jd}
          onChange={e => setJd(e.target.value)}
          placeholder="Paste the job description to optimise your resume against..."
          className="input-base resize-none"
          style={{ height: '110px' }}
        />
      </CardSection>

      {/* ATS result */}
      {checkResult && (
        <Card>
          <CardBody className="space-y-5">
            <div className="flex items-center gap-4">
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
                    <li key={i} className="flex items-start gap-2 text-[13px] text-amber">
                      <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="flex-shrink-0 mt-0.5">
                        <path d="M8 3v5M8 11v.5"/><path d="M8 1L1 13h14L8 1z"/>
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-[13px] text-green">
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
              <div className="flex items-center gap-3 bg-surface-2 rounded-sm px-4 py-3">
                <span className="text-[12.5px] text-t2">Keyword coverage:</span>
                <span className="font-bold text-red">{Math.round(optimResult.coverage_before)}%</span>
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--t3)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
                <span className="font-bold text-green">{Math.round(optimResult.coverage_after)}%</span>
              </div>
            )}

            {optimResult.resume_text && (
              <pre className="bg-surface-2 border border-border rounded-sm p-4 text-[12px] text-t1 whitespace-pre-wrap overflow-auto max-h-96 leading-relaxed">
                {optimResult.resume_text}
              </pre>
            )}
          </CardBody>
        </Card>
      )}
    </div>
  )
}
