import { useEffect, useMemo, useRef, useState, type WheelEventHandler } from 'react'
import {
  AlarmClock,
  Award,
  BellRing,
  CalendarCheck,
  Camera,
  CheckCircle2,
  ChevronDown,
  Download,
  EyeOff,
  FileArchive,
  Gift,
  HeartHandshake,
  LockKeyhole,
  MousePointerClick,
  PawPrint,
  RotateCw,
  Settings2,
  Sparkles,
} from 'lucide-react'
import './App.css'
import './polish.css'
import { PetGallery } from './PetGallery'

const releaseVersion = '1.0.32'
const releaseInstallerName = `WindowPet_Setup_v${releaseVersion}.exe`
const releaseInstallerHref = `https://github.com/panda008006/WindowPet/releases/download/v${releaseVersion}/${releaseInstallerName}`
const githubRepoUrl = 'https://github.com/panda008006/WindowPet'

const sectionIds = ['home', 'pets', 'features', 'custom', 'control'] as const

const sectionDots = [
  { id: 'home', label: '首页' },
  { id: 'pets', label: '角色' },
  { id: 'features', label: '功能' },
  { id: 'custom', label: '爱宠定制' },
  { id: 'control', label: '下载' },
] as const

const pets = [
  {
    id: 'jiyi',
    code: '0006',
    name: '吉伊',
    folderName: '人气主角',
    title: '轻快活泼，适合每天陪着你',
    intro: '吉伊会用挥手、表演和害羞反馈回应你的点击。她适合作为第一只桌面伙伴，存在感明亮，但不会打扰你做事。',
    mood: '明亮 / 亲近 / 活泼',
    traits: ['欢迎互动', '表情丰富', '轻量陪伴'],
    actions: [
      { id: 'waving', label: '挥手', src: 'jiyi-action-waving.webp', description: '打开电脑时先打个招呼' },
      { id: 'concert', label: '演奏', src: 'jiyi-action-concert.webp', description: '给桌面加一点元气' },
      { id: 'shy', label: '害羞', src: 'jiyi-action-shy.webp', description: '被点到时的小反应' },
    ],
    stats: [
      ['日常', '陪伴风格'],
      ['3 个', '精选动作'],
      ['可调', '大小位置'],
    ],
  },
  {
    id: 'dora',
    code: '0021',
    name: 'Dora',
    folderName: '软萌陪伴',
    title: '软萌、爱回应的小伙伴',
    intro: 'Dora 的反应更柔和，适合喜欢治愈感的用户。无论是挥手、跳跃，还是被小工具逗到，都会给桌面一点轻松感。',
    mood: '软萌 / 治愈 / 反馈',
    traits: ['治愈感', '轻快反馈', '可爱反应'],
    actions: [
      { id: 'waving', label: '挥手', src: 'dora-action-waving.webp', description: '轻轻挥手打招呼' },
      { id: 'jump', label: '跳跃', src: 'dora-action-jump.webp', description: '开心时蹦一下' },
      { id: 'feather', label: '羽毛逗弄', src: 'dora-action-feather.webp', description: '被逗到的小表情' },
    ],
    stats: [
      ['治愈', '陪伴风格'],
      ['3 个', '精选动作'],
      ['可调', '大小位置'],
    ],
  },
  {
    id: 'fox',
    code: '0005',
    name: '狐狸',
    folderName: '灵敏搭档',
    title: '小狐狸，适合喜欢互动感的人',
    intro: '狐狸更适合承担工具反馈：提醒触发、逗弄、点击都会有更明确的动作回应，让桌面看起来更有生命力。',
    mood: '灵敏 / 轻快 / 工具',
    traits: ['反应灵敏', '工具互动', '状态反馈'],
    actions: [
      { id: 'waving', label: '挥手', src: 'fox-action-waving.webp', description: '待机时也能保持存在感' },
      { id: 'feather', label: '羽毛逗弄', src: 'fox-action-feather.webp', description: '被羽毛逗到的反应' },
      { id: 'whip', label: '鞭子命中', src: 'fox-action-whip.webp', description: '工具命中后的反馈' },
    ],
    stats: [
      ['灵敏', '陪伴风格'],
      ['3 个', '精选动作'],
      ['可调', '大小位置'],
    ],
  },
]

const featureCards = [
  {
    icon: CalendarCheck,
    title: '备忘录',
    text: '把临时想法、待办和小提醒留在桌面边上，打开电脑就能看见。',
  },
  {
    icon: AlarmClock,
    title: '闹钟',
    text: '会议、休息、喝水、番茄钟，都可以交给桌面伙伴轻轻提醒你。',
  },
  {
    icon: BellRing,
    title: '提醒队列',
    text: '今天要做的事集中放在一起，少开一个窗口，也少忘一件小事。',
  },
  {
    icon: MousePointerClick,
    title: '桌面互动',
    text: '点一下、拖一下、逗一下，它都会用动作回应，让桌面不再只是背景。',
  },
]

const controlViews = [
  {
    id: 'pets',
    label: '角色管理',
    icon: PawPrint,
    image: 'jiyi-action-waving.webp',
    eyebrow: '角色管理',
    title: '选择喜欢的桌面伙伴',
    text: '吉伊、Dora 和狐狸可以随时切换。想安静陪伴，还是想多一点互动，都能按自己的节奏来。',
    points: ['切换角色', '调整大小', '保持置顶'],
  },
  {
    id: 'actions',
    label: '动作调试',
    icon: Settings2,
    image: 'dora-action-feather.webp',
    eyebrow: '动作调试',
    title: '试试它们怎么回应你',
    text: '每个角色适配 5 个基础操作，规则统一、容易记住；每个操作还可以收纳多个动作候选。这里可以提前预览它们的回应。',
    points: ['5 个基础操作', '一个操作多个动作', '互动道具反应'],
  },
  {
    id: 'updates',
    label: '更新中心',
    icon: RotateCw,
    image: 'fox-action-whip.webp',
    eyebrow: '更新中心',
    title: '下载和更新更省心',
    text: '当前版本、下载入口和更新信息集中显示。之后有新版本，也能更快知道该怎么升级。',
    points: ['版本信息', '下载入口', '文件校验'],
  },
  {
    id: 'medals',
    label: '勋章墙',
    icon: Award,
    image: 'jiyi-action-concert.webp',
    eyebrow: '轻量收藏',
    title: '不打扰你的勋章墙',
    text: '勋章会在自然使用中悄悄解锁，不要求每日打卡，也不会影响角色的核心功能。',
    points: ['自然解锁', '不设断签惩罚', '随时隐藏'],
  },
] as const

const medals = [
  { id: 'hello', icon: '✦', title: '第一次回应', detail: '第一次让角色回应你的互动', status: '已解锁', tone: 'blue' },
  { id: 'three-days', icon: '☼', title: '熟悉的身影', detail: '自然使用 Window Pet 3 天', status: '已解锁', tone: 'mint' },
  { id: 'actions', icon: '✧', title: '三种回应', detail: '体验过待机、单击和拖拽三种基础状态', status: '已解锁', tone: 'violet' },
  { id: 'pet-collector', icon: '♢', title: '角色收藏家', detail: '认识 3 位桌面伙伴', status: '已解锁', tone: 'amber' },
  { id: 'week', icon: '◌', title: '一周陪伴', detail: '继续自然使用即可解锁', status: '还有 4 天', tone: 'soft' },
  { id: 'custom', icon: '♡', title: '专属伙伴', detail: '拥有一只定制角色后解锁', status: '待解锁', tone: 'soft' },
  { id: 'quiet', icon: '⌁', title: '安静陪伴', detail: '让角色保持静态陪伴', status: '待解锁', tone: 'soft' },
  { id: 'all-actions', icon: '✺', title: '动作体验家', detail: '慢慢体验更多互动，不用赶进度', status: '待解锁', tone: 'soft' },
  { id: 'seasonal', icon: '❋', title: '夏日来信', detail: '下一次季节活动开放后解锁', status: '活动限定', tone: 'soft' },
 ] as const

function MedalWall() {
  const [isHidden, setIsHidden] = useState(false)

  if (isHidden) {
    return (
      <div className="medal-wall-hidden">
        <EyeOff size={28} />
        <strong>勋章墙已暂时隐藏</strong>
        <p>它不会打扰你的日常使用，想看时再回来就好。</p>
        <button type="button" onClick={() => setIsHidden(false)}>
          重新显示
        </button>
      </div>
    )
  }

  const unlockedCount = medals.filter((medal) => medal.status === '已解锁').length

  return (
    <div className="medal-wall" aria-label="勋章墙预览">
      <div className="medal-wall-header">
        <div>
          <span className="cockpit-hero-eyebrow">COLLECTION / OPTIONAL</span>
          <strong>慢慢收集，不用赶进度</strong>
          <p>目前已发现 {unlockedCount} 枚。没有每日任务，也不会因为几天没打开而失去进度。</p>
        </div>
        <button className="medal-hide-button" type="button" onClick={() => setIsHidden(true)}>
          <EyeOff size={16} />
          暂时隐藏
        </button>
      </div>
      <div className="medal-wall-note">
        <Sparkles size={16} />
        <span>勋章只用于收藏和装扮，不会锁住角色功能。</span>
      </div>
      <div className="medal-grid">
        {medals.map((medal) => {
          const unlocked = medal.status === '已解锁'
          return (
            <article className={`medal-card ${unlocked ? 'is-unlocked' : 'is-locked'} tone-${medal.tone}`} key={medal.id}>
              <div className="medal-icon" aria-hidden="true">
                {unlocked ? medal.icon : <LockKeyhole size={18} />}
              </div>
              <div className="medal-copy">
                <strong>{medal.title}</strong>
                <span>{medal.detail}</span>
              </div>
              <small>{medal.status}</small>
            </article>
          )
        })}
      </div>
    </div>
  )
}

function petImage(id: string) {
  return `${import.meta.env.BASE_URL}pets/${id}.png`
}

function petAsset(fileName: string) {
  return `${import.meta.env.BASE_URL}pets/${fileName}`
}

function App() {
  const [currentView, setCurrentView] = useState<'home' | 'gallery'>(() => {
    return typeof window !== 'undefined' && window.location.hash === '#/gallery' ? 'gallery' : 'home'
  })

  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash === '#/gallery') {
        setCurrentView('gallery')
      } else {
        setCurrentView('home')
      }
    }
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  const handleOpenGallery = () => {
    setCurrentView('gallery')
    window.location.hash = '#/gallery'
  }

  const handleBackToHome = () => {
    setCurrentView('home')
    if (window.location.hash === '#/gallery') {
      history.replaceState(null, '', window.location.pathname + window.location.search)
    }
  }

  const handleNavHome = () => {
    handleBackToHome()
    scrollToSection(0)
  }

  const [selectedPetId, setSelectedPetId] = useState(pets[0].id)
  const [selectedActionId, setSelectedActionId] = useState(pets[0].actions[0].id)
  const [activeControlViewId, setActiveControlViewId] = useState<(typeof controlViews)[number]['id']>(
    controlViews[0].id,
  )
  const [activeIndex, setActiveIndex] = useState(0)
  const activeIndexRef = useRef(0)
  const wheelLockRef = useRef(false)
  const shellRef = useRef<HTMLElement | null>(null)

  const selectedPet = useMemo(() => pets.find((pet) => pet.id === selectedPetId) ?? pets[0], [selectedPetId])
  const selectedPetAction = useMemo(
    () => selectedPet.actions.find((action) => action.id === selectedActionId) ?? selectedPet.actions[0],
    [selectedPet, selectedActionId],
  )
  const activeControlView = useMemo(
    () => controlViews.find((view) => view.id === activeControlViewId) ?? controlViews[0],
    [activeControlViewId],
  )

  useEffect(() => {
    activeIndexRef.current = activeIndex
  }, [activeIndex])

  useEffect(() => {
    const root = shellRef.current
    if (!root) return

    const observer = new IntersectionObserver(
      (entries) => {
        const bestEntry = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        if (!bestEntry) return

        const nextIndex = sectionIds.indexOf(bestEntry.target.id as (typeof sectionIds)[number])
        if (nextIndex >= 0) {
          setActiveIndex(nextIndex)
        }
      },
      { root, threshold: [0.45, 0.62, 0.8] },
    )

    sectionIds.forEach((id) => {
      const section = document.getElementById(id)
      if (section) observer.observe(section)
    })

    return () => observer.disconnect()
  }, [])

  const scrollToSection = (index: number) => {
    const root = shellRef.current
    const nextIndex = Math.max(0, Math.min(sectionIds.length - 1, index))
    const target = document.getElementById(sectionIds[nextIndex])
    if (!root || !target) return

    activeIndexRef.current = nextIndex
    setActiveIndex(nextIndex)
    root.scrollTo({ top: target.offsetTop, behavior: 'smooth' })
  }

  const handleWheel: WheelEventHandler<HTMLElement> = (event) => {
    if (currentView !== 'home') return
    if (window.matchMedia('(max-width: 860px)').matches || Math.abs(event.deltaY) < 18) return

    event.preventDefault()
    if (wheelLockRef.current) return

    const direction = event.deltaY > 0 ? 1 : -1
    const nextIndex = Math.max(0, Math.min(sectionIds.length - 1, activeIndexRef.current + direction))
    if (nextIndex === activeIndexRef.current) return

    wheelLockRef.current = true
    scrollToSection(nextIndex)
    window.setTimeout(() => {
      wheelLockRef.current = false
    }, 760)
  }

  return (
    <div className="site-wrapper">
      <header className="site-nav">
        <button className="brand-lockup" type="button" onClick={handleNavHome} aria-label="返回首页">
          <span className="brand-symbol">
            <img src={`${import.meta.env.BASE_URL}apple-touch-icon.png`} alt="" />
          </span>
          <span>
            <strong>Window Pet</strong>
            <small>桌面萌宠下载</small>
          </span>
        </button>

        <nav aria-label="官网导航">
          <button
            type="button"
            className={`nav-link-btn ${currentView === 'home' ? 'is-active' : ''}`}
            onClick={handleNavHome}
          >
            首页
          </button>
          <button
            type="button"
            className={`nav-gallery-link nav-link-btn ${currentView === 'gallery' ? 'is-active' : ''}`}
            onClick={handleOpenGallery}
            title="打开小鼻嘎展馆，查看全部 24 款萌宠"
          >
            小鼻嘎展馆
            <span className="nav-gallery-tag">NEW</span>
          </button>
          <a
            className="nav-github-link"
            href={githubRepoUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontWeight: 600, color: 'var(--wp-ink)' }}
          >
            GitHub 开源
          </a>
        </nav>

        <a className="nav-download" href={releaseInstallerHref} download={releaseInstallerName}>
          <Download size={17} />
          免费下载 (50MB)
        </a>
      </header>

      {currentView === 'home' && (
        <aside className="section-dots" aria-label="页面进度">
          {sectionDots.map((item, index) => (
            <button
              aria-label={`跳转到第 ${index + 1} 屏：${item.label}`}
              className={activeIndex === index ? 'is-active' : undefined}
              key={item.id}
              type="button"
              onClick={() => scrollToSection(index)}
              title={item.label}
            />
          ))}
        </aside>
      )}

      <main
        className="fullpage-site"
        ref={shellRef}
        onWheel={handleWheel}
        style={{ display: currentView === 'home' ? 'block' : 'none' }}
      >

      <section className="snap-section hero-page" id="home" aria-label="Window Pet 首页">
        <div className="section-inner hero-layout">
          <div className="hero-copy">
            <p className="eyebrow">WINDOWS DESKTOP COMPANION</p>
            <h1>让桌面多一个会回应你的伙伴</h1>
            <p className="hero-subtitle">
              Window Pet 把可爱的角色、日常提醒和轻量桌面工具放在一起。下载后，选择喜欢的伙伴，让它陪你工作、休息和记录琐事。
            </p>
            <div className="hero-actions">
              <a className="primary-download" href={releaseInstallerHref} download={releaseInstallerName}>
                <Download size={21} />
                下载 Windows 安装包 (仅 50MB)
              </a>
              <button className="secondary-action" type="button" onClick={() => scrollToSection(1)}>
                浏览全部 24 款角色
                <ChevronDown size={18} />
              </button>
            </div>
            <div className="hero-meta" aria-label="版本信息">
              <span>v{releaseVersion} 正式版</span>
              <span>仅 50MB 极速秒开</span>
              <span>24 款全套萌宠</span>
              <span>100% 永久免费开源</span>
            </div>
          </div>

          <div className="hero-visual" aria-label="Window Pet 主视觉">
            <div className="hero-screen-card">
              <div className="hero-screen-toolbar">
                <span />
                <span />
                <span />
                <strong>角色预览</strong>
              </div>
              <div className="hero-pet-stage">
                {pets.map((pet, index) => (
                  <img
                    alt={`${pet.name} 动态预览`}
                    className={`hero-pet hero-pet-${index + 1}`}
                    key={pet.id}
                    src={petImage(pet.id)}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="snap-section pets-page" id="pets" aria-label="角色选择">
        <div className="section-inner pet-layout">
          <div className="section-heading">
            <p className="eyebrow">CHOOSE YOUR PET</p>
            <h2>选择你的桌面伙伴</h2>
            <p>
              喜欢安静陪伴、软萌反馈，还是灵敏互动？点击角色和动作，先看看它在桌面上的样子。
              <button
                type="button"
                className="section-heading-gallery-link"
                onClick={handleOpenGallery}
                title="打开小鼻嘎展馆，探索全部 24 款萌宠"
              >
                <Sparkles size={14} />
                <span>探索全部 24 款萌宠图鉴</span>
              </button>
            </p>
          </div>

          <div className="pet-showcase">
            <div className="selected-pet-panel">
              <div className="selected-pet-art">
                <img
                  key={`${selectedPet.id}-${selectedPetAction.id}`}
                  src={petAsset(selectedPetAction.src)}
                  alt={`${selectedPet.name} ${selectedPetAction.label}动作预览`}
                />
              </div>
              <div className="selected-pet-copy">
                <span>NO.{selectedPet.code} / {selectedPet.folderName}</span>
                <h3>{selectedPet.name}</h3>
                <strong>{selectedPet.title}</strong>
                <p>{selectedPet.intro}</p>
                <div className="trait-row">
                  {selectedPet.traits.map((trait) => (
                    <span key={trait}>{trait}</span>
                  ))}
                </div>
                <div className="action-shelf" aria-label={`${selectedPet.name} 动作预览`}>
                  <strong>5 个基础操作 · 先试试三个</strong>
                  <div>
                    {selectedPet.actions.map((action) => (
                      <button
                        aria-pressed={selectedPetAction.id === action.id}
                        className={selectedPetAction.id === action.id ? 'is-active' : undefined}
                        key={action.id}
                        type="button"
                        onClick={() => setSelectedActionId(action.id)}
                      >
                        <span>{action.label}</span>
                        <small>{action.description}</small>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="pet-stats">
                {selectedPet.stats.map(([value, label]) => (
                  <div key={label}>
                    <strong>{value}</strong>
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pet-selector" aria-label="选择宠物">
              {pets.map((pet) => (
                <button
                  aria-pressed={selectedPet.id === pet.id}
                  className={selectedPet.id === pet.id ? 'is-selected' : undefined}
                  key={pet.id}
                  type="button"
                  onClick={() => {
                    setSelectedPetId(pet.id)
                    setSelectedActionId(pet.actions[0].id)
                  }}
                >
                  <img src={petImage(pet.id)} alt="" />
                  <span>{pet.name}</span>
                  <small>NO.{pet.code} · {pet.mood}</small>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="snap-section features-page" id="features" aria-label="功能亮点">
        <div className="section-inner features-layout">
          <div className="section-heading">
            <p className="eyebrow">DESKTOP TOOLS</p>
            <h2>不只是可爱，也能帮你记事</h2>
            <p>把备忘录、闹钟、提醒和桌面互动放在一个轻量工具里，让陪伴感和实用性同时留在屏幕边上。</p>
          </div>

          <div className="feature-stage">
            <div className="assistant-board" aria-label="桌面助手功能预览">
              <div className="board-topbar">
                <span>今日提醒</span>
                <strong>09:30</strong>
              </div>
              <div className="memo-list">
                <article>
                  <CalendarCheck size={18} />
                  <div>
                    <strong>备忘录</strong>
                    <span>晚上整理桌面文件</span>
                  </div>
                </article>
                <article>
                  <AlarmClock size={18} />
                  <div>
                    <strong>闹钟</strong>
                    <span>10 分钟后休息一下</span>
                  </div>
                </article>
                <article>
                  <BellRing size={18} />
                  <div>
                    <strong>提醒</strong>
                    <span>有新版本时提醒我</span>
                  </div>
                </article>
              </div>
              <div className="board-pet">
                <img src={petImage('fox')} alt="狐狸功能演示" />
                <div>
                  <strong>狐狸准备提醒你</strong>
                  <span>到点后用动作给出反馈</span>
                </div>
              </div>
            </div>

            <div className="feature-card-grid">
              {featureCards.map((feature) => {
                const Icon = feature.icon
                return (
                  <article className="feature-card" key={feature.title}>
                    <Icon size={24} strokeWidth={2.1} />
                    <h3>{feature.title}</h3>
                    <p>{feature.text}</p>
                  </article>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="snap-section custom-page" id="custom" aria-label="自家爱宠专属定制">
        <div className="section-inner custom-layout">
          <div className="section-heading">
            <p className="eyebrow">CUSTOM PET STUDIO</p>
            <h2>把自家毛孩子，做进电脑桌面陪伴你</h2>
            <p>
              不只是现成动漫角色！提供 1~3 张爱宠生活照（猫咪、狗狗、龙猫、鹦鹉），
              AI 风格化提取 + 专业动作设计，生成专属陪伴桌宠。每一次敲键盘、看屏幕，爱宠都在身边。
            </p>
          </div>

          <div className="custom-funnel-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', margin: '32px 0' }}>
            <article className="feature-card" style={{ padding: '24px', background: 'var(--wp-surface)', borderRadius: '20px', border: '1px solid var(--wp-line)' }}>
              <Camera size={28} color="var(--wp-coral-deep)" />
              <h3 style={{ margin: '14px 0 8px', fontSize: '1.2rem' }}>01. 提供生活照</h3>
              <p style={{ color: 'var(--wp-muted)', fontSize: '0.92rem', lineHeight: '1.6' }}>准备 1~3 张爱宠清晰的全身照（站立、坐姿或趴卧正面），AI 将自动提取外观花色特征与轮廓。</p>
            </article>

            <article className="feature-card" style={{ padding: '24px', background: 'var(--wp-surface)', borderRadius: '20px', border: '1px solid var(--wp-line)' }}>
              <Sparkles size={28} color="var(--wp-mint-deep)" />
              <h3 style={{ margin: '14px 0 8px', fontSize: '1.2rem' }}>02. 动作与性格定制</h3>
              <p style={{ color: 'var(--wp-muted)', fontSize: '0.92rem', lineHeight: '1.6' }}>可自由挑选动作风格：日常发呆、桌面散步、打瞌睡、敲键盘陪加班，甚至专属小玩具互动。</p>
            </article>

            <article className="feature-card" style={{ padding: '24px', background: 'var(--wp-surface)', borderRadius: '20px', border: '1px solid var(--wp-line)' }}>
              <Gift size={28} color="var(--wp-coral)" />
              <h3 style={{ margin: '14px 0 8px', fontSize: '1.2rem' }}>03. 专属安装包交付</h3>
              <p style={{ color: 'var(--wp-muted)', fontSize: '0.92rem', lineHeight: '1.6' }}>生成独一无二的专属角色包，双击即可召唤自家的毛孩子常驻桌面，永久陪伴。</p>
            </article>
          </div>

          <div className="custom-cta-card" style={{ padding: '24px 32px', background: 'linear-gradient(135deg, rgba(255, 231, 234, 0.7) 0%, rgba(220, 247, 241, 0.7) 100%)', borderRadius: '24px', border: '1px solid rgba(255, 255, 255, 0.8)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <strong style={{ fontSize: '1.15rem', display: 'block', color: 'var(--wp-ink)' }}>想给自家宠物定制独一无二的专属桌宠？</strong>
              <span style={{ color: 'var(--wp-muted)', fontSize: '0.9rem' }}>官方交流群现已开放预约，透明进度，支持验收满意后再交付。</span>
            </div>
            <a
              className="primary-download"
              href="https://qm.qq.com/q/cYlRBbvuda"
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', textDecoration: 'none' }}
            >
              <HeartHandshake size={18} />
              立即预约爱宠定制 / 进群交流
            </a>
          </div>
        </div>
      </section>

      <section className="snap-section control-page" id="control" aria-label="控制台和下载">
        <div className="section-inner control-layout">
          <div className="section-heading">
            <p className="eyebrow">CONTROL & DOWNLOAD</p>
            <h2>下载后，在一个窗口里管好它</h2>
            <p>选择角色、预览动作、检查更新，都可以在 Window Pet 控制台里完成。入口更集中，设置也更直观。</p>
          </div>

          <div className="cockpit-and-download">
            <div className="cockpit-window" aria-label="Window Pet Cockpit 控制台预览">
              <div className="cockpit-toolbar">
                <span />
                <span />
                <span />
                <strong>Window Pet Cockpit</strong>
              </div>
              <div className="cockpit-body">
                <aside>
                  {controlViews.map((view) => {
                    const Icon = view.icon
                    return (
                      <button
                        className={activeControlView.id === view.id ? 'is-active' : undefined}
                        key={view.id}
                        type="button"
                        onClick={() => setActiveControlViewId(view.id)}
                      >
                        <Icon size={16} />
                        {view.label}
                      </button>
                    )
                  })}
                </aside>
                <div className="cockpit-main">
                  {activeControlView.id === 'medals' ? (
                    <MedalWall />
                  ) : (
                    <>
                      <div className="cockpit-hero">
                        <img src={petAsset(activeControlView.image)} alt={`${activeControlView.label}界面预览`} />
                        <div>
                          <span>{activeControlView.eyebrow}</span>
                          <strong>{activeControlView.title}</strong>
                          <p>{activeControlView.text}</p>
                        </div>
                      </div>
                      <div className="cockpit-tools">
                        {activeControlView.points.map((point) => (
                          <div key={point}>
                            <CheckCircle2 size={18} />
                            {point}
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="download-panel">
              <div className="download-head">
                <FileArchive size={24} />
                <div>
                  <h3>WindowPet 官方发布版</h3>
                  <span>Version {releaseVersion} · Windows 10/11</span>
                </div>
              </div>
              <a className="primary-download wide" href={releaseInstallerHref} download={releaseInstallerName}>
                <Download size={20} />
                下载 Windows 安装包 (仅 50MB · 极速推荐)
              </a>
              <a
                className="secondary-action wide"
                href="https://github.com/panda008006/WindowPet/releases"
                target="_blank"
                rel="noopener noreferrer"
                style={{ marginTop: '10px', width: '100%', justifyContent: 'center' }}
              >
                前往 GitHub Releases 查看发布动态
              </a>
              <div className="safety-note">
                <strong>开源安全背书与 Windows 提示说明</strong>
                <span>WindowPet 已在 GitHub 全量开源，绿色安全。若初次运行提示“未知发布者”，点击【更多信息】选择【仍要运行】即可正常开启。</span>
              </div>
              <div className="download-links">
                <a href={githubRepoUrl} target="_blank" rel="noopener noreferrer">GitHub 开源仓库</a>
                <span>·</span>
                <a href="https://github.com/panda008006/WindowPet/releases" target="_blank" rel="noopener noreferrer">版本发布记录</a>
                <span>·</span>
                <span>MIT 协议</span>
              </div>
            </div>
          </div>

          <footer className="page-bottom-footer">
            <span>© 2026 WindowPet Open Source Community · 永久开源免费</span>
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
              桂ICP备2026009615号-2
            </a>
          </footer>
        </div>
      </section>
    </main>

    {/* 小鼻嘎展馆：顶部导航栏保持不变，展馆呈现在下方的独立展示界面 */}
    {currentView === 'gallery' && (
      <div className="gallery-view-pane">
        <PetGallery onBackToHome={handleBackToHome} />
      </div>
    )}
  </div>
  )
}

export default App

