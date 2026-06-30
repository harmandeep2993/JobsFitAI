import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

const SLOT_NAMES = ['Base Resume', 'Tailored 1', 'Tailored 2']

function ResumeSlot({ slot, resume, onUpload, onDelete, onLabel, onUseForMatching, loading }) {
  const fileRef = useRef(null)
  const [editing, setEditing] = useState(false)
  const [labelVal, setLabelVal] = useState('')

  function startEdit() {
    setLabelVal(resume?.label || resume?.original_name || '')
    setEditing(true)
  }

  async function saveLabel() {
    if (labelVal.trim()) await onLabel(resume.id, labelVal.trim())
    setEditing(false)
  }

  return (
    <div className="card p-5">
      {/* Slot header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-7 h-7 rounded-sm bg-accent/10 flex items-center justify-center text-accent text-[12px] font-bold flex-shrink-0">
          {slot + 1}
        </div>
        <div>
          <div className="text-[13px] font-semibold text-t1">{SLOT_NAMES[slot]}</div>
          {!resume && <div className="text-[12px] text-t3">Empty slot</div>}
        </div>
        {resume && (
          <div className="ml-auto flex items-center gap-1.5">
            <span className="px-2 py-0.5 text-[11px] font-medium rounded-xs bg-green-bg border border-green-bd text-green">
              Uploaded
            </span>
          </div>
        )}
      </div>

      {resume ? (
        <div className="space-y-4">
          {/* Label */}
          {editing ? (
            <div className="flex items-center gap-2">
              <input
                autoFocus
                value={labelVal}
                onChange={e => setLabelVal(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') saveLabel(); if (e.key === 'Escape') setEditing(false) }}
                className="input-base flex-1"
                placeholder="Resume label..."
              />
              <button onClick={saveLabel} className="btn-primary py-1.5 px-3 text-[12.5px]">Save</button>
              <button onClick={() => setEditing(false)} className="btn-secondary py-1.5 px-3 text-[12.5px]">Cancel</button>
            </div>
          ) : (
            <div className="flex items-center gap-2 group">
              <span className="text-[14px] font-medium text-t1">{resume.label || resume.original_name}</span>
              <button
                onClick={startEdit}
                className="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center text-t3 hover:text-t1 hover:bg-hover rounded-xs transition-all"
                title="Rename"
              >
                <svg width="11" height="11" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10 2l2 2-7 7H3V9l7-7z"/>
                </svg>
              </button>
            </div>
          )}

          {/* File info */}
          <div className="flex items-center gap-4 py-3 px-4 bg-surface-2 rounded-sm text-[12px]">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--t3)" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="1" width="10" height="14" rx="1.5"/>
              <path d="M6 5h4M6 7.5h4M6 10h2.5"/>
            </svg>
            <span className="text-t2 flex-1 truncate">{resume.original_name}</span>
            <span className="text-t3">{Math.round(resume.file_size_kb)} KB</span>
          </div>

          {!resume.extracted_json && (
            <div className="flex items-center gap-2 text-[12px] text-amber">
              <svg className="animate-spin" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M21 12a9 9 0 11-6-8.5"/>
              </svg>
              Extracting resume data...
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => onUseForMatching(resume.id)}
              disabled={!resume.extracted_json}
              className="btn-primary py-1.5 px-3.5 text-[12.5px]"
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="8" cy="8" r="6.5"/>
                <path d="M5 8l2 2 4-4"/>
              </svg>
              Use for matching
            </button>
            <a
              href={`/api/resumes/${resume.id}/file`}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary py-1.5 px-3 text-[12.5px]"
            >
              Preview
            </a>
            <button
              onClick={() => onDelete(resume.id)}
              className="ml-auto w-8 h-8 flex items-center justify-center text-t3 hover:text-red hover:bg-red-bg border border-transparent hover:border-red-bd rounded-sm transition-colors"
              title="Delete"
            >
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 4h10M5 4V2h6v2M4 4l.7 9.3h6.6L12 4"/>
              </svg>
            </button>
          </div>
        </div>
      ) : (
        <div>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={loading}
            className="w-full border-2 border-dashed border-border rounded-sm py-8 flex flex-col items-center gap-2 text-t3 hover:border-accent/40 hover:bg-accent-s hover:text-t2 transition-all cursor-pointer"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span className="text-[13px] font-medium">Upload resume</span>
            <span className="text-[11.5px]">PDF or DOCX</span>
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={e => onUpload(slot, e.target.files[0])}
          />
        </div>
      )}
    </div>
  )
}

export default function Resumes() {
  const toast = useToast()
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(false)

  async function load() {
    const res = await apiFetch('/api/resumes')
    if (res?.ok) {
      const d = await res.json()
      setResumes(d.resumes || [])
    }
  }

  useEffect(() => { load() }, [])

  async function upload(slot, file) {
    if (!file) return
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('slot', slot)
      const res = await apiFetch('/api/resumes/upload', { method: 'POST', body: fd })
      if (res?.ok) {
        toast('Resume uploaded successfully', 'success')
        load()
      } else {
        const d = await res.json()
        toast(d.detail || 'Upload failed', 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  async function del(id) {
    const res = await apiFetch(`/api/resumes/${id}`, { method: 'DELETE' })
    if (res?.ok) { toast('Resume deleted', 'info'); load() }
    else toast('Delete failed', 'error')
  }

  async function saveLabel(id, label) {
    const res = await apiFetch(`/api/resumes/${id}/label`, {
      method: 'POST',
      body: JSON.stringify({ label }),
    })
    if (res?.ok) { toast('Label saved', 'success'); load() }
    else toast('Save failed', 'error')
  }

  async function useForMatching(id) {
    const res = await apiFetch(`/api/resumes/${id}/use-for-matching`, { method: 'POST' })
    if (res?.ok) {
      const d = await res.json()
      toast(d.cached ? 'Resume already active' : `Loaded - rescored ${d.rescored} jobs`, 'success')
    } else {
      toast('Could not load resume', 'error')
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-t1">Resumes</h1>
        <p className="text-sm text-t2 mt-1">Upload up to 3 resume versions. Activate any slot for job matching.</p>
      </div>

      <div className="space-y-3">
        {[0, 1, 2].map(slot => (
          <ResumeSlot
            key={slot}
            slot={slot}
            resume={resumes.find(r => r.slot === slot)}
            onUpload={upload}
            onDelete={del}
            onLabel={saveLabel}
            onUseForMatching={useForMatching}
            loading={loading}
          />
        ))}
      </div>
    </div>
  )
}
