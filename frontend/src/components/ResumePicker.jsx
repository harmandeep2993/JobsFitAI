/**
 * Shared resume picker - lists all saved resumes + upload new, all visible at once.
 * Used by Analyzer and ATS Check.
 */
import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../lib/auth.js'

const INNER_BG     = 'rgba(99,102,241,0.04)'
const INNER_BORDER = 'rgba(99,102,241,0.18)'

const FileIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
)

const UploadIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
)

export function ResumePicker({ selected, onSelect, onClear, height = '218px' }) {
  const fileRef = useRef(null)
  const [resumes, setResumes] = useState([])
  const [draggingOver, setDraggingOver] = useState(false)

  useEffect(() => {
    apiFetch('/api/resumes').then(async r => {
      if (r?.ok) {
        const list = (await r.json()).resumes || []
        setResumes(list.filter(r => r.extracted_json))
      }
    })
  }, [])

  function pickFile(f) {
    if (f) onSelect({ file: f, resumeId: null, name: f.name })
  }

  function handleDrop(e) {
    e.preventDefault(); setDraggingOver(false)
    const f = e.dataTransfer.files[0]
    if (f) pickFile(f)
  }

  // === Selected state ===
  if (selected) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl gap-3 text-center"
        style={{ background: INNER_BG, border: `1.5px dashed rgba(22,163,74,0.4)`, height, padding: '20px' }}>
        <div className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(99,102,241,0.12)', color: 'rgb(var(--accent))' }}>
          <FileIcon />
        </div>
        <div>
          <div className="text-[13px] font-semibold text-t1 truncate max-w-[200px]">{selected.name}</div>
          <div className="text-[11.5px] text-t3 mt-0.5">Resume selected</div>
        </div>
        <button onClick={onClear}
          className="text-[12px] font-semibold px-3 py-1 rounded-lg transition-colors"
          style={{ color: 'rgb(var(--accent))', background: 'rgba(99,102,241,0.1)' }}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.18)'}
          onMouseLeave={e => e.currentTarget.style.background = 'rgba(99,102,241,0.1)'}
        >
          Change
        </button>
      </div>
    )
  }

  // === Picker list ===
  return (
    <div className="flex flex-col rounded-xl overflow-hidden"
      style={{ height, border: `1.5px solid ${INNER_BORDER}`, background: INNER_BG }}>

      <div className="flex-1 overflow-y-auto">
        {/* Saved resume rows */}
        {resumes.map(r => (
          <button
            key={r.id}
            onClick={() => onSelect({ file: null, resumeId: r.id, name: r.label || r.original_name })}
            className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors"
            style={{ borderBottom: `1px solid ${INNER_BORDER}` }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.07)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
              <FileIcon />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-semibold text-t1 truncate">{r.label || r.original_name}</div>
              <div className="text-[11px] text-t3">{r.original_name} &middot; {r.file_size_kb} KB</div>
            </div>
            <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="rgb(var(--t3))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 2l5 5-5 5"/>
            </svg>
          </button>
        ))}

        {/* Upload new row */}
        <button
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDraggingOver(true) }}
          onDragLeave={() => setDraggingOver(false)}
          onDrop={handleDrop}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors"
          style={{ background: draggingOver ? 'rgba(99,102,241,0.1)' : 'transparent' }}
          onMouseEnter={e => { if (!draggingOver) e.currentTarget.style.background = 'rgba(99,102,241,0.07)' }}
          onMouseLeave={e => { if (!draggingOver) e.currentTarget.style.background = 'transparent' }}
        >
          <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(99,102,241,0.08)', color: 'rgb(var(--accent))' }}>
            <UploadIcon />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-semibold" style={{ color: 'rgb(var(--accent))' }}>
              {draggingOver ? 'Drop to upload' : 'Upload new resume'}
            </div>
            <div className="text-[11px] text-t3">PDF or DOCX, up to 10 MB</div>
          </div>
          <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 2l5 5-5 5"/>
          </svg>
        </button>

        {/* Empty state when no saved resumes */}
        {resumes.length === 0 && (
          <div className="px-4 py-3 text-[11.5px] text-t3 text-center" style={{ borderBottom: `1px solid ${INNER_BORDER}` }}>
            No saved resumes yet
          </div>
        )}
      </div>

      <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden"
        onChange={e => pickFile(e.target.files[0])} />
    </div>
  )
}
