import { useState } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

function SectionFlag({ label, ok }) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-sm border text-[12.5px] font-medium ${
        ok
          ? 'bg-green-bg border-green-bd text-green'
          : 'bg-red-bg border-red-bd text-red'
      }`}
    >
      {ok ? (
        <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2.5 7l3 3 6-6"/>
        </svg>
      ) : (
        <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 3l8 8M11 3L3 11"/>
        </svg>
      )}
      <span className="capitalize">{label}</span>
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
      const res = await apiFetch('/api/ats/check', {
        method: 'POST',
        body: JSON.stringify({ resume_text: resumeText }),
      })
      if (!res?.ok) { toast('Check failed', 'error'); return }
      setCheckResult(await res.json())
    } finally {
      setLoading('')
    }
  }

  async function optimise() {
    if (resumeText.trim().length < 50) { toast('Paste your resume text first', 'warn'); return }
    if (jd.trim().length < 100) { toast('Paste a job description to optimise against', 'warn'); return }
    setLoading('optimise')
    try {
      const res = await apiFetch('/api/ats/optimise', {
        method: 'POST',
        body: JSON.stringify({ resume_text: resumeText, jd_text: jd }),
      })
      if (!res?.ok) { toast('Optimise failed', 'error'); return }
      setOptimResult(await res.json())
    } finally {
      setLoading('')
    }
  }

  const scoreColor =
    checkResult?.score >= 80 ? 'text-green' :
    checkResult?.score >= 60 ? 'text-blue' :
    checkResult?.score >= 40 ? 'text-amber' : 'text-red'

  return (
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-t1">ATS Check</h1>
        <p className="text-sm text-t2 mt-1">Scan your resume for ATS compatibility and get AI-powered keyword optimisation.</p>
      </div>

      <div className="card p-5 space-y-4">
        <div className="space-y-2">
          <label className="block text-[12.5px] font-medium text-t2">Resume text</label>
          <textarea
            value={resumeText}
            onChange={e => setResumeText(e.target.value)}
            placeholder="Paste your full resume text here..."
            className="input-base resize-none"
            style={{ height: '160px' }}
          />
        </div>

        <div className="space-y-2">
          <label className="block text-[12.5px] font-medium text-t2">
            Job description
            <span className="font-normal text-t3 ml-1">(optional - needed for AI optimise)</span>
          </label>
          <textarea
            value={jd}
            onChange={e => setJd(e.target.value)}
            placeholder="Paste the job description to optimise your resume against..."
            className="input-base resize-none"
            style={{ height: '110px' }}
          />
        </div>

        <div className="flex gap-2.5">
          <button
            onClick={check}
            disabled={!!loading}
            className="btn-primary py-2 px-5 text-[13.5px]"
          >
            {loading === 'check' ? (
              <>
                <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M21 12a9 9 0 11-6-8.5"/>
                </svg>
                Checking...
              </>
            ) : 'ATS Check'}
          </button>
          <button
            onClick={optimise}
            disabled={!!loading}
            className="btn-secondary py-2 px-5 text-[13.5px]"
          >
            {loading === 'optimise' ? (
              <>
                <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M21 12a9 9 0 11-6-8.5"/>
                </svg>
                Optimising...
              </>
            ) : 'AI Optimise'}
          </button>
        </div>
      </div>

      {/* ATS Check result */}
      {checkResult && (
        <div className="card p-5 space-y-5">
          <div className="flex items-center gap-4">
            <div className="text-[14px] font-semibold text-t1">ATS Score</div>
            <div className={`text-2xl font-bold ${scoreColor}`}>
              {Math.round(checkResult.score || 0)}
              <span className="text-sm font-normal text-t3 ml-1">/ 100</span>
            </div>
          </div>

          {checkResult.section_flags && Object.keys(checkResult.section_flags).length > 0 && (
            <div>
              <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide mb-2.5">Section presence</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(checkResult.section_flags).map(([k, v]) => (
                  <SectionFlag key={k} label={k} ok={v} />
                ))}
              </div>
            </div>
          )}

          {checkResult.formatting_flags?.length > 0 && (
            <div>
              <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide mb-2.5">Formatting warnings</div>
              <ul className="space-y-1.5">
                {checkResult.formatting_flags.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-[13px] text-amber">
                    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="flex-shrink-0 mt-0.5">
                      <path d="M8 3v5M8 11v.5"/>
                      <path d="M8 1L1 13h14L8 1z"/>
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {checkResult.formatting_flags?.length === 0 && (
            <div className="flex items-center gap-2 text-[13px] text-green">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 8l3.5 3.5L13 5"/>
              </svg>
              No formatting issues detected
            </div>
          )}
        </div>
      )}

      {/* Optimise result */}
      {optimResult && (
        <div className="card p-5 space-y-4">
          <div className="text-[14px] font-semibold text-t1">Optimised Resume</div>

          {optimResult.coverage_before !== undefined && optimResult.coverage_after !== undefined && (
            <div className="flex items-center gap-3 bg-surface-2 rounded-sm px-4 py-3">
              <span className="text-[12.5px] text-t2">Keyword coverage:</span>
              <span className="text-red font-bold">{Math.round(optimResult.coverage_before)}%</span>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--t3)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 8h10M9 4l4 4-4 4"/>
              </svg>
              <span className="text-green font-bold">{Math.round(optimResult.coverage_after)}%</span>
            </div>
          )}

          {optimResult.resume_text && (
            <pre className="bg-surface-2 border border-border rounded-sm p-4 text-[12px] text-t1 whitespace-pre-wrap overflow-auto max-h-96 leading-relaxed">
              {optimResult.resume_text}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
