/**
 * Shared resume picker used by Analyzer and ATS Check.
 * Shows stored resumes as selectable rows, plus a drop zone to upload a new file.
 * Calls onSelect({ file, resumeId, name }) when a source is chosen; onClear to reset.
 */
import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../lib/auth.js'
import { Spinner } from './ui.jsx'

const INNER_BG     = 'rgba(99,102,241,0.04)'
const INNER_BORDER = 'rgba(99,102,241,0.18)'

export function ResumePicker({ selected, onSelect, onClear, height = '218px' }) {
  const fileRef = useRef(null)
  const [resumes, setResumes] = useState([])
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    apiFetch('/api/resumes').then(async r => {
      if (r?.ok) setResumes((await r.json()).resumes || [])
    })
  }, [])

  function pickFile(f) {
    if (f) onSelect({ file: f, resumeId: null, name: f.name })
  }

  function pickStored(r) {
    onSelect({ file: null, resumeId: r.id, name: r.label || r.original_name })
  }

  function handleDrop(e) {
    e.preventDefault(); setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) pickFile(f)
  }

  // === Selected state ===
  if (selected) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg gap-2 text-center"
        style={{ background: INNER_BG, border: `2px dashed rgba(22,163,74,0.4)`, height, padding: '20px' }}>
        <div className="w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(99,102,241,0.12)' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
            <line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/>
          </svg>
        </div>
        <div className="text-[13.5px] font-semibold text-t1 truncate max-w-full px-2">{selected.name}</div>
        <button onClick={onClear} className="text-[11.5px] font-medium underline underline-offset-2 mt-0.5"
          style={{ color: 'rgb(var(--accent))' }}>
          Change resume
        </button>
      </div>
    )
  }

  // === Picker: dropdown + upload zone ===
  const readyResumes = resumes.filter(r => r.extracted_json)

  return (
    <div className="flex flex-col gap-3" style={{ height }}>
      {/* Dropdown - only shown when there are stored resumes */}
      {readyResumes.length > 0 && (
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: 'rgb(var(--accent))' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <select
            defaultValue=""
            onChange={e => {
              const r = readyResumes.find(r => r.id === e.target.value)
              if (r) pickStored(r)
            }}
            className="w-full pl-9 pr-8 py-2.5 rounded-lg text-[13px] font-medium appearance-none cursor-pointer transition-colors"
            style={{
              background: INNER_BG,
              border: `1.5px solid ${INNER_BORDER}`,
              color: 'rgb(var(--t1))',
              outline: 'none',
              fontFamily: 'inherit',
            }}
            onFocus={e => e.currentTarget.style.borderColor = 'rgb(var(--accent))'}
            onBlur={e => e.currentTarget.style.borderColor = INNER_BORDER}
          >
            <option value="" disabled>Choose a stored resume...</option>
            {readyResumes.map(r => (
              <option key={r.id} value={r.id}>{r.label || r.original_name}</option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: 'rgb(var(--t3))' }}>
            <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 5l5 5 5-5"/>
            </svg>
          </div>
        </div>
      )}

      {/* Divider with "or" when both options exist */}
      {readyResumes.length > 0 && (
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px" style={{ background: INNER_BORDER }} />
          <span className="text-[11px] font-medium text-t3">or upload new</span>
          <div className="flex-1 h-px" style={{ background: INNER_BORDER }} />
        </div>
      )}

      {/* Upload drop zone */}
      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className="flex-1 flex flex-col items-center justify-center gap-2 rounded-lg cursor-pointer transition-all text-center"
        style={{
          background: dragging ? 'rgba(99,102,241,0.08)' : INNER_BG,
          border: `2px dashed ${dragging ? 'rgba(99,102,241,0.5)' : INNER_BORDER}`,
          minHeight: '80px',
          padding: '16px',
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.08)'; e.currentTarget.style.borderColor = 'rgba(99,102,241,0.35)' }}
        onMouseLeave={e => { if (!dragging) { e.currentTarget.style.background = INNER_BG; e.currentTarget.style.borderColor = INNER_BORDER } }}
      >
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: 'rgba(99,102,241,0.1)' }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <div>
          <div className="text-[12.5px] font-semibold" style={{ color: 'rgb(var(--accent))' }}>
            {readyResumes.length > 0 ? 'Upload new file' : 'Upload resume'}
          </div>
          <div className="text-[11.5px] text-t3">PDF or DOCX</div>
        </div>
      </div>

      <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={e => pickFile(e.target.files[0])} />
    </div>
  )
}
