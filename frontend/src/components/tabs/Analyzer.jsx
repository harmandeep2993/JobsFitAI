import { useState, useRef } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

function ScoreRing({ score }) {
  const cfg =
    score >= 80 ? { color: '#16a34a', label: 'Excellent' } :
    score >= 60 ? { color: '#4f46e5', label: 'Good' } :
    score >= 40 ? { color: '#d97706', label: 'Partial' } :
                  { color: '#dc2626', label: 'Poor' }
  const r = 36
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ

  return (
    <div className="flex items-center gap-5">
      <div className="relative flex-shrink-0">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r={r} fill="none" stroke="var(--border)" strokeWidth="7" />
          <circle
            cx="50" cy="50" r={r}
            fill="none"
            stroke={cfg.color}
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            transform="rotate(-90 50 50)"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
          <text x="50" y="47" textAnchor="middle" fontSize="22" fontWeight="700" fill={cfg.color} fontFamily="Inter, sans-serif">{score}</text>
          <text x="50" y="60" textAnchor="middle" fontSize="8.5" fill="var(--t3)" fontFamily="Inter, sans-serif">/ 100</text>
        </svg>
      </div>
      <div>
        <div className="text-lg font-bold text-t1" style={{ color: cfg.color }}>{cfg.label}</div>
        <div className="text-sm text-t2 mt-0.5">Match score</div>
      </div>
    </div>
  )
}

function ScoreBar({ label, value }) {
  const color =
    value >= 80 ? '#16a34a' :
    value >= 60 ? '#4f46e5' :
    value >= 40 ? '#d97706' : '#dc2626'
  return (
    <div className="flex items-center gap-3">
      <div className="w-28 text-[12.5px] text-t2 capitalize flex-shrink-0">{label.replace(/_/g, ' ')}</div>
      <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${value}%`, background: color }}
        />
      </div>
      <div className="w-7 text-xs font-semibold text-right flex-shrink-0" style={{ color }}>{Math.round(value)}</div>
    </div>
  )
}

function KeywordChip({ text, matched }) {
  return (
    <span
      className={`px-2.5 py-1 rounded-sm text-[12px] font-medium border ${
        matched
          ? 'bg-green-bg border-green-bd text-green'
          : 'bg-red-bg border-red-bd text-red'
      }`}
    >
      {text}
    </span>
  )
}

export default function Analyzer() {
  const toast = useToast()
  const fileRef = useRef(null)
  const [file, setFile] = useState(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const canAnalyze = file && jd.trim().length >= 100

  async function analyze() {
    if (!file) { toast('Upload a resume file', 'warn'); return }
    if (jd.trim().length < 100) { toast('Job description is too short (need at least 100 characters)', 'warn'); return }

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
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-t1">Resume Analyzer</h1>
        <p className="text-sm text-t2 mt-1">Upload your resume and paste a job description to get an AI-powered match score.</p>
      </div>

      {/* Input section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Resume upload */}
        <div className="card p-5 space-y-3">
          <div className="text-[13px] font-semibold text-t1">Resume</div>
          <div
            onClick={() => fileRef.current?.click()}
            className={`relative border-2 border-dashed rounded-sm p-7 text-center cursor-pointer transition-all ${
              file
                ? 'border-green-bd bg-green-bg'
                : 'border-border hover:border-accent/40 hover:bg-accent-s'
            }`}
          >
            {file ? (
              <div className="space-y-1.5">
                <div className="flex items-center justify-center">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="var(--green)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="4" y="2" width="12" height="16" rx="2"/>
                    <path d="M8 7h4M8 10h4M8 13h2"/>
                  </svg>
                </div>
                <div className="text-sm font-medium text-t1 truncate px-2">{file.name}</div>
                <div className="text-xs text-t3">{(file.size / 1024).toFixed(0)} KB - click to change</div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-center">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--t3)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <div className="text-sm font-medium text-t2">Drop your resume here</div>
                <div className="text-xs text-t3">PDF or DOCX, up to 10 MB</div>
              </div>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={e => setFile(e.target.files[0])}
          />
        </div>

        {/* JD input */}
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-[13px] font-semibold text-t1">Job Description</div>
            <div className={`text-[11px] font-medium transition-colors ${
              jd.length >= 100 ? 'text-green' : 'text-t3'
            }`}>
              {jd.length} chars {jd.length < 100 ? `(need ${100 - jd.length} more)` : ''}
            </div>
          </div>
          <textarea
            value={jd}
            onChange={e => setJd(e.target.value)}
            placeholder="Paste the full job description here..."
            className="input-base resize-none"
            style={{ height: '186px' }}
          />
        </div>
      </div>

      {/* Analyze button */}
      <button
        onClick={analyze}
        disabled={loading || !canAnalyze}
        className="btn-primary px-7 py-2.5 text-[14px]"
      >
        {loading ? (
          <>
            <svg className="animate-spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M21 12a9 9 0 11-6-8.5"/>
            </svg>
            Analyzing...
          </>
        ) : 'Analyze Resume'}
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-4 animate-in">

          {/* Score + breakdown */}
          <div className="card p-6">
            <div className="flex flex-col sm:flex-row sm:items-start gap-6">
              <ScoreRing score={Math.round(result.score)} />

              {result.summary?.profile && (
                <div className="flex-1">
                  <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide mb-2">Profile summary</div>
                  <p className="text-[13.5px] text-t2 leading-relaxed">{result.summary.profile}</p>
                </div>
              )}
            </div>

            {result.breakdown && Object.keys(result.breakdown).length > 0 && (
              <div className="mt-6 pt-5 border-t border-border space-y-2.5">
                <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide mb-3">Section breakdown</div>
                {Object.entries(result.breakdown).map(([k, v]) => (
                  <ScoreBar key={k} label={k} value={v} />
                ))}
              </div>
            )}
          </div>

          {/* Keywords */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-green flex-shrink-0" />
                <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide">Matched keywords</div>
                <span className="ml-auto text-xs text-green font-semibold">{result.matched_keywords?.length || 0}</span>
              </div>
              {result.matched_keywords?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {result.matched_keywords.map(k => <KeywordChip key={k} text={k} matched />)}
                </div>
              ) : (
                <p className="text-xs text-t3">No matched keywords found.</p>
              )}
            </div>
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-red flex-shrink-0" />
                <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide">Missing keywords</div>
                <span className="ml-auto text-xs text-red font-semibold">{result.missing_keywords?.length || 0}</span>
              </div>
              {result.missing_keywords?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {result.missing_keywords.map(k => <KeywordChip key={k} text={k} matched={false} />)}
                </div>
              ) : (
                <p className="text-xs text-t3">No missing keywords.</p>
              )}
            </div>
          </div>

          {/* Strengths + Gaps */}
          {(result.summary?.strengths?.length > 0 || result.summary?.gaps?.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.summary?.strengths?.length > 0 && (
                <div className="card p-5">
                  <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide mb-3">Strengths</div>
                  <ul className="space-y-2">
                    {result.summary.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-[13px] text-t1">
                        <span className="w-4 h-4 rounded-full bg-green-bg border border-green-bd text-green flex items-center justify-center flex-shrink-0 mt-0.5 text-[10px] font-bold">+</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {result.summary?.gaps?.length > 0 && (
                <div className="card p-5">
                  <div className="text-[12px] font-semibold text-t3 uppercase tracking-wide mb-3">Gaps to address</div>
                  <ul className="space-y-2">
                    {result.summary.gaps.map((g, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-[13px] text-t1">
                        <span className="w-4 h-4 rounded-full bg-amber-bg border border-amber-bd text-amber flex items-center justify-center flex-shrink-0 mt-0.5 text-[10px] font-bold">!</span>
                        {g}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="card p-12 text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="w-10 h-10 border-2 border-border border-t-accent rounded-full animate-spin" />
          </div>
          <div className="text-sm font-medium text-t1">Analyzing your resume...</div>
          <div className="text-xs text-t3 mt-1">This takes 15-30 seconds</div>
        </div>
      )}
    </div>
  )
}
