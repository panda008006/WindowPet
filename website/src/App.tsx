import { useEffect, useMemo, useRef, useState, type WheelEventHandler } from 'react'
import {
  AlarmClock,
  Award,
  BellRing,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  Download,
  EyeOff,
  FileArchive,
  HeartHandshake,
  Home,
  LockKeyhole,
  MessageSquareHeart,
  MousePointerClick,
  PawPrint,
  RotateCw,
  Settings2,
  Sparkles,
} from 'lucide-react'
import './App.css'
import './polish.css'
import './subpages.css'
import './community.css'
import './wanted.css'
import { PetGallery } from './PetGallery'
import { CustomPetPage } from './CustomPetPage'
import { WantedPetPage } from './WantedPetPage'
import { TutorialPage } from './TutorialPage'
import { FaqPage } from './FaqPage'
import { SubmissionPage } from './SubmissionPage'
import { SubmissionReviewPage } from './SubmissionReviewPage'
import { releaseInstallerHref, releaseInstallerName, releaseSha256, releaseVersion } from './releaseConfig'

function QqIcon({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" fill="currentColor" aria-hidden="true" style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0 }}>
      <path d="M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 683.4 128 512 128s-254.5 134.2-250.1 319.9c-28.3 70.7-46.7 113.9-62.7 165.3-21.1 67.7-42 165.1 41.5 165.1 41.5 0 71.9-52.5 90.7-94.4 70.3 35.8 153.6 37.1 178.6 37.1 25 0 108.3-1.3 178.6-37.1 18.8 41.9 49.2 94.4 90.7 94.4 83.5 0 62.6-97.4 41.5-165.1z" />
    </svg>
  )
}

function BilibiliIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" fill="currentColor" aria-hidden="true" style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0 }}>
      <path d="M784 224h-100l60-60c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L587.3 224H436.7L325.3 118.7c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3l60 60H240C151.6 224 80 295.6 80 384v384c0 88.4 71.6 160 160 160h544c88.4 0 160-71.6 160-160V384c0-88.4-71.6-160-160-160zm96 544c0 53-43 96-96 96H240c-53 0-96-43-96-96V384c0-53 43-96 96-96h544c53 0 96 43 96 96v384zm-520-224c0-26.5 21.5-48 48-48s48 21.5 48 48-21.5 48-48 48-48-21.5-48-48zm304 0c0-26.5 21.5-48 48-48s48 21.5 48 48-21.5 48-48 48-48-21.5-48-48z" />
    </svg>
  )
}

function GithubIcon({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0 }}>
      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  )
}

const githubRepoUrl = 'https://github.com/panda008006/WindowPet'
const bilibiliVideoUrl = 'https://www.bilibili.com/video/BV1E2eb6PE5Q/'
const qqGroupUrl = 'https://qm.qq.com/q/aCrzrRQkqA'
const qqGroupNumber = '536254840'

const sectionIds = ['home', 'pets', 'features', 'control'] as const

const sectionDots = [
  { id: 'home', label: '首页' },
  { id: 'pets', label: '精选角色' },
  { id: 'features', label: '实用功能' },
  { id: 'control', label: '极速下载' },
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
    id: 'dadeepseek',
    code: '1020',
    name: '大DeepSeek',
    folderName: '开源深海',
    title: '女仆装深海蓝灵，桌面超清陪伴',
    intro: '全套 UltraKey 原生发丝级抠像女仆装大DeepSeek。支持待机微动、互动提溜、深度思考与问答名场面。',
    mood: '智慧 / 俏皮 / 陪伴',
    traits: ['原生发丝抠像', '深度思考', '互动灵敏', '1080P超清'],
    actions: [
      { id: 'idle', label: '待机萌动', src: 'dadeepseek-animated.webp', description: '深海萌蓝，好奇微动' },
      { id: 'click', label: '开怀大笑', src: 'dadeepseek-action-click.webp', description: '左键轻戳，开怀回应' },
      { id: 'thinking', label: '深度思考', src: 'dadeepseek-action-thinking.webp', description: 'AI思考中，灵动眨眼' },
    ],
    stats: [
      ['超清', '1080P全动效'],
      ['3 个', '精选动作'],
      ['免费', '开箱即用'],
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
    text: '吉伊、Dora、狐狸、大DeepSeek、小DeepSeek与各类萌宠随时召唤。支持多宠同屏、错位排布，每只伙伴都能独立互动。',
    points: ['多宠同屏共存', '双击极速召唤', '独立关闭与控制'],
  },
  {
    id: 'actions',
    label: '动作工坊',
    icon: Settings2,
    image: 'dora-action-feather.webp',
    eyebrow: '动作工坊',
    title: '极简动作，灵活绑定',
    text: '全新升级的极简「动作」界面，支持自由预览并直接绑定待机、单击、拖拽等各类高保真动作。',
    points: ['极简直观界面', '拖拽快速绑定', '1440P 原生超清呈现'],
  },
  {
    id: 'updates',
    label: '更新中心',
    icon: RotateCw,
    image: 'fox-action-whip.webp',
    eyebrow: '更新中心',
    title: '下载和更新更省心',
    text: '开机静默后台检测最新版本，当前版本、下载入口和更新信息集中显示，一键轻松升级。',
    points: ['静默后台检测', '绿色免安装', '极速解压即用'],
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

export type ViewMode = 'home' | 'gallery' | 'wanted' | 'custom' | 'tutorial' | 'faq' | 'submit' | 'review'

function App() {
  const [currentView, setCurrentView] = useState<ViewMode>(() => {
    if (typeof window === 'undefined') return 'home'
    const hash = window.location.hash
    if (hash === '#/gallery') return 'gallery'
    if (hash === '#/wanted') return 'wanted'
    if (hash === '#/custom') return 'custom'
    if (hash === '#/tutorial') return 'tutorial'
    if (hash === '#/faq') return 'faq'
    if (hash === '#/submit') return 'submit'
    if (hash === '#/review') return 'review'
    return 'home'
  })

  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash
      if (hash === '#/gallery') {
        setCurrentView('gallery')
      } else if (hash === '#/wanted') {
        setCurrentView('wanted')
      } else if (hash === '#/custom') {
        setCurrentView('custom')
      } else if (hash === '#/tutorial') {
        setCurrentView('tutorial')
      } else if (hash === '#/faq') {
        setCurrentView('faq')
      } else if (hash === '#/submit') {
        setCurrentView('submit')
      } else if (hash === '#/review') {
        setCurrentView('review')
      } else {
        setCurrentView('home')
      }
    }
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  const navigateTo = (view: ViewMode) => {
    setCurrentView(view)
    if (view === 'home') {
      if (window.location.hash && window.location.hash !== '#/') {
        history.replaceState(null, '', window.location.pathname + window.location.search)
      }
      if (currentView === 'home') {
        scrollToSection(0)
      }
    } else {
      history.pushState(null, '', `#/${view}`)
      window.dispatchEvent(new Event('hashchange'))
    }
  }

  const [copiedQq, setCopiedQq] = useState(false)

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
        <button className="brand-lockup" type="button" onClick={() => navigateTo('home')} aria-label="返回首页">
          <span className="brand-symbol">
            <img src={`${import.meta.env.BASE_URL}apple-touch-icon.png`} alt="" />
          </span>
          <span>
            <strong>Window Pet</strong>
            <small>小鼻嘎</small>
          </span>
        </button>

        <nav aria-label="官网导航">
          <button
            type="button"
            className={`nav-link-btn ${currentView === 'home' ? 'is-active' : ''}`}
            onClick={() => navigateTo('home')}
          >
            <Home size={15} />
            <span>角色</span>
          </button>
          <button
            type="button"
            className={`nav-gallery-link nav-link-btn ${currentView === 'gallery' ? 'is-active' : ''}`}
            onClick={() => navigateTo('gallery')}
            title="打开小鼻嘎展馆，探索全部萌宠"
          >
            <Sparkles size={15} />
            <span>小鼻嘎展馆</span>
            <span className="nav-heart-badge" title="超可爱">❤️</span>
          </button>
          <button
            type="button"
            className={`nav-link-btn ${currentView === 'wanted' ? 'is-active' : ''}`}
            onClick={() => navigateTo('wanted')}
            title="许愿你喜欢的桌面角色"
          >
            <MessageSquareHeart size={15} />
            <span>许愿角色</span>
          </button>
          <button
            type="button"
            className={`nav-link-btn ${currentView === 'custom' ? 'is-active' : ''}`}
            onClick={() => navigateTo('custom')}
            title="自家毛孩子专属桌宠定制（小汪生示范）"
          >
            <HeartHandshake size={15} />
            <span>宠物设计</span>
            <span className="nav-pet-avatar-badge" title="小汪生">
              <img src={`${import.meta.env.BASE_URL}pets/xiaowang-avatar.png`} alt="小汪" className="nav-xiaowang-mini-avatar" />
            </span>
          </button>
          <button
            type="button"
            className={`nav-link-btn ${currentView === 'tutorial' ? 'is-active' : ''}`}
            onClick={() => navigateTo('tutorial')}
            title="查看 WindowPet 使用说明与操作教程"
          >
            <BookOpen size={15} />
            <span>说明</span>
          </button>
        </nav>

        <div className="nav-actions action-buttons">
          <div className="nav-community-actions" aria-label="社区交流群与外链">
            <div className="nav-qq-wrapper">
              <a
                href={qqGroupUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={`nav-community-btn nav-community-btn--qq ${copiedQq ? 'nav-community-btn--copied' : ''}`}
                onClick={() => {
                  try {
                    navigator.clipboard.writeText(qqGroupNumber)
                    setCopiedQq(true)
                    setTimeout(() => setCopiedQq(false), 2200)
                  } catch {
                    // ignore
                  }
                }}
                title={`加入 WindowPet 官方 QQ 交流群：${qqGroupNumber}（点击自动复制群号并唤起加群，悬停查看群二维码）`}
              >
                <QqIcon size={15} />
                <span>{copiedQq ? '✓ 群号已复制！' : `群: ${qqGroupNumber}`}</span>
              </a>

              {/* 悬停展示官方 QQ 群二维码卡片 */}
              <div className="nav-qq-hover-card" role="tooltip">
                <img
                  src={`${import.meta.env.BASE_URL}qq-group-qrcode.png`}
                  alt="WindowPet 官方 QQ 群二维码"
                  className="nav-qq-qrcode-img"
                />
                <div className="nav-qq-card-footer">
                  <strong>官方交流群：{qqGroupNumber}</strong>
                  <span>扫一扫或点击一键加入</span>
                </div>
              </div>
            </div>
            <a
              href={bilibiliVideoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="nav-community-btn nav-community-btn--bilibili"
              title="在哔哩哔哩观看演示视频"
            >
              <BilibiliIcon size={16} />
              <span>B站演示</span>
            </a>
            <a
              href={githubRepoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="nav-community-btn nav-community-btn--github"
              title="前往 GitHub 开源仓库 Star"
            >
              <GithubIcon size={15} />
              <span>GitHub</span>
            </a>
          </div>

          <a
            className="nav-download"
            href={releaseInstallerHref}
            download={releaseInstallerName}
            title={`下载 WindowPet ${releaseVersion} 官方正式版 (绿色免安装)`}
          >
            <Download size={15} />
            <span>下载</span>
          </a>
        </div>
      </header>

      <main
        className="fullpage-site"
        ref={shellRef}
        onWheel={handleWheel}
        style={{ display: currentView === 'home' ? 'block' : 'none' }}
      >
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

      <section className="snap-section hero-page" id="home" aria-label="Window Pet 首页">
        <div className="section-inner hero-layout">
          <div className="hero-copy">
            <h1 style={{ fontSize: 'clamp(32px, 3.6vw, 48px)', lineHeight: 1.3, fontWeight: 900, letterSpacing: '-0.5px' }}>
              <span style={{ display: 'inline-block', whiteSpace: 'nowrap' }}>在满是工作的屏幕角落，</span>
              <br />
              <span style={{ display: 'inline-block', whiteSpace: 'nowrap' }}>给你留一个发呆的地方。</span>
            </h1>
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
                {pets.slice(0, 3).map((pet, index) => (
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
                onClick={() => navigateTo('gallery')}
                title="打开小鼻嘎展馆，探索全部 50+ 款萌宠"
              >
                <Sparkles size={14} />
                <span>探索全部 50+ 款萌宠图鉴</span>
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
                  <h3>WindowPet 2.0 官方正式版</h3>
                  <span>Version {releaseVersion} · 绿色免安装 · Windows 10/11</span>
                </div>
              </div>
              <a
                className="primary-download wide"
                href={releaseInstallerHref}
                download={releaseInstallerName}
                title={releaseSha256 ? `SHA-256: ${releaseSha256}` : undefined}
              >
                <Download size={20} />
                下载 Windows 绿色免安装版 (极速解压即用)
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
            <span>·</span>
            <button
              type="button"
              className="footer-sub-link"
              onClick={() => navigateTo('submit')}
              style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '13px' }}
            >
              角色投稿与入驻中心
            </button>
          </footer>
        </div>
      </section>
    </main>

    {/* 小鼻嘎展馆独立展示界面 */}
    {currentView === 'gallery' && (
      <div className="gallery-view-pane">
        <PetGallery
          onBackToHome={() => navigateTo('home')}
          onNavigateCustom={() => navigateTo('custom')}
          onNavigateSubmit={() => navigateTo('submit')}
        />
      </div>
    )}

    {/* 想要角色独立专属页面 */}
    {currentView === 'wanted' && (
      <div className="wanted-view-pane">
        <WantedPetPage
          onBackToHome={() => navigateTo('home')}
          onOpenGallery={() => navigateTo('gallery')}
          onOpenCustom={() => navigateTo('custom')}
        />
      </div>
    )}

    {/* 爱宠定制独立专属页面 */}
    {currentView === 'custom' && (
      <CustomPetPage
        onBackToHome={() => navigateTo('home')}
        onOpenGallery={() => navigateTo('gallery')}
      />
    )}

    {/* 使用教程独立专属页面 */}
    {currentView === 'tutorial' && (
      <TutorialPage
        onBackToHome={() => navigateTo('home')}
        onOpenGallery={() => navigateTo('gallery')}
        onOpenFaq={() => navigateTo('faq')}
        onOpenSubmit={() => navigateTo('submit')}
      />
    )}

    {/* 常见问题 FAQ 独立专属页面 */}
    {currentView === 'faq' && (
      <FaqPage
        onBackToHome={() => navigateTo('home')}
        onOpenCustom={() => navigateTo('custom')}
        onOpenGallery={() => navigateTo('gallery')}
      />
    )}
    {currentView === 'submit' && (
      <SubmissionPage
        onBackToHome={() => navigateTo('home')}
        onOpenGallery={() => navigateTo('gallery')}
      />
    )}
    {currentView === 'review' && <SubmissionReviewPage onBackToHome={() => navigateTo('home')} />}
  </div>
  )
}

export default App

