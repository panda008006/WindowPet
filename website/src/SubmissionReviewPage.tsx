import { useEffect, useState } from 'react'
import { ArrowLeft, Check, ExternalLink, LoaderCircle, RefreshCw, X } from 'lucide-react'
import type { SubmissionResult } from './SubmissionPage'

interface SubmissionReviewPageProps {
  onBackToHome: () => void
}

interface AdminSubmission extends SubmissionResult {
  authorEmail: string
  licenseText: string
  sourceUrl: string
  packageUrl: string
  demoUrl: string
}

const apiBase = import.meta.env.VITE_API_BASE || '/pet-api'
const adminStatusLabels: Record<SubmissionResult['status'], string> = {
  pending_review: '待审核',
  approved: '已通过并上线',
  rejected: '已拒绝',
  changes_requested: '需补充材料',
}

export function SubmissionReviewPage({ onBackToHome }: SubmissionReviewPageProps) {
  const [token, setToken] = useState('windowpet-admin-local')
  const [submissions, setSubmissions] = useState<AdminSubmission[]>([])
  const [noteById, setNoteById] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const loadSubmissions = async () => {
    if (!token.trim()) {
      setError('请输入管理员口令。')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${apiBase}/api/admin/submissions`, {
        headers: { 'X-WindowPet-Admin-Token': token.trim() },
      })
      const body = (await response.json()) as { error?: string; submissions?: AdminSubmission[] }
      if (!response.ok || !body.submissions) throw new Error(body.error || '读取投稿列表失败。')
      setSubmissions(body.submissions)
      setMessage(`✅ 成功读取 ${body.submissions.length} 条角色投稿记录。`)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '读取投稿列表失败。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSubmissions()
  }, [])

  const review = async (submission: AdminSubmission, status: SubmissionResult['status']) => {
    setBusyId(submission.id)
    setError(null)
    setMessage(null)
    try {
      const response = await fetch(`${apiBase}/api/admin/submissions/${encodeURIComponent(submission.id)}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-WindowPet-Admin-Token': token.trim() },
        body: JSON.stringify({ status, reviewNote: noteById[submission.id] || '' }),
      })
      const body = (await response.json()) as { error?: string; submission?: AdminSubmission }
      if (!response.ok || !body.submission) throw new Error(body.error || '更新审核状态失败。')
      setSubmissions((current) => current.map((item) => item.id === submission.id ? body.submission! : item))
      setMessage(`「${submission.displayName}」已标记为${adminStatusLabels[status]}。`)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '更新审核状态失败。')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="submission-page submission-review-page">
      <header className="submission-topbar">
        <button type="button" className="submission-back-btn" onClick={onBackToHome}>
          <ArrowLeft size={16} />
          <span>返回官网首页</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <a
            href="#/submit"
            className="submission-link-btn"
            title="前往创作者投稿页面"
          >
            <span>📝 角色投稿端</span>
          </a>
          <a
            href="#/gallery"
            className="submission-link-btn"
            title="小鼻嘎展馆"
          >
            <span>🐾 逛逛展馆</span>
          </a>
        </div>
      </header>
      <main className="submission-main">
        <section className="submission-hero">
          <div><p className="submission-eyebrow">ADMIN REVIEW</p><h1>角色投稿审核</h1><p>输入后台口令后查看投稿文件、演示视频和版权说明。只有标记为“已通过”的投稿会进入公开角色目录。</p></div>
        </section>
        <section className="submission-card review-console-card">
          <div className="review-console-form"><label>管理员口令<input type="password" value={token} onChange={(event) => setToken(event.target.value)} placeholder="只在本机输入，不要发给投稿者" /></label><button type="button" className="submission-submit-btn" onClick={loadSubmissions} disabled={loading}>{loading ? <LoaderCircle size={16} className="submission-spin" /> : <RefreshCw size={16} />}读取投稿</button></div>
          {error && <p className="submission-message is-error" role="alert">{error}</p>}
          {message && <p className="submission-message is-success" role="status">{message}</p>}
        </section>
        <section className="review-list" aria-live="polite">
          {!loading && submissions.length === 0 && <div className="submission-card review-empty">输入管理员口令后，这里会显示投稿队列。</div>}
          {submissions.map((submission) => (
            <article className="submission-card review-item" key={submission.id}>
              <div className="review-item-header"><div><p className="submission-card-kicker">{new Date(submission.createdAt).toLocaleString()}</p><h2>{submission.displayName} <span className={`submission-status-badge status-${submission.status}`}>{adminStatusLabels[submission.status]}</span></h2><p className="review-author">{submission.authorName} · {submission.authorEmail} · v{submission.version}</p></div><div className="review-file-links"><a href={`${apiBase}${submission.demoUrl}?adminToken=${encodeURIComponent(token)}`} target="_blank" rel="noreferrer"><ExternalLink size={14} />预览 MP4</a><a href={`${apiBase}${submission.packageUrl}?adminToken=${encodeURIComponent(token)}`}><ExternalLink size={14} />下载角色包</a></div></div>
              <p className="review-description">{submission.description}</p>
              <details className="review-license"><summary>查看版权/授权说明</summary><p>{submission.licenseText}</p>{submission.sourceUrl && <a href={submission.sourceUrl} target="_blank" rel="noreferrer">打开参考链接</a>}</details>
              <div className="review-actions"><textarea value={noteById[submission.id] || ''} onChange={(event) => setNoteById((current) => ({ ...current, [submission.id]: event.target.value }))} placeholder="审核意见（可选）" /><div className="review-action-buttons"><button type="button" className="review-action-btn is-approve" onClick={() => review(submission, 'approved')} disabled={busyId === submission.id}><Check size={15} />通过并发布</button><button type="button" className="review-action-btn is-changes" onClick={() => review(submission, 'changes_requested')} disabled={busyId === submission.id}><RefreshCw size={15} />要求补充</button><button type="button" className="review-action-btn is-reject" onClick={() => review(submission, 'rejected')} disabled={busyId === submission.id}><X size={15} />拒绝</button></div></div>
            </article>
          ))}
        </section>
      </main>
    </div>
  )
}
