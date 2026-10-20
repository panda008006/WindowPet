import { useEffect, useState, type FormEvent } from 'react'
import { Check, LogIn, LogOut, Save, UserRound } from 'lucide-react'
import { authHeaders } from './creatorAuth'

export interface SocialHandles {
  douyin: string
  bilibili: string
  qq: string
}

export interface AuthUser {
  id: string
  userNumber?: number | null
  name: string
  email: string
  provider?: string
  socialHandles?: SocialHandles
}

interface CreatorAccountPanelProps {
  apiBase: string
  onAuthChange: (token: string, user: AuthUser | null) => void
}

const emptySocials: SocialHandles = { douyin: '', bilibili: '', qq: '' }

export function CreatorAccountPanel({ apiBase, onAuthChange }: CreatorAccountPanelProps) {
  const [token, setToken] = useState(() => localStorage.getItem('windowpet_auth_token') || '')
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const value = localStorage.getItem('windowpet_auth_user')
      return value ? (JSON.parse(value) as AuthUser) : null
    } catch {
      return null
    }
  })
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [emailCode, setEmailCode] = useState('')
  const [socials, setSocials] = useState<SocialHandles>(() => ({ ...emptySocials, ...(user?.socialHandles || {}) }))
  const [busy, setBusy] = useState(false)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    fetch(`${apiBase}/api/auth/me`, { headers: authHeaders(token) })
      .then(async (response) => {
        if (!response.ok) throw new Error('登录已过期，请重新登录。')
        const body = (await response.json()) as { user: AuthUser }
        setUser(body.user)
        setSocials({ ...emptySocials, ...(body.user.socialHandles || {}) })
        onAuthChange(token, body.user)
      })
      .catch(() => {
        localStorage.removeItem('windowpet_auth_token')
        localStorage.removeItem('windowpet_auth_user')
        setToken('')
        setUser(null)
        onAuthChange('', null)
      })
  }, [apiBase, onAuthChange, token])

  const finishAuth = (nextToken: string, nextUser: AuthUser) => {
    setToken(nextToken)
    setUser(nextUser)
    setSocials({ ...emptySocials, ...(nextUser.socialHandles || {}) })
    localStorage.setItem('windowpet_auth_token', nextToken)
    localStorage.setItem('windowpet_auth_user', JSON.stringify(nextUser))
    onAuthChange(nextToken, nextUser)
  }

  const submitAuth = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const payload = mode === 'login' ? { email, password } : { name, email, password, emailCode }
      const response = await fetch(`${apiBase}${endpoint}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      const body = (await response.json()) as { error?: string; token?: string; user?: AuthUser; message?: string }
      if (!response.ok || !body.token || !body.user) throw new Error(body.error || '账号操作失败。')
      finishAuth(body.token, body.user)
      setNotice(mode === 'login' ? '已登录，投稿会自动归档到你的账号。' : '注册成功，已自动登录。')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '账号操作失败。')
    } finally {
      setBusy(false)
    }
  }

  const requestCode = async () => {
    if (!email) {
      setError('请先填写邮箱。')
      return
    }
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const response = await fetch(`${apiBase}/api/auth/email-code`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, purpose: 'register' }) })
      const body = (await response.json()) as { error?: string; message?: string; devCode?: string }
      if (!response.ok) throw new Error(body.error || '验证码发送失败。')
      setNotice(body.devCode ? `开发环境验证码：${body.devCode}` : body.message || '验证码已发送，请检查邮箱。')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '验证码发送失败。')
    } finally {
      setBusy(false)
    }
  }

  const saveProfile = async () => {
    if (!token) return
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const response = await fetch(`${apiBase}/api/auth/profile`, { method: 'PATCH', headers: { ...authHeaders(token), 'Content-Type': 'application/json' }, body: JSON.stringify({ name: user?.name, socialHandles: socials }) })
      const body = (await response.json()) as { error?: string; user?: AuthUser }
      if (!response.ok || !body.user) throw new Error(body.error || '资料保存失败。')
      setUser(body.user)
      localStorage.setItem('windowpet_auth_user', JSON.stringify(body.user))
      onAuthChange(token, body.user)
      setNotice('账号资料已保存。')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '资料保存失败。')
    } finally {
      setSaving(false)
    }
  }

  const logout = async () => {
    await fetch(`${apiBase}/api/auth/logout`, { method: 'POST', headers: authHeaders(token) }).catch(() => undefined)
    localStorage.removeItem('windowpet_auth_token')
    localStorage.removeItem('windowpet_auth_user')
    setToken('')
    setUser(null)
    setSocials(emptySocials)
    onAuthChange('', null)
  }

  if (user) {
    return (
      <section className="creator-account-card is-signed-in">
        <div className="creator-account-heading"><span className="creator-account-icon"><UserRound size={17} /></span><div><strong>{user.name}</strong><small>{user.email} · 登录用户</small></div><button type="button" className="creator-logout-btn" onClick={logout}><LogOut size={14} />退出</button></div>
        <div className="creator-social-grid">
          <label>抖音号<input value={socials.douyin} onChange={(event) => setSocials((current) => ({ ...current, douyin: event.target.value }))} placeholder="可选" /></label>
          <label>B站名称/UID<input value={socials.bilibili} onChange={(event) => setSocials((current) => ({ ...current, bilibili: event.target.value }))} placeholder="可选" /></label>
          <label>QQ号<input value={socials.qq} onChange={(event) => setSocials((current) => ({ ...current, qq: event.target.value }))} placeholder="可选" /></label>
        </div>
        <button type="button" className="creator-save-profile-btn" onClick={saveProfile} disabled={saving}><Save size={14} />{saving ? '保存中…' : '保存创作者资料'}</button>
        {notice && <p className="creator-account-message is-success"><Check size={14} />{notice}</p>}
        {error && <p className="creator-account-message is-error">{error}</p>}
      </section>
    )
  }

  return (
    <section className="creator-account-card">
      <div className="creator-account-heading"><span className="creator-account-icon"><LogIn size={17} /></span><div><strong>{mode === 'login' ? '登录后管理你的投稿' : '注册创作者账号'}</strong><small>游客也可以投稿，登录后可在账号内追踪状态</small></div></div>
      <div className="creator-auth-tabs"><button type="button" className={mode === 'login' ? 'is-active' : ''} onClick={() => { setMode('login'); setError(''); setNotice('') }}>登录</button><button type="button" className={mode === 'register' ? 'is-active' : ''} onClick={() => { setMode('register'); setError(''); setNotice('') }}>注册</button><span>也可以直接作为游客投稿</span></div>
      <form className="creator-auth-form" onSubmit={submitAuth}>
        {mode === 'register' && <label>显示名称<input value={name} onChange={(event) => setName(event.target.value)} required placeholder="投稿页面显示的名字" /></label>}
        <label>邮箱<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="用于登录和接收审核通知" /></label>
        <label>密码<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={6} placeholder="至少 6 位" /></label>
        {mode === 'register' && <div className="creator-code-row"><label>邮箱验证码<input value={emailCode} onChange={(event) => setEmailCode(event.target.value)} required placeholder="填写验证码" /></label><button type="button" className="creator-code-btn" onClick={requestCode} disabled={busy}>发送验证码</button></div>}
        <button type="submit" className="creator-auth-submit" disabled={busy}><LogIn size={15} />{busy ? '处理中…' : mode === 'login' ? '登录并继续投稿' : '注册并继续投稿'}</button>
      </form>
      {notice && <p className="creator-account-message is-success"><Check size={14} />{notice}</p>}
      {error && <p className="creator-account-message is-error">{error}</p>}
    </section>
  )
}
