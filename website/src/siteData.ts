import type { LucideIcon } from 'lucide-react'

export type IconName =
  | 'badge-check'
  | 'bell'
  | 'clipboard-check'
  | 'database'
  | 'download'
  | 'file-archive'
  | 'file-code'
  | 'layout-dashboard'
  | 'mail'
  | 'monitor-smartphone'
  | 'package'
  | 'paw-print'
  | 'scan-search'
  | 'server'
  | 'shield'
  | 'sparkles'
  | 'store'
  | 'truck'
  | 'upload'
  | 'user-check'
  | 'users'
  | 'wechat'

export type SiteIcon = LucideIcon

export type PetPack = {
  id: string
  name: string
  tagline: string
  image: string
  description: string
  tags: string[]
  version: string
  fileName: string
  fileSize: string
  folderName: string
  assetType: 'frame_animation'
  canvas: string
  frameCount: number
  actionCount: number
  actionKeys: string[]
  idleVariants: string[]
  accessoryKeys: string[]
  previewFrame: string
  owner: string
}

export const navItems = [
  { label: '下载', href: '#download' },
  { label: '账号', href: '#account' },
  { label: '活动', href: '#campaign' },
  { label: '角色展示', href: '#store' },
  { label: '我的资源', href: '#library' },
  { label: '云同步', href: '#sync' },
  { label: '控制台', href: '#admin' },
]

export const petPacks: PetPack[] = [
  {
    id: 'jiyi',
    name: '吉伊',
    tagline: '轻快互动与合奏哼唱',
    image: '/pet/pets/jiyi.png',
    description: '吉伊是当前桌面端的高表现力主角，覆盖悬停、点击、拖拽、奔跑、害羞反应、合奏哼唱和桌面边缘动作，适合放在官网首屏做品牌记忆点。',
    tags: ['主推角色', '动作丰富', '桌面互动'],
    version: '1.0.14',
    fileName: 'jiyi.wpet',
    fileSize: '3.10 MB',
    folderName: 'JiyiPet',
    assetType: 'frame_animation',
    canvas: '192x208',
    frameCount: 69,
    actionCount: 29,
    actionKeys: [
      'idle',
      'hover',
      'click',
      'drag',
      'waiting',
      'waving',
      'running',
      'review',
      'concert-hum',
      'feather-tickle',
      'whip-hit',
      'edge-crawl',
    ],
    idleVariants: ['waiting', 'waving', 'review', 'running'],
    accessoryKeys: [],
    previewFrame: 'jiyi_01.png',
    owner: 'Window Pet 官方角色',
  },
  {
    id: 'kukukaka',
    name: '库库咔咔',
    tagline: '清爽灵动，适合做日常陪伴',
    image: '/pet/pets/kukukaka.png',
    description: '库库咔咔来自桌面端 KumikoPet 资源，动作节奏干净，适合展示登录后添加资源、授权下载和云端同步这些基础流程。',
    tags: ['陪伴主角', '动作清爽', '流程演示'],
    version: '1.0.14',
    fileName: 'kukukaka.wpet',
    fileSize: '3.02 MB',
    folderName: 'KumikoPet',
    assetType: 'frame_animation',
    canvas: '192x208',
    frameCount: 69,
    actionCount: 12,
    actionKeys: ['idle', 'hover', 'click', 'drag', 'waiting', 'waving', 'jumping', 'failed', 'running', 'running-left', 'running-right', 'review'],
    idleVariants: ['waiting', 'waving'],
    accessoryKeys: [],
    previewFrame: 'kumiko_01.png',
    owner: 'Window Pet 官方角色',
  },
  {
    id: 'fox',
    name: '狐狸',
    tagline: '小狐反应灵敏，适合突出桌面工具互动',
    image: '/pet/pets/fox.png',
    description: '狐狸使用 HuhuPet 的小狐资源，已具备羽毛逗弄和抽鞭子命中反应，适合承接桌面工具、动作反馈和高级感视觉展示。',
    tags: ['狐狸主角', '工具互动', '反馈明确'],
    version: '1.0.14',
    fileName: 'fox.wpet',
    fileSize: '2.65 MB',
    folderName: 'HuhuPet',
    assetType: 'frame_animation',
    canvas: '192x208',
    frameCount: 69,
    actionCount: 15,
    actionKeys: ['idle', 'hover', 'click', 'drag', 'waiting', 'waving', 'jumping', 'failed', 'running', 'running-left', 'running-right', 'review', 'reward', 'feather-tickle', 'whip-hit'],
    idleVariants: ['running', 'waving'],
    accessoryKeys: [],
    previewFrame: 'huhu_01.png',
    owner: 'Window Pet 官方角色',
  },
]

export const heroPets = ['jiyi', 'kukukaka', 'fox']

export const mvpModules = [
  {
    icon: 'mail' as IconName,
    title: '邮箱账号',
    text: '邮箱验证码注册、密码登录和会话令牌已经接到本地 Mock Cloud API。',
  },
  {
    icon: 'sparkles' as IconName,
    title: '活动领取',
    text: '敲金蛋活动改为后台生成兑换码，用户登录后输入兑换码领取免费权益。',
  },
  {
    icon: 'package' as IconName,
    title: '角色展示',
    text: '当前页面重点展示吉伊、库库咔咔、狐狸三位主角的预览图、动作信息和下载入口。',
  },
  {
    icon: 'download' as IconName,
    title: '资源下载',
    text: '角色资源页保留文件名、版本、尺寸和下载令牌说明，用于后续对接真实文件分发。',
  },
  {
    icon: 'layout-dashboard' as IconName,
    title: '控制台预览',
    text: '控制台继续保留，用来展示资源记录、同步状态和后续后台管理结构。',
  },
]

export const adminMetrics = [
  { icon: 'users' as IconName, label: '体验用户', value: '128', note: '本地演示数据' },
  { icon: 'package' as IconName, label: '展示角色', value: '3', note: '吉伊 / 库库咔咔 / 狐狸' },
  { icon: 'download' as IconName, label: '下载记录', value: '36', note: '演示统计' },
  { icon: 'scan-search' as IconName, label: '待整理事项', value: '1', note: '后续扩展' },
]

export const adminMenu = ['仪表盘', '兑换码管理', '角色资源', '下载记录', '同步状态', '内容整理', '更新日志']

export const reviewQueue = [
  {
    name: '吉伊资源包',
    owner: 'Window Pet 官方角色',
    status: '已整理',
    action: '检查封面图和文件信息',
  },
  {
    name: '库库咔咔资源包',
    owner: 'Window Pet 官方角色',
    status: '已整理',
    action: '检查预览图和动作说明',
  },
  {
    name: '狐狸资源包',
    owner: 'Window Pet 官方角色',
    status: '已整理',
    action: '查看下载记录',
  },
]

export const callbackSafety = [
  '真实文件下载仍应通过服务端接口控制',
  '记录号和文件令牌需要和具体角色资源对应',
  '下载令牌应有时效限制，避免公开页面直接暴露真实文件地址',
  '更新清单文件需要和客户端版本保持一致',
  '密钥和真实配置只放服务器环境变量，不进入前端包',
]

export const roadmapRows = [
  {
    module: '邮箱账号系统',
    mvp: 'Mock Cloud API 已支持邮箱验证码注册、密码登录和会话令牌；微信仍为本地演示',
    real: '接真实邮件服务、正式数据库、风控和微信开放平台网站应用',
  },
  {
    module: '活动中心',
    mvp: 'Mock Cloud API 已支持兑换码库存、兑换记录、后台批量生成和启停状态',
    real: '接正式活动配置后台、奖池库存、风控和运营数据看板',
  },
  {
    module: '角色资源页',
    mvp: '当前先展示吉伊、库库咔咔、狐狸三位主角',
    real: '后续接入更多角色、筛选、分类和版本管理',
  },
  {
    module: '下载文件',
    mvp: '页面展示文件名、版本、帧数、动作和资源尺寸',
    real: '对象存储私有桶，后端签发 5-10 分钟短链',
  },
  {
    module: '云同步',
    mvp: '继续保留当前设备状态上传和恢复演示',
    real: '接真实数据库、账号体系和设备同步逻辑',
  },
]
