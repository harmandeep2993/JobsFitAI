import { useState, useEffect } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { useToast } from '../Toast.jsx'

function Section({ title, children }) {
  return (
    <div className="card p-5 space-y-4">
      <div className="text-[13.5px] font-semibold text-t1 pb-1 border-b border-border">{title}</div>
      {children}
    </div>
  )
}

function Field({ label, hint, children }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-[12.5px] font-medium text-t2">
        {label}
        {hint && <span className="font-normal text-t3 ml-1">{hint}</span>}
      </label>
      {children}
    </div>
  )
}

export default function Settings() {
  const toast = useToast()
  const [state, setState] = useState(null)
  const [llm, setLlm] = useState(null)
  const [saving, setSaving] = useState('')

  useEffect(() => {
    apiFetch('/api/match/state').then(r => r?.json()).then(d => setState(d))
    apiFetch('/api/llm-settings').then(r => r?.json()).then(d => setLlm(d))
  }, [])

  async function saveFilters(e) {
    e.preventDefault()
    setSaving('filters')
    const fd = new FormData(e.target)
    const titles   = (fd.get('titles') || '').split('\n').map(t => t.trim()).filter(Boolean)
    const location = (fd.get('location') || '').trim()
    const countries = (fd.get('countries') || '').split(',').map(c => c.trim()).filter(Boolean)
    const res = await apiFetch('/api/match/filters', {
      method: 'POST',
      body: JSON.stringify({ titles, location, countries }),
    })
    setSaving('')
    if (res?.ok) toast('Job search settings saved', 'success')
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
    else toast('Could not update scheduler', 'error')
  }

  async function saveLlm(e) {
    e.preventDefault()
    setSaving('llm')
    const fd = new FormData(e.target)
    const res = await apiFetch('/api/llm-settings', {
      method: 'POST',
      body: JSON.stringify({ provider: fd.get('provider'), model: fd.get('model') }),
    })
    setSaving('')
    if (res?.ok) toast('LLM settings saved', 'success')
    else toast('Save failed', 'error')
  }

  async function pingLlm() {
    const res = await apiFetch('/api/llm-ping')
    const d = await res?.json()
    toast(
      d?.ok ? `Connected to ${d.provider}` : 'LLM unreachable',
      d?.ok ? 'success' : 'error'
    )
  }

  const isLoading = !state && !llm

  if (isLoading) {
    return (
      <div className="space-y-5">
        <div>
          <h1 className="text-xl font-semibold text-t1">Settings</h1>
        </div>
        <div className="card p-8 text-center text-sm text-t3">Loading settings...</div>
      </div>
    )
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold text-t1">Settings</h1>
        <p className="text-sm text-t2 mt-1">Configure job search targets, scheduler, and AI provider.</p>
      </div>

      {/* Job search */}
      {state && (
        <form onSubmit={saveFilters}>
          <Section title="Job Search">
            <Field label="Job titles" hint="(one per line)">
              <textarea
                name="titles"
                defaultValue={(state.filters?.titles || []).join('\n')}
                rows={4}
                placeholder={"Software Engineer\nBackend Developer\nPython Developer"}
                className="input-base resize-none"
              />
            </Field>

            <Field label="Location">
              <input
                type="text"
                name="location"
                defaultValue={state.filters?.location || ''}
                placeholder="Berlin, Munich, Remote..."
                className="input-base"
              />
            </Field>

            <Field label="Countries" hint="(comma separated ISO codes)">
              <input
                type="text"
                name="countries"
                defaultValue={(state.filters?.countries || []).join(', ')}
                placeholder="de, at, ch"
                className="input-base"
              />
            </Field>

            <button
              type="submit"
              disabled={saving === 'filters'}
              className="btn-primary py-2 px-5 text-[13.5px]"
            >
              {saving === 'filters' ? 'Saving...' : 'Save job search settings'}
            </button>
          </Section>
        </form>
      )}

      {/* Scheduler */}
      {state && (
        <Section title="Auto Scheduler">
          <p className="text-[13px] text-t2">Automatically fetch and score new jobs in the background.</p>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={toggleScheduler}
              className={`relative w-10 h-6 rounded-full transition-colors flex-shrink-0 ${
                state.scheduler_enabled ? 'bg-accent' : 'bg-border'
              }`}
            >
              <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                state.scheduler_enabled ? 'translate-x-5' : 'translate-x-1'
              }`} />
            </button>
            <span className="text-[13px] font-medium text-t1">
              {state.scheduler_enabled ? 'Enabled' : 'Disabled'}
            </span>
            {state.scheduler_interval && (
              <span className="text-[12px] text-t3">- runs every {state.scheduler_interval} min</span>
            )}
          </div>
        </Section>
      )}

      {/* LLM */}
      {llm && (
        <form onSubmit={saveLlm}>
          <Section title="LLM Provider">
            <Field label="Provider">
              <select
                name="provider"
                defaultValue={llm.active_provider}
                className="input-base"
              >
                {llm.catalog?.map(p => (
                  <option key={p.name} value={p.name}>
                    {p.name}{!p.has_key && p.needs_key ? ' (no API key)' : ''}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Model" hint="(leave blank for default)">
              <input
                type="text"
                name="model"
                defaultValue={llm.active_model || ''}
                placeholder="e.g. gpt-4o-mini, llama3-8b-8192"
                className="input-base"
              />
            </Field>

            <div className="flex gap-2.5">
              <button
                type="submit"
                disabled={saving === 'llm'}
                className="btn-primary py-2 px-5 text-[13.5px]"
              >
                {saving === 'llm' ? 'Saving...' : 'Save LLM settings'}
              </button>
              <button
                type="button"
                onClick={pingLlm}
                className="btn-secondary py-2 px-4 text-[13.5px]"
              >
                Test connection
              </button>
            </div>
          </Section>
        </form>
      )}
    </div>
  )
}
