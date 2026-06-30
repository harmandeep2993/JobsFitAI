import { useState, useEffect, useRef } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

const SLOTS = ['Base Resume', 'Tailored 1', 'Tailored 2']

export default function Resumes() {
  const toast = useToast()
  const fileRefs = [useRef(null), useRef(null), useRef(null)]
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(false)
  const [editLabel, setEditLabel] = useState({})

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
        toast('Resume uploaded', 'success')
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
    if (res?.ok) { toast('Deleted', 'info'); load() }
  }

  async function saveLabel(id) {
    const label = editLabel[id]?.trim()
    if (!label) return
    const res = await apiFetch(`/api/resumes/${id}/label`, {
      method: 'POST',
      body: JSON.stringify({ label }),
    })
    if (res?.ok) {
      setEditLabel(l => { const n = { ...l }; delete n[id]; return n })
      load()
    }
  }

  async function useForMatching(id) {
    const res = await apiFetch(`/api/resumes/${id}/use-for-matching`, { method: 'POST' })
    if (res?.ok) {
      const d = await res.json()
      toast(d.cached ? 'Already active' : `Loaded - rescored ${d.rescored} jobs`, 'success')
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">Resumes</h1>
      <p className="text-sm text-t2">Upload up to 3 resume versions. Use any slot as the active resume for job matching.</p>

      <div className="space-y-3">
        {SLOTS.map((slotName, slot) => {
          const r = resumes.find(x => x.slot === slot)
          return (
            <div key={slot} className="bg-surface border border-border rounded p-4">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-s bg-accent/10 flex items-center justify-center text-accent text-xs font-bold flex-shrink-0">
                  {slot + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-t3 font-medium mb-1">{slotName}</div>

                  {r ? (
                    <div className="space-y-2">
                      {/* Label edit */}
                      {editLabel[r.id] !== undefined ? (
                        <div className="flex items-center gap-2">
                          <input
                            autoFocus
                            value={editLabel[r.id]}
                            onChange={e => setEditLabel(l => ({ ...l, [r.id]: e.target.value }))}
                            onKeyDown={e => { if (e.key === 'Enter') saveLabel(r.id) }}
                            className="flex-1 px-2 py-1 bg-bg border border-border rounded-xs text-sm text-t1 focus:outline-none focus:border-accent"
                          />
                          <button onClick={() => saveLabel(r.id)} className="text-xs text-accent font-semibold">Save</button>
                          <button onClick={() => setEditLabel(l => { const n = {...l}; delete n[r.id]; return n })} className="text-xs text-t2">Cancel</button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold">{r.label || r.original_name}</span>
                          <button
                            onClick={() => setEditLabel(l => ({ ...l, [r.id]: r.label || r.original_name }))}
                            className="text-xs text-t3 hover:text-t1"
                          >
                            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                              <path d="M11.5 2.5a2 2 0 012 2l-9 9L2 14l.5-2.5 9-9z"/>
                            </svg>
                          </button>
                        </div>
                      )}

                      <div className="text-xs text-t2">{r.original_name} - {Math.round(r.file_size_kb)}kb</div>

                      {!r.extracted_json && (
                        <div className="text-xs text-amber">Extracting resume data...</div>
                      )}

                      <div className="flex items-center gap-2 mt-2">
                        <button
                          onClick={() => useForMatching(r.id)}
                          disabled={!r.extracted_json}
                          className="text-xs px-3 py-1.5 bg-accent text-white rounded-xs hover:bg-accent-h disabled:opacity-50 transition-colors"
                        >
                          Use for matching
                        </button>
                        <a
                          href={`/api/resumes/${r.id}/file`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs px-2.5 py-1.5 border border-border rounded-xs text-t2 hover:text-t1 hover:bg-hover transition-colors"
                        >
                          Preview
                        </a>
                        <button
                          onClick={() => del(r.id)}
                          className="text-xs text-t3 hover:text-red transition-colors ml-auto"
                        >
                          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                            <path d="M3 4h10M5 4V2h6v2M6 7v5M10 7v5M4 4l.6 9h6.8L12 4"/>
                          </svg>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <button
                        onClick={() => fileRefs[slot].current?.click()}
                        disabled={loading}
                        className="text-xs px-4 py-2 border-2 border-dashed border-border rounded-s text-t2 hover:border-accent/40 hover:text-t1 hover:bg-accent-s/20 transition-colors"
                      >
                        Upload resume
                      </button>
                      <input
                        ref={fileRefs[slot]}
                        type="file"
                        accept=".pdf,.docx"
                        className="hidden"
                        onChange={e => upload(slot, e.target.files[0])}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
