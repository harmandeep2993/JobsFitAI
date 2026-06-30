import { useState, useRef } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'
import {
  PageHeader, Card, CardBody, CardSection, SectionLabel,
  Spinner, EmptyState, ScoreLabel,
} from '../ui.jsx'

function ScoreRing({ score }) {
  const r = 36
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color =
    score >= 80 ? '#16a34a' :
    score >= 60 ? '#4f46e5' :
    score >= 40 ? '#d97706' : '#dc2626'

  return (
    <div className="flex items-center gap-5">
      <svg width="96" height="96" viewBox="0 0 100 100" className="flex-shrink-0">
        <circle cx="50" cy="50" r={r} fill="none" stroke="var(--border)" strokeWidth="7" />
        <circle
          cx="50" cy="50" r={r}
          fill="none" stroke={color} strokeWidth="7" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        <text x="50" y="47" textAnchor="middle" fontSize="22" fontWeight="700" fill={color} fontFamily="Inter,sans-serif">{score}</text>
        <text x="50" y="61" textAnchor="middle" fontSize="9" fill="var(--t3)" fontFamily="Inter,sans-serif">/ 100</text>
      </svg>
      <div>
        <ScoreLabel score={score} />
        <div className="text-[13px] text-t2 mt-0.5">Overall match</div>
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
      <div className="flex-1 h-1.5 bg-surface-2 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: color, transition: 'width 0.5s ease' }} />
      </div>
      <div className="w-7 text-[12px] font-semibold text-right flex-shrink-0" style={{ color }}>{Math.round(value)}</div>
    </div>
  )
}

function KeywordChip({ text, matched }) {
  return (
    <span className={`px-2.5 py-0.5 rounded-sm text-[12px] font-medium border ${
      matched ? 'bg-green-bg border-green-bd text-green' : 'bg-red-bg border-red-bd text-red'
    }`}>
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
    <div className="space-y-5">
      <PageHeader
        title="Resume Analyser"
        description="Upload your resume and paste a job description to get an AI-powered match score with keyword and section breakdown."
        action={
          <button onClick={analyze} disabled={loading || !canAnalyze} className="btn-primary px-5 py-2 text-[13.5px]">
            {loading ? <><Spinner size={14} /> Analysing...</> : 'Analyse Resume'}
          </button>
        }
      />

      {/* Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <CardSection title="Resume">
          <div
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
              file ? 'border-green-bd bg-green-bg' : 'border-border hover:border-accent/40 hover:bg-accent-s'
            }`}
          >
            {file ? (
              <div className="space-y-1">
                <div className="text-[22px]">📄</div>
                <div className="text-[13px] font-medium text-t1 truncate px-2">{file.name}</div>
                <div className="text-[12px] text-t3">{(file.size / 1024).toFixed(0)} KB - click to change</div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex justify-center">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--t3)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <div className="text-[13px] font-medium text-t2">Click to upload</div>
                <div className="text-[12px] text-t3">PDF or DOCX, up to 10 MB</div>
              </div>
            )}
          </div>
          <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={e => setFile(e.target.files[0])} />
        </CardSection>

        <CardSection
          title="Job Description"
          action={
            <span className={`text-[11px] font-medium ${jd.length >= 100 ? 'text-green' : 'text-t3'}`}>
              {jd.length < 100 ? `${100 - jd.length} more chars needed` : `${jd.length} chars`}
            </span>
          }
        >
          <textarea
            value={jd}
            onChange={e => setJd(e.target.value)}
            placeholder="Paste the full job description here..."
            className="input-base resize-none"
            style={{ height: '170px' }}
          />
        </CardSection>
      </div>

      {/* Loading */}
      {loading && (
        <Card>
          <CardBody className="py-14 flex flex-col items-center gap-3 text-center">
            <div className="w-10 h-10 border-2 border-border border-t-accent rounded-full animate-spin" />
            <div className="text-[14px] font-medium text-t1">Analysing your resume...</div>
            <div className="text-[13px] text-t2">This takes 15-30 seconds</div>
          </CardBody>
        </Card>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Score + profile */}
          <Card>
            <CardBody className="p-6">
              <div className="flex flex-col sm:flex-row gap-6">
                <ScoreRing score={Math.round(result.score)} />
                {result.summary?.profile && (
                  <div className="flex-1">
                    <SectionLabel>Profile summary</SectionLabel>
                    <p className="text-[13.5px] text-t2 leading-relaxed">{result.summary.profile}</p>
                  </div>
                )}
              </div>

              {result.breakdown && Object.keys(result.breakdown).length > 0 && (
                <div className="mt-6 pt-5 border-t border-border space-y-2.5">
                  <SectionLabel>Section breakdown</SectionLabel>
                  {Object.entries(result.breakdown).map(([k, v]) => <ScoreBar key={k} label={k} value={v} />)}
                </div>
              )}
            </CardBody>
          </Card>

          {/* Keywords */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { label: 'Matched keywords', items: result.matched_keywords, matched: true },
              { label: 'Missing keywords',  items: result.missing_keywords, matched: false },
            ].map(({ label, items, matched }) => (
              <CardSection key={label} title={label} action={
                <span className={`text-[11px] font-semibold ${matched ? 'text-green' : 'text-red'}`}>
                  {items?.length || 0}
                </span>
              }>
                {items?.length > 0
                  ? <div className="flex flex-wrap gap-1.5">{items.map(k => <KeywordChip key={k} text={k} matched={matched} />)}</div>
                  : <p className="text-[13px] text-t3">{matched ? 'No matched keywords.' : 'No missing keywords.'}</p>
                }
              </CardSection>
            ))}
          </div>

          {/* Strengths + Gaps */}
          {(result.summary?.strengths?.length > 0 || result.summary?.gaps?.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { label: 'Strengths', items: result.summary?.strengths, icon: '+', color: 'bg-green-bg border-green-bd text-green' },
                { label: 'Gaps to address', items: result.summary?.gaps, icon: '!', color: 'bg-amber-bg border-amber-bd text-amber' },
              ].filter(s => s.items?.length > 0).map(s => (
                <CardSection key={s.label} title={s.label}>
                  <ul className="space-y-2">
                    {s.items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-[13px] text-t1">
                        <span className={`w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0 mt-0.5 text-[10px] font-bold ${s.color}`}>{s.icon}</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </CardSection>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
