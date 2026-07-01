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

async function previewResume(id) {
  const res = await apiFetch(`/api/resumes/${id}/file`)
  if (!res?.ok) return
  const blob = await res.blob()
  window.open(URL.createObjectURL(blob), '_blank')
}

function ResumeSlot({ slot, resume, onUpload, onDelete, onLabel, onUseForMatching }) {
  const fileRef = useRef(null)
  const [editing, setEditing] = useState(false)
  const [labelVal, setLabelVal] = useState('')

  function startEdit() {
    setLabelVal(resume?.label || resume?.original_name || '')
    setEditing(true)
  }

  const hasExtracted = Boolean(resume?.extracted_json)

  return (
    <Card className="flex flex-col h-full">
      <div className="px-5 py-3.5 border-b flex items-center gap-3" style={{ borderColor: 'rgba(0,0,0,0.06)' }}>
        <div className="w-7 h-7 rounded-md flex items-center justify-center text-[12px] font-bold flex-shrink-0"
          style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
          {slot + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[13px] font-semibold text-t1 truncate">{SLOT_NAMES[slot]}</div>
        </div>
        {resume && (
          <span className="px-2 py-0.5 text-[10.5px] font-semibold rounded-sm flex-shrink-0"
            style={{ background: 'rgba(22,163,74,0.1)', color: '#16a34a', border: '1px solid rgba(22,163,74,0.25)' }}>
            Uploaded
          </span>
        )}
      </div>

      <CardBody className="p-4 flex-1 flex flex-col">
        {resume ? (
          <div className="flex flex-col gap-3 h-full">
            {/* File card */}
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

            {/* Label */}
            {editing ? (
              <div className="flex items-center gap-2">
                <input
                  autoFocus
                  value={labelVal}
                  onChange={e => setLabelVal(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') { onLabel(resume.id, labelVal.trim()); setEditing(false) }
                    if (e.key === 'Escape') setEditing(false)
                  }}
                  className="input-base flex-1 text-[12.5px]"
                  placeholder="Resume label..."
                />
                <button onClick={() => { onLabel(resume.id, labelVal.trim()); setEditing(false) }} className="btn-primary py-1 px-3 text-[12px]">Save</button>
                <button onClick={() => setEditing(false)} className="btn-secondary py-1 px-2 text-[12px]">X</button>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 group">
                <span className="text-[12.5px] font-medium text-t2 truncate flex-1">{resume.label || resume.original_name}</span>
                <button onClick={startEdit}
                  className="opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center text-t3 hover:text-accent rounded-sm transition-all"
                  title="Rename">
                  <svg width="10" height="10" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 2l2 2-7 7H3V9l7-7z"/>
                  </svg>
                </button>
              </div>
            )}

            {/* Extraction status */}
            <div className="flex items-center gap-2 text-[12px]"
              style={{ color: hasExtracted ? '#16a34a' : 'rgb(var(--t3))' }}>
              {hasExtracted ? (
                <>
                  <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2.5 7l3 3 6-6"/>
                  </svg>
                  Data extracted
                </>
              ) : (
                <>
                  <Spinner size={11} />
                  Extracting data...
                </>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 mt-auto pt-1">
              <button
                onClick={() => onUseForMatching(resume.id)}
                disabled={!hasExtracted}
                className="btn-primary py-1.5 px-3 text-[12px] flex-1"
              >
                Use for matching
              </button>
              <button
                onClick={() => previewResume(resume.id)}
                className="btn-secondary py-1.5 px-3 text-[12px]"
              >
                Preview
              </button>
              <button
                onClick={() => onDelete(resume.id)}
                className="w-8 h-8 flex items-center justify-center text-t3 rounded-sm transition-colors flex-shrink-0"
                style={{ border: '1.5px solid rgba(0,0,0,0.06)' }}
                onMouseEnter={e => { e.currentTarget.style.color = '#dc2626'; e.currentTarget.style.background = 'rgba(220,38,38,0.06)'; e.currentTarget.style.borderColor = 'rgba(220,38,38,0.25)' }}
                onMouseLeave={e => { e.currentTarget.style.color = 'rgb(var(--t3))'; e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(0,0,0,0.06)' }}
                title="Delete"
              >
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 4h10M5 4V2h6v2M4 4l.7 9.3h6.6L12 4"/>
                </svg>
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col h-full">
            <p className="text-[12px] text-t3 mb-3">{SLOT_DESC[slot]}</p>
            <button
              onClick={() => fileRef.current?.click()}
              className="flex-1 rounded-xl flex flex-col items-center justify-center gap-3 transition-all cursor-pointer"
              style={{ background: INNER_BG, border: `2px dashed ${INNER_BORDER}`, minHeight: '160px' }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.08)'; e.currentTarget.style.borderColor = 'rgba(99,102,241,0.35)' }}
              onMouseLeave={e => { e.currentTarget.style.background = INNER_BG; e.currentTarget.style.borderColor = INNER_BORDER }}
            >
              <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ background: 'rgba(99,102,241,0.1)' }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <div>
                <div className="text-[13px] font-semibold text-t2">Click to upload</div>
                <div className="text-[12px] text-t3 mt-0.5">PDF or DOCX</div>
              </div>
            </button>
            <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={e => onUpload(slot, e.target.files[0])} />
          </div>
        )}
      </CardBody>
    </Card>
  )
}

export default function Resumes() {
  const toast = useToast()
  const [resumes, setResumes] = useState([])

  async function load() {
    const res = await apiFetch('/api/resumes')
    if (res?.ok) setResumes((await res.json()).resumes || [])
  }

  useEffect(() => { load() }, [])

  // Poll while any slot is still extracting
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

  async function useForMatching(id) {
    const res = await apiFetch(`/api/resumes/${id}/use-for-matching`, { method: 'POST' })
    if (res?.ok) {
      const d = await res.json()
      toast(d.cached ? 'Resume already active' : `Loaded - rescored ${d.rescored} jobs`, 'success')
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Resumes"
        description="Store up to 3 resume versions. Activate any slot as your active resume for job matching."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[0, 1, 2].map(slot => (
          <ResumeSlot
            key={slot}
            slot={slot}
            resume={resumes.find(r => r.slot === slot)}
            onUpload={upload}
            onDelete={del}
            onLabel={saveLabel}
            onUseForMatching={useForMatching}
          />
        ))}
      </div>
    </div>
  )
}
