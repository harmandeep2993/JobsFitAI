import { useState } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

function Flag({ ok, label }) {
  return (
    <div className={`flex items-center gap-2 text-xs px-3 py-2 rounded-xs border ${
      ok ? 'bg-green-bg border-green-bd text-green' : 'bg-red-bg border-red-bd text-red'
    }`}>
      <span>{ok ? '✓' : '✗'}</span>
      <span>{label}</span>
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
      const data = await res.json()
      setCheckResult(data)
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
      const data = await res.json()
      setOptimResult(data)
    } finally {
      setLoading('')
    }
  }

  return (
    <div className="space-y-5 max-w-3xl">
      <h1 className="text-lg font-bold">ATS Check</h1>

      <div className="bg-surface border border-border rounded p-4 space-y-3">
        <div className="text-sm font-semibold">Resume text</div>
        <textarea
          value={resumeText}
          onChange={e => setResumeText(e.target.value)}
          placeholder="Paste your resume text here..."
          className="w-full h-40 px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent resize-none transition-colors"
        />
      </div>

      <div className="bg-surface border border-border rounded p-4 space-y-3">
        <div className="text-sm font-semibold">Job description <span className="text-t3 font-normal">(optional - for optimise)</span></div>
        <textarea
          value={jd}
          onChange={e => setJd(e.target.value)}
          placeholder="Paste the job description to optimise against..."
          className="w-full h-28 px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent resize-none transition-colors"
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={check}
          disabled={loading === 'check'}
          className="px-5 py-2 bg-accent text-white rounded-s text-sm font-semibold hover:bg-accent-h disabled:opacity-60 transition-colors"
        >
          {loading === 'check' ? 'Checking...' : 'ATS Check'}
        </button>
        <button
          onClick={optimise}
          disabled={loading === 'optimise'}
          className="px-5 py-2 bg-surface border border-border rounded-s text-sm font-medium text-t1 hover:bg-hover disabled:opacity-60 transition-colors"
        >
          {loading === 'optimise' ? 'Optimising...' : 'AI Optimise'}
        </button>
      </div>

      {checkResult && (
        <div className="bg-surface border border-border rounded p-5 space-y-4">
          <div className="flex items-center gap-3">
            <div className="text-sm font-semibold">ATS Result</div>
            <div className={`text-xs font-bold px-2.5 py-1 rounded-xs border ${
              checkResult.score >= 80 ? 'bg-green-bg border-green-bd text-green' :
              checkResult.score >= 60 ? 'bg-blue-bg border-blue-bd text-blue' :
              checkResult.score >= 40 ? 'bg-amber-bg border-amber-bd text-amber' :
              'bg-red-bg border-red-bd text-red'
            }`}>
              Score: {Math.round(checkResult.score || 0)}
            </div>
          </div>

          {checkResult.section_flags && (
            <div>
              <div className="text-xs font-semibold text-t2 uppercase tracking-wide mb-2">Sections</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(checkResult.section_flags).map(([k, v]) => (
                  <Flag key={k} ok={v} label={k} />
                ))}
              </div>
            </div>
          )}

          {checkResult.formatting_flags?.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-t2 uppercase tracking-wide mb-2">Warnings</div>
              <ul className="space-y-1">
                {checkResult.formatting_flags.map((f, i) => (
                  <li key={i} className="flex gap-2 text-xs text-amber">
                    <span>!</span>{f}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {optimResult && (
        <div className="bg-surface border border-border rounded p-5 space-y-4">
          <div className="text-sm font-semibold">Optimised Resume</div>
          {optimResult.coverage_before !== undefined && optimResult.coverage_after !== undefined && (
            <div className="flex items-center gap-3 text-xs">
              <span className="text-t2">Coverage:</span>
              <span className="text-red font-semibold">{Math.round(optimResult.coverage_before)}%</span>
              <span className="text-t3">-&gt;</span>
              <span className="text-green font-semibold">{Math.round(optimResult.coverage_after)}%</span>
            </div>
          )}
          {optimResult.resume_text && (
            <pre className="bg-bg border border-border rounded-xs p-4 text-[12px] text-t1 whitespace-pre-wrap overflow-auto max-h-96">
              {optimResult.resume_text}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
