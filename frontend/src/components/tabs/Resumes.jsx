import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'
import { PageHeader, Card, CardBody, CardSection, SectionLabel, Spinner } from '../ui.jsx'

const SLOT_NAMES = ['Base Resume', 'Tailored 1', 'Tailored 2']
const SLOT_DESC  = ['Your primary resume', 'Tailored for a specific role', 'Tailored for a specific role']

function ResumeSlot({ slot, resume, onUpload, onDelete, onLabel, onUseForMatching }) {
  const fileRef = useRef(null)
  const [editing, setEditing] = useState(false)
  const [labelVal, setLabelVal] = useState('')

  function startEdit() {
    setLabelVal(resume?.label || resume?.original_name || '')
    setEditing(true)
  }

  return (
    <Card>
      <CardBody>
        {/* Slot header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center text-accent text-[13px] font-bold flex-shrink-0">
            {slot + 1}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[13.5px] font-semibold text-t1">{SLOT_NAMES[slot]}</div>
            <div className="text-[12px] text-t2">{resume ? resume.original_name : SLOT_DESC[slot]}</div>
          </div>
          {resume && (
            <span className="px-2 py-0.5 text-[11px] font-medium rounded-sm bg-green-bg border border-green-bd text-green flex-shrink-0">
              Uploaded
            </span>
          )}
        </div>

        {resume ? (
          <div className="space-y-4">
            {/* Label edit */}
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
                  className="input-base flex-1"
                  placeholder="Resume label..."
                />
                <button onClick={() => { onLabel(resume.id, labelVal.trim()); setEditing(false) }} className="btn-primary py-1.5 px-3 text-[12.5px]">Save</button>
                <button onClick={() => setEditing(false)} className="btn-secondary py-1.5 px-3 text-[12.5px]">Cancel</button>
              </div>
            ) : (
              <div className="flex items-center gap-2 group">
                <span className="text-[14px] font-medium text-t1">{resume.label || resume.original_name}</span>
                <button onClick={startEdit} className="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center text-t3 hover:text-t1 hover:bg-hover rounded-sm transition-all" title="Rename">
                  <svg width="11" height="11" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M10 2l2 2-7 7H3V9l7-7z"/></svg>
                </button>
              </div>
            )}

            {/* File info row */}
            <div className="flex items-center gap-3 px-3.5 py-2.5 bg-surface-2 rounded-sm text-[12.5px] text-t2">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--t3)" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="1" width="10" height="14" rx="1.5"/>
                <path d="M6 5h4M6 7.5h4M6 10h2.5"/>
              </svg>
              <span className="flex-1 truncate">{resume.original_name}</span>
              <span className="text-t3">{Math.round(resume.file_size_kb)} KB</span>
            </div>

            {!resume.extracted_json && (
              <div className="flex items-center gap-2 text-[12.5px] text-amber">
                <Spinner size={12} />
                Extracting resume data...
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 pt-1">
              <button onClick={() => onUseForMatching(resume.id)} disabled={!resume.extracted_json} className="btn-primary py-1.5 px-3.5 text-[12.5px]">
                Use for matching
              </button>
              <a href={`/api/resumes/${resume.id}/file`} target="_blank" rel="noreferrer" className="btn-secondary py-1.5 px-3 text-[12.5px]">
                Preview
              </a>
              <button onClick={() => onDelete(resume.id)} className="ml-auto w-8 h-8 flex items-center justify-center text-t3 hover:text-red hover:bg-red-bg border border-transparent hover:border-red-bd rounded-sm transition-colors" title="Delete">
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
              className="w-full border-2 border-dashed border-border rounded-lg py-7 flex flex-col items-center gap-2 text-t3 hover:border-accent/40 hover:bg-accent-s hover:text-t2 transition-all cursor-pointer"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span className="text-[13px] font-medium">Click to upload resume</span>
              <span className="text-[12px]">PDF or DOCX</span>
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
        description="Store up to 3 resume versions. Activate any slot as your active resume for job matching and scoring."
      />

      <div className="grid grid-cols-1 gap-4">
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
