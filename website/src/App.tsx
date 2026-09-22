import { useEffect, useMemo, useState } from 'react'
import {
  AlarmClock,
  Camera,
  CheckCircle2,
  ChevronRight,
  Download,
  Heart,
  HelpCircle,
  MessageSquare,
  MousePointerClick,
  PawPrint,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  X,
} from 'lucide-react'
import './App.css'
import './polish.css'
import { galleryCategories, galleryPets, type GalleryPet } from './galleryData'

const releaseVersion = '1.0.32'
const releaseInstallerName = `WindowPet_Setup_v${releaseVersion}.exe`
const releaseInstallerHref = `https://github.com/panda008006/WindowPet/releases/download/v${releaseVersion}/${releaseInstallerName}`
const githubRepoUrl = 'https://github.com/panda008006/WindowPet'
const qqGroupUrl = 'https://qm.qq.com/q/cYlRBbvuda'

interface NavItem {
  id: 'home' | 'models' | 'custom' | 'tutorial' | 'faq'
  label: string
  badge?: string
}

const navItems: readonly NavItem[] = [
  { id: 'home', label: '首页' },
  { id: 'models', label: '模型库', badge: '24款' },
  { id: 'custom', label: '爱宠定制' },
  { id: 'tutorial', label: '使用教程' },
  { id: 'faq', label: '常见问题' },
] as const

type SectionId = (typeof navItems)[number]['id']

// 3 只精选代表萌宠用于首页动态展示
const heroShowcasePets = [
  {
    id: 'jiyi',
    name: '吉伊',
    badge: '人气担当',
    desc: '活泼元气，打开电脑时欢快挥手打招呼',
    image: 'pets/jiyi.png',
    actionImage: 'pets/jiyi-action-waving.webp',
    actions: [
      { label: '挥手问候', image: 'pets/jiyi-action-waving.webp', tip: '开机打招呼' },
      { label: '合奏协奏', image: 'pets/jiyi-action-concert.webp', tip: '欢快背景音' },
      { label: '害羞捂脸', image: 'pets/jiyi-action-shy.webp', tip: '点击小互动' },
    ],
  },
  {
    id: 'xiaochai',
    name: '小柴犬',
    badge: '治愈萌宠',
    desc: '摇尾巴摇出残影，专注蹲在屏幕边看着你',
    image: 'pets/xiaochai.png',
    actionImage: 'pets/xiaochai.png',
    actions: [
      { label: '摇尾示好', image: 'pets/xiaochai.png', tip: '忠诚陪伴' },
      { label: '乖乖坐好', image: 'pets/xiaochai.png', tip: '专注注视' },
      { label: '兴奋扑腾', image: 'pets/xiaochai.png', tip: '完成任务庆祝' },
    ],
  },
  {
    id: 'fox',
    name: '狐狸',
    badge: '灵敏互动',
    desc: '大尾巴随节拍晃动，支持羽毛逗弄与状态反馈',
    image: 'pets/fox.png',
    actionImage: 'pets/fox-action-waving.webp',
    actions: [
      { label: '翘尾致意', image: 'pets/fox-action-waving.webp', tip: '待机轻晃' },
      { label: '羽毛逗弄', image: 'pets/fox-action-feather.webp', tip: '灵敏歪头' },
      { label: '工具反馈', image: 'pets/fox-action-whip.webp', tip: '受击翻滚' },
    ],
  },
]

const faqItems = [
  {
    q: '为什么首次在 Windows 运行会提示“未知发布者”？',
    a: 'WindowPet 是个人大学毕业开源心血之作，尚未向商业认证机构购买昂贵的代码数字签名（每年需数千元）。本项目已在 GitHub 100% 全量开源、绿色透明，绝无任何后门或恶意行为。首次运行时只需点击【更多信息】并选择【仍要运行】即可放心使用。',
  },
  {
    q: '运行该软件会占用很多电脑 CPU 或内存吗？',
    a: '完全不会！新版 1.0.32 经过深度重构与体积优化，无任何冗余大视频占用。待机 CPU 占用率接近 0%，内存常驻仅约 30~50MB，即使在后台全天开启，玩 3A 游戏、写代码或办公也不会有丝毫卡顿。',
  },
  {
    q: '支持双显示器、带鱼屏或不同屏幕缩放（高 DPI）吗？',
    a: '完美支持！WindowPet 具备智能屏幕边界检测引擎，您可以将萌宠自由拖拽到副屏、主屏底部或任务栏上方，并完美适配 Windows 100% ~ 250% 显示缩放。',
  },
  {
    q: '所有 24 款角色都是完全免费的吗？如何更新？',
    a: '100% 永久免费开放！所有内置角色与动画均开箱可用，无需注册登录或付费。每次新版本发布时，访问官网或 GitHub Releases 页面下载新安装包直接覆盖安装即可，您的角色设置会自动继承保全。',
  },
  {
    q: '我可以自己制作专属角色并向社区投稿吗？',
    a: '非常欢迎！WindowPet 秉承开源共建原则（MIT 协议），无论您是画师、动画爱好者还是普通玩家，欢迎加入官方 QQ 交流群获取标准动作帧切片规范，共建小鼻嘎开源角色大家族！',
  },
]

function petAsset(path: string) {
  if (!path) return ''
  if (path.startsWith('http') || path.startsWith('/')) return path
  const base = import.meta.env.BASE_URL
  const cleanPath = path.startsWith('./') ? path.slice(2) : path
  return `${base}${cleanPath}`
}

export function App() {
  const [activeSection, setActiveSection] = useState<SectionId>('home')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // 首页精选萌宠交互状态
  const [heroPetIndex, setHeroPetIndex] = useState(0)
  const [heroActionIndex, setHeroActionIndex] = useState(0)

  // 模型库筛选与搜索状态
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // 角色动作试玩弹窗状态
  const [previewPet, setPreviewPet] = useState<GalleryPet | null>(null)
  const [previewActionIndex, setPreviewActionIndex] = useState(0)
  const [copyCodeToast, setCopyCodeToast] = useState(false)

  // FAQ 展开状态
  const [expandedFaq, setExpandedFaq] = useState<number | null>(0)

  // 滚动监听（ScrollSpy），自动高亮顶栏对应标签
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY + 180
      for (let i = navItems.length - 1; i >= 0; i--) {
        const el = document.getElementById(navItems[i].id)
        if (el && el.offsetTop <= scrollY) {
          setActiveSection(navItems[i].id)
          break
        }
      }
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // 监听 ESC 关闭试玩弹窗
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && previewPet) {
        setPreviewPet(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [previewPet])

  const scrollToSection = (id: SectionId) => {
    setMobileMenuOpen(false)
    const el = document.getElementById(id)
    if (el) {
      const topOffset = el.getBoundingClientRect().top + window.scrollY - 72
      window.scrollTo({ top: topOffset, behavior: 'smooth' })
    }
  }

  // 过滤后的模型列表
  const filteredPets = useMemo(() => {
    return galleryPets.filter((pet) => {
      const matchCat = selectedCategory === 'all' || pet.category === selectedCategory
      const matchSearch =
        !searchQuery.trim() ||
        pet.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pet.enName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pet.description.toLowerCase().includes(searchQuery.toLowerCase())
      return matchCat && matchSearch
    })
  }, [selectedCategory, searchQuery])

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopyCodeToast(true)
    setTimeout(() => setCopyCodeToast(false), 2000)
  }

  const currentHeroPet = heroShowcasePets[heroPetIndex]
  const currentHeroAction = currentHeroPet.actions[heroActionIndex] || currentHeroPet.actions[0]

  return (
    <div className="bongo-site-container">
      {/* 顶部常驻磨砂吸顶导航栏 */}
      <header className="site-nav">
        <div className="site-nav-left">
          <button
            className="brand-lockup"
            type="button"
            onClick={() => scrollToSection('home')}
            aria-label="返回首页"
          >
            <span className="brand-symbol">
              <PawPrint size={20} color="#126ad6" />
            </span>
            <div className="brand-text">
              <strong>WindowPet</strong>
              <small>桌面伙伴社区</small>
            </div>
          </button>
        </div>

        <nav className="site-nav-center" aria-label="官网导航">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`site-nav-link ${activeSection === item.id ? 'is-active' : ''}`}
              onClick={() => scrollToSection(item.id)}
            >
              {item.label}
              {item.badge && <span className="nav-badge-pill">{item.badge}</span>}
            </button>
          ))}
        </nav>

        <div className="site-nav-right">
          <a
            className="nav-community-link"
            href={qqGroupUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="加入 WindowPet 官方 QQ 交流群"
          >
            <MessageSquare size={15} />
            <span>官方群</span>
          </a>

          <a
            className="nav-star-btn"
            href={githubRepoUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="在 GitHub 上点亮 Star 支持"
          >
            <Star size={14} fill="currentColor" />
            <span>Star</span>
          </a>

          <a
            className="nav-download-btn"
            href={releaseInstallerHref}
            download={releaseInstallerName}
            title="下载 Windows 安装包"
          >
            <Download size={15} />
            <span>免费下载 (50MB)</span>
          </a>

          {/* 移动端汉堡菜单按钮 */}
          <button
            className="mobile-menu-toggle"
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="切换菜单"
          >
            {mobileMenuOpen ? <X size={20} /> : <ChevronRight size={20} />}
          </button>
        </div>
      </header>

      {/* 移动端折叠导航抽屉 */}
      {mobileMenuOpen && (
        <div className="mobile-nav-drawer">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`mobile-nav-item ${activeSection === item.id ? 'is-active' : ''}`}
              onClick={() => scrollToSection(item.id)}
            >
              <span>{item.label}</span>
              {item.badge && <span className="nav-badge-pill">{item.badge}</span>}
            </button>
          ))}
          <div className="mobile-drawer-actions">
            <a className="mobile-action-btn qq" href={qqGroupUrl} target="_blank" rel="noopener noreferrer">
              <MessageSquare size={16} /> 官方 QQ 交流群
            </a>
            <a className="mobile-action-btn github" href={githubRepoUrl} target="_blank" rel="noopener noreferrer">
              <Star size={16} fill="currentColor" /> GitHub 开源仓库
            </a>
            <a className="mobile-action-btn download" href={releaseInstallerHref} download={releaseInstallerName}>
              <Download size={16} /> 免费下载 Windows 版 (50MB)
            </a>
          </div>
        </div>
      )}

      {/* 主体长滚动模块内容 */}
      <main className="bongo-main-flow">
        {/* ==================== 1. 首页 (Hero Section) ==================== */}
        <section className="site-section hero-section" id="home">
          <div className="section-inner hero-grid">
            <div className="hero-copy">
              <div className="hero-badge">
                <span className="pulse-dot" />
                <span>永久开源免费 · 仅 50MB 极速秒开 · 24 款萌宠全内置</span>
              </div>

              <h1 className="hero-heading">
                新一代超轻量
                <br />
                <span className="hero-gradient-text">桌面动态伙伴宠</span>
              </h1>

              <p className="hero-desc">
                告别数百兆笨重体积，毫秒级轻快响应！基于现代响应式架构打造，支持 24
                款萌宠自由换乘、屏幕边缘吸附漫步、丰富按键动作与贴心番茄钟提醒，低资源占用零打扰。
              </p>

              <div className="hero-actions">
                <a className="hero-btn-primary" href={releaseInstallerHref} download={releaseInstallerName}>
                  <Download size={18} />
                  <span>下载 Windows 安装包 (仅 50MB)</span>
                </a>
                <button
                  type="button"
                  className="hero-btn-secondary"
                  onClick={() => scrollToSection('models')}
                >
                  <PawPrint size={17} />
                  <span>浏览 24 款模型库 ↓</span>
                </button>
                <a
                  className="hero-btn-ghost"
                  href={qqGroupUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <MessageSquare size={17} />
                  <span>加入 QQ 官方群</span>
                </a>
              </div>

              <div className="hero-stats-row">
                <div className="stat-item">
                  <strong>24 只</strong>
                  <span>开箱即玩萌宠</span>
                </div>
                <div className="stat-item">
                  <strong>~50 MB</strong>
                  <span>极简小安装包</span>
                </div>
                <div className="stat-item">
                  <strong>0 元</strong>
                  <span>永久免费开源</span>
                </div>
                <div className="stat-item">
                  <strong>&lt;1%</strong>
                  <span>待机 CPU 占用</span>
                </div>
              </div>
            </div>

            {/* Hero 右侧互动展台 */}
            <div className="hero-interactive-stage">
              <div className="stage-window-card">
                <div className="stage-toolbar">
                  <div className="stage-dots">
                    <span />
                    <span />
                    <span />
                  </div>
                  <span className="stage-title">WindowPet 实时动态预览</span>
                </div>

                <div className="stage-body">
                  <div className="stage-art-display">
                    <img
                      key={`${currentHeroPet.id}-${heroActionIndex}`}
                      src={petAsset(currentHeroAction.image)}
                      alt={`${currentHeroPet.name} 动作预览`}
                      className="stage-pet-avatar"
                    />
                    <div className="stage-pet-tagline">
                      <strong>{currentHeroPet.name}</strong>
                      <span>{currentHeroAction.tip}</span>
                    </div>
                  </div>

                  {/* 动作切换按钮组 */}
                  <div className="stage-actions-shelf">
                    <small>动作试看：</small>
                    <div className="stage-action-pills">
                      {currentHeroPet.actions.map((act, idx) => (
                        <button
                          key={act.label}
                          type="button"
                          className={`action-pill ${heroActionIndex === idx ? 'is-active' : ''}`}
                          onClick={() => setHeroActionIndex(idx)}
                        >
                          {act.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 代表萌宠选择器 */}
                  <div className="stage-pet-selector">
                    {heroShowcasePets.map((pet, idx) => (
                      <button
                        key={pet.id}
                        type="button"
                        className={`pet-tab-btn ${heroPetIndex === idx ? 'is-active' : ''}`}
                        onClick={() => {
                          setHeroPetIndex(idx)
                          setHeroActionIndex(0)
                        }}
                      >
                        <img src={petAsset(pet.image)} alt={pet.name} />
                        <div>
                          <strong>{pet.name}</strong>
                          <small>{pet.badge}</small>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ==================== 2. 模型库 (Models Section) ==================== */}
        <section className="site-section models-section" id="models">
          <div className="section-inner">
            <div className="section-heading text-center">
              <p className="eyebrow">MODELS REPOSITORY</p>
              <h2>小鼻嘎模型库 · 24 款萌宠全收录</h2>
              <p>
                对标 BongoCat 开放模型生态，所有角色 100% 永久免费内置，支持自由换宠、动作试玩与画师民间共建。点击卡片即刻预览生动动作。
              </p>
            </div>

            {/* 筛选与搜索工具条 */}
            <div className="models-toolbar">
              <div className="category-chips-wrap">
                {galleryCategories.map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    className={`cat-chip ${selectedCategory === cat.id ? 'is-active' : ''}`}
                    onClick={() => setSelectedCategory(cat.id)}
                  >
                    <span>{cat.label}</span>
                    <small>{cat.count}</small>
                  </button>
                ))}
              </div>

              <div className="models-search-box">
                <Search size={16} className="search-icon" />
                <input
                  type="text"
                  placeholder="搜索萌宠：吉伊、柴犬、卡皮巴拉、fox..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {searchQuery && (
                  <button type="button" className="clear-btn" onClick={() => setSearchQuery('')}>
                    <X size={14} />
                  </button>
                )}
              </div>
            </div>

            {/* 24 款萌宠卡片网格 */}
            <div className="models-grid">
              {filteredPets.map((pet) => (
                <div
                  key={pet.id}
                  className="model-card"
                  onClick={() => {
                    setPreviewPet(pet)
                    setPreviewActionIndex(0)
                  }}
                >
                  <div className="card-top-bar">
                    <span className={`rarity-badge rarity-${pet.rarity.toLowerCase()}`}>{pet.rarity}</span>
                    <span className="card-cat-label">{pet.categoryLabel}</span>
                  </div>

                  <div className="card-avatar-wrap">
                    <img src={petAsset(pet.image)} alt={pet.name} className="card-avatar" />
                  </div>

                  <div className="card-body">
                    <div className="card-name-row">
                      <strong>{pet.name}</strong>
                      <span className="card-en">{pet.enName}</span>
                    </div>
                    <p className="card-tagline">{pet.tagline}</p>

                    <div className="card-action-tags">
                      {pet.actions.slice(0, 3).map((act) => (
                        <span key={act.id} className="act-tag">
                          {act.label}
                        </span>
                      ))}
                      {pet.actions.length > 3 && <span className="act-tag more">+{pet.actions.length - 3}</span>}
                    </div>

                    <button type="button" className="card-preview-btn">
                      <Sparkles size={14} />
                      <span>试看动作详情</span>
                      <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {filteredPets.length === 0 && (
              <div className="models-empty">
                <PawPrint size={42} color="#94a3b8" />
                <p>没有找到匹配的角色，试试其他关键词吧~</p>
                <button type="button" onClick={() => setSearchQuery('')}>
                  清除搜索条件
                </button>
              </div>
            )}
          </div>
        </section>

        {/* ==================== 3. 爱宠定制 (Custom Section) ==================== */}
        <section className="site-section custom-section" id="custom">
          <div className="section-inner">
            <div className="section-heading text-center">
              <p className="eyebrow">CUSTOM PET STUDIO</p>
              <h2>把自家的毛孩子，做成电脑桌面伙伴</h2>
              <p>
                喜欢你家猫咪踩奶、狗狗摇尾巴的乖巧模样吗？专属画师一对一动作还原，支持待机、走动、睡觉与被逗弄全套动作！
              </p>
            </div>

            <div className="custom-steps-grid">
              <div className="custom-step-card">
                <div className="step-num">01</div>
                <div className="step-icon-wrap">
                  <Camera size={26} color="#126ad6" />
                </div>
                <h3>拍照收集日常照片</h3>
                <p>
                  只需提供 3~5 张毛孩子日常生活抓拍照（正面呆萌、侧脸玩耍、伸懒腰或趴卧睡姿），标注性格特色。
                </p>
              </div>

              <div className="custom-step-card">
                <div className="step-num">02</div>
                <div className="step-icon-wrap">
                  <Heart size={26} color="#e11d48" />
                </div>
                <h3>画师逐帧纯手绘还原</h3>
                <p>
                  专属画师进行高精度像素/矢量重绘，还原 5~8 组专属交互动作帧，赋予它独特的屏幕生命力。
                </p>
              </div>

              <div className="custom-step-card">
                <div className="step-num">03</div>
                <div className="step-icon-wrap">
                  <CheckCircle2 size={26} color="#059669" />
                </div>
                <h3>进群验收与一键导入</h3>
                <p>
                  在官方 QQ 交流群透明沟通制作进度，满意验收后生成独一无二的兑换码，客户端内输入直接导入桌面！
                </p>
              </div>
            </div>

            {/* 定制预约 CTA 卡片 */}
            <div className="custom-cta-banner">
              <div className="cta-content">
                <span className="cta-badge">OFFICIAL COMMUNITY</span>
                <h3>官方交流群现已开放预约通道</h3>
                <p>画师一对一沟通细节，进度公开透明，支持验收满意后再交付，快来为心爱的毛孩子定制吧！</p>
              </div>
              <a className="cta-btn" href={qqGroupUrl} target="_blank" rel="noopener noreferrer">
                <MessageSquare size={18} />
                <span>立即预约定制 / 进群交流 (QQ: cYlRBbvuda)</span>
              </a>
            </div>
          </div>
        </section>

        {/* ==================== 4. 使用教程 (Tutorial Section) ==================== */}
        <section className="site-section tutorial-section" id="tutorial">
          <div className="section-inner">
            <div className="section-heading text-center">
              <p className="eyebrow">TUTORIAL & SHORTCUTS</p>
              <h2>简单 3 步，在桌面上玩转它</h2>
              <p>免除繁琐配置，双击即玩；统一的交互规则与贴心的日常效率小工具，让桌面不再是单调的背景。</p>
            </div>

            <div className="tutorial-cards-grid">
              <div className="tutorial-card">
                <div className="tut-icon-box">
                  <MousePointerClick size={24} color="#126ad6" />
                </div>
                <h3>🐾 基础交互与边缘探头</h3>
                <ul className="tut-list">
                  <li>
                    <strong>左键单击：</strong>抚摸、逗弄它，触发害羞、合奏等可爱动作反馈；
                  </li>
                  <li>
                    <strong>右键菜单：</strong>随时切换 24 款角色、调节大小（50%~200%）或保持置顶；
                  </li>
                  <li>
                    <strong>长按拖拽：</strong>随意拖到屏幕底端或两侧边缘，它会自动趴在任务栏或吸附漫步！
                  </li>
                </ul>
              </div>

              <div className="tutorial-card">
                <div className="tut-icon-box">
                  <ShieldCheck size={24} color="#059669" />
                </div>
                <h3>⚡ 快捷键与老板键避让</h3>
                <ul className="tut-list">
                  <li>
                    <strong>Ctrl + H 老板键：</strong>一键瞬间隐藏到右下角托盘，工作学习安心无忧；
                  </li>
                  <li>
                    <strong>全屏智能避让：</strong>玩全屏 3A 游戏或观影时自动休眠，绝不遮挡视线与掉帧；
                  </li>
                  <li>
                    <strong>极简控制台 (Cockpit)：</strong>单窗口预览所有动作反应、检查版本更新与切换角色。
                  </li>
                </ul>
              </div>

              <div className="tutorial-card">
                <div className="tut-icon-box">
                  <AlarmClock size={24} color="#d97706" />
                </div>
                <h3>⏰ 日常健康与专注提醒</h3>
                <ul className="tut-list">
                  <li>
                    <strong>喝水与久坐提醒：</strong>设定时间间隔，萌宠在桌面轻快弹窗提醒起身喝水活动；
                  </li>
                  <li>
                    <strong>番茄钟工作法：</strong>陪伴你高效专注工作 25 分钟，完成后欢呼跳跃庆祝；
                  </li>
                  <li>
                    <strong>桌面临时备忘录：</strong>随手记下一天的三件小事，不再忘掉任何关键安排。
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* ==================== 5. 常见问题 (FAQ Section) ==================== */}
        <section className="site-section faq-section" id="faq">
          <div className="section-inner">
            <div className="section-heading text-center">
              <p className="eyebrow">HELP & FAQ</p>
              <h2>常见疑问与安全答疑</h2>
              <p>开源透明，绿色安全，解答您在使用与运行过程中的所有顾虑。</p>
            </div>

            <div className="faq-list">
              {faqItems.map((item, idx) => {
                const isOpen = expandedFaq === idx
                return (
                  <div key={item.q} className={`faq-card ${isOpen ? 'is-open' : ''}`}>
                    <button
                      type="button"
                      className="faq-question-btn"
                      onClick={() => setExpandedFaq(isOpen ? null : idx)}
                    >
                      <HelpCircle size={18} className="faq-icon" />
                      <span>{item.q}</span>
                      <ChevronRight size={18} className="faq-arrow" />
                    </button>
                    {isOpen && (
                      <div className="faq-answer">
                        <p>{item.a}</p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        {/* ==================== 底部下载与安全说明 Banner ==================== */}
        <section className="site-section cta-download-section">
          <div className="section-inner download-cta-box">
            <h2>准备好开启你的桌面陪伴了吗？</h2>
            <p>Windows 10 / 11 完美兼容 · 仅 50MB · 全量 24 款萌宠开箱即用 · 100% 永久免费开源</p>
            <div className="download-cta-actions">
              <a className="main-download-btn" href={releaseInstallerHref} download={releaseInstallerName}>
                <Download size={20} />
                <span>立即下载 Windows 正式版安装包</span>
              </a>
              <a className="secondary-repo-btn" href={githubRepoUrl} target="_blank" rel="noopener noreferrer">
                <Star size={18} fill="currentColor" />
                <span>前往 GitHub 查看开源代码</span>
              </a>
            </div>
            <div className="security-subtext">
              <span>🔒 纯净绿色无广告 · 无任何弹窗骚扰 · 不上传任何用户个人数据</span>
            </div>
          </div>
        </section>
      </main>

      {/* ==================== 底部 Footer ==================== */}
      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-brand-col">
            <div className="footer-logo">
              <PawPrint size={22} color="#126ad6" />
              <strong>WindowPet</strong>
            </div>
            <p>大学毕业独立开源心愿之作 · 超轻量桌面伙伴生态社区</p>
            <small>© 2026 WindowPet Community. Released under the MIT License.</small>
          </div>

          <div className="footer-links-col">
            <strong>快速导航</strong>
            <button type="button" onClick={() => scrollToSection('home')}>
              官网首页
            </button>
            <button type="button" onClick={() => scrollToSection('models')}>
              24款模型库
            </button>
            <button type="button" onClick={() => scrollToSection('custom')}>
              毛孩子专属定制
            </button>
            <button type="button" onClick={() => scrollToSection('tutorial')}>
              快速上手教程
            </button>
            <button type="button" onClick={() => scrollToSection('faq')}>
              常见问题 FAQ
            </button>
          </div>

          <div className="footer-community-col">
            <strong>社区与支持</strong>
            <a href={githubRepoUrl} target="_blank" rel="noopener noreferrer">
              GitHub 仓库 (Star 支持)
            </a>
            <a href={`${githubRepoUrl}/releases`} target="_blank" rel="noopener noreferrer">
              版本发布日志 (Releases)
            </a>
            <a href={qqGroupUrl} target="_blank" rel="noopener noreferrer">
              官方 QQ 交流群 (预约与答疑)
            </a>
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer" className="footer-icp-link">
              桂ICP备2026009615号-2
            </a>
          </div>
        </div>
      </footer>

      {/* ==================== 角色动作试看弹窗 (Modal) ==================== */}
      {previewPet && (
        <div className="pet-preview-modal-overlay" onClick={() => setPreviewPet(null)}>
          <div className="pet-preview-dialog" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="dialog-close-btn"
              onClick={() => setPreviewPet(null)}
              title="关闭 (ESC)"
            >
              <X size={18} />
            </button>

            <div className="dialog-header">
              <span className={`rarity-badge rarity-${previewPet.rarity.toLowerCase()}`}>
                {previewPet.rarity}
              </span>
              <h3>{previewPet.name}</h3>
              <span className="dialog-en">{previewPet.enName}</span>
              <span className="dialog-cat">{previewPet.categoryLabel}</span>
            </div>

            <div className="dialog-body">
              <div className="dialog-stage">
                <img
                  src={petAsset(previewPet.image)}
                  alt={previewPet.name}
                  className="dialog-avatar"
                />
                <p className="dialog-tagline">{previewPet.tagline}</p>
              </div>

              <div className="dialog-info">
                <strong>选择动作即时试看：</strong>
                <div className="dialog-action-chips">
                  {previewPet.actions.map((act, idx) => (
                    <button
                      key={act.id}
                      type="button"
                      className={`dialog-act-chip ${previewActionIndex === idx ? 'is-active' : ''}`}
                      onClick={() => setPreviewActionIndex(idx)}
                    >
                      {act.label}
                    </button>
                  ))}
                </div>

                {previewPet.actions[previewActionIndex] && (
                  <div className="dialog-act-detail">
                    <strong>动作【{previewPet.actions[previewActionIndex].label}】：</strong>
                    <span>{previewPet.actions[previewActionIndex].description}</span>
                  </div>
                )}

                <div className="dialog-desc">
                  <p>{previewPet.description}</p>
                </div>

                <div className="dialog-code-box">
                  <div>
                    <small>角色导入兑换码：</small>
                    <code>{previewPet.redeemCode}</code>
                  </div>
                  <button
                    type="button"
                    className="copy-code-btn"
                    onClick={() => handleCopyCode(previewPet.redeemCode)}
                  >
                    {copyCodeToast ? '已复制！' : '一键复制'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
