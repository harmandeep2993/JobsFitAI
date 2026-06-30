import { useState, useRef } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

function ScoreBadge({ score }) {
  const cfg =
    score >= 80 ? { bg: 'bg-green-bg', border: 'border-green-bd', text: 'text-green', label: 'Excellent' } :
    score >= 60 ? { bg: 'bg-blue-bg',  border: 'border-blue-bd',  text: 'text-blue',  label: 'Good' } :
    score >= 40 ? { bg: 'bg-amber-bg', border: 'border-amber-bd', text: 'text-amber', label: 'Partial' } :
                  { bg: 'bg-red-bg',   border: 'border-red-bd',   text: 'text-red',   label: 'Poor' }
  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded border ${cfg.bg} ${cfg.border}`}>
      <span className={`text-3xl font-black ${cfg.text}`}>{score}</span>
      <span className={`text-xs font-semibold ${cfg.text}`}>{cfg.label}</span>
    </div>
  )
}

function KeywordList({ items, matched }) {
  if (!items?.length) return <p className="text-xs text-t3">None</p>
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map(k => (
        <span
          key={k}
          className={`px-2 py-0.5 rounded-xs text-[11px] font-medium border ${
            matched
              ? 'bg-green-bg border-green-bd text-green'
              : 'bg-red-bg border-red-bd text-red'
          }`}
        >
          {k}
        </span>
      ))}
    </div>
  )
}

export default function Analyzer() {
  const toast = useToast()
  const fileRef = useRef(null)

  const [file, setFile] = useState(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  async function analyze() {
    if (!file && !jd) { toast('Upload a resume and paste a job description', 'warn'); return }
    if (!file) { toast('Upload a resume file', 'warn'); return }
    if (jd.trim().length < 100) { toast('Job description is too short', 'warn'); return }

    setLoading(true)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const up = await apiFetch('/api/upload', { method: 'POST', body: fd })
      if (!up?.ok) { toast('Upload failed', 'error'); return }
      const { tmp } = await up.json()

      const res = await apiFetch('/api/analyze', {
        method: 'POST',
        body: JSON.stringify({ tmp_path: tmp, jd_text: jd }),
      })
      if (!res?.ok) { toast('Analysis failed', 'error'); return }
      const data = await res.json()
      if (!data.ok) { toast(data.error || 'Analysis failed', 'error'); return }
      setResult(data)
    } catch (e) {
      toast('Error: ' + e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <h1 className="text-lg font-bold">Resume Analyzer</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Resume upload */}
        <div className="bg-surface border border-border rounded p-4 space-y-3">
          <div className="text-sm font-semibold">Resume</div>
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-border rounded-s p-6 text-center cursor-pointer hover:border-accent/40 hover:bg-accent-s/30 transition-colors"
          >
            {file ? (
              <div className="text-sm text-t1 font-medium">{file.name}</div>
            ) : (
              <>
                <div className="text-t3 mb-1">
                  <svg className="mx-auto mb-2" width="24" height="24" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 14V6M7 9l3-3 3 3"/><rect x="2" y="14" width="16" height="4" rx="1"/>
                  </svg>
                </div>
                <div className="text-xs text-t2">Click to upload PDF or DOCX</div>
              </>
            )}
          </div>
          <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={e => setFile(e.target.files[0])} />
        </div>

        {/* JD input */}
        <div className="bg-surface border border-border rounded p-4 space-y-3">
          <div className="text-sm font-semibold">Job Description</div>
          <textarea
            value={jd}
            onChange={e => setJd(e.target.value)}
            placeholder="Paste the full job description here..."
            className="w-full h-32 px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent resize-none transition-colors"
          />
          <div className="text-xs text-t3">{jd.length} characters</div>
        </div>
      </div>

      <button
        onClick={analyze}
        disabled={loading}
        className="px-6 py-2.5 bg-accent text-white rounded-s text-sm font-semibold hover:bg-accent-h disabled:opacity-60 transition-colors"
      >
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Score */}
          <div className="bg-surface border border-border rounded p-5">
            <div className="flex items-center gap-4 mb-4">
              <ScoreBadge score={Math.round(result.score)} />
              <div>
                <div className="text-sm font-semibold">{result.label}</div>
                {result.summary?.profile && <div className="text-xs text-t2 mt-0.5">{result.summary.profile}</div>}
              </div>
            </div>

            {/* Section breakdown */}
            {result.breakdown && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-t2 uppercase tracking-wide mb-2">Section scores</div>
                {Object.entries(result.breakdown).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-3">
                    <div className="w-24 text-xs text-t2 capitalize">{k.replace(/_/g, ' ')}</div>
                    <div className="flex-1 h-1.5 bg-bg rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          v >= 80 ? 'bg-green' : v >= 60 ? 'bg-blue' : v >= 40 ? 'bg-amber' : 'bg-red'
                        }`}
                        style={{ width: `${v}%` }}
                      />
                    </div>
                    <div className="w-8 text-xs text-t2 text-right">{Math.round(v)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Keywords */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-surface border border-border rounded p-4">
              <div className="text-xs font-semibold text-t2 uppercase tracking-wide mb-3">Matched keywords</div>
              <KeywordList items={result.matched_keywords} matched />
            </div>
            <div className="bg-surface border border-border rounded p-4">
              <div className="text-xs font-semibold text-t2 uppercase tracking-wide mb-3">Missing keywords</div>
              <KeywordList items={result.missing_keywords} matched={false} />
            </div>
          </div>

          {/* Strengths / Gaps */}
          {(result.summary?.strengths?.length || result.summary?.gaps?.length) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.summary?.strengths?.length > 0 && (
                <div className="bg-surface border border-border rounded p-4">
                  <div className="text-xs font-semibold text-t2 uppercase tracking-wide mb-3">Strengths</div>
                  <ul className="space-y-1.5">
                    {result.summary.strengths.map((s, i) => (
                      <li key={i} className="flex gap-2 text-xs text-t1">
                        <span className="text-green mt-0.5 flex-shrink-0">+</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.summary?.gaps?.length > 0 && (
                <div className="bg-surface border border-border rounded p-4">
                  <div className="text-xs font-semibold text-t2 uppercase tracking-wide mb-3">Gaps</div>
                  <ul className="space-y-1.5">
                    {result.summary.gaps.map((g, i) => (
                      <li key={i} className="flex gap-2 text-xs text-t1">
                        <span className="text-amber mt-0.5 flex-shrink-0">!</span>{g}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
