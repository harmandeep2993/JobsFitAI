/**
 * Resumes tab - three resume slots displayed side by side (1 row x 3 cols).
 */
import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'
import { PageHeader, Card, CardBody, Spinner } from '../ui.jsx'

const INNER_BG     = 'rgba(99,102,241,0.04)'
const INNER_BORDER = 'rgba(99,102,241,0.18)'

const SLOT_NAMES = ['Base Resume', 'Tailored 1', 'Tailored 2']
const SLOT_DESC  = ['Your primary resume', 'Tailored for a specific role', 'Tailored for a specific role']

// === Preview modal ===
function PreviewModal({ resume, onClose }) {
  const [url, setUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const isPdf = resume?.original_name?.toLowerCase().endsWith('.pdf')

  useEffect(() => {
    let objectUrl
    apiFetch(`/api/resumes/${resume.id}/file`).then(async res => {
      if (!res?.ok) { setError('Could not load file'); setLoading(false); return }
      const blob = await res.blob()
      objectUrl = URL.createObjectURL(blob)
      setUrl(objectUrl)
      setLoading(false)
    })
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [resume.id])

  // Close on backdrop click or Escape
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[300] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}
      onClick={onClose}
    >
      <div
        className="relative flex flex-col rounded-xl overflow-hidden shadow-2xl"
        style={{ width: 'min(860px, 100%)', height: 'min(90vh, 900px)', background: 'rgb(var(--surface))' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b flex-shrink-0" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(99,102,241,0.1)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <span className="text-[13.5px] font-semibold text-t1 truncate max-w-xs">{resume.label || resume.original_name}</span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg transition-colors flex-shrink-0"
            style={{ color: 'rgb(var(--t2))' }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgb(var(--surface-2))'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 2l10 10M12 2L2 12"/>
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {loading && (
            <div className="h-full flex flex-col items-center justify-center gap-3">
              <Spinner size={24} />
              <span className="text-[13px] text-t2">Loading preview...</span>
            </div>
          )}
          {error && (
            <div className="h-full flex items-center justify-center text-[13px] text-t2">{error}</div>
          )}
          {url && isPdf && (
            <iframe src={url} className="w-full h-full border-0" title="Resume preview" />
          )}
          {url && !isPdf && (
            <div className="h-full flex flex-col items-center justify-center gap-4 p-8 text-center">
              <div className="w-14 h-14 rounded-xl flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.1)' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <div>
                <div className="text-[14px] font-semibold text-t1">DOCX files cannot be previewed inline</div>
                <div className="text-[13px] text-t2 mt-1">Download the file to open it in Word or Google Docs.</div>
              </div>
              <a href={url} download={resume.original_name} className="btn-primary px-5">
                Download file
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// After this many ms without extracted data, treat extraction as stuck
// and offer a manual retry (normal extraction finishes in under a minute).
const EXTRACTION_STUCK_MS = 2 * 60 * 1000

// === Uploaded resume card ===
function ResumeCard({ resume, index, onDelete, onLabel, onUseForMatching, onPreview, onRetry, retrying }) {
  const [editing, setEditing] = useState(false)
  const [labelVal, setLabelVal] = useState('')
  const hasExtracted = Boolean(resume.extracted_json)
  const uploadedMs = resume.uploaded_at ? Date.now() - new Date(resume.uploaded_at).getTime() : 0
  const extractionStuck = !hasExtracted && uploadedMs > EXTRACTION_STUCK_MS

  function startEdit() {
    setLabelVal(resume.label || resume.original_name || '')
    setEditing(true)
  }

  return (
    <Card className="flex flex-col">
      {/* Header: slot badge + resume name + edit */}
      <div className="px-5 py-3.5 border-b flex items-center gap-3" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
        <div className="w-7 h-7 rounded-md flex items-center justify-center text-[12px] font-bold flex-shrink-0"
          style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="flex items-center gap-1.5">
              <input
                autoFocus
                value={labelVal}
                onChange={e => setLabelVal(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') { onLabel(resume.id, labelVal.trim()); setEditing(false) }
                  if (e.key === 'Escape') setEditing(false)
                }}
                className="input-base flex-1 py-0.5 text-[12px]"
                placeholder="Resume name..."
              />
              <button onClick={() => { onLabel(resume.id, labelVal.trim()); setEditing(false) }} className="btn-primary py-0.5 px-2 text-[11px]">Save</button>
              <button onClick={() => setEditing(false)} className="btn-secondary py-0.5 px-2 text-[11px]">Cancel</button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 group">
              <span className="text-[13px] font-semibold text-t1 truncate">{resume.label || resume.original_name}</span>
              <button onClick={startEdit}
                className="opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center rounded-sm transition-all flex-shrink-0"
                style={{ color: 'rgb(var(--t3))' }}
                onMouseEnter={e => e.currentTarget.style.color = 'rgb(var(--accent))'}
                onMouseLeave={e => e.currentTarget.style.color = 'rgb(var(--t3))'}
                title="Rename">
                <svg width="10" height="10" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10 2l2 2-7 7H3V9l7-7z"/>
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      <CardBody className="p-4 flex flex-col gap-3">
        {/* File info */}
        <div className="flex items-center gap-3 rounded-lg px-3.5 py-3"
          style={{ background: INNER_BG, border: `1.5px dashed ${INNER_BORDER}` }}>
          <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(99,102,241,0.12)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
              <line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/>
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[12.5px] font-semibold text-t1 truncate">{resume.original_name}</div>
            <div className="text-[11.5px] text-t3">{Math.round(resume.file_size_kb)} KB</div>
          </div>
        </div>

        {/* Extraction status */}
        <div className="flex items-center gap-2 text-[12px]"
          style={{ color: hasExtracted ? '#16a34a' : extractionStuck ? '#dc2626' : 'rgb(var(--t3))' }}>
          {hasExtracted ? (
            <>
              <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2.5 7l3 3 6-6"/>
              </svg>
              Data extracted
            </>
          ) : extractionStuck ? (
            <>
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M8 3v5M8 11v.5"/><path d="M8 1L1 13h14L8 1z"/>
              </svg>
              Extraction failed
              <button onClick={() => onRetry(resume.id)} disabled={retrying}
                className="ml-1 px-2 py-0.5 text-[11px] font-medium rounded-sm transition-colors"
                style={{ color: 'rgb(var(--accent))', background: 'rgba(99,102,241,0.08)' }}>
                {retrying ? 'Retrying...' : 'Retry'}
              </button>
            </>
          ) : (
            <><Spinner size={11} /> Extracting data...</>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-auto pt-1">
          <button onClick={() => onUseForMatching(resume.id)} disabled={!hasExtracted} className="btn-primary py-1.5 px-3 text-[12px] flex-1">
            Use for matching
          </button>
          <button onClick={() => onPreview(resume)} className="btn-secondary py-1.5 px-3 text-[12px]">
            Preview
          </button>
          <button
            onClick={() => onDelete(resume.id)}
            className="w-8 h-8 flex items-center justify-center rounded-sm transition-colors flex-shrink-0"
            style={{ border: '1.5px solid rgba(0,0,0,0.06)', color: 'rgb(var(--t3))' }}
            onMouseEnter={e => { e.currentTarget.style.color = '#dc2626'; e.currentTarget.style.background = 'rgba(220,38,38,0.06)'; e.currentTarget.style.borderColor = 'rgba(220,38,38,0.25)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'rgb(var(--t3))'; e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(0,0,0,0.06)' }}
            title="Delete"
          >
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 4h10M5 4V2h6v2M4 4l.7 9.3h6.6L12 4"/>
            </svg>
          </button>
        </div>
      </CardBody>
    </Card>
  )
}

// === Add resume card (+ button) ===
function AddResumeCard({ nextSlot, onUpload }) {
  const fileRef = useRef(null)
  return (
    <div>
      <button
        onClick={() => fileRef.current?.click()}
        className="w-full rounded-xl flex flex-col items-center justify-center gap-3 transition-all cursor-pointer"
        style={{ background: INNER_BG, border: `2px dashed ${INNER_BORDER}`, minHeight: '220px' }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.08)'; e.currentTarget.style.borderColor = 'rgba(99,102,241,0.35)' }}
        onMouseLeave={e => { e.currentTarget.style.background = INNER_BG; e.currentTarget.style.borderColor = INNER_BORDER }}
      >
        <div className="w-12 h-12 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(99,102,241,0.1)' }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </div>
        <div className="text-center">
          <div className="text-[13px] font-semibold" style={{ color: 'rgb(var(--accent))' }}>Add resume</div>
          <div className="text-[12px] text-t3 mt-0.5">PDF or DOCX</div>
        </div>
      </button>
      <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={e => onUpload(nextSlot, e.target.files[0])} />
    </div>
  )
}

export default function Resumes() {
  const toast = useToast()
  const [resumes, setResumes] = useState([])
  const [previewing, setPreviewing] = useState(null)
  const [retryingId, setRetryingId] = useState(null)

  async function load() {
    const res = await apiFetch('/api/resumes')
    if (res?.ok) setResumes((await res.json()).resumes || [])
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    const pending = resumes.some(r => !r.extracted_json)
    if (!pending) return
    const iv = setInterval(load, 4000)
    return () => clearInterval(iv)
  }, [resumes])

  async function upload(slot, file) {
    if (!file) return
    const fd = new FormData()
    fd.append('file', file); fd.append('slot', slot)
    const res = await apiFetch('/api/resumes/upload', { method: 'POST', body: fd })
    if (res?.ok) { toast('Resume uploaded', 'success'); load() }
    else { const d = await res.json(); toast(d.detail || 'Upload failed', 'error') }
  }

  async function del(id) {
    const res = await apiFetch(`/api/resumes/${id}`, { method: 'DELETE' })
    if (res?.ok) { toast('Deleted', 'info'); load() }
  }

  async function saveLabel(id, label) {
    const res = await apiFetch(`/api/resumes/${id}/label`, { method: 'POST', body: JSON.stringify({ label }) })
    if (res?.ok) { toast('Label saved', 'success'); load() }
  }

  async function retryExtraction(id) {
    setRetryingId(id)
    try {
      const res = await apiFetch(`/api/resumes/${id}/re-extract`, { method: 'POST' })
      if (res?.ok) { toast('Extraction complete', 'success'); load() }
      else toast('Extraction failed again - the file may be image-based. Try re-saving it as a text-based PDF.', 'error')
    } finally { setRetryingId(null) }
  }

  async function useForMatching(id) {
    const res = await apiFetch(`/api/resumes/${id}/use-for-matching`, { method: 'POST' })
    if (res?.ok) {
      const d = await res.json()
      toast(d.cached ? 'Resume already active' : `Loaded - rescored ${d.rescored} jobs`, 'success')
    }
  }

  const MAX_SLOTS = 3
  // Next available slot number (fills gaps left by deletions)
  const usedSlots = new Set(resumes.map(r => r.slot))
  const nextSlot = [0, 1, 2].find(s => !usedSlots.has(s)) ?? 0
  const canAddMore = resumes.length < MAX_SLOTS

  return (
    <div className="space-y-5">
      <PageHeader
        title="Resumes"
        description="Store up to 3 resume versions. Activate any slot as your active resume for job matching."
        action={
          <span className="text-[13px] font-semibold px-3 py-1.5 rounded-lg"
            title="The free plan includes 3 resume slots - delete one to make room for another version."
            style={{ background: 'rgba(99,102,241,0.08)', color: 'rgb(var(--accent))' }}>
            {resumes.length} / {MAX_SLOTS} slots
          </span>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
        {resumes.map((r, i) => (
          <ResumeCard
            key={r.id}
            resume={r}
            index={i}
            onDelete={del}
            onLabel={saveLabel}
            onUseForMatching={useForMatching}
            onPreview={setPreviewing}
            onRetry={retryExtraction}
            retrying={retryingId === r.id}
          />
        ))}
        {canAddMore && (
          <AddResumeCard nextSlot={nextSlot} onUpload={upload} />
        )}
      </div>

      {previewing && <PreviewModal resume={previewing} onClose={() => setPreviewing(null)} />}
    </div>
  )
}
