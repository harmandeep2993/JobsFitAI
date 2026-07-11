/**
 * Settings tab - general settings: account profile, password, and
 * (admin only) the app-wide LLM provider selection.
 * Job search targets and the scheduler live in the Job Matches tab.
 */
import { useState, useEffect } from 'react'
import { apiFetch } from '../../lib/auth.js'
import { errMsg } from '../../lib/errors.js'
import { useToast } from '../Toast.jsx'
import { PageHeader, CardSection, FieldLabel, PageSpinner } from '../ui.jsx'

export default function Settings() {
  const toast = useToast()
  const [llm, setLlm] = useState(null)
  const [me, setMe] = useState(null)
  const [saving, setSaving] = useState('')

  useEffect(() => {
    apiFetch('/api/llm-settings').then(r => r?.json()).then(d => setLlm(d))
    apiFetch('/api/auth/me').then(r => r?.json()).then(d => setMe(d))
  }, [])

  async function saveLlm(e) {
    e.preventDefault()
    setSaving('llm')
    const fd = new FormData(e.target)
    const res = await apiFetch('/api/llm-settings', {
      method: 'POST',
      body: JSON.stringify({ provider: fd.get('provider'), model: fd.get('model') || '' }),
    })
    const data = await res?.json().catch(() => ({}))
    setSaving('')
    if (res?.ok && data.ok) {
      toast(data.online ? 'LLM settings saved and verified' : 'Saved, but the provider is not reachable', data.online ? 'success' : 'warn')
    } else {
      toast(errMsg(data, 'Save failed'), 'error')
    }
  }

  async function pingLlm() {
    const res = await apiFetch('/api/llm-ping')
    const d = await res?.json().catch(() => ({}))
    if (d?.online) toast(`Connected to ${d.current?.provider || 'provider'}`, 'success')
    else toast('LLM provider unreachable', 'error')
  }

  async function changePassword(e) {
    e.preventDefault()
    const fd = new FormData(e.target)
    const current_password = fd.get('current_password') || ''
    const new_password = fd.get('new_password') || ''
    if (new_password.length < 8) { toast('New password must be at least 8 characters', 'warn'); return }
    setSaving('password')
    const res = await apiFetch('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password, new_password }),
    })
    const data = await res?.json().catch(() => ({}))
    setSaving('')
    if (res?.ok && data.ok) { toast('Password changed', 'success'); e.target.reset() }
    else toast(errMsg(data, 'Could not change password'), 'error')
  }

  if (!me && !llm) return (
    <div className="space-y-5">
      <PageHeader title="Settings" description="Manage your account and app preferences." />
      <PageSpinner />
    </div>
  )

  const isAdmin = Boolean(me?.is_admin)

  return (
    <div className="space-y-5 max-w-2xl">
      <PageHeader
        title="Settings"
        description="Manage your account and app preferences. Job search targets live in the Job Matches tab."
      />

      {/* Account */}
      {me && (
        <CardSection title="Account">
          <div className="space-y-4">
            <div className="flex items-center gap-6 text-[13px]">
              <div>
                <div className="text-t3 text-[11.5px] uppercase tracking-wide font-semibold">Email</div>
                <div className="text-t1 mt-0.5">{me.email}</div>
              </div>
              <div>
                <div className="text-t3 text-[11.5px] uppercase tracking-wide font-semibold">Member since</div>
                <div className="text-t1 mt-0.5">{(me.created_at || '').slice(0, 10)}</div>
              </div>
              {isAdmin && (
                <span className="px-2 py-0.5 text-[11px] font-semibold rounded-sm self-end"
                  style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(var(--accent))' }}>
                  Admin
                </span>
              )}
            </div>

            <form onSubmit={changePassword} className="space-y-3 pt-3" style={{ borderTop: '1px solid rgba(0,0,0,0.06)' }}>
              <FieldLabel>Change password</FieldLabel>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input type="password" name="current_password" placeholder="Current password" autoComplete="current-password" required className="input-base" />
                <input type="password" name="new_password" placeholder="New password (min 8 chars)" autoComplete="new-password" required className="input-base" />
              </div>
              <button type="submit" disabled={saving === 'password'} className="btn-secondary h-8 px-4 text-[12.5px]">
                {saving === 'password' ? 'Changing...' : 'Change password'}
              </button>
            </form>
          </div>
        </CardSection>
      )}

      {/* LLM - admin only: the provider selection is app-wide */}
      {llm && isAdmin && (
        <form onSubmit={saveLlm}>
          <CardSection
            title="LLM Provider (admin)"
            action={
              <div className="flex gap-1.5">
                <button type="button" onClick={pingLlm} className="btn-secondary h-7 px-3 text-[12.5px]">Test</button>
                <button type="submit" disabled={saving === 'llm'} className="btn-primary h-7 px-3.5 text-[12.5px]">
                  {saving === 'llm' ? 'Saving...' : 'Save'}
                </button>
              </div>
            }
          >
            <p className="text-[12.5px] text-t3 mb-4">This setting applies to all users of the app.</p>
            <div className="space-y-4">
              <div>
                <FieldLabel>Provider</FieldLabel>
                <select name="provider" defaultValue={llm.current?.provider} className="input-base">
                  {llm.providers?.map(p => (
                    <option key={p.name} value={p.name}>
                      {p.name}{!p.has_key && p.needs_key ? ' (no API key)' : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <FieldLabel hint="(leave blank for default)">Model</FieldLabel>
                <input type="text" name="model" defaultValue={llm.current?.model || ''} placeholder="e.g. gpt-4o-mini, llama3-8b-8192" className="input-base" />
              </div>
            </div>
          </CardSection>
        </form>
      )}
    </div>
  )
}
