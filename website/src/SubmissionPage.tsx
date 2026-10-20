import { useMemo, useState, type ChangeEvent, type FormEvent } from 'react'
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  Clipboard,
  FileVideo,
  FolderOpen,
  Plus,
  QrCode,
  RefreshCw,
  Send,
  Sparkles,
  Trash2,
  Upload,
} from 'lucide-react'
import './submission.css'
import { authHeaders } from './creatorAuth'

interface SubmissionPageProps {
  onBackToHome: () => void
  onOpenGallery?: () => void
}

export interface SubmissionResult {
  id: string
  status: 'pending_review' | 'approved' | 'rejected' | 'changes_requested'
  displayName: string
  authorName: string
  description: string
  version: string
  sourceUrl: string
  packageOriginalName: string
  packageSizeBytes: number
  demoOriginalName: string
  demoSizeBytes: number
  packageDownloadUrl: string | null
  demoUrl: string
  reviewNote: string
  createdAt: string
  updatedAt: string
  publishedAt: string | null
}

interface ActionUploadRow {
  id: string
  label: string
  description: string
  required: boolean
  accept: string
  file: File | null
  files?: File[]
  isCustom?: boolean
}

const initialActionRows: ActionUploadRow[] = [
  { id: 'static', label: '原始静态封面', description: '展馆卡片与桌面静默封面图', required: true, accept: 'image/png,image/jpeg,image/webp', file: null },
  { id: 'idle', label: '待机动作', description: '日常桌面呼吸循环动画', required: true, accept: 'video/*,image/*', file: null },
  { id: 'click', label: '单击互动', description: '鼠标轻点播放一次', required: true, accept: 'video/*,image/*', file: null },
  { id: 'drag', label: '拖拽动作', description: '抓起悬空提起时循环播放', required: true, accept: 'video/*,image/*', file: null },
  { id: 'thinking', label: '思考动作', description: 'AI 思考时触发 (可选)', required: false, accept: 'video/*,image/*', file: null, isCustom: true },
  { id: 'answer', label: '回答动作', description: 'AI 回复时触发 (可选)', required: false, accept: 'video/*,image/*', file: null, isCustom: true },
]

interface StoredSubmission {
  submission: SubmissionResult
  trackingToken: string
}

const apiBase = import.meta.env.VITE_API_BASE || '/pet-api'

const statusLabels: Record<SubmissionResult['status'], string> = {
  pending_review: '等待人工审核',
  approved: '审核通过，已入驻展馆',
  rejected: '审核未通过',
  changes_requested: '需要补充材料',
}

const statusDescriptions: Record<SubmissionResult['status'], string> = {
  pending_review: '官方将检查角色包结构、动作纯净度与演示动画。审核完成后，状态将自动在此更新。',
  approved: '角色已成功发布至小鼻嘎展馆，全网用户可直接一键导入到 WindowPet 桌面端！',
  rejected: '审核记录已保留，请参考下方审核意见修改后重新提交。',
  changes_requested: '请根据下方审核意见补充完善素材，重新提交后即可加速复核。',
}

function formatBytes(value: number) {
  if (!value) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`
}

const defaultDemoSubmission: StoredSubmission = {
  submission: {
    id: 'submission-xbg-2026-demo',
    displayName: '草莓奶酪喵',
    authorName: 'WindowPet 官方创作者',
    status: 'pending_review',
    description: '超甜粉嫩治愈系元气猫猫！不仅拥有轻快自然的待机呼吸，摸摸头还会害羞捂脸。',
    version: '2.0.0',
    sourceUrl: '',
    packageOriginalName: 'caomei-cat.wpet',
    packageSizeBytes: 4892014,
    demoOriginalName: 'caomei-cat-demo.mp4',
    demoSizeBytes: 2450120,
    packageDownloadUrl: null,
    demoUrl: '',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    publishedAt: null,
    reviewNote: '素材格式规范，透明背景检验通过，已进入首批推荐位排期复核。',
  },
  trackingToken: 'wp_token_demo_9876543210',
}

function readStoredSubmission(): StoredSubmission | null {
  try {
    const raw = localStorage.getItem('windowpet_last_submission')
    if (raw) return JSON.parse(raw) as StoredSubmission
    return defaultDemoSubmission
  } catch {
    return defaultDemoSubmission
  }
}

function safeFileName(value: string, fallback: string) {
  const normalized = value.normalize('NFKC').replace(/[^a-zA-Z0-9._-]+/g, '-').replace(/^-+|-+$/g, '')
  return normalized || fallback
}

function crc32(data: Uint8Array) {
  let crc = 0xffffffff
  for (const byte of data) {
    crc ^= byte
    for (let bit = 0; bit < 8; bit += 1) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0)
  }
  return (crc ^ 0xffffffff) >>> 0
}

function writeU16(view: DataView, offset: number, value: number) { view.setUint16(offset, value, true) }
function writeU32(view: DataView, offset: number, value: number) { view.setUint32(offset, value >>> 0, true) }

async function createStoredZip(entries: Array<{ name: string; data: Blob | string }>) {
  const encoder = new TextEncoder()
  const locals: Uint8Array[] = []
  const centrals: Uint8Array[] = []
  let offset = 0
  for (const entry of entries) {
    const name = encoder.encode(entry.name)
    const data = typeof entry.data === 'string' ? encoder.encode(entry.data) : new Uint8Array(await entry.data.arrayBuffer())
    const checksum = crc32(data)
    const local = new Uint8Array(30 + name.length + data.length)
    const localView = new DataView(local.buffer)
    writeU32(localView, 0, 0x04034b50); writeU16(localView, 4, 20); writeU16(localView, 6, 0x800); writeU16(localView, 8, 0)
    writeU16(localView, 10, 0); writeU16(localView, 12, 0); writeU32(localView, 14, checksum); writeU32(localView, 18, data.length); writeU32(localView, 22, data.length)
    writeU16(localView, 26, name.length); writeU16(localView, 28, 0); local.set(name, 30); local.set(data, 30 + name.length)
    locals.push(local)
    const central = new Uint8Array(46 + name.length)
    const centralView = new DataView(central.buffer)
    writeU32(centralView, 0, 0x02014b50); writeU16(centralView, 4, 20); writeU16(centralView, 6, 20); writeU16(centralView, 8, 0x800); writeU16(centralView, 10, 0)
    writeU16(centralView, 12, 0); writeU16(centralView, 14, 0); writeU32(centralView, 16, checksum); writeU32(centralView, 20, data.length); writeU32(centralView, 24, data.length)
    writeU16(centralView, 28, name.length); writeU16(centralView, 30, 0); writeU16(centralView, 32, 0); writeU16(centralView, 34, 0); writeU16(centralView, 36, 0); writeU32(centralView, 38, 0); writeU32(centralView, 42, offset)
    central.set(name, 46); centrals.push(central); offset += local.length
  }
  const centralOffset = offset
  const centralSize = centrals.reduce((sum, item) => sum + item.length, 0)
  const end = new Uint8Array(22)
  const endView = new DataView(end.buffer)
  writeU32(endView, 0, 0x06054b50); writeU16(endView, 4, 0); writeU16(endView, 6, 0); writeU16(endView, 8, entries.length); writeU16(endView, 10, entries.length)
  writeU32(endView, 12, centralSize); writeU32(endView, 16, centralOffset); writeU16(endView, 20, 0)
  const parts = [...locals, ...centrals, end]
  const merged = new Uint8Array(parts.reduce((sum, part) => sum + part.length, 0))
  let cursor = 0
  for (const part of parts) { merged.set(part, cursor); cursor += part.length }
  return new Blob([merged.buffer], { type: 'application/zip' })
}

async function buildCharacterPackage(
  displayName: string,
  authorName: string,
  authorEmail: string,
  rows: ActionUploadRow[],
  rewardQrCode: File | null
) {
  const slug = safeFileName(displayName, 'windowpet-character')
  const root = `${slug}Pet`
  const entries: Array<{ name: string; data: Blob | string }> = []
  const manifest: Record<string, unknown> = {
    format_version: 2,
    type: 'creator_package',
    name: displayName,
    author: authorName,
    author_email: authorEmail,
    character_id: root,
    preview: 'preview.png',
    static: 'static.png',
    animations: {},
    triggers: { 'left-click': 'click', 'left-drag': 'drag' },
  }
  const animations = manifest.animations as Record<string, unknown>
  const triggers = manifest.triggers as Record<string, string>

  for (const row of rows) {
    const rowFiles = row.files?.length ? row.files : row.file ? [row.file] : []
    if (!rowFiles.length) continue
    const file = rowFiles[0]
    const extension = file.name.split('.').pop()?.toLowerCase() || 'bin'
    const filename = safeFileName(file.name, `${row.id}.${extension}`)

    if (row.id === 'static') {
      entries.push({ name: `${root}/preview.png`, data: file })
      entries.push({ name: `${root}/static.png`, data: file })
      continue
    }

    const actionKey = row.id === 'thinking' ? 'habit1' : row.id === 'answer' ? 'habit2' : row.id
    const relative = `${actionKey}/${filename}`

    if (rowFiles.length === 1) {
      entries.push({ name: `${root}/${relative}`, data: file })
      animations[actionKey] = { video: relative, loop: actionKey === 'idle' || actionKey === 'drag', label: row.label }
    } else {
      const frames: string[] = []
      rowFiles.forEach((frame, index) => {
        const frameName = `${actionKey}/frame-${String(index + 1).padStart(3, '0')}-${safeFileName(frame.name, `frame-${index + 1}.${extension}`)}`
        entries.push({ name: `${root}/${frameName}`, data: frame })
        frames.push(frameName)
      })
      animations[actionKey] = { frames, loop: actionKey === 'idle' || actionKey === 'drag', label: row.label }
    }

    if (row.id === 'thinking') {
      animations.thinking = { video: relative, loop: false, label: row.label }
      triggers['deepseek-thinking'] = 'thinking'
    }
    if (row.id === 'answer') {
      animations.result = { video: relative, loop: false, label: row.label }
      triggers['ai-result'] = 'result'
    }
  }

  // 创作者收款码 (若已上传，打包到角色根目录并写入 asset.json)
  if (rewardQrCode) {
    const qrExt = rewardQrCode.name.split('.').pop()?.toLowerCase() || 'png'
    const qrName = `reward_qrcode.${qrExt}`
    entries.push({ name: `${root}/${qrName}`, data: rewardQrCode })
    manifest.reward_qrcode = qrName
  }

  entries.push({ name: `${root}/asset.json`, data: JSON.stringify(manifest, null, 2) })
  return { blob: await createStoredZip(entries), fileName: `${slug}.wpet` }
}

/**
 * 递归读取拖拽文件夹中的所有文件
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function readAllEntriesRecursively(entry: any): Promise<File[]> {
  if (!entry) return []
  if (entry.isFile) {
    return new Promise((resolve) => {
      entry.file((file: File) => resolve([file]), () => resolve([]))
    })
  } else if (entry.isDirectory) {
    const reader = entry.createReader()
    const allFiles: File[] = []
    const readEntries = (): Promise<void> => {
      return new Promise((resolve) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        reader.readEntries(async (batch: any[]) => {
          if (!batch || batch.length === 0) {
            resolve()
          } else {
            for (const child of batch) {
              const childFiles = await readAllEntriesRecursively(child)
              allFiles.push(...childFiles)
            }
            await readEntries()
            resolve()
          }
        }, () => resolve())
      })
    }
    await readEntries()
    return allFiles
  }
  return []
}

export function SubmissionPage({ onBackToHome, onOpenGallery }: SubmissionPageProps) {
  // 1. 角色基本资料
  const [displayName, setDisplayName] = useState('')
  const [authorName, setAuthorName] = useState('')
  const [authorEmail, setAuthorEmail] = useState('')
  const [description, setDescription] = useState('')
  const [qqGroup, setQqGroup] = useState('')
  const [bilibiliId, setBilibiliId] = useState('')
  const [douyinId, setDouyinId] = useState('')

  // 创作者收款码
  const [rewardQrCode, setRewardQrCode] = useState<File | null>(null)
  const [rewardQrPreview, setRewardQrPreview] = useState<string | null>(null)

  // 2. 动作素材与演示
  const [actionRows, setActionRows] = useState<ActionUploadRow[]>(initialActionRows)
  const [demoVideo, setDemoVideo] = useState<File | null>(null)
  const [dragOverRowId, setDragOverRowId] = useState<string | null>(null)

  // 3. 提交与确认
  const [licenseAccepted, setLicenseAccepted] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [stored, setStored] = useState<StoredSubmission | null>(() => readStoredSubmission())

  const authToken = useMemo(() => localStorage.getItem('windowpet_auth_token') || '', [])

  const demoHint = useMemo(() => {
    if (!demoVideo) return '支持 .mp4，建议 5~30 秒（最大 100 MB）'
    return `${demoVideo.name} · ${formatBytes(demoVideo.size)}`
  }, [demoVideo])

  // 收款码选择处理
  const handleQrCodeChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!/\.(png|jpe?g|webp)$/i.test(file.name)) {
      setError('收款码请上传 PNG / JPG / WebP 图片格式。')
      return
    }
    setRewardQrCode(file)
    setRewardQrPreview(URL.createObjectURL(file))
    setError(null)
  }

  const removeQrCode = () => {
    setRewardQrCode(null)
    if (rewardQrPreview) URL.revokeObjectURL(rewardQrPreview)
    setRewardQrPreview(null)
  }

  const fillDemoData = () => {
    setDisplayName('草莓奶酪喵')
    setAuthorName('WindowPet画师团队')
    setAuthorEmail('creator-support@windowpet.cn')
    setDescription('超甜粉嫩治愈系元气猫猫！不仅拥有轻快自然的待机呼吸，摸摸头还会害羞捂脸，更深度适配了 AI 思考发呆与开心回答的专属桌面互动。')
    setQqGroup('536254840')
    setBilibiliId('WindowPet官方')
    setDouyinId('WindowPet2026')
    setNotice('✨ 已为您自动填入完整的角色资料！您可以直接查看各字段排布。')
  }

  const showDemoStep3 = () => {
    setStored(defaultDemoSubmission)
    localStorage.setItem('windowpet_last_submission', JSON.stringify(defaultDemoSubmission))
    setNotice('🎉 已为您展示【第③步：审核发布】实况页面！')
  }

  // 动态增删动作槽位（最多支持 10 个动作）
  const addExtraAction = () => {
    if (actionRows.length >= 10) return
    const customIdx = actionRows.length - 3 // 自定义动作编号
    setActionRows((current) => [
      ...current,
      {
        id: `action-${Date.now()}`,
        label: `动作 ${customIdx}`,
        description: '可选单视频或纯 PNG 序列帧文件夹',
        required: false,
        accept: 'video/*,image/*',
        file: null,
        files: [],
        isCustom: true,
      },
    ])
  }

  const removeActionRow = (id: string) => {
    setActionRows((current) => current.filter((row) => row.id !== id))
  }

  const updateActionLabel = (id: string, newLabel: string) => {
    setActionRows((current) =>
      current.map((row) => (row.id === id ? { ...row, label: newLabel } : row)),
    )
  }

  const updateActionFiles = (id: string, files: File[]) => {
    setActionRows((current) =>
      current.map((row) => (row.id === id ? { ...row, file: files[0] || null, files } : row)),
    )
  }

  // 严格的拖拽文件与文件夹校验逻辑
  const handleDropToSlot = async (e: React.DragEvent, row: ActionUploadRow) => {
    e.preventDefault()
    e.stopPropagation()
    setDragOverRowId(null)
    setError(null)

    const items = e.dataTransfer.items
    if (!items || items.length === 0) return

    const collectedFiles: File[] = []
    let isDirectoryDrop = false
    let folderName = ''

    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (typeof item.webkitGetAsEntry === 'function') {
        const entry = item.webkitGetAsEntry()
        if (entry) {
          if (entry.isDirectory) {
            isDirectoryDrop = true
            folderName = entry.name
            const dirFiles = await readAllEntriesRecursively(entry)
            collectedFiles.push(...dirFiles)
          } else if (entry.isFile) {
            const file = item.getAsFile()
            if (file) collectedFiles.push(file)
          }
        }
      } else {
        const file = item.getAsFile()
        if (file) collectedFiles.push(file)
      }
    }

    // 过滤系统隐藏与无用杂项文件 (.DS_Store / Thumbs.db)
    const cleanFiles = collectedFiles.filter(
      (f) => !f.name.startsWith('.') && f.name !== 'Thumbs.db' && !f.name.includes('__MACOSX')
    )

    if (cleanFiles.length === 0) {
      setError('未检测到有效的文件或文件夹为空。')
      return
    }

    if (row.id === 'static') {
      // 静态封面必须为单张图片
      const file = cleanFiles[0]
      if (!/\.(png|jpe?g|webp)$/i.test(file.name)) {
        setError(`❌ 静态封面必须为单张图片（PNG / JPG / WebP），检测到不符文件：${file.name}`)
        return
      }
      updateActionFiles(row.id, [file])
      setNotice(`✅ 封面图已加载：${file.name}`)
      return
    }

    // 动作素材：可能是单文件，也可能是整个文件夹
    if (isDirectoryDrop || cleanFiles.length > 1) {
      // 文件夹模式：必须 100% 全部为纯 PNG 序列帧，严禁混入杂质防止客户端崩溃！
      const nonPng = cleanFiles.find((f) => !/\.png$/i.test(f.name))
      if (nonPng) {
        setError(
          `❌ 文件夹【${folderName || '序列帧'}】内检测到非法文件：【${nonPng.name}】！为保证 WindowPet 桌面端稳定运行不崩溃，文件夹内必须 100% 全部为纯 PNG 序列帧！`
        )
        return
      }
      // 自然数字排序 (frame-1, frame-2, frame-10)
      cleanFiles.sort((a, b) =>
        a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' })
      )
      updateActionFiles(row.id, cleanFiles)
      setNotice(`✅ 文件夹【${folderName || '序列帧'}】校验通过！已载入 ${cleanFiles.length} 帧纯 PNG 序列。`)
    } else {
      // 单文件模式：允许 .mov / .mp4 / .webp
      const file = cleanFiles[0]
      if (!/\.(mov|mp4|webp)$/i.test(file.name)) {
        setError(
          `❌ 动作单文件仅支持 MOV / MP4 / WebP 格式；若使用图片序列，请将全部 PNG 文件放入同一个文件夹拖入。`
        )
        return
      }
      updateActionFiles(row.id, [file])
      setNotice(`✅ 动作素材已载入：${file.name}`)
    }
  }

  // 点击选择文件输入框校验
  const handleFileInputChange = (row: ActionUploadRow, files: File[]) => {
    setError(null)
    if (!files.length) return

    if (row.id === 'static') {
      const file = files[0]
      if (!/\.(png|jpe?g|webp)$/i.test(file.name)) {
        setError('静态封面只支持 PNG / JPG / WebP 格式。')
        return
      }
      updateActionFiles(row.id, [file])
      return
    }

    if (files.length > 1) {
      // 多文件/文件夹选择：严格纯 PNG 校验
      const nonPng = files.find((f) => !/\.png$/i.test(f.name))
      if (nonPng) {
        setError(
          `❌ 所选文件中包含非法文件：【${nonPng.name}】！序列帧必须全部为纯 PNG 文件，请剔除杂项后重新选择。`
        )
        return
      }
      files.sort((a, b) =>
        a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' })
      )
      updateActionFiles(row.id, files)
    } else {
      const file = files[0]
      if (!/\.(mov|mp4|webp)$/i.test(file.name)) {
        setError('动作单文件请上传 MOV / MP4 / WebP 视频动画。')
        return
      }
      updateActionFiles(row.id, [file])
    }
  }

  const handleDemoVideoChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null
    if (file && !/\.mp4$/i.test(file.name)) {
      setError('演示动画须为 MP4 格式。')
      return
    }
    setDemoVideo(file)
    setError(null)
  }

  // 刷新状态
  const refreshStatus = async () => {
    if (!stored) return
    setRefreshing(true)
    setError(null)
    try {
      const res = await fetch(
        `${apiBase}/api/submissions/${encodeURIComponent(stored.submission.id)}?token=${encodeURIComponent(
          stored.trackingToken
        )}`
      )
      const body = (await res.json()) as { error?: string; submission?: SubmissionResult }
      if (!res.ok || !body.submission) throw new Error(body.error || '查询状态失败。')
      const next = { submission: body.submission, trackingToken: stored.trackingToken }
      setStored(next)
      localStorage.setItem('windowpet_last_submission', JSON.stringify(next))
      setNotice('审核状态已刷新。')
    } catch (err) {
      setError(err instanceof Error ? err.message : '查询状态失败。')
    } finally {
      setRefreshing(false)
    }
  }

  // 提交总逻辑
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setNotice(null)
    setError(null)

    if (!displayName.trim()) {
      setError('请填写角色名称。')
      setSubmitting(false)
      return
    }
    if (!authorName.trim()) {
      setError('请填写创作者昵称。')
      setSubmitting(false)
      return
    }
    if (!authorEmail.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(authorEmail.trim())) {
      setError('请填写有效的创作者联系邮箱（如需撤销角色申请，后期需以此邮箱验证身份）。')
      setSubmitting(false)
      return
    }
    if (!description.trim() || description.trim().length < 5) {
      setError('请填写角色简介与玩法亮点（至少 5 个字）。')
      setSubmitting(false)
      return
    }

    const missingRequired = actionRows.filter((r) => r.required && !r.file && (!r.files || r.files.length === 0))
    if (missingRequired.length > 0) {
      setError(`请上传必填动作：${missingRequired.map((r) => r.label).join('、')}。`)
      setSubmitting(false)
      return
    }

    if (!demoVideo) {
      setError('请上传角色在桌面的实际演示 MP4 视频。')
      setSubmitting(false)
      return
    }

    try {
      // 客户端自动打包封装为 .wpet 结构
      const generatedPackage = await buildCharacterPackage(displayName, authorName, authorEmail, actionRows, rewardQrCode)

      const formData = new FormData()
      formData.set('displayName', displayName.trim())
      formData.set('authorName', authorName.trim())
      formData.set('authorEmail', authorEmail.trim())
      formData.set('version', '2.0.0')
      formData.set('description', description.trim())
      formData.set('licenseAccepted', String(licenseAccepted))
      formData.set('qq', qqGroup.trim())
      formData.set('bilibili', bilibiliId.trim())
      formData.set('douyin', douyinId.trim())
      formData.set('packageFile', generatedPackage.blob, generatedPackage.fileName)
      formData.set('demoVideo', demoVideo)
      if (rewardQrCode) {
        formData.set('rewardQrCode', rewardQrCode)
      }

      const res = await fetch(`${apiBase}/api/submissions`, {
        method: 'POST',
        headers: authHeaders(authToken),
        body: formData,
      })
      const body = (await res.json()) as {
        error?: string
        message?: string
        submission?: SubmissionResult
        trackingToken?: string
      }

      if (!res.ok || !body.submission || !body.trackingToken) {
        throw new Error(body.error || '投稿提交失败，请稍后再试。')
      }

      const next = { submission: body.submission, trackingToken: body.trackingToken }
      setStored(next)
      localStorage.setItem('windowpet_last_submission', JSON.stringify(next))
      setNotice('🎉 恭喜！角色投稿已成功提交，进入官方审核发布队列。')
      setDemoVideo(null)
      setAuthorEmail('')
      removeQrCode()
      setActionRows(initialActionRows)
    } catch (err) {
      setError(err instanceof Error ? err.message : '投稿提交失败，请检查网络或稍后再试。')
    } finally {
      setSubmitting(false)
    }
  }

  const copyTrackingToken = async () => {
    if (!stored) return
    try {
      await navigator.clipboard.writeText(`${stored.submission.id}\n${stored.trackingToken}`)
      setNotice('投稿编号与查询凭证已复制到剪贴板。')
    } catch {
      setNotice('请手动保存页面中的投稿编号。')
    }
  }

  return (
    <div className="submission-page">
      {/* 顶部极简导航 */}
      <header className="submission-topbar">
        <button type="button" className="submission-back-btn" onClick={onBackToHome}>
          <ArrowLeft size={16} />
          <span>返回官网首页</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onOpenGallery && (
            <button type="button" className="submission-link-btn" onClick={onOpenGallery}>
              <span>🐾 逛逛小鼻嘎展馆</span>
            </button>
          )}
          <a
            href="#/review"
            className="submission-link-btn"
            style={{ borderColor: 'rgba(255, 107, 129, 0.4)', color: '#d94858' }}
            title="平台管理与审核后台"
          >
            <span>🛡️ 审核管理端</span>
          </a>
        </div>
      </header>

      <main className="submission-main">
        {/* 顶部标题与三步流程 */}
        <section className="submission-hero">
          <div className="submission-eyebrow">
            <Sparkles size={14} />
            <span>WINDOWPET CREATOR STUDIO</span>
          </div>
          <h1>WindowPet 原创角色投稿</h1>
          <p>
            免注册免登录，从上到下填写角色资料并上传动作素材。支持拖入单个视频文件或全 PNG 序列帧文件夹，自动打包并快速入驻小鼻嘎展馆！
          </p>

          <div className="submission-three-steps" aria-label="投稿流程">
            <span className={`step-item ${stored ? 'is-done' : 'is-active'}`}>
              <span>{stored ? '✓ ① 填写投稿' : '① 填写投稿'}</span>
            </span>
            <span className="step-divider">➔</span>
            <span className={`step-item ${stored ? 'is-done' : 'is-active'}`}>
              <span>{stored ? '✓ ② 格式检验' : '② 格式检验'}</span>
            </span>
            <span className="step-divider">➔</span>
            <span className={`step-item ${stored ? 'is-active is-highlight' : ''}`}>
              <span>③ 审核发布</span>
            </span>
          </div>
        </section>

        {/* 如果已有投稿记录，重点展示【第③步：审核与发布实况卡片】 */}
        {stored && (
          <section className="submission-card-box submission-status-card">
            <div className="status-success-banner">
              <div className="status-success-icon">
                <CheckCircle2 size={28} />
              </div>
              <div>
                <h3 className="status-success-title">🎉 角色投稿已成功提交，进入官方审核发布队列！</h3>
                <p className="status-success-desc">
                  已完成格式检验与客户端防崩测试，正在等待官方人工复核。复核通过后将直接收录上线「小鼻嘎展馆」！
                </p>
              </div>
            </div>

            <div className="submission-status-heading">
              <div>
                <span className="submission-eyebrow" style={{ margin: '0 0 6px' }}>
                  STEP 3 · 审核与发布跟踪
                </span>
                <h2>{stored.submission.displayName}</h2>
              </div>
              <span className={`submission-status-badge status-${stored.submission.status}`}>
                ● {statusLabels[stored.submission.status]}
              </span>
            </div>

            <p style={{ margin: '12px 0 0', color: 'var(--sub-text-body)', fontSize: '13.5px', lineHeight: 1.65 }}>
              {statusDescriptions[stored.submission.status]}
            </p>

            <div className="submission-status-meta">
              <span>投稿存证 ID：<code>{stored.submission.id}</code></span>
              <span>创作者：<strong>{stored.submission.authorName}</strong></span>
              <span>提交时间：{new Date(stored.submission.createdAt).toLocaleString()}</span>
              <span>
                自动封装包：{stored.submission.packageOriginalName}（{formatBytes(stored.submission.packageSizeBytes)}）
              </span>
            </div>

            {stored.submission.reviewNote && (
              <div className="submission-review-feedback">
                <strong>💡 官方反馈说明：</strong>
                <span>{stored.submission.reviewNote}</span>
              </div>
            )}

            <div className="submission-status-actions">
              <button
                type="button"
                className="submission-secondary-btn"
                onClick={refreshStatus}
                disabled={refreshing}
              >
                <RefreshCw size={14} className={refreshing ? 'submission-spin' : ''} />
                <span>刷新审核进度</span>
              </button>
              <button type="button" className="submission-secondary-btn" onClick={copyTrackingToken}>
                <Clipboard size={14} />
                <span>复制凭证编号</span>
              </button>
              {stored.submission.packageDownloadUrl ? (
                <a
                  className="submission-download-btn"
                  href={`${apiBase}${stored.submission.packageDownloadUrl}`}
                  download
                >
                  <CheckCircle2 size={14} />
                  <span>下载已封装 .wpet</span>
                </a>
              ) : (
                <span className="submission-download-btn is-disabled" title="审核员通过后即可在此直接下载生成的 .wpet 角色包">
                  <CheckCircle2 size={14} />
                  <span>审核通过后开放下载</span>
                </span>
              )}
              <button
                type="button"
                className="submission-secondary-btn"
                onClick={() => {
                  setStored(null)
                  localStorage.removeItem('windowpet_last_submission')
                }}
                style={{ marginLeft: 'auto' }}
              >
                <span>➕ 投稿另一个新角色</span>
              </button>
            </div>
          </section>
        )}

        {/* 顶部示范填充快捷操作区 */}
        {!stored && (
          <div className="form-demo-actions">
            <button type="button" className="demo-fill-btn" onClick={fillDemoData}>
              <Sparkles size={14} />
              <span>⚡ 一键填入示范资料</span>
            </button>
            <button type="button" className="demo-preview-btn" onClick={showDemoStep3}>
              <CheckCircle2 size={14} />
              <span>👀 直接预览【第③步：审核完成态】</span>
            </button>
          </div>
        )}

        {/* =================================================================
            纵向单列表单流 (Vertical Single-Column Stream)
            ================================================================= */}
        <form className="submission-form-stream" onSubmit={handleSubmit}>
          {/* 卡片一：① 填写投稿 (角色档案与创作者信息) */}
          <section className="submission-card-box">
            <div className="card-title-row">
              <span className="card-num-badge">1</span>
              <div>
                <h3>角色档案与创作者信息</h3>
                <p>填写角色的基本称谓、创作灵感与打赏收款方式</p>
              </div>
            </div>

            <div className="form-vertical-stream">
              <div className="form-item">
                <label>
                  角色名称 <span className="required-star">*</span>
                </label>
                <input
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  minLength={2}
                  maxLength={80}
                  required
                  placeholder="给你的角色起个名字，例如：自嘲熊、小黄鸡、小橘猫"
                />
              </div>

              <div className="form-item">
                <label>
                  创作者昵称 <span className="required-star">*</span>
                </label>
                <input
                  value={authorName}
                  onChange={(e) => setAuthorName(e.target.value)}
                  maxLength={80}
                  required
                  placeholder="展示在展馆图鉴与桌面卡片上的作者署名"
                />
              </div>

              <div className="form-item">
                <label>
                  创作者联系邮箱 <span className="required-star">*</span>
                </label>
                <input
                  type="email"
                  value={authorEmail}
                  onChange={(e) => setAuthorEmail(e.target.value)}
                  maxLength={120}
                  required
                  placeholder="例如: your-email@qq.com"
                />
                <div className="form-item-note">
                  💡 如需撤销角色申请，后期需输入正确邮箱地址，请谨慎记住。
                </div>
              </div>

              <div className="form-item">
                <label>
                  角色简介与动作亮点 <span className="required-star">*</span>
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  minLength={5}
                  maxLength={2000}
                  required
                  placeholder="介绍角色的性格特点、桌面动作设计亮点或互动小技巧..."
                />
              </div>

              {/* 创作者社交主页（可选） */}
              <div className="form-item">
                <label>创作者社交主页 (选填，方便粉丝关注与交流)</label>
                <div className="social-three-row">
                  <input
                    value={qqGroup}
                    onChange={(e) => setQqGroup(e.target.value)}
                    placeholder="QQ号 / 交流群号"
                  />
                  <input
                    value={bilibiliId}
                    onChange={(e) => setBilibiliId(e.target.value)}
                    placeholder="B站 UID / 空间主页"
                  />
                  <input
                    value={douyinId}
                    onChange={(e) => setDouyinId(e.target.value)}
                    placeholder="抖音号 / 小红书号"
                  />
                </div>
              </div>

              {/* 创作者收款码上传专区 (选填) */}
              <div className="form-item">
                <label>
                  <QrCode size={15} color="#e85f6d" />
                  <span>创作者收款码 (选填，鼓励打赏激励创作)</span>
                </label>
                <div className="reward-qr-box">
                  <div className="reward-qr-left">
                    {rewardQrPreview ? (
                      <img src={rewardQrPreview} alt="收款码预览" className="reward-qr-preview-thumb" />
                    ) : (
                      <div className="reward-qr-icon">
                        <QrCode size={22} />
                      </div>
                    )}
                    <div className="reward-qr-info">
                      <strong>
                        {rewardQrCode ? `已上传：${rewardQrCode.name}` : '上传微信 / 支付宝赞赏码'}
                      </strong>
                      <small>
                        用户在桌面端或小鼻嘎展馆点击「投喂」时可直接扫码向您赞赏，收益 100% 归作者！
                      </small>
                    </div>
                  </div>

                  <div className="reward-qr-actions">
                    {rewardQrCode ? (
                      <button type="button" className="slot-delete-btn" onClick={removeQrCode} title="移除收款码">
                        <Trash2 size={16} />
                      </button>
                    ) : (
                      <label className="upload-pill-btn">
                        <Upload size={14} />
                        <span>选择图片</span>
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          onChange={handleQrCodeChange}
                        />
                      </label>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 卡片二：② 格式检验 (动作素材与演示视频) */}
          <section className="submission-card-box">
            <div className="card-title-row">
              <span className="card-num-badge">2</span>
              <div>
                <h3>动作素材与演示视频</h3>
                <p>支持直接拖入文件或文件夹，内置严格格式纯净度校验</p>
              </div>
            </div>

            <div className="format-notice-tip">
              💡 <strong>素材格式指南</strong>：支持单个 <code>.mov</code> / <code>.mp4</code> / <code>.webp</code> 文件，或者<strong>直接将整套 PNG 序列帧的文件夹拖入槽位</strong>！
              <br />
              🛡️ <strong>纯净度保护</strong>：若拖入文件夹，系统将<strong>自动递归检查，必须 100% 为纯 PNG 文件</strong>，严禁混入杂质格式，以保障客户端渲染绝不崩溃。
            </div>

            {/* 动作槽位列表 */}
            <div className="action-slots-list">
              {actionRows.map((row) => {
                const isDragOver = dragOverRowId === row.id
                const isFilled = Boolean(row.file || (row.files && row.files.length > 0))
                const fileCount = row.files ? row.files.length : row.file ? 1 : 0

                return (
                  <div
                    key={row.id}
                    className={`action-slot-row ${isDragOver ? 'is-dragover' : ''} ${isFilled ? 'is-filled' : ''}`}
                    onDragOver={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setDragOverRowId(row.id)
                    }}
                    onDragLeave={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setDragOverRowId(null)
                    }}
                    onDrop={(e) => handleDropToSlot(e, row)}
                  >
                    <div className="slot-left-meta">
                      <span className={`slot-tag ${row.required ? 'is-req' : 'is-opt'}`}>
                        {row.required ? '必填' : '可选'}
                      </span>

                      <div className="slot-name-col">
                        {row.isCustom ? (
                          <input
                            className="slot-name-input"
                            value={row.label}
                            onChange={(e) => updateActionLabel(row.id, e.target.value)}
                            placeholder="自定义动作名"
                            title="点击可直接编辑修改此动作名称"
                          />
                        ) : (
                          <strong>{row.label}</strong>
                        )}
                        <small>{row.description}</small>
                      </div>
                    </div>

                    <div className="slot-right-picker">
                      <label className="file-status-pill">
                        {isFilled ? <Check size={14} color="#059669" /> : <FolderOpen size={14} />}
                        <span>
                          {fileCount > 1
                            ? `已加载 ${fileCount} 帧纯 PNG 序列`
                            : row.file
                            ? `${row.file.name} (${formatBytes(row.file.size)})`
                            : '拖入文件/文件夹 或点击选择'}
                        </span>
                        <input
                          type="file"
                          accept={row.accept}
                          multiple={row.id !== 'static'}
                          onChange={(e) =>
                            handleFileInputChange(row, Array.from(e.target.files || []))
                          }
                        />
                      </label>

                      {row.isCustom && row.id.startsWith('action-') && (
                        <button
                          type="button"
                          className="slot-delete-btn"
                          onClick={() => removeActionRow(row.id)}
                          title="删除此动作槽位"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* 允许继续添加自定义动作（最多 10 个动作） */}
            <button
              type="button"
              className="add-slot-btn"
              onClick={addExtraAction}
              disabled={actionRows.length >= 10}
            >
              <Plus size={16} />
              <span>
                {actionRows.length >= 10
                  ? '已达到最大 10 个动作上限'
                  : `添加自定义新动作 (当前 ${actionRows.length}/10，支持自拟动作名称)`}
              </span>
            </button>

            {/* 角色实际演示录屏 */}
            <div className="form-item" style={{ marginTop: '22px' }}>
              <label>
                角色桌面实际演示录屏 <span className="required-star">*</span>
              </label>
              <label className="demo-slot-card">
                <span className="demo-slot-icon">
                  <FileVideo size={24} />
                </span>
                <div className="demo-slot-meta">
                  <strong>{demoVideo ? demoVideo.name : '拖入或点击上传 MP4 演示录屏 *'}</strong>
                  <small>{demoHint}</small>
                </div>
                <input
                  type="file"
                  accept="video/mp4,.mp4"
                  onChange={handleDemoVideoChange}
                  required={!demoVideo}
                />
              </label>
            </div>
          </section>

          {/* 卡片三：③ 审核发布 (确认与提交) */}
          <section className="submission-card-box">
            <div className="card-title-row">
              <span className="card-num-badge">3</span>
              <div>
                <h3>确认授权与审核发布</h3>
                <p>提交后由官方引擎一键封装为标准 .wpet 并在审核后发布至展馆</p>
              </div>
            </div>

            <label className="submission-check-agreement">
              <input
                type="checkbox"
                checked={licenseAccepted}
                onChange={(e) => setLicenseAccepted(e.target.checked)}
                required
              />
              <span>
                我确认拥有所提交素材的版权或合法授权，同意 WindowPet 将其封装分发并在展馆中向用户展示。
              </span>
            </label>

            {error && (
              <p className="submission-message is-error" role="alert">
                {error}
              </p>
            )}
            {notice && (
              <p className="submission-message is-success" role="status">
                {notice}
              </p>
            )}

            <button type="submit" className="submission-submit-btn" disabled={submitting}>
              {submitting ? <RefreshCw size={18} className="submission-spin" /> : <Send size={18} />}
              <span>{submitting ? '正在自动封装并上传中…' : '🚀 确认无误，提交角色审核发布'}</span>
            </button>
          </section>
        </form>
      </main>
    </div>
  )
}
