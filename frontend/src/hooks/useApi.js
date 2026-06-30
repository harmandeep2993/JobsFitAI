/**
 * useApi - thin wrapper around apiFetch for data-fetching hooks.
 *
 * Returns { data, loading, error, refetch } and re-fetches whenever url changes.
 * Callers that need to trigger a manual refresh call refetch().
 */
import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../lib/auth.js'

export function useApi(url) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setData(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [url])

  useEffect(() => { refetch() }, [refetch])

  return { data, loading, error, refetch }
}
