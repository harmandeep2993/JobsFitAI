/**
 * Shared resume picker - always shows two rows: saved resume selector + upload new.
 * Clicking the resume row opens a dropdown to switch between uploaded resumes.
 * Used by Analyzer and ATS Check.
 */
import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../lib/auth.js'

const INNER_BG     = 'rgba(99,102,241,0.04)'
const INNER_BORDER = 'rgba(99,102,241,0.18)'

const FileIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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

const ChevronIcon = ({ open }) => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={open ? 'M2 8l4-4 4 4' : 'M2 4l4 4 4-4'}/>
  </svg>
)

export function ResumePicker({ selected, onSelect, onClear, height = '218px' }) {
  const fileRef    = useRef(null)
  const rowRef     = useRef(null)
  const dropRef    = useRef(null)
  const [resumes, setResumes]           = useState([])
  const [draggingOver, setDraggingOver] = useState(false)
  const [dropOpen, setDropOpen]         = useState(false)

  useEffect(() => {
    apiFetch('/api/resumes').then(async r => {
      if (r?.ok) {
        const list = (await r.json()).resumes || []
        setResumes(list.filter(r => r.extracted_json))
      }
    })
  }, [])

  // Close dropdown on outside click
  useEffect(() => {
    if (!dropOpen) return
    function handleClick(e) {
      if (
        dropRef.current && !dropRef.current.contains(e.target) &&
        rowRef.current  && !rowRef.current.contains(e.target)
      ) {
        setDropOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [dropOpen])

  function pickFile(f) {
    if (f) { onSelect({ file: f, resumeId: null, name: f.name }) }
  }

  function handleDrop(e) {
    e.preventDefault(); setDraggingOver(false)
    pickFile(e.dataTransfer.files[0])
  }

  function selectSaved(r) {
    onSelect({ file: null, resumeId: r.id, name: r.label || r.original_name })
    setDropOpen(false)
  }

  // No saved resumes yet - show only the upload row, full height
  if (resumes.length === 0 && !selected) {
    return (
      <div className="relative" style={{ height }}>
        <button
          className="w-full h-full flex flex-col items-center justify-center gap-3 rounded-xl transition-colors"
          style={{
            background: draggingOver ? 'rgba(99,102,241,0.08)' : INNER_BG,
            border: `1.5px dashed ${INNER_BORDER}`,
          }}
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDraggingOver(true) }}
          onDragLeave={() => setDraggingOver(false)}
          onDrop={handleDrop}
          onMouseEnter={e => { if (!draggingOver) e.currentTarget.style.background = 'rgba(99,102,241,0.07)' }}
          onMouseLeave={e => { if (!draggingOver) e.currentTarget.style.background = INNER_BG }}
        >
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
            <UploadIcon />
          </div>
          <div>
            <div className="text-[13px] font-semibold" style={{ color: 'rgb(var(--accent))' }}>
              {draggingOver ? 'Drop to upload' : 'Upload your resume'}
            </div>
            <div className="text-[11.5px] text-t3 mt-0.5">PDF or DOCX, up to 10 MB</div>
          </div>
        </button>
        <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden"
          onChange={e => pickFile(e.target.files[0])} />
      </div>
    )
  }

  return (
    <div
      className="flex flex-col rounded-xl overflow-visible relative"
      style={{ height, border: `1.5px solid ${INNER_BORDER}`, background: INNER_BG }}
    >
      {/* === Row 1: Base resume selector === */}
      <div className="relative flex-1" ref={rowRef}>
        <button
          className="w-full h-full flex items-center gap-3 px-4 text-left transition-colors"
          style={{ borderBottom: `1px solid ${INNER_BORDER}` }}
          onClick={() => resumes.length > 0 && setDropOpen(v => !v)}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.06)'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{
              background: selected ? 'rgba(99,102,241,0.12)' : 'rgba(99,102,241,0.06)',
              color: 'rgb(var(--accent))',
            }}>
            <FileIcon size={16} />
          </div>

          <div className="flex-1 min-w-0">
            {selected ? (
              <>
                <div className="text-[12px] font-bold uppercase tracking-wide text-t3 mb-0.5">Base Resume</div>
                <div className="text-[13px] font-semibold text-t1 truncate">{selected.name}</div>
              </>
            ) : (
              <>
                <div className="text-[12px] font-bold uppercase tracking-wide text-t3 mb-0.5">Base Resume</div>
                <div className="text-[13px] text-t3">
                  {resumes.length > 0 ? 'Click to select a resume' : 'No resumes yet - upload below'}
                </div>
              </>
            )}
          </div>

          {resumes.length > 0 && (
            <span style={{ color: 'rgb(var(--accent))' }}>
              <ChevronIcon open={dropOpen} />
            </span>
          )}
        </button>

        {/* === Dropdown listing all saved resumes === */}
        {dropOpen && (
          <div
            ref={dropRef}
            className="absolute z-50 rounded-xl overflow-hidden left-0 right-0"
            style={{
              top: 'calc(100% + 6px)',
              background: 'rgb(var(--surface))',
              border: `1.5px solid ${INNER_BORDER}`,
              boxShadow: '0 8px 32px rgba(0,0,0,0.13)',
            }}
          >
            <div className="px-3 pt-2.5 pb-1 text-[10.5px] font-bold uppercase tracking-widest"
              style={{ color: 'rgb(var(--t3))' }}>
              Select resume
            </div>

            {resumes.map(r => (
              <button
                key={r.id}
                onClick={() => selectSaved(r)}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition-colors"
                style={{ background: selected?.resumeId === r.id ? 'rgba(99,102,241,0.08)' : 'transparent' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.07)'}
                onMouseLeave={e => e.currentTarget.style.background = selected?.resumeId === r.id ? 'rgba(99,102,241,0.08)' : 'transparent'}
              >
                <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                  style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
                  <FileIcon />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[12.5px] font-semibold text-t1 truncate">{r.label || r.original_name}</div>
                  <div className="text-[10.5px] text-t3">{r.file_size_kb} KB</div>
                </div>
                {selected?.resumeId === r.id && (
                  <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="rgb(var(--accent))" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 7l3.5 3.5L12 3"/>
                  </svg>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* === Row 2: Upload new resume === */}
      <button
        className="flex items-center gap-3 px-4 transition-colors"
        style={{ flex: 1, background: draggingOver ? 'rgba(99,102,241,0.08)' : 'transparent' }}
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDraggingOver(true) }}
        onDragLeave={() => setDraggingOver(false)}
        onDrop={handleDrop}
        onMouseEnter={e => { if (!draggingOver) e.currentTarget.style.background = 'rgba(99,102,241,0.06)' }}
        onMouseLeave={e => { if (!draggingOver) e.currentTarget.style.background = 'transparent' }}
      >
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: 'rgba(99,102,241,0.08)', color: 'rgb(var(--accent))' }}>
          <UploadIcon />
        </div>
        <div className="flex-1 min-w-0 text-left">
          <div className="text-[12px] font-bold uppercase tracking-wide text-t3 mb-0.5">Upload New</div>
          <div className="text-[13px] font-semibold" style={{ color: 'rgb(var(--accent))' }}>
            {draggingOver ? 'Drop to upload' : 'PDF or DOCX, up to 10 MB'}
          </div>
        </div>
        <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="rgb(var(--accent))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 2l5 5-5 5"/>
        </svg>
      </button>

      <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden"
        onChange={e => pickFile(e.target.files[0])} />
    </div>
  )
}
