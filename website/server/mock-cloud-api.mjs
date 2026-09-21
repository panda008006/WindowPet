import { createServer } from 'node:http'
import { createHash, createSign, createVerify, randomBytes, randomUUID, scryptSync, timingSafeEqual } from 'node:crypto'
import { existsSync, readFileSync } from 'node:fs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
let QRCode = null
try {
  QRCode = require('qrcode')
} catch {}

const __dirname = dirname(fileURLToPath(import.meta.url))
const dataPath = join(__dirname, '.data', 'sync-db.json')

function loadLocalEnv() {
  for (const envPath of [join(__dirname, '..', '.env'), join(__dirname, '.env')]) {
    if (!existsSync(envPath)) continue
    for (const line of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) continue
      const index = trimmed.indexOf('=')
      if (index <= 0) continue
      const key = trimmed.slice(0, index).trim()
      let value = trimmed.slice(index + 1).trim()
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1)
      }
      if (key && process.env[key] === undefined) {
        process.env[key] = value
      }
    }
  }
}

loadLocalEnv()

const port = Number(process.env.PORT || 8787)
const authSessionTtlMs = 30 * 24 * 60 * 60 * 1000
const emailCodeTtlMs = 10 * 60 * 1000
const emailCodeCooldownMs = 30 * 1000
const isDevelopment = process.env.NODE_ENV === 'development'
const allowDevEmailCode =
  isDevelopment && process.env.WINDOWPET_ALLOW_DEV_EMAIL_CODE === 'true' && process.env.WINDOWPET_RETURN_DEV_CODE === 'true'
const allowMockLogin = isDevelopment && process.env.WINDOWPET_ALLOW_MOCK_LOGIN === 'true'
const logEmailCodes = process.env.WINDOWPET_LOG_EMAIL_CODES === 'true'
const resendApiKey = String(process.env.WINDOWPET_RESEND_API_KEY || '').trim()
const emailFrom = String(process.env.WINDOWPET_EMAIL_FROM || '').trim()
const emailFromName = String(process.env.WINDOWPET_EMAIL_FROM_NAME || 'WindowPet 小鼻嘎').trim()
const localEmailCode = process.env.WP_DEV_EMAIL_CODE || '246810'
const defaultEggCode = 'XBG-2026'
const adminToken = String(process.env.WINDOWPET_ADMIN_TOKEN || (isDevelopment ? 'windowpet-admin-local' : '')).trim()
const allowDesktopSyncBootstrap = isDevelopment && process.env.WINDOWPET_ALLOW_DESKTOP_SYNC_BOOTSTRAP === 'true'
const eggDrawLimit = 3
const userNumberStart = 1000
const emailChallenges = new Map()
const feedbackStatuses = new Set(['new', 'reviewed', 'archived'])

const alipayAppId = String(process.env.ALIPAY_APP_ID || '').trim()
const alipayPrivateKeyRaw = String(process.env.ALIPAY_PRIVATE_KEY || '').trim()
const alipayPublicKeyRaw = String(process.env.ALIPAY_PUBLIC_KEY || '').trim()
const alipayGatewayUrl = String(process.env.ALIPAY_GATEWAY_URL || 'https://openapi.alipay.com/gateway.do').trim()
const alipayNotifyUrl = String(process.env.ALIPAY_NOTIFY_URL || 'https://windowpet.cn/pet-api/api/pay/alipay-notify').trim()
const allowPaymentSimulation = process.env.WINDOWPET_PAYMENT_SIMULATION !== 'false'

const paymentPlans = [
  {
    id: 'plan_lifetime',
    name: 'WindowPet 永久全角色解锁与支持',
    tagline: '一次购买，永久解锁全部现有与未来角色',
    amount: '9.90',
    originalPrice: '29.90',
    badge: '限时特惠',
    features: [
      '永久解锁 8 只官方精品角色（含最新小王、赤狼、蜜蜂猫、尾虫等）',
      '无限制使用「九宫格动作工坊」全套动作设计与一键导入',
      '未来所有新增角色自动免费解锁，无需二次付费',
      '支持个人开发者持续维护与功能迭代',
    ],
  },
  {
    id: 'plan_sponsor_super',
    name: '深情投喂与核心支持者',
    tagline: '为作者加鸡腿，赠送永久全特权与专属金色徽章',
    amount: '19.90',
    originalPrice: '49.90',
    badge: '作者推荐',
    features: [
      '包含「永久全角色解锁与支持」全部特权',
      '专属支持者光环与金色昵称',
      '新角色与新功能内测尝鲜特权',
      '优先采纳互动动作与角色建议',
    ],
  },
]

const now = () => new Date().toISOString()

const eggRewards = [
  {
    id: 'jiyi-library-pass',
    title: '吉小伊资源直领',
    badge: '角色资源',
    description: '自动加入我的资源，适合展示小鼻嘎基础下载链路和主角资源授权。',
    petId: 'jiyi',
  },
  {
    id: 'kukukaka-library-pass',
    title: '库库咔咔资源直领',
    badge: '角色资源',
    description: '自动加入我的资源，后续可替换成真实授权记录。',
    petId: 'kukukaka',
  },
  {
    id: 'fox-library-pass',
    title: '狐狸资源直领',
    badge: '角色资源',
    description: '自动加入我的资源，用来演示活动领取和桌面工具反应。',
    petId: 'fox',
  },
  {
    id: 'sync-lab-ticket',
    title: '云同步体验券',
    badge: '功能体验',
    description: '用于展示登录账号绑定云同步体验。',
  },
]

const eggCodeStatuses = new Set(['active', 'disabled'])

function normalizeEggCode(code) {
  return String(code || '').trim().toUpperCase().replace(/\s+/g, '')
}

function normalizeEggCodeEntry(entry) {
  const source = entry && typeof entry === 'object' ? entry : {}
  const maxUses = Number.isFinite(Number(source.maxUses)) ? Math.max(1, Math.floor(Number(source.maxUses))) : 1
  const usedCount = Number.isFinite(Number(source.usedCount)) ? Math.max(0, Math.floor(Number(source.usedCount))) : 0
  const status = eggCodeStatuses.has(source.status) ? source.status : 'active'
  return {
    id: String(source.id || `egg-code-${randomUUID()}`),
    code: normalizeEggCode(source.code),
    batchName: String(source.batchName || '金蛋兑换码').trim(),
    status,
    rewardId: String(source.rewardId || 'random').trim() || 'random',
    maxUses,
    usedCount,
    notes: String(source.notes || '').trim(),
    createdAt: source.createdAt || now(),
    expiresAt: source.expiresAt || null,
    disabledAt: source.disabledAt || null,
  }
}

function normalizeEggRedemption(entry) {
  const source = entry && typeof entry === 'object' ? entry : {}
  const usedAt = source.usedAt || source.createdAt || now()
  return {
    id: String(source.id || `egg-redemption-${randomUUID()}`),
    code: normalizeEggCode(source.code || source.inviteCode || defaultEggCode),
    userId: String(source.userId || '').trim(),
    userEmail: normalizeEmail(source.userEmail || ''),
    rewardId: String(source.rewardId || '').trim(),
    batchName: String(source.batchName || '').trim(),
    usedAt,
    createdAt: source.createdAt || usedAt,
  }
}

function normalizeFeedback(entry) {
  const source = entry && typeof entry === 'object' ? entry : {}
  const createdAt = source.createdAt || now()
  const status = feedbackStatuses.has(source.status) ? source.status : 'new'
  return {
    id: String(source.id || `feedback-${randomUUID()}`),
    message: String(source.message || '').trim().slice(0, 2000),
    status,
    source: String(source.source || 'desktop').trim().slice(0, 80) || 'desktop',
    userId: String(source.userId || '').trim(),
    userEmail: normalizeEmail(source.userEmail || source.email || ''),
    userName: String(source.userName || source.name || '').trim().slice(0, 80),
    appVersion: String(source.appVersion || '').trim().slice(0, 40),
    deviceId: String(source.deviceId || '').trim().slice(0, 120),
    localAccountId: String(source.localAccountId || '').trim().slice(0, 160),
    createdAt,
    updatedAt: source.updatedAt || createdAt,
  }
}

function normalizeOrder(entry) {
  const source = entry && typeof entry === 'object' ? entry : {}
  return {
    id: String(source.id || `WP-ORDER-${randomUUID()}`),
    userId: String(source.userId || '').trim(),
    userEmail: normalizeEmail(source.userEmail || source.email || ''),
    planId: String(source.planId || 'plan_lifetime'),
    planName: String(source.planName || 'WindowPet 永久全角色解锁与支持'),
    amount: String(source.amount || '9.90'),
    currency: 'CNY',
    channel: String(source.channel || 'alipay'),
    status: ['pending', 'paid', 'expired', 'cancelled'].includes(source.status) ? source.status : 'pending',
    isSimulation: Boolean(source.isSimulation),
    qrCodeUrl: String(source.qrCodeUrl || ''),
    qrCodeSvg: String(source.qrCodeSvg || ''),
    tradeNo: String(source.tradeNo || ''),
    createdAt: source.createdAt || now(),
    paidAt: source.paidAt || null,
    expiresAt: source.expiresAt || null,
  }
}

function normalizeEntitlement(entry) {
  const source = entry && typeof entry === 'object' ? entry : {}
  return {
    id: String(source.id || `ent-${randomUUID()}`),
    userId: String(source.userId || '').trim(),
    userEmail: normalizeEmail(source.userEmail || source.email || ''),
    planId: String(source.planId || 'plan_lifetime'),
    status: String(source.status || 'active'),
    sourceOrderId: String(source.sourceOrderId || ''),
    createdAt: source.createdAt || now(),
  }
}

function defaultEggCodeEntry() {
  return normalizeEggCodeEntry({
    id: 'egg-code-default-xbg-2026',
    code: defaultEggCode,
    batchName: '默认演示码',
    rewardId: 'random',
    maxUses: 1000,
    usedCount: 0,
    notes: '本地演示用，正式上线请在后台批量生成独立兑换码。',
    createdAt: now(),
  })
}

function ensureDefaultEggCode(db) {
  if (!db.eggCodes.some((entry) => entry.code === defaultEggCode)) {
    db.eggCodes.unshift(defaultEggCodeEntry())
  }
}

const packages = [
  {
    id: 'jiyi',
    packageCode: '0006',
    folderName: 'JiyiPet',
    displayName: '吉小伊',
    tagline: '轻快互动与合奏哼唱',
    description: '官方互动小鼻嘎，支持悬停、点击、拖拽、奔跑和三宠合奏哼唱。',
    type: 'frame_animation',
    version: '1.0.1',
    official: true,
    sourceType: 'official',
    owner: 'WindowPet 官方',
    previewImage: '/pets/jiyi.png',
    previewFrame: 'jiyi_01.png',
    accessType: 'included',
    sortOrder: 10,
    reviewStatus: 'approved',
    canvas: '192x208',
    frameCount: 69,
    packageSizeBytes: 3103564,
    idleVariants: ['waiting', 'waving', 'review', 'running'],
    accessoryKeys: [],
    actionKeys: [
      'idle',
      'hover',
      'click',
      'drag',
      'waiting',
      'waving',
      'jumping',
      'failed',
      'running',
      'running-left',
      'running-right',
      'review',
      'concert-hum',
    ],
  },
  {
    id: 'kukukaka',
    packageCode: '0020',
    folderName: 'KumikoPet',
    displayName: '库库咔咔',
    tagline: '清爽灵动的日常陪伴主角',
    description: '官方互动小鼻嘎，支持悬停、点击、拖拽、等待、挥手、跳跃、奔跑和复盘动作。',
    type: 'frame_animation',
    version: '1.0.14',
    official: true,
    sourceType: 'official',
    owner: 'WindowPet 官方',
    previewImage: '/pets/kukukaka.png',
    previewFrame: 'kumiko_01.png',
    accessType: 'included',
    sortOrder: 20,
    reviewStatus: 'approved',
    canvas: '192x208',
    frameCount: 69,
    packageSizeBytes: 3020000,
    idleVariants: ['waiting', 'waving', 'review', 'running'],
    accessoryKeys: [],
    actionKeys: [
      'idle',
      'hover',
      'click',
      'drag',
      'waiting',
      'waving',
      'jumping',
      'failed',
      'running',
      'running-left',
      'running-right',
      'review',
    ],
  },
  {
    id: 'fox',
    packageCode: '0005',
    folderName: 'HuhuPet',
    displayName: '狐狸',
    tagline: '突出桌面工具互动的小狐主角',
    description: '官方互动小鼻嘎，支持羽毛逗弄和抽鞭子命中反应，适合展示桌面工具反馈。',
    type: 'frame_animation',
    version: '1.0.14',
    official: true,
    sourceType: 'official',
    owner: 'WindowPet 官方',
    previewImage: '/pets/fox.png',
    previewFrame: 'huhu_01.png',
    accessType: 'included',
    sortOrder: 30,
    reviewStatus: 'approved',
    canvas: '192x208',
    frameCount: 69,
    packageSizeBytes: 2650000,
    idleVariants: ['waiting', 'waving', 'review', 'running'],
    accessoryKeys: [],
    actionKeys: [
      'idle',
      'hover',
      'click',
      'drag',
      'waiting',
      'waving',
      'jumping',
      'failed',
      'running',
      'running-left',
      'running-right',
      'review',
      'reward',
      'feather-tickle',
      'whip-hit',
    ],
  },
  {
    id: 'usagi',
    packageCode: '0016',
    folderName: 'UsagiPet',
    displayName: '乌小萨奇',
    tagline: '治愈陪伴与烟花合奏',
    description: '治愈风格官方小鼻嘎包，基础交互完整，并内置烟花合奏动作。',
    type: 'frame_animation',
    version: '1.0.0',
    official: true,
    sourceType: 'official',
    owner: 'WindowPet 官方',
    previewImage: '/pets/usagi.png',
    previewFrame: 'usagi_01.png',
    accessType: 'included',
    sortOrder: 40,
    reviewStatus: 'approved',
    canvas: '192x208',
    frameCount: 69,
    packageSizeBytes: 2650083,
    idleVariants: ['waiting', 'waving', 'review', 'running'],
    accessoryKeys: [],
    actionKeys: [
      'idle',
      'hover',
      'click',
      'drag',
      'waiting',
      'waving',
      'jumping',
      'failed',
      'running',
      'running-left',
      'running-right',
      'review',
      'concert-fireworks',
    ],
  },
  {
    id: 'xiaoba',
    packageCode: '1001',
    folderName: 'XiaobaPet',
    displayName: '小小八',
    tagline: '创作者投稿审核示例',
    description: '第三方小鼻嘎包审核示例，动作结构与官方三宠兼容，包含钢琴合奏动作。',
    type: 'frame_animation',
    version: '0.9.0',
    official: false,
    sourceType: 'creator',
    owner: 'XiaoBaLab',
    previewImage: '/pets/xiaoba.png',
    previewFrame: 'xiaoba_01.png',
    accessType: 'preview',
    sortOrder: 50,
    reviewStatus: 'pending_review',
    canvas: '192x208',
    frameCount: 69,
    packageSizeBytes: 3262911,
    idleVariants: ['waiting', 'waving', 'review', 'running'],
    accessoryKeys: [],
    actionKeys: [
      'idle',
      'hover',
      'click',
      'drag',
      'waiting',
      'waving',
      'jumping',
      'failed',
      'running',
      'running-left',
      'running-right',
      'review',
      'concert-piano',
    ],
  },
  {
    id: 'window-pet-buddy',
    packageCode: '0019',
    folderName: 'WindowPetBuddy',
    displayName: '电光小鼻嘎',
    tagline: '高清预览包与可切换配饰',
    description: '512x512 高清帧动画小鼻嘎，支持随机待机动作和帽子、项链配饰。',
    type: 'frame_animation',
    version: '1.0.0',
    official: true,
    sourceType: 'official',
    owner: 'WindowPet 官方',
    previewImage: '/pets/window-pet-buddy.png',
    previewFrame: 'window_pet_01.png',
    accessType: 'preview',
    sortOrder: 60,
    reviewStatus: 'approved',
    canvas: '512x512',
    frameCount: 82,
    packageSizeBytes: 7784913,
    idleVariants: ['idle_blink', 'idle_look', 'idle_spark', 'idle_sleepy'],
    accessoryKeys: ['spark_cap', 'volt_necklace'],
    actionKeys: ['idle', 'hover', 'click', 'drag', 'idle_blink', 'idle_look', 'idle_spark', 'idle_sleepy'],
  },
]

function normalizePackageCode(value) {
  const digits = String(value || '').trim()
  if (!/^\d{1,4}$/.test(digits)) return ''
  return digits.padStart(4, '0')
}

function packageWithDelivery(item) {
  const packageCode = normalizePackageCode(item.packageCode)
  const fileName = packageCode ? `window-pet-package-${packageCode}.zip` : ''
  return {
    ...item,
    packageCode,
    delivery: {
      available: false,
      fileName,
      downloadUrl: packageCode ? `/pet/packages/${packageCode}/${fileName}` : null,
      sha256: null,
    },
  }
}

const catalogPackages = packages.map(packageWithDelivery)

function defaultDb() {
  const createdAt = now()
  return {
    schemaVersion: 1,
    nextUserNumber: userNumberStart + 1,
    packages: catalogPackages,
    users: [
      {
        id: 'wp-demo-user',
        userNumber: userNumberStart,
        email: 'demo@windowpet.local',
        displayName: '演示用户',
        provider: 'email',
        salt: '',
        passwordHash: '',
        sessions: [],
        createdAt,
        updatedAt: createdAt,
      },
    ],
    installs: [
      {
        id: 'install-jiyi',
        userId: 'wp-demo-user',
        packageId: 'jiyi',
        packageVersion: '1.0.14',
        installed: true,
        favorite: true,
        nickname: '我的吉小伊',
        createdAt,
        updatedAt: createdAt,
      },
    ],
    deviceStates: [
      {
        id: 'wp-state-demo-device-001',
        userId: 'wp-demo-user',
        deviceId: 'wp-demo-device-001',
        installId: 'install-jiyi',
        packageId: 'jiyi',
        assetType: 'frame_animation',
        petDisplayName: '吉小伊',
        x: 80,
        y: 100,
        scale: 100,
        opacity: 100,
        speed: 100,
        locked: false,
        alwaysOnTop: true,
        clickThrough: false,
        dockMode: 'none',
        currentAnimation: 'idle',
        enabledAccessories: [],
        memoVisible: false,
        memoText: '',
        memoChecked: false,
        revision: 1,
        updatedAt: createdAt,
      },
    ],
    eggCodes: [defaultEggCodeEntry()],
    eggRedemptions: [],
    eggClaims: [],
    orders: [],
    entitlements: [],
    feedback: [],
    events: [],
  }
}

function normalizeDb(db) {
  if (!db || typeof db !== 'object') {
    return defaultDb()
  }
  const normalized = {
    ...db,
    schemaVersion: 1,
    nextUserNumber: normalizeNextUserNumber(db.nextUserNumber),
    packages: catalogPackages,
    users: Array.isArray(db.users) ? db.users.map((user) => normalizeUser(user)) : [],
    installs: Array.isArray(db.installs) ? db.installs : [],
    deviceStates: Array.isArray(db.deviceStates) ? db.deviceStates : [],
    eggCodes: Array.isArray(db.eggCodes) ? db.eggCodes.map(normalizeEggCodeEntry).filter((item) => item.code) : [],
    eggRedemptions: Array.isArray(db.eggRedemptions)
      ? db.eggRedemptions.map(normalizeEggRedemption).filter((item) => item.code && item.userId)
      : [],
    eggClaims: Array.isArray(db.eggClaims) ? db.eggClaims : [],
    orders: Array.isArray(db.orders) ? db.orders.map(normalizeOrder).filter((item) => item.id) : [],
    entitlements: Array.isArray(db.entitlements) ? db.entitlements.map(normalizeEntitlement).filter((item) => item.id) : [],
    feedback: Array.isArray(db.feedback)
      ? db.feedback.map(normalizeFeedback).filter((item) => item.message)
      : [],
    events: Array.isArray(db.events) ? db.events : [],
  }
  ensureUserNumbers(normalized)
  ensureDefaultEggCode(normalized)
  return normalized
}

async function loadDb() {
  try {
    return normalizeDb(JSON.parse(await readFile(dataPath, 'utf8')))
  } catch {
    const db = defaultDb()
    await saveDb(db)
    return db
  }
}

async function saveDb(db) {
  await mkdir(dirname(dataPath), { recursive: true })
  await writeFile(dataPath, `${JSON.stringify(db, null, 2)}\n`, 'utf8')
}

function sendJson(response, status, body) {
  const corsOrigin = String(process.env.WINDOWPET_CORS_ORIGIN || (isDevelopment ? '*' : '')).trim() || 'null'
  response.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': corsOrigin,
    'Access-Control-Allow-Methods': 'GET,POST,PUT,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-WindowPet-Admin-Token',
    Vary: 'Origin',
    'Cache-Control': 'no-store',
  })
  response.end(JSON.stringify(body, null, 2))
}

function randomEmailCode() {
  return String(Math.floor(100000 + Math.random() * 900000))
}

async function sendEmailCode(email, code) {
  if (!resendApiKey || !emailFrom) {
    if (allowDevEmailCode) return { ok: true, devOnly: true }
    return { ok: false, error: '邮件服务还没有配置完成，请稍后再试。' }
  }

  const subject = 'WindowPet 小鼻嘎注册验证码'
  const text = `你的 WindowPet 小鼻嘎注册验证码是：${code}\n\n验证码 10 分钟内有效。如果不是你本人操作，可以忽略这封邮件。`
  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.7;color:#102033">
      <h2>WindowPet 小鼻嘎注册验证码</h2>
      <p>你的验证码是：</p>
      <p style="font-size:28px;font-weight:700;letter-spacing:4px">${code}</p>
      <p>验证码 10 分钟内有效。如果不是你本人操作，可以忽略这封邮件。</p>
    </div>
  `

  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${resendApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: `${emailFromName} <${emailFrom}>`,
        to: [email],
        subject,
        text,
        html,
      }),
    })
    if (!response.ok) {
      let detail = ''
      try {
        detail = JSON.stringify(await response.json())
      } catch {
        detail = await response.text()
      }
      console.error(`[WindowPet auth] email send failed: ${response.status} ${detail}`)
      return { ok: false, error: '验证码邮件发送失败，请稍后再试。' }
    }
    return { ok: true }
  } catch (error) {
    console.error('[WindowPet auth] email send error:', error)
    return { ok: false, error: '验证码邮件发送失败，请稍后再试。' }
  }
}

function normalizeEmail(value) {
  return String(value || '').trim().toLowerCase()
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizeEmail(email))
}

function passwordHash(password, salt) {
  return scryptSync(String(password || ''), salt, 32).toString('hex')
}

function tokenHash(token) {
  return createHash('sha256').update(String(token || '')).digest('hex')
}

function inviteCodeForIdentity(identity) {
  const seed = normalizeEmail(identity)
  if (!seed) return null
  const hex = createHash('sha256').update(seed).digest('hex').slice(0, 8).toUpperCase()
  return `WP-${hex.slice(0, 4)}-${hex.slice(4)}`
}

function publicUser(user, db = null) {
  const inviteCode = user.inviteCode || inviteCodeForIdentity(user.email || user.id)
  const isVip = Boolean(
    user.isVip ||
    (db && db.entitlements && db.entitlements.some((e) => (e.userId === user.id || (user.email && normalizeEmail(e.userEmail) === normalizeEmail(user.email))) && e.status === 'active'))
  )
  return {
    id: user.id,
    userNumber: user.userNumber,
    name: user.displayName || user.name || normalizeEmail(user.email).split('@')[0] || 'WindowPet 用户',
    email: user.email,
    inviteCode,
    provider: user.provider || 'email',
    isVip,
    allUnlocked: isVip,
    createdAt: user.createdAt,
    lastLoginAt: user.lastLoginAt || null,
  }
}

function publicOrder(order) {
  return {
    id: order.id,
    planId: order.planId,
    planName: order.planName,
    amount: order.amount,
    currency: order.currency,
    channel: order.channel,
    status: order.status,
    isSimulation: Boolean(order.isSimulation),
    qrCodeUrl: order.qrCodeUrl,
    qrCodeSvg: order.qrCodeSvg,
    createdAt: order.createdAt,
    paidAt: order.paidAt,
    expiresAt: order.expiresAt,
  }
}

function publicAdminUser(db, user) {
  const installs = db.installs.filter((item) => item.userId === user.id)
  const deviceStates = db.deviceStates.filter((item) => item.userId === user.id)
  const redemptions = db.eggRedemptions.filter((item) => item.userId === user.id)
  const localIds = new Set([user.localAccountId, user.externalIdentity].filter(Boolean).map((item) => String(item).toLowerCase()))
  const feedback = db.feedback.filter(
    (item) =>
      item.userId === user.id ||
      normalizeEmail(item.userEmail) === normalizeEmail(user.email) ||
      (item.localAccountId && localIds.has(String(item.localAccountId).toLowerCase())),
  )
  return {
    id: user.id,
    userNumber: user.userNumber,
    name: user.displayName || user.name || normalizeEmail(user.email).split('@')[0] || 'WindowPet 用户',
    email: user.email,
    provider: user.provider || 'email',
    createdAt: user.createdAt,
    updatedAt: user.updatedAt,
    lastLoginAt: user.lastLoginAt || null,
    sessionCount: Array.isArray(user.sessions) ? user.sessions.length : 0,
    installCount: installs.length,
    deviceCount: deviceStates.length,
    redemptionCount: redemptions.length,
    feedbackCount: feedback.length,
  }
}

function normalizeUser(user) {
  const email = normalizeEmail(user.email)
  return {
    ...user,
    id: String(user.id || `user-${randomUUID()}`),
    userNumber: normalizeUserNumber(user.userNumber ?? user.numericId ?? user.memberId),
    email,
    displayName: String(user.displayName || user.name || email.split('@')[0] || 'WindowPet 用户').trim(),
    provider: user.provider || 'email',
    salt: String(user.salt || ''),
    passwordHash: String(user.passwordHash || ''),
    sessions: Array.isArray(user.sessions) ? user.sessions : [],
    createdAt: user.createdAt || now(),
    updatedAt: user.updatedAt || user.createdAt || now(),
    lastLoginAt: user.lastLoginAt || null,
  }
}

function normalizeUserNumber(value) {
  const number = Number(value)
  if (!Number.isInteger(number) || number < userNumberStart) return null
  return number
}

function normalizeNextUserNumber(value) {
  const number = Number(value)
  if (!Number.isInteger(number) || number < userNumberStart) return userNumberStart
  return number
}

function ensureUserNumbers(db) {
  const used = new Set()
  for (const user of db.users) {
    const number = normalizeUserNumber(user.userNumber)
    if (number && !used.has(number)) {
      user.userNumber = number
      used.add(number)
    } else {
      user.userNumber = null
    }
  }

  let next = userNumberStart
  for (const user of db.users) {
    if (user.userNumber) continue
    while (used.has(next)) next += 1
    user.userNumber = next
    used.add(next)
    next += 1
  }

  const maxNumber = used.size ? Math.max(...used) : userNumberStart - 1
  db.nextUserNumber = Math.max(normalizeNextUserNumber(db.nextUserNumber), maxNumber + 1)
}

function assignUserNumber(db, user) {
  if (normalizeUserNumber(user.userNumber)) return user.userNumber
  const used = new Set(db.users.map((item) => normalizeUserNumber(item.userNumber)).filter(Boolean))
  let next = normalizeNextUserNumber(db.nextUserNumber)
  while (used.has(next)) next += 1
  user.userNumber = next
  db.nextUserNumber = next + 1
  return user.userNumber
}

function verifyPassword(user, password) {
  if (!user.salt || !user.passwordHash) return false
  try {
    const expected = Buffer.from(user.passwordHash, 'hex')
    const actual = Buffer.from(passwordHash(password, user.salt), 'hex')
    return expected.length === actual.length && timingSafeEqual(expected, actual)
  } catch {
    return false
  }
}

function issueSession(user) {
  const token = randomBytes(32).toString('base64url')
  const timestamp = Date.now()
  user.sessions = (user.sessions || [])
    .filter((session) => new Date(session.expiresAt).getTime() > timestamp)
    .concat({
      tokenHash: tokenHash(token),
      createdAt: new Date(timestamp).toISOString(),
      expiresAt: new Date(timestamp + authSessionTtlMs).toISOString(),
    })
  user.lastLoginAt = new Date(timestamp).toISOString()
  user.updatedAt = user.lastLoginAt
  return token
}

function authTokenFromRequest(request) {
  const auth = String(request.headers.authorization || '')
  return auth.toLowerCase().startsWith('bearer ') ? auth.slice(7).trim() : ''
}

function userFromRequest(db, request) {
  const token = authTokenFromRequest(request)
  if (!token) return null
  const hash = tokenHash(token)
  const timestamp = Date.now()
  let matched = null
  for (const user of db.users) {
    user.sessions = (user.sessions || []).filter((session) => new Date(session.expiresAt).getTime() > timestamp)
    if (user.sessions.some((session) => session.tokenHash === hash)) {
      matched = user
    }
  }
  return matched
}

function requireUser(db, request, response) {
  const user = userFromRequest(db, request)
  if (!user) {
    sendJson(response, 401, { error: '请先登录账号。' })
    return null
  }
  return user
}

function adminTokenFromRequest(request, url) {
  const auth = String(request.headers.authorization || '')
  if (auth.toLowerCase().startsWith('bearer ')) return auth.slice(7).trim()
  return String(request.headers['x-windowpet-admin-token'] || url.searchParams.get('adminToken') || '').trim()
}

function requireAdmin(request, response, url) {
  if (!adminToken || adminTokenFromRequest(request, url) !== adminToken) {
    sendJson(response, 401, { error: '后台口令不正确。' })
    return false
  }
  return true
}

function emailChallengeKey(email, purpose) {
  return `${purpose}:${normalizeEmail(email)}`
}

function issueEmailCode(email, purpose) {
  const timestamp = Date.now()
  const code = allowDevEmailCode ? localEmailCode : randomEmailCode()
  emailChallenges.set(emailChallengeKey(email, purpose), {
    email: normalizeEmail(email),
    purpose,
    codeHash: createHash('sha256').update(`${normalizeEmail(email)}:${purpose}:${code}`).digest('hex'),
    createdAt: timestamp,
    expiresAt: timestamp + emailCodeTtlMs,
    attempts: 0,
    lastSentAt: timestamp,
  })
  return code
}

function emailCodeCooldown(email, purpose) {
  const challenge = emailChallenges.get(emailChallengeKey(email, purpose))
  if (!challenge) return 0
  return Math.max(0, Math.ceil((emailCodeCooldownMs - (Date.now() - challenge.lastSentAt)) / 1000))
}

function verifyEmailCode(email, purpose, code) {
  const trimmed = String(code || '').trim()
  if (allowDevEmailCode && trimmed === localEmailCode) {
    return { ok: true }
  }
  const key = emailChallengeKey(email, purpose)
  const challenge = emailChallenges.get(key)
  if (!challenge || Date.now() > challenge.expiresAt) {
    emailChallenges.delete(key)
    return { ok: false, error: '验证码已过期，请重新获取。' }
  }
  challenge.attempts += 1
  if (challenge.attempts > 8) {
    emailChallenges.delete(key)
    return { ok: false, error: '验证码错误次数过多，请重新获取。' }
  }
  const inputHash = createHash('sha256')
    .update(`${normalizeEmail(email)}:${purpose}:${trimmed}`)
    .digest('hex')
  if (inputHash !== challenge.codeHash) {
    return { ok: false, error: '邮箱验证码不正确。' }
  }
  emailChallenges.delete(key)
  return { ok: true }
}

function formatAlipayTimestamp(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  const y = date.getFullYear()
  const m = pad(date.getMonth() + 1)
  const d = pad(date.getDate())
  const h = pad(date.getHours())
  const min = pad(date.getMinutes())
  const s = pad(date.getSeconds())
  return `${y}-${m}-${d} ${h}:${min}:${s}`
}

function formatAlipayKey(rawKey, type = 'RSA PRIVATE KEY') {
  if (!rawKey) return ''
  let key = rawKey.trim()
  if (key.includes('-----BEGIN')) return key
  const chunked = key.match(/.{1,64}/g) ? key.match(/.{1,64}/g).join('\n') : key
  return `-----BEGIN ${type}-----\n${chunked}\n-----END ${type}-----`
}

function alipayRsa2Sign(params, privateKeyPem) {
  const sortedKeys = Object.keys(params).filter((k) => k !== 'sign' && params[k] !== undefined && params[k] !== null && String(params[k]).trim() !== '').sort()
  const signString = sortedKeys.map((k) => `${k}=${params[k]}`).join('&')
  const signer = createSign('RSA-SHA256')
  signer.update(signString, 'utf8')
  return signer.sign(privateKeyPem, 'base64')
}

function alipayRsa2Verify(params, signature, publicKeyPem) {
  const sortedKeys = Object.keys(params).filter((k) => k !== 'sign' && k !== 'sign_type' && params[k] !== undefined && params[k] !== null && String(params[k]).trim() !== '').sort()
  const signString = sortedKeys.map((k) => `${k}=${params[k]}`).join('&')
  const verifier = createVerify('RSA-SHA256')
  verifier.update(signString, 'utf8')
  return verifier.verify(publicKeyPem, signature, 'base64')
}

async function generateQrCodeSvg(text) {
  if (QRCode) {
    try {
      return await QRCode.toString(text, {
        type: 'svg',
        margin: 1,
        width: 260,
        color: {
          dark: '#1677ff',
          light: '#ffffff',
        },
      })
    } catch (err) {
      console.warn('[QR Gen Error]', err)
    }
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 260" width="260" height="260">
    <rect width="100%" height="100%" fill="#ffffff" rx="12"/>
    <rect x="20" y="20" width="220" height="220" fill="#f6f9fc" stroke="#1677ff" stroke-width="2" stroke-dasharray="6,4" rx="8"/>
    <text x="130" y="110" font-size="14" font-weight="bold" fill="#1677ff" text-anchor="middle">支付宝扫码支付</text>
    <text x="130" y="140" font-size="12" fill="#555555" text-anchor="middle">请扫描或点击模拟付款</text>
  </svg>`
}

async function requestAlipayPrecreate(order) {
  const appId = alipayAppId
  const privateKeyRaw = alipayPrivateKeyRaw
  const gateway = alipayGatewayUrl
  const notifyUrl = alipayNotifyUrl

  if (!appId || !privateKeyRaw) {
    return {
      simulation: true,
      qrCodeUrl: `https://windowpet.cn/pet/#pay-mock-${order.id}`,
      warn: '系统尚未配置支付宝商户密钥，已自动运行在沙箱模拟支付模式。',
    }
  }

  const privateKey = formatAlipayKey(privateKeyRaw, 'RSA PRIVATE KEY')
  const params = {
    app_id: appId,
    method: 'alipay.trade.precreate',
    format: 'JSON',
    charset: 'utf-8',
    sign_type: 'RSA2',
    timestamp: formatAlipayTimestamp(),
    version: '1.0',
    notify_url: notifyUrl,
    biz_content: JSON.stringify({
      out_trade_no: order.id,
      total_amount: order.amount,
      subject: order.planName,
      timeout_express: '15m',
    }),
  }

  try {
    params.sign = alipayRsa2Sign(params, privateKey)
    const formBody = new URLSearchParams(params).toString()
    const res = await fetch(gateway, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' },
      body: formBody,
    })
    const json = await res.json()
    const resp = json.alipay_trade_precreate_response
    if (resp && resp.code === '10000' && resp.qr_code) {
      return {
        simulation: false,
        qrCodeUrl: resp.qr_code,
      }
    }
    console.warn('[Alipay precreate response]', json)
    return {
      simulation: true,
      qrCodeUrl: `https://windowpet.cn/pet/#pay-mock-${order.id}`,
      warn: (resp && (resp.sub_msg || resp.msg)) || '支付宝下单未成功，已自动启用测试模拟模式',
    }
  } catch (err) {
    console.warn('[Alipay precreate error]', err)
    return {
      simulation: true,
      qrCodeUrl: `https://windowpet.cn/pet/#pay-mock-${order.id}`,
      warn: '网络通信异常，已自动启用测试模拟模式',
    }
  }
}

function grantOrderEntitlement(db, order) {
  const existing = db.entitlements.find((e) => e.sourceOrderId === order.id)
  if (existing) return existing

  const entitlement = normalizeEntitlement({
    id: `ent-${randomUUID()}`,
    userId: order.userId,
    userEmail: order.userEmail,
    planId: order.planId,
    status: 'active',
    sourceOrderId: order.id,
    createdAt: now(),
  })
  db.entitlements.push(entitlement)

  let user = null
  if (order.userId) {
    user = db.users.find((u) => u.id === order.userId)
  }
  if (!user && order.userEmail) {
    user = db.users.find((u) => normalizeEmail(u.email) === normalizeEmail(order.userEmail))
  }

  if (user) {
    user.isVip = true
    user.allUnlocked = true
    for (const pkg of db.packages) {
      let install = db.installs.find((item) => item.userId === user.id && item.packageId === pkg.id)
      if (!install) {
        db.installs.push({
          id: `install-${randomUUID()}`,
          userId: user.id,
          packageId: pkg.id,
          packageVersion: pkg.version,
          installed: true,
          favorite: false,
          nickname: pkg.displayName,
          createdAt: now(),
          updatedAt: now(),
        })
      } else {
        install.installed = true
        install.updatedAt = now()
      }
    }
  }

  return entitlement
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let raw = ''
    request.on('data', (chunk) => {
      raw += chunk
      if (raw.length > 1_000_000) {
        request.destroy()
        reject(new Error('Request body too large'))
      }
    })
    request.on('end', () => {
      if (!raw.trim()) {
        resolve({})
        return
      }
      const contentType = String(request.headers['content-type'] || '').toLowerCase()
      if (contentType.includes('application/x-www-form-urlencoded')) {
        const params = new URLSearchParams(raw)
        const obj = {}
        for (const [k, v] of params.entries()) {
          obj[k] = v
        }
        resolve(obj)
        return
      }
      try {
        resolve(JSON.parse(raw))
      } catch {
        try {
          const params = new URLSearchParams(raw)
          const obj = {}
          for (const [k, v] of params.entries()) {
            obj[k] = v
          }
          if (Object.keys(obj).length > 0) {
            resolve(obj)
            return
          }
        } catch {}
        reject(new Error('Invalid body'))
      }
    })
    request.on('error', reject)
  })
}

function readJson(request) {
  return readBody(request)
}

function ensureUser(db, email = 'demo@windowpet.local', input = {}) {
  const normalizedEmail = normalizeEmail(email)
  db.users = db.users.map((user) => normalizeUser(user))
  let user = db.users.find((item) => normalizeEmail(item.email) === normalizedEmail)
  if (!user) {
    const timestamp = now()
    user = normalizeUser({
      id: `user-${randomUUID()}`,
      email: normalizedEmail,
      displayName: String(input.displayName || input.name || normalizedEmail.split('@')[0] || 'WindowPet 用户'),
      provider: input.provider || 'email',
      createdAt: timestamp,
      updatedAt: timestamp,
    })
    assignUserNumber(db, user)
    db.users.push(user)
  }
  return user
}

function ensureExternalUser(db, input = {}) {
  const email = normalizeEmail(input.email || '')
  const identity = String(input.identity || input.phone || input.localAccountId || email || '').trim()
  const lookup = email || identity.toLowerCase()
  let user = db.users.find(
    (item) =>
      (email && normalizeEmail(item.email) === email) ||
      (lookup && String(item.externalIdentity || item.localAccountId || '').toLowerCase() === lookup),
  )
  const timestamp = now()
  if (!user) {
    user = normalizeUser({
      id: `user-${randomUUID()}`,
      email: email || `${createHash('sha1').update(lookup || randomUUID()).digest('hex').slice(0, 12)}@local.windowpet`,
      displayName: String(input.name || input.displayName || email.split('@')[0] || identity || 'WindowPet 用户').trim(),
      provider: input.provider || 'desktop-local',
      createdAt: timestamp,
      updatedAt: timestamp,
    })
    assignUserNumber(db, user)
    db.users.push(user)
  }
  user.displayName = String(input.name || input.displayName || user.displayName || '').trim() || user.displayName
  user.provider = String(input.provider || user.provider || 'desktop-local')
  user.externalIdentity = identity || user.externalIdentity || ''
  user.localAccountId = String(input.localAccountId || user.localAccountId || '').trim()
  user.appVersion = String(input.appVersion || user.appVersion || '').trim()
  user.lastLoginAt = timestamp
  user.updatedAt = timestamp
  return user
}

function eggStatus(db, user) {
  const redemptions = db.eggRedemptions
    .filter((claim) => claim.userId === user.id)
    .map((claim) => ({
      ...claim,
      reward: eggRewards.find((reward) => reward.id === claim.rewardId) ?? null,
    }))
  const legacyClaims = db.eggClaims
    .filter((claim) => claim.userId === user.id)
    .map((claim) => ({
      ...claim,
      code: normalizeEggCode(claim.code || claim.inviteCode || defaultEggCode),
      usedAt: claim.usedAt || claim.createdAt,
      reward: eggRewards.find((reward) => reward.id === claim.rewardId) ?? null,
    }))
  const claims = [...redemptions, ...legacyClaims].sort((a, b) =>
    String(b.usedAt || b.createdAt || '').localeCompare(String(a.usedAt || a.createdAt || '')),
  )
  const claimedRewardIds = new Set(claims.map((claim) => claim.rewardId))
  return {
    redeemCode: defaultEggCode,
    drawLimit: Math.max(eggDrawLimit, claims.length),
    used: claims.length,
    canDraw: db.eggCodes.some((entry) => entry.status === 'active' && !eggCodeIsExpired(entry)),
    rewardsRemaining: Math.max(0, eggRewards.length - claimedRewardIds.size),
    claims,
  }
}

function eggCodeIsExpired(entry, current = new Date()) {
  return Boolean(entry.expiresAt && new Date(entry.expiresAt).getTime() < current.getTime())
}

function publicEggCode(entry) {
  const reward = eggRewards.find((item) => item.id === entry.rewardId) ?? null
  return {
    ...entry,
    reward,
    remaining: Math.max(0, entry.maxUses - entry.usedCount),
    expired: eggCodeIsExpired(entry),
  }
}

function pickRewardForCode(db, user, codeEntry) {
  if (codeEntry.rewardId && codeEntry.rewardId !== 'random') {
    return eggRewards.find((reward) => reward.id === codeEntry.rewardId) ?? null
  }
  const userRewardIds = new Set(
    db.eggRedemptions.filter((item) => item.userId === user.id).map((item) => item.rewardId),
  )
  const available = eggRewards.filter((reward) => !userRewardIds.has(reward.id))
  const pool = available.length ? available : eggRewards
  return pool[Math.floor(Math.random() * pool.length)] ?? null
}

function redeemEggCode(db, user, rawCode) {
  const code = normalizeEggCode(rawCode)
  const entry = db.eggCodes.find((item) => item.code === code)
  if (!entry || entry.status !== 'active' || eggCodeIsExpired(entry)) {
    return { error: '兑换码不可用，请检查后重试。' }
  }
  if (entry.usedCount >= entry.maxUses) {
    return { error: '兑换码已经被使用完。' }
  }
  if (db.eggRedemptions.some((item) => item.userId === user.id && item.code === code)) {
    return { error: '这个兑换码当前账号已经使用过。' }
  }

  const reward = pickRewardForCode(db, user, entry)
  if (!reward) {
    return { error: '兑换码奖励配置不正确，请联系后台处理。' }
  }

  const timestamp = now()
  const redemption = normalizeEggRedemption({
    id: `egg-redemption-${randomUUID()}`,
    code,
    userId: user.id,
    userEmail: user.email,
    rewardId: reward.id,
    batchName: entry.batchName,
    usedAt: timestamp,
  })
  db.eggRedemptions.unshift(redemption)
  entry.usedCount += 1
  db.events.unshift({
    id: `event-${randomUUID()}`,
    userId: user.id,
    type: 'egg_code_redeemed',
    code,
    rewardId: reward.id,
    createdAt: timestamp,
  })
  db.events = db.events.slice(0, 100)
  return {
    reward,
    claim: { ...redemption, reward },
    status: eggStatus(db, user),
  }
}

function syncPayload(db, userId, deviceId) {
  const user = db.users.find((item) => item.id === userId)
  const isVip = Boolean(
    user &&
    (user.isVip ||
      (db.entitlements &&
        db.entitlements.some(
          (e) =>
            (e.userId === userId || (user.email && normalizeEmail(e.userEmail) === normalizeEmail(user.email))) &&
            e.status === 'active',
        )))
  )
  return {
    user: user ? publicUser(user, db) : null,
    isVip,
    allUnlocked: isVip,
    unlockedAll: isVip,
    packages: db.packages,
    installs: db.installs.filter((install) => install.userId === userId),
    deviceStates: db.deviceStates.filter(
      (state) => state.userId === userId && (!deviceId || state.deviceId === deviceId),
    ),
  }
}

function adminFeedbackItem(db, item) {
  const user = db.users.find(
    (entry) =>
      entry.id === item.userId ||
      normalizeEmail(entry.email) === normalizeEmail(item.userEmail) ||
      (item.localAccountId &&
        [entry.localAccountId, entry.externalIdentity]
          .filter(Boolean)
          .map((value) => String(value).toLowerCase())
          .includes(String(item.localAccountId).toLowerCase())),
  )
  return {
    ...item,
    user: user ? publicAdminUser(db, user) : null,
  }
}

function adminRedemptionItem(db, item) {
  const user = db.users.find((entry) => entry.id === item.userId || normalizeEmail(entry.email) === normalizeEmail(item.userEmail))
  return {
    ...item,
    user: user ? publicAdminUser(db, user) : null,
    reward: eggRewards.find((reward) => reward.id === item.rewardId) ?? null,
  }
}

function adminOverview(db) {
  const feedback = db.feedback
    .map((item) => adminFeedbackItem(db, item))
    .sort((a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || '')))
  const redemptions = db.eggRedemptions
    .map((item) => adminRedemptionItem(db, item))
    .sort((a, b) => String(b.usedAt || b.createdAt || '').localeCompare(String(a.usedAt || a.createdAt || '')))

  return {
    metrics: {
      users: db.users.length,
      lastUserNumber: db.users.reduce((max, user) => Math.max(max, Number(user.userNumber) || 0), 0),
      feedback: feedback.length,
      newFeedback: feedback.filter((item) => item.status === 'new').length,
      devices: db.deviceStates.length,
      installs: db.installs.length,
      redemptions: redemptions.length,
      activeEggCodes: db.eggCodes.filter((item) => item.status === 'active' && !eggCodeIsExpired(item)).length,
    },
    users: db.users
      .map((user) => publicAdminUser(db, user))
      .sort((a, b) => String(b.updatedAt || b.createdAt || '').localeCompare(String(a.updatedAt || a.createdAt || ''))),
    feedback,
    redemptions: redemptions.slice(0, 300),
    eggCodes: db.eggCodes
      .map(publicEggCode)
      .sort((a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || ''))),
  }
}

function upsertDeviceState(db, userId, deviceId, body) {
  const timestamp = now()
  const stateInput = body.state && typeof body.state === 'object' ? body.state : body
  const installId = String(body.installId || stateInput.installId || 'install-jiyi')
  const packageId = String(body.packageId || stateInput.packageId || 'usagi')
  let state = db.deviceStates.find((item) => item.userId === userId && item.deviceId === deviceId)
  if (!state) {
    state = {
      id: `state-${randomUUID()}`,
      userId,
      deviceId,
      installId,
      packageId,
      assetType: 'frame_animation',
      revision: 0,
      updatedAt: timestamp,
    }
    db.deviceStates.push(state)
  }

  const allowed = [
    'assetType',
    'petDisplayName',
    'x',
    'y',
    'scale',
    'opacity',
    'speed',
    'locked',
    'alwaysOnTop',
    'clickThrough',
    'dockMode',
    'currentAnimation',
    'enabledAccessories',
    'memoVisible',
    'memoText',
    'memoChecked',
  ]

  for (const key of allowed) {
    if (key in stateInput) {
      state[key] = stateInput[key]
    }
  }
  state.installId = installId
  state.packageId = packageId
  state.revision = Number(state.revision || 0) + 1
  state.updatedAt = timestamp

  db.events.unshift({
    id: `event-${randomUUID()}`,
    userId,
    deviceId,
    type: 'device_state_synced',
    revision: state.revision,
    createdAt: timestamp,
  })
  db.events = db.events.slice(0, 100)
  return state
}

async function handle(request, response) {
  if (request.method === 'OPTIONS') {
    sendJson(response, 204, {})
    return
  }

  const url = new URL(request.url ?? '/', `http://${request.headers.host ?? 'localhost'}`)
  const path = url.pathname
  const db = await loadDb()

  try {
    if (request.method === 'GET' && path === '/api/health') {
      sendJson(response, 200, {
        ok: true,
        service: 'WindowPet Mock Cloud',
        version: '0.1.0',
        dataPath,
        time: now(),
      })
      return
    }

    if (request.method === 'GET' && path === '/api/auth/providers') {
      sendJson(response, 200, {
        password: true,
        emailCode: Boolean((resendApiKey && emailFrom) || allowDevEmailCode),
        wechatQr: Boolean(String(process.env.WINDOWPET_WECHAT_APP_ID || '').trim()),
        sms: Boolean(String(process.env.WINDOWPET_SMS_PROVIDER || '').trim()),
        note: '微信和短信只有在完成供应商配置、回调校验和限流后才会显示为可用。',
      })
      return
    }

    if (request.method === 'GET' && path === '/api/store/pets') {
      sendJson(response, 200, { packages: db.packages })
      return
    }

    if (request.method === 'GET' && path === '/api/store/packages') {
      sendJson(response, 200, { packages: db.packages })
      return
    }

    const packageCodeMatch = path.match(/^\/api\/store\/packages\/(\d{1,4})$/)
    if (request.method === 'GET' && packageCodeMatch) {
      const packageCode = normalizePackageCode(packageCodeMatch[1])
      const item = db.packages.find((entry) => normalizePackageCode(entry.packageCode) === packageCode)
      if (!item) {
        sendJson(response, 404, { error: 'Package code not found', packageCode })
        return
      }
      sendJson(response, 200, { package: item })
      return
    }

    if (request.method === 'GET' && path === '/api/admin/overview') {
      if (!requireAdmin(request, response, url)) return
      sendJson(response, 200, adminOverview(db))
      return
    }

    const feedbackStatusMatch = path.match(/^\/api\/admin\/feedback\/([^/]+)\/status$/)
    if (request.method === 'POST' && feedbackStatusMatch) {
      if (!requireAdmin(request, response, url)) return
      const body = await readJson(request)
      const status = String(body.status || '').trim()
      if (!feedbackStatuses.has(status)) {
        sendJson(response, 400, { error: '反馈状态不正确。' })
        return
      }
      const feedbackId = decodeURIComponent(feedbackStatusMatch[1])
      const feedback = db.feedback.find((item) => item.id === feedbackId)
      if (!feedback) {
        sendJson(response, 404, { error: '反馈不存在。' })
        return
      }
      feedback.status = status
      feedback.updatedAt = now()
      await saveDb(db)
      sendJson(response, 200, { feedback: adminFeedbackItem(db, feedback), overview: adminOverview(db) })
      return
    }

    if (request.method === 'GET' && path === '/api/admin/egg-codes') {
      if (!requireAdmin(request, response, url)) return
      sendJson(response, 200, {
        rewards: eggRewards,
        codes: db.eggCodes
          .map(publicEggCode)
          .sort((a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || ''))),
        redemptions: db.eggRedemptions
          .map((item) => ({
            ...item,
            reward: eggRewards.find((reward) => reward.id === item.rewardId) ?? null,
          }))
          .sort((a, b) => String(b.usedAt || '').localeCompare(String(a.usedAt || '')))
          .slice(0, 200),
      })
      return
    }

    if (request.method === 'POST' && path === '/api/admin/egg-codes/batch') {
      if (!requireAdmin(request, response, url)) return
      const body = await readJson(request)
      const count = Math.max(1, Math.min(1000, Math.trunc(Number(body.count || 1))))
      const maxUses = Math.max(1, Math.min(10000, Math.trunc(Number(body.maxUses || 1))))
      const prefix = normalizeEggCode(body.prefix || 'WPX').slice(0, 12) || 'WPX'
      const batchName = String(body.batchName || '金蛋兑换码').trim().slice(0, 80) || '金蛋兑换码'
      const rewardId = String(body.rewardId || 'random').trim() || 'random'
      const expiresAt = String(body.expiresAt || '').trim() || null
      const notes = String(body.notes || '').trim().slice(0, 200)

      if (rewardId !== 'random' && !eggRewards.some((reward) => reward.id === rewardId)) {
        sendJson(response, 400, { error: '奖励配置不存在。' })
        return
      }

      const existing = new Set(db.eggCodes.map((item) => item.code))
      const created = []
      while (created.length < count) {
        const code = `${prefix}${randomBytes(5).toString('hex').toUpperCase()}`
        if (existing.has(code)) continue
        existing.add(code)
        created.push(
          normalizeEggCodeEntry({
            id: `egg-code-${randomUUID()}`,
            code,
            batchName,
            status: 'active',
            rewardId,
            maxUses,
            usedCount: 0,
            notes,
            createdAt: now(),
            expiresAt,
          }),
        )
      }
      db.eggCodes.unshift(...created)
      await saveDb(db)
      sendJson(response, 201, { message: `已生成 ${created.length} 个金蛋兑换码。`, codes: created })
      return
    }

    if (request.method === 'POST' && path === '/api/feedback') {
      const body = await readJson(request)
      const message = String(body.message || '').trim()
      if (!message) {
        sendJson(response, 400, { error: '请先填写反馈内容。' })
        return
      }
      const user = userFromRequest(db, request)
      const feedback = normalizeFeedback({
        message,
        source: body.source || 'desktop',
        userId: user?.id || body.userId || '',
        userEmail: user?.email || body.userEmail || body.email || '',
        userName: user?.displayName || body.userName || body.name || '',
        appVersion: body.appVersion,
        deviceId: body.deviceId,
        localAccountId: body.localAccountId,
      })
      db.feedback.unshift(feedback)
      db.feedback = db.feedback.slice(0, 1000)
      db.events.unshift({
        id: `event-${randomUUID()}`,
        userId: feedback.userId,
        type: 'feedback_created',
        feedbackId: feedback.id,
        createdAt: feedback.createdAt,
      })
      db.events = db.events.slice(0, 100)
      await saveDb(db)
      sendJson(response, 201, { message: '反馈已提交，谢谢。', feedback: adminFeedbackItem(db, feedback) })
      return
    }

    const eggCodeStatusMatch = path.match(/^\/api\/admin\/egg-codes\/([^/]+)\/status$/)
    if (request.method === 'POST' && eggCodeStatusMatch) {
      if (!requireAdmin(request, response, url)) return
      const body = await readJson(request)
      const status = String(body.status || '').trim()
      if (!eggCodeStatuses.has(status)) {
        sendJson(response, 400, { error: '兑换码状态不正确。' })
        return
      }
      const code = normalizeEggCode(decodeURIComponent(eggCodeStatusMatch[1]))
      const entry = db.eggCodes.find((item) => item.code === code)
      if (!entry) {
        sendJson(response, 404, { error: '兑换码不存在。' })
        return
      }
      entry.status = status
      entry.disabledAt = status === 'disabled' ? now() : null
      await saveDb(db)
      sendJson(response, 200, { message: '兑换码状态已更新。', code: publicEggCode(entry) })
      return
    }

    if (request.method === 'POST' && path === '/api/auth/email-code') {
      const body = await readJson(request)
      const email = normalizeEmail(body.email)
      const purpose = String(body.purpose || 'register')
      if (!['register', 'reset_password'].includes(purpose)) {
        sendJson(response, 400, { error: '验证码用途不正确。' })
        return
      }
      if (!isValidEmail(email)) {
        sendJson(response, 400, { error: '请填写有效邮箱地址。' })
        return
      }
      const exists = db.users.some((user) => normalizeEmail(user.email) === email && user.passwordHash)
      if (purpose === 'register' && exists) {
        sendJson(response, 409, { error: '这个邮箱已经注册，请直接登录。' })
        return
      }
      if (purpose === 'reset_password' && !exists) {
        sendJson(response, 404, { error: '未找到该邮箱对应的注册账号。' })
        return
      }
      const cooldown = emailCodeCooldown(email, purpose)
      if (cooldown > 0) {
        sendJson(response, 429, { error: `验证码已生成，请 ${cooldown} 秒后再试。` })
        return
      }
      const devCode = issueEmailCode(email, purpose)
      if (logEmailCodes || allowDevEmailCode) {
        console.log(`[WindowPet auth] ${email} ${purpose} email code: ${devCode}`)
      }
      const sendResult = await sendEmailCode(email, devCode)
      if (!sendResult.ok) {
        sendJson(response, 503, { error: sendResult.error || '验证码邮件发送失败，请稍后再试。' })
        return
      }
      const payload = {
        ok: true,
        message: '验证码已发送，请去邮箱查看。',
        expiresInSeconds: Math.floor(emailCodeTtlMs / 1000),
      }
      if (allowDevEmailCode) {
        payload.devCode = devCode
      }
      sendJson(response, 200, payload)
      return
    }

    if (request.method === 'POST' && (path === '/api/auth/desktop-sync' || path === '/api/sync/desktop')) {
      const body = await readJson(request)
      const email = normalizeEmail(body.email || body.identity || '')
      const user = db.users.find((u) => normalizeEmail(u.email) === email)
      const userId = user ? user.id : (body.userId || 'guest')
      const isVip = Boolean(
        (user && user.isVip) ||
        (db.entitlements && db.entitlements.some((e) => (email && normalizeEmail(e.userEmail) === email) || (userId && e.userId === userId)))
      )
      sendJson(response, 200, {
        success: true,
        ok: true,
        isVip,
        allUnlocked: isVip,
        user: user ? publicUser(user, db) : null,
        sync: syncPayload(db, userId, body.deviceId || body.device_id)
      })
      return
    }

    if (request.method === 'POST' && path === '/api/auth/register') {
      const body = await readJson(request)
      const email = normalizeEmail(body.email)
      const name = String(body.name || '').trim()
      const password = String(body.password || '')
      const emailCode = String(body.emailCode || '').trim()

      if (!name || !email || !password || !emailCode) {
        sendJson(response, 400, { error: '请填写昵称、邮箱、密码和验证码。' })
        return
      }
      if (!isValidEmail(email)) {
        sendJson(response, 400, { error: '请填写有效邮箱地址。' })
        return
      }
      if (password.length < 6) {
        sendJson(response, 400, { error: '密码至少需要 6 位。' })
        return
      }
      if (db.users.some((user) => normalizeEmail(user.email) === email && user.passwordHash)) {
        sendJson(response, 409, { error: '这个邮箱已经注册，请直接登录。' })
        return
      }
      const codeCheck = verifyEmailCode(email, 'register', emailCode)
      if (!codeCheck.ok) {
        sendJson(response, 400, { error: codeCheck.error })
        return
      }

      const salt = randomBytes(16).toString('hex')
      const user = ensureUser(db, email, { name, provider: 'email' })
      user.displayName = name
      user.provider = 'email'
      user.salt = salt
      user.passwordHash = passwordHash(password, salt)
      user.updatedAt = now()
      const token = issueSession(user)
      await saveDb(db)
      sendJson(response, 201, {
        message: '注册成功，已登录。',
        token,
        user: publicUser(user),
      })
      return
    }

    if (request.method === 'POST' && path === '/api/auth/login') {
      const body = await readJson(request)
      const email = normalizeEmail(body.email)
      const password = String(body.password || '')
      if (!isValidEmail(email) || !password) {
        sendJson(response, 400, { error: '请填写邮箱和密码。' })
        return
      }
      const user = db.users.find((item) => normalizeEmail(item.email) === email)
      if (!user || !verifyPassword(user, password)) {
        sendJson(response, 401, { error: '邮箱或密码不正确。' })
        return
      }
      const token = issueSession(user)
      await saveDb(db)
      sendJson(response, 200, {
        message: '登录成功。',
        token,
        user: publicUser(user),
      })
      return
    }

    if (request.method === 'GET' && path === '/api/auth/me') {
      const user = requireUser(db, request, response)
      if (!user) return
      await saveDb(db)
      sendJson(response, 200, { user: publicUser(user) })
      return
    }

    if (request.method === 'POST' && path === '/api/auth/logout') {
      const token = authTokenFromRequest(request)
      const hash = tokenHash(token)
      const user = token ? userFromRequest(db, request) : null
      if (user) {
        user.sessions = (user.sessions || []).filter((session) => session.tokenHash !== hash)
        user.updatedAt = now()
        await saveDb(db)
      }
      sendJson(response, 200, { ok: true })
      return
    }

    if (request.method === 'GET' && path === '/api/campaign/egg-draw/status') {
      const user = requireUser(db, request, response)
      if (!user) return
      await saveDb(db)
      sendJson(response, 200, { status: eggStatus(db, user) })
      return
    }

    if (request.method === 'POST' && (path === '/api/campaign/egg-draw' || path === '/api/campaign/egg-redeem' || path === '/api/redeem')) {
      const user = requireUser(db, request, response)
      if (!user) return
      const body = await readJson(request)
      const result = redeemEggCode(db, user, body.code || body.inviteCode)
      if (result.error) {
        sendJson(response, 400, { error: result.error, status: eggStatus(db, user) })
        return
      }
      await saveDb(db)
      sendJson(response, 200, result)
      return
    }

    if (request.method === 'POST' && path === '/api/auth/mock-login') {
      if (!allowMockLogin) {
        sendJson(response, 404, { error: 'Not found' })
        return
      }
      const body = await readJson(request)
      const user = ensureUser(db, body.email)
      user.updatedAt = now()
      const token = issueSession(user)
      await saveDb(db)
      sendJson(response, 200, {
        token,
        user: publicUser(user),
      })
      return
    }

    if (request.method === 'POST' && path === '/api/auth/reset-password') {
      const body = await readBody(request)
      const email = normalizeEmail(body.email)
      const newPassword = String(body.newPassword || body.password || '')
      const emailCode = String(body.emailCode || '').trim()

      if (!isValidEmail(email)) {
        sendJson(response, 400, { error: '请填写有效邮箱地址。' })
        return
      }
      if (newPassword.length < 4) {
        sendJson(response, 400, { error: '密码长度至少为 4 位。' })
        return
      }
      const user = db.users.find((u) => normalizeEmail(u.email) === email)
      if (!user) {
        sendJson(response, 404, { error: '未找到该邮箱对应的账号。' })
        return
      }
      const verification = verifyEmailCode(email, 'reset_password', emailCode)
      if (!verification.ok) {
        sendJson(response, 400, { error: verification.error })
        return
      }
      user.salt = randomBytes(16).toString('hex')
      user.passwordHash = passwordHash(newPassword, user.salt)
      user.updatedAt = now()
      const token = issueSession(user)
      await saveDb(db)
      sendJson(response, 200, {
        ok: true,
        message: '密码重置成功，已自动为您登录。',
        token,
        user: publicUser(user, db),
      })
      return
    }

    // === 支付与订单系统 ===
    if (request.method === 'GET' && path === '/api/pay/plans') {
      sendJson(response, 200, {
        ok: true,
        plans: paymentPlans,
        defaultPlanId: 'plan_lifetime',
      })
      return
    }

    if (request.method === 'POST' && path === '/api/pay/order/create') {
      const body = await readBody(request)
      const planId = String(body.planId || 'plan_lifetime').trim()
      const plan = paymentPlans.find((p) => p.id === planId) || paymentPlans[0]
      const user = userFromRequest(db, request)
      const userId = user ? user.id : String(body.userId || '').trim()
      const userEmail = user ? user.email : normalizeEmail(body.userEmail || body.email || '')

      const orderId = `WP-${Date.now().toString(36).toUpperCase()}-${randomBytes(3).toString('hex').toUpperCase()}`
      const order = normalizeOrder({
        id: orderId,
        userId,
        userEmail,
        planId: plan.id,
        planName: plan.name,
        amount: plan.amount,
        currency: 'CNY',
        channel: 'alipay',
        status: 'pending',
        createdAt: now(),
        expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      })

      const alipayRes = await requestAlipayPrecreate(order)
      order.isSimulation = Boolean(alipayRes.simulation)
      order.qrCodeUrl = alipayRes.qrCodeUrl
      order.qrCodeSvg = await generateQrCodeSvg(order.qrCodeUrl)

      db.orders.unshift(order)
      await saveDb(db)
      sendJson(response, 200, {
        ok: true,
        orderId: order.id,
        order: publicOrder(order),
        isSimulation: order.isSimulation,
        simulation: order.isSimulation,
        qrCodeUrl: order.qrCodeUrl,
        warn: alipayRes.warn || null,
      })
      return
    }

    const orderStatusMatch = path.match(/^\/api\/pay\/order\/status\/([^/]+)$/)
    if (request.method === 'GET' && orderStatusMatch) {
      const orderId = decodeURIComponent(orderStatusMatch[1])
      const order = db.orders.find((o) => o.id === orderId)
      if (!order) {
        sendJson(response, 404, { error: '未找到订单。' })
        return
      }
      sendJson(response, 200, {
        ok: true,
        orderId: order.id,
        status: order.status,
        isPaid: order.status === 'paid',
        paidAt: order.paidAt,
        planId: order.planId,
        isSimulation: order.isSimulation,
      })
      return
    }

    const qrCodeMatch = path.match(/^\/api\/pay\/qrcode\/([^/]+)$/)
    if (request.method === 'GET' && qrCodeMatch) {
      const orderId = decodeURIComponent(qrCodeMatch[1])
      const order = db.orders.find((o) => o.id === orderId)
      if (!order) {
        sendJson(response, 404, { error: '未找到订单。' })
        return
      }
      const svg = order.qrCodeSvg || (await generateQrCodeSvg(order.qrCodeUrl || `https://windowpet.cn/pet/#pay-${order.id}`))
      response.writeHead(200, {
        'Content-Type': 'image/svg+xml; charset=utf-8',
        'Cache-Control': 'no-store',
        'Access-Control-Allow-Origin': '*',
      })
      response.end(svg)
      return
    }

    if (request.method === 'POST' && path === '/api/pay/alipay-notify') {
      const body = await readBody(request)
      const outTradeNo = String(body.out_trade_no || '').trim()
      const tradeStatus = String(body.trade_status || '').trim()
      const totalAmount = String(body.total_amount || '').trim()
      const tradeNo = String(body.trade_no || '').trim()
      const sign = String(body.sign || '').trim()

      console.log(`[Alipay notify] received for order ${outTradeNo}, status: ${tradeStatus}`)

      if (alipayPublicKeyRaw && sign) {
        const publicKeyPem = formatAlipayKey(alipayPublicKeyRaw, 'PUBLIC KEY')
        const verified = alipayRsa2Verify(body, sign, publicKeyPem)
        if (!verified) {
          console.error(`[Alipay notify] RSA2 signature verification failed for ${outTradeNo}`)
          response.writeHead(400, { 'Content-Type': 'text/plain' })
          response.end('fail')
          return
        }
      }

      const order = db.orders.find((o) => o.id === outTradeNo)
      if (!order) {
        console.error(`[Alipay notify] order not found: ${outTradeNo}`)
        response.writeHead(404, { 'Content-Type': 'text/plain' })
        response.end('fail')
        return
      }

      if (totalAmount && Number(totalAmount) !== Number(order.amount)) {
        console.error(`[Alipay notify] amount mismatch: expected ${order.amount}, got ${totalAmount}`)
        response.writeHead(400, { 'Content-Type': 'text/plain' })
        response.end('fail')
        return
      }

      if (tradeStatus === 'TRADE_SUCCESS' || tradeStatus === 'TRADE_FINISHED') {
        order.status = 'paid'
        order.paidAt = body.gmt_payment || now()
        order.tradeNo = tradeNo
        grantOrderEntitlement(db, order)
        await saveDb(db)
      }

      response.writeHead(200, { 'Content-Type': 'text/plain' })
      response.end('success')
      return
    }

    if (request.method === 'POST' && path === '/api/pay/order/mock-pay') {
      const body = await readBody(request)
      const orderId = String(body.orderId || '').trim()
      const order = db.orders.find((o) => o.id === orderId)
      if (!order) {
        sendJson(response, 404, { error: '未找到订单。' })
        return
      }
      if (order.status !== 'paid') {
        order.status = 'paid'
        order.paidAt = now()
        order.tradeNo = `MOCK-${Date.now()}-${randomBytes(4).toString('hex').toUpperCase()}`
        grantOrderEntitlement(db, order)
        await saveDb(db)
      }
      sendJson(response, 200, {
        ok: true,
        success: true,
        message: '模拟支付成功！已为您开通全角色特权。',
        order: publicOrder(order),
      })
      return
    }

    if (request.method === 'GET' && path === '/api/pay/my-entitlements') {
      const user = requireUser(db, request, response)
      if (!user) return
      const userEnts = db.entitlements.filter(
        (e) => e.userId === user.id || (user.email && normalizeEmail(e.userEmail) === normalizeEmail(user.email)),
      )
      const isVip = userEnts.some((e) => e.status === 'active')
      sendJson(response, 200, {
        ok: true,
        isVip,
        allUnlocked: isVip,
        entitlements: userEnts,
      })
      return
    }

    const syncMatch = path.match(/^\/api\/sync\/([^/]+)$/)
    if (request.method === 'GET' && syncMatch) {
      const userId = decodeURIComponent(syncMatch[1])
      sendJson(response, 200, syncPayload(db, userId, url.searchParams.get('deviceId')))
      return
    }

    const deviceMatch = path.match(/^\/api\/sync\/([^/]+)\/devices\/([^/]+)$/)
    if (request.method === 'PUT' && deviceMatch) {
      const userId = decodeURIComponent(deviceMatch[1])
      const deviceId = decodeURIComponent(deviceMatch[2])
      const body = await readJson(request)
      const state = upsertDeviceState(db, userId, deviceId, body)
      await saveDb(db)
      sendJson(response, 200, { state, sync: syncPayload(db, userId, deviceId) })
      return
    }

    const installMatch = path.match(/^\/api\/sync\/([^/]+)\/installations$/)
    if (request.method === 'POST' && installMatch) {
      const userId = decodeURIComponent(installMatch[1])
      const body = await readJson(request)
      const packageId = String(body.packageId || '')
      if (!db.packages.some((item) => item.id === packageId)) {
        sendJson(response, 400, { error: 'Unknown packageId' })
        return
      }
      const timestamp = now()
      let install = db.installs.find((item) => item.userId === userId && item.packageId === packageId)
      if (!install) {
        install = {
          id: `install-${randomUUID()}`,
          userId,
          packageId,
          packageVersion: String(body.packageVersion || '1.0.0'),
          installed: true,
          favorite: Boolean(body.favorite),
          nickname: String(body.nickname || ''),
          createdAt: timestamp,
          updatedAt: timestamp,
        }
        db.installs.push(install)
      } else {
        install.installed = body.installed !== false
        install.favorite = Boolean(body.favorite ?? install.favorite)
        install.nickname = String(body.nickname ?? install.nickname ?? '')
        install.updatedAt = timestamp
      }
      await saveDb(db)
      sendJson(response, 200, { install, sync: syncPayload(db, userId) })
      return
    }

    sendJson(response, 404, { error: 'Not found' })
  } catch (error) {
    sendJson(response, 400, { error: error instanceof Error ? error.message : 'Bad request' })
  }
}

createServer((request, response) => {
  handle(request, response).catch((error) => {
    sendJson(response, 500, { error: error instanceof Error ? error.message : 'Server error' })
  })
}).listen(port, '127.0.0.1', () => {
  console.log(`WindowPet mock cloud API running at http://127.0.0.1:${port}`)
})
