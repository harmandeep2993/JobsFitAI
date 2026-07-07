const TOKEN_KEY = 'jfai_token'

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getUser() {
  const token = getToken()
  if (!token) return null
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export function isAuthed() {
  return Boolean(getToken())
}

export async function apiFetch(url, options = {}) {
  const token = getToken()
  const headers = { ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(url, { ...options, headers })
  if (res.status === 401) {
    // Expired or invalidated session - clear it and send the user back to
    // login instead of letting every tab surface its own opaque error.
    clearToken()
    window.location.href = '/login'
    return res
  }
  return res
}

export function logout() {
  clearToken()
  window.location.href = '/'
}
