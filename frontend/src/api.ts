/** Порожній origin = браузер б’ється в той же хост що й Vite, проксі веде на Django :8000. */
const apiOrigin = (import.meta.env.VITE_API_ORIGIN as string | undefined) ?? 'https://beneficial-empathy-production-927e.up.railway.app'
function url(path: string) {
  if (path.startsWith('http')) return path
  return `${apiOrigin}${path}`
}

export async function fetchApi(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers)
  const hasBody = init.body != null && !(init.body instanceof FormData)
  if (hasBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const res = await fetch(url(path), {
    credentials: 'include',
    ...init,
    headers,
  })
  return res
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetchApi(path, init)
  if (!res.ok) {
    const text = await res.text()
    let detail: unknown = text
    try {
      detail = JSON.parse(text)
    } catch {
      /* ignore */
    }
    throw Object.assign(new Error('HTTP error'), {
      status: res.status,
      detail,
    })
  }
  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return undefined as T
  }
  const ct = res.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    return undefined as T
  }
  return (await res.json()) as T
}

export async function getCsrfToken(): Promise<string> {
  const data = await fetchJson<{ csrfToken: string }>('/api/v1/csrf/', { method: 'GET' })
  return data.csrfToken
}

export type UserMe = {
  id: number
  username: string
  email: string
  is_premium: boolean
  total_xp: number
}

export async function loginRequest(username: string, password: string): Promise<UserMe> {
  const csrfToken = await getCsrfToken()
  return fetchJson<UserMe>('/api/v1/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    headers: { 'X-CSRFToken': csrfToken },
  })
}

export async function logoutRequest(): Promise<void> {
  const csrfToken = await getCsrfToken()
  await fetchJson('/api/v1/auth/logout/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
  })
}

export async function fetchMe(): Promise<UserMe | null> {
  try {
    return await fetchJson<UserMe>('/api/v1/auth/me/', { method: 'GET' })
  } catch (e: unknown) {
    const status = (e as { status?: number })?.status
    if (status === 403 || status === 401) return null
    throw e
  }
}

export type LessonListItem = {
  id: number
  title: string
  level: string
  course_tag: string
  icon: string
  order: number
  xp_reward: number
}

export async function fetchLessons(scope: 'main' | 'all' = 'main'): Promise<LessonListItem[]> {
  const q = scope === 'main' ? '?scope=main' : '?scope=all'
  return fetchJson<LessonListItem[]>(`/api/v1/lessons/${q}`)
}

export type LessonDetail = LessonListItem & {
  theory: string
  exercises: Array<{
    id: number
    question: string
    exercise_type: string
    option_a: string
    option_b: string
    option_c: string
    order: number
  }>
}

export async function fetchLesson(id: number): Promise<LessonDetail> {
  return fetchJson<LessonDetail>(`/api/v1/lessons/${id}/`)
}
