/**
 * Analyzer tab - two upload boxes side by side, analyse button below aligned right.
 */
import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'
import {
  PageHeader, Card, CardBody, CardSection, SectionLabel,
  Spinner, ScoreLabel,
} from '../ui.jsx'

// === Shared inner background for both input boxes ===
const INNER_BG = 'rgb(var(--surface-2))'

// === Clear button ===
function ClearBtn({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-6 h-6 flex items-center justify-center rounded-sm transition-colors flex-shrink-0"
      title="Clear"
      style={{ color: 'rgb(var(--t3))' }}
      onMouseEnter={e => { e.currentTarget.style.background = 'rgba(220,38,38,0.08)'; e.currentTarget.style.color = '#dc2626' }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'rgb(var(--t3))' }}
    >
      <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 2l10 10M12 2L2 12"/>
      </svg>
    </button>
  )
}

// === Score ring ===
function ScoreRing({ score }) {
  const r = 38
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 80 ? '#16a34a' : score >= 60 ? '#6366f1' : score >= 40 ? '#d97706' : '#dc2626'

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="6" />
        <circle
          cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset} transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 0.7s cubic-bezier(0.4,0,0.2,1)' }}
        />
        <text x="50" y="46" textAnchor="middle" fontSize="24" fontWeight="700" fill={color} fontFamily="'Plus Jakarta Sans',Inter,sans-serif">{score}</text>
        <text x="50" y="62" textAnchor="middle" fontSize="9" fill="rgb(156,163,175)" fontFamily="Inter,sans-serif">/ 100</text>
      </svg>
      <ScoreLabel score={score} />
    </div>
  )
}

// === Score bar ===
function ScoreBar({ label, value }) {
  const color = value >= 80 ? '#16a34a' : value >= 60 ? '#6366f1' : value >= 40 ? '#d97706' : '#dc2626'
  return (
    <div className="flex items-center gap-3">
      <div className="w-28 text-[12px] text-t2 capitalize flex-shrink-0">{label.replace(/_/g, ' ')}</div>
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(0,0,0,0.06)' }}>
        <motion.div
          className="h-full rounded-full" style={{ background: color }}
          initial={{ width: 0 }} animate={{ width: `${value}%` }}
          transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
      <div className="w-7 text-[12px] font-bold text-right flex-shrink-0" style={{ color }}>{Math.round(value)}</div>
    </div>
  )
}

// === Keyword chip ===
function KeywordChip({ text, matched }) {
  const style = matched
    ? { background: 'rgba(22,163,74,0.08)', borderColor: 'rgba(22,163,74,0.25)', color: '#16a34a' }
    : { background: 'rgba(220,38,38,0.08)', borderColor: 'rgba(220,38,38,0.25)', color: '#dc2626' }
  return (
    <span className="px-2.5 py-0.5 rounded-sm text-[12px] font-medium border" style={style}>{text}</span>
  )
}

// === Upload drop zone ===
function UploadZone({ file, onFile, onClear }) {
  const fileRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  function handleDrop(e) {
    e.preventDefault(); setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) onFile(f)
  }

  return (
    <div
      onClick={() => !file && fileRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className="relative h-full flex flex-col items-center justify-center rounded-lg transition-all select-none"
      style={{
        background: INNER_BG,
        border: `2px dashed ${file ? 'rgba(22,163,74,0.4)' : dragging ? 'rgb(var(--accent))' : 'rgba(0,0,0,0.1)'}`,
        cursor: file ? 'default' : 'pointer',
        minHeight: '160px',
        padding: '28px 20px',
      }}
    >
      {file ? (
        <div className="flex flex-col items-center gap-2 w-full">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(22,163,74,0.12)' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="15" y2="17"/>
            </svg>
          </div>
          <div className="text-[13.5px] font-semibold text-t1 truncate max-w-full px-2 text-center">{file.name}</div>
          <div className="text-[12px] text-t3">{(file.size / 1024).toFixed(0)} KB</div>
          <button
            onClick={e => { e.stopPropagation(); onClear() }}
            className="mt-1 text-[11.5px] font-medium underline underline-offset-2"
            style={{ color: 'rgb(var(--accent))' }}
          >
            Replace file
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.06)' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--t3))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div className="text-[13.5px] font-semibold text-t2">Drop resume here</div>
          <div className="text-[12px] text-t3">PDF or DOCX, max 10 MB</div>
        </div>
      )}
      <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={e => onFile(e.target.files[0])} />
    </div>
  )
}

// === Results panel ===
function ResultsPanel({ result }) {
  const breakdownScores = Object.fromEntries(
    Object.entries(result.breakdown || {}).map(([k, v]) => [k, typeof v === 'object' ? v.score : v])
  )
  const matchedKw = result.keywords?.matched || []
  const missingKw = result.keywords?.missing || []

  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <Card>
        <CardBody className="p-5">
          <div className="flex gap-5">
            <ScoreRing score={Math.round(result.score)} />
            {result.summary?.profile && (
              <div className="flex-1 min-w-0">
                <SectionLabel>Profile summary</SectionLabel>
                <p className="text-[13px] text-t2 leading-relaxed">
                  {Array.isArray(result.summary.profile) ? result.summary.profile.join(' ') : result.summary.profile}
                </p>
              </div>
            )}
          </div>
          {Object.keys(breakdownScores).length > 0 && (
            <div className="mt-5 pt-4 space-y-2.5" style={{ borderTop: '1px solid rgba(0,0,0,0.06)' }}>
              <SectionLabel>Section breakdown</SectionLabel>
              {Object.entries(breakdownScores).map(([k, v]) => <ScoreBar key={k} label={k} value={v} />)}
            </div>
          )}
        </CardBody>
      </Card>

      {(matchedKw.length > 0 || missingKw.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { label: 'Matched keywords', items: matchedKw, matched: true },
            { label: 'Missing keywords',  items: missingKw, matched: false },
          ].map(({ label, items, matched }) => (
            <CardSection key={label} title={label} action={
              <span className="text-[11px] font-bold" style={{ color: matched ? '#16a34a' : '#dc2626' }}>{items.length}</span>
            }>
              {items.length > 0
                ? <div className="flex flex-wrap gap-1.5">{items.map(k => <KeywordChip key={k} text={k} matched={matched} />)}</div>
                : <p className="text-[13px] text-t3">{matched ? 'No matches found.' : 'All keywords covered!'}</p>
              }
            </CardSection>
          ))}
        </div>
      )}

      {(result.summary?.strengths?.length > 0 || result.summary?.gaps?.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { label: 'Strengths', items: result.summary.strengths, color: '#16a34a', icon: <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="2,6 5,9 10,3"/></svg>, bg: 'rgba(22,163,74,0.08)', bd: 'rgba(22,163,74,0.25)' },
            { label: 'Gaps to address', items: result.summary.gaps, color: '#d97706', icon: <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 3v3M6 8v.5"/></svg>, bg: 'rgba(217,119,6,0.08)', bd: 'rgba(217,119,6,0.25)' },
          ].filter(s => s.items?.length > 0).map(s => (
            <CardSection key={s.label} title={s.label}>
              <ul className="space-y-2">
                {s.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-[13px] text-t1">
                    <span className="w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{ background: s.bg, borderColor: s.bd, color: s.color }}>{s.icon}</span>
                    {item}
                  </li>
                ))}
              </ul>
            </CardSection>
          ))}
        </div>
      )}

      {result.summary?.focus && (Array.isArray(result.summary.focus) ? result.summary.focus.length > 0 : result.summary.focus) && (
        <Card>
          <CardBody>
            <SectionLabel>Recommended focus</SectionLabel>
            <p className="text-[13px] text-t2 leading-relaxed">
              {Array.isArray(result.summary.focus) ? result.summary.focus.join(' ') : result.summary.focus}
            </p>
          </CardBody>
        </Card>
      )}
    </motion.div>
  )
}

// === Main ===
export default function Analyzer() {
  const toast = useToast()
  const [file, setFile] = useState(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const canAnalyze = file && jd.trim().length >= 50

  async function analyze() {
    if (!file) { toast('Upload a resume file first', 'warn'); return }
    if (jd.trim().length < 50) { toast('Job description is too short', 'warn'); return }
    setLoading(true); setResult(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const up = await apiFetch('/api/upload', { method: 'POST', body: fd })
      if (!up?.ok) { toast('Upload failed', 'error'); return }
      const upData = await up.json()
      if (!upData.ok) { toast(upData.detail || 'Upload failed', 'error'); return }

      const res = await apiFetch('/api/analyze', {
        method: 'POST',
        body: JSON.stringify({ tmp: upData.tmp, jd }),
      })
      if (!res?.ok) {
        const errData = await res.json().catch(() => ({}))
        toast(errData.error || errData.detail || 'Analysis failed', 'error'); return
      }
      const data = await res.json()
      if (!data.ok) { toast(data.error || data.message || 'Analysis failed', 'error'); return }
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
        description="Upload your resume and paste a job description to get an AI-powered match score."
      />

      {/* Input boxes + action row */}
      <div className="space-y-3">
        {/* Two boxes side by side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Resume box */}
          <Card>
            <div className="px-5 py-3 border-b flex items-center justify-between" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
              <span className="text-[13px] font-semibold text-t1">Resume</span>
              {file && <ClearBtn onClick={() => { setFile(null); setResult(null) }} />}
            </div>
            <CardBody className="p-4">
              <UploadZone file={file} onFile={f => { setFile(f); setResult(null) }} onClear={() => { setFile(null); setResult(null) }} />
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
              <textarea
                value={jd}
                onChange={e => setJd(e.target.value)}
                placeholder="Paste the full job description here..."
                className="input-base resize-none"
                style={{ height: '210px', background: INNER_BG, border: '2px dashed rgba(0,0,0,0.1)' }}
              />
            </CardBody>
          </Card>
        </div>

        {/* Analyse button - bottom right */}
        <div className="flex justify-end">
          <button onClick={analyze} disabled={loading || !canAnalyze} className="btn-primary px-6">
            {loading ? <><Spinner size={14} /> Analysing...</> : 'Analyse Resume'}
          </button>
        </div>
      </div>

      {/* Loading */}
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
                  <div className="text-[14px] font-semibold text-t1">Analysing your resume</div>
                  <div className="text-[13px] text-t2 mt-1">This takes 15-30 seconds</div>
                </div>
              </CardBody>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      {result && !loading && <ResultsPanel result={result} />}
    </div>
  )
}
