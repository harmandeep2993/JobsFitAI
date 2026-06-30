import { useState, useEffect } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

export default function Settings() {
  const toast = useToast()
  const [state, setState] = useState(null)
  const [llm, setLlm] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    apiFetch('/api/match/state').then(r => r?.json()).then(d => setState(d))
    apiFetch('/api/llm-settings').then(r => r?.json()).then(d => setLlm(d))
  }, [])

  async function saveFilters(e) {
    e.preventDefault()
    setSaving(true)
    const fd = new FormData(e.target)
    const titles = (fd.get('titles') || '').split('\n').map(t => t.trim()).filter(Boolean)
    const location = (fd.get('location') || '').trim()
    const countries = (fd.get('countries') || '').split(',').map(c => c.trim()).filter(Boolean)
    const res = await apiFetch('/api/match/filters', {
      method: 'POST',
      body: JSON.stringify({ titles, location, countries }),
    })
    setSaving(false)
    if (res?.ok) toast('Settings saved', 'success')
    else toast('Save failed', 'error')
  }

  async function toggleScheduler() {
    if (!state) return
    const enabled = !state.scheduler_enabled
    const res = await apiFetch('/api/match/scheduler', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    })
    if (res?.ok) setState(s => ({ ...s, scheduler_enabled: enabled }))
  }

  async function saveLlm(e) {
    e.preventDefault()
    const fd = new FormData(e.target)
    const res = await apiFetch('/api/llm-settings', {
      method: 'POST',
      body: JSON.stringify({ provider: fd.get('provider'), model: fd.get('model') }),
    })
    if (res?.ok) toast('LLM settings saved', 'success')
    else toast('Save failed', 'error')
  }

  async function pingLlm() {
    const res = await apiFetch('/api/llm-ping')
    const d = await res?.json()
    toast(d?.ok ? `Connected (${d.provider})` : 'LLM unreachable', d?.ok ? 'success' : 'error')
  }

  if (!state && !llm) return <div className="text-sm text-t3">Loading...</div>

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-lg font-bold">Settings</h1>

      {/* Job search settings */}
      <form onSubmit={saveFilters} className="bg-surface border border-border rounded p-5 space-y-4">
        <div className="text-sm font-semibold">Job Search</div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-t2">Job titles (one per line)</label>
          <textarea
            name="titles"
            defaultValue={(state?.filters?.titles || []).join('\n')}
            rows={4}
            placeholder="Software Engineer&#10;Backend Developer&#10;Python Developer"
            className="w-full px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent resize-none transition-colors"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-t2">Location</label>
          <input
            type="text"
            name="location"
            defaultValue={state?.filters?.location || ''}
            placeholder="Berlin, Munich, Remote..."
            className="w-full px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-t2">Countries (comma separated)</label>
          <input
            type="text"
            name="countries"
            defaultValue={(state?.filters?.countries || []).join(', ')}
            placeholder="de, at, ch"
            className="w-full px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="px-5 py-2 bg-accent text-white rounded-s text-sm font-semibold hover:bg-accent-h disabled:opacity-60 transition-colors"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
      </form>

      {/* Scheduler */}
      <div className="bg-surface border border-border rounded p-5 space-y-3">
        <div className="text-sm font-semibold">Auto Scheduler</div>
        <p className="text-xs text-t2">Automatically fetch and score new jobs on a set interval.</p>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleScheduler}
            className={`relative w-10 h-5 rounded-full transition-colors ${
              state?.scheduler_enabled ? 'bg-accent' : 'bg-border'
            }`}
          >
            <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
              state?.scheduler_enabled ? 'translate-x-5' : 'translate-x-0.5'
            }`} />
          </button>
          <span className="text-sm text-t2">{state?.scheduler_enabled ? 'Enabled' : 'Disabled'}</span>
          {state?.scheduler_interval && (
            <span className="text-xs text-t3">every {state.scheduler_interval} min</span>
          )}
        </div>
      </div>

      {/* LLM settings */}
      {llm && (
        <form onSubmit={saveLlm} className="bg-surface border border-border rounded p-5 space-y-4">
          <div className="text-sm font-semibold">LLM Provider</div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-t2">Provider</label>
            <select
              name="provider"
              defaultValue={llm.active_provider}
              className="w-full px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 focus:outline-none focus:border-accent"
            >
              {llm.catalog?.map(p => (
                <option key={p.name} value={p.name}>
                  {p.name} {!p.has_key && p.needs_key ? '(no key)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-t2">Model</label>
            <input
              type="text"
              name="model"
              defaultValue={llm.active_model}
              placeholder="Leave blank for default"
              className="w-full px-3 py-2 bg-bg border border-border rounded-xs text-[13px] text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              className="px-5 py-2 bg-accent text-white rounded-s text-sm font-semibold hover:bg-accent-h transition-colors"
            >
              Save
            </button>
            <button
              type="button"
              onClick={pingLlm}
              className="px-4 py-2 border border-border rounded-s text-sm text-t2 hover:text-t1 hover:bg-hover transition-colors"
            >
              Test connection
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
