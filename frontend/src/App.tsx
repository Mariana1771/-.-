import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from 'react-router-dom'
import {
  fetchLesson,
  fetchLessons,
  fetchMe,
  loginRequest,
  logoutRequest,
} from './api'
import type { LessonDetail, LessonListItem, UserMe } from './api'
import './App.css'

function NavBar({
  user,
  onLoggedOut,
}: {
  user: UserMe | null
  onLoggedOut: () => void
}) {
  async function handleLogout() {
    await logoutRequest()
    onLoggedOut()
  }
  return (
    <header className="nav">
      <Link to="/" className="brand">
        Lingua (SPA)
      </Link>
      <nav>
        <Link to="/">Уроки</Link>
        <a href="/dashboard/">Класичний Django</a>
      </nav>
      <div className="nav-user">
        {user ? (
          <>
            <span>{user.username}</span>
            <button type="button" className="linkish" onClick={() => handleLogout()}>
              Вийти
            </button>
          </>
        ) : (
          <Link to="/login">Увійти</Link>
        )}
      </div>
    </header>
  )
}

function LessonsRoute() {
  const [items, setItems] = useState<LessonListItem[] | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    fetchLessons('main')
      .then(setItems)
      .catch(() => setErr('Не вдалося завантажити уроки. Перевір, що Django працює на :8000.'))
  }, [])

  if (err) return <p className="muted">{err}</p>
  if (!items) return <p className="muted">Завантаження…</p>

  return (
    <ul className="lesson-list">
      {items.map((l) => (
        <li key={l.id}>
          <Link to={`/lesson/${l.id}`}>
            [{l.level}] {l.icon} {l.title}
          </Link>
        </li>
      ))}
    </ul>
  )
}

function LessonRoute() {
  const { id } = useParams()
  const lessonId = Number(id)
  const [lesson, setLesson] = useState<LessonDetail | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!Number.isFinite(lessonId)) return
    setErr(null)
    fetchLesson(lessonId)
      .then(setLesson)
      .catch((e: Error & { status?: number }) => {
        if (e.status === 403) setErr('Доступ заборонено (Premium / сертифікація тощо).')
        else setErr('Помилка завантаження уроку.')
      })
  }, [lessonId])

  if (!Number.isFinite(lessonId)) return <Navigate to="/" replace />
  if (err) return <p className="muted">{err}</p>
  if (!lesson) return <p className="muted">Завантаження…</p>

  return (
    <article className="lesson">
      <h1>
        [{lesson.level}] {lesson.title}
      </h1>
      <div className="theory" dangerouslySetInnerHTML={{ __html: lesson.theory }} />
      <section>
        <h2>Вправи ({lesson.exercises.length})</h2>
        <p className="muted">
          Правильні відповіді з API приховані; інтерактив краще доробити окремими ендпоінтами.
        </p>
        <ul>
          {lesson.exercises.map((ex) => (
            <li key={ex.id}>
              <strong>{ex.question}</strong>
              <span className="tag">{ex.exercise_type}</span>
            </li>
          ))}
        </ul>
      </section>
      <p>
        <a href={`/grammar/${lesson.id}/`}>Відкрити цей урок у класичній версії Django</a>
      </p>
    </article>
  )
}

function LoginRoute({
  user,
  onLoggedIn,
}: {
  user: UserMe | null
  onLoggedIn: (u: UserMe) => void
}) {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (user) {
    return <Navigate to="/" replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const u = await loginRequest(username.trim(), password)
      onLoggedIn(u)
      navigate('/', { replace: true })
    } catch {
      setError('Невірний логін або пароль.')
    }
  }

  return (
    <form className="stack" onSubmit={onSubmit}>
      <label>
        Імʼя користувача
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
      </label>
      <label>
        Пароль
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
      </label>
      {error ? <p className="warn">{error}</p> : null}
      <button type="submit">Увійти</button>
    </form>
  )
}

export default function App() {
  const [user, setUser] = useState<UserMe | null | undefined>(undefined)

  useEffect(() => {
    fetchMe().then(setUser).catch(() => setUser(null))
  }, [])

  if (user === undefined) {
    return <p className="muted layout">Ініціалізація…</p>
  }

  return (
    <div className="layout">
      <NavBar user={user} onLoggedOut={() => setUser(null)} />
      <main>
        <Routes>
          <Route
            path="/"
            element={
              <>
                <h1>Уроки</h1>
                <LessonsRoute />
              </>
            }
          />
          <Route path="/lesson/:id" element={<LessonRoute />} />
          <Route
            path="/login"
            element={<LoginRoute user={user} onLoggedIn={(u) => setUser(u)} />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
