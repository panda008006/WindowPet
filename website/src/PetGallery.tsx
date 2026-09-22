import { useEffect, useMemo, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Camera,
  Check,
  Copy,
  Heart,
  Home,
  Info,
  MessageSquare,
  PawPrint,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
  Zap,
} from 'lucide-react'
import { galleryCategories, galleryPets, galleryAuthors, type GalleryPet, type PetAuthor } from './galleryData'
import './gallery.css'

function QqIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" fill="currentColor" aria-hidden="true" style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0 }}>
      <path d="M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 683.4 128 512 128s-254.5 134.2-250.1 319.9c-28.3 70.7-46.7 113.9-62.7 165.3-21.1 67.7-42 165.1 41.5 165.1 41.5 0 71.9-52.5 90.7-94.4 70.3 35.8 153.6 37.1 178.6 37.1 25 0 108.3-1.3 178.6-37.1 18.8 41.9 49.2 94.4 90.7 94.4 83.5 0 62.6-97.4 41.5-165.1z" />
    </svg>
  )
}

interface PetGalleryProps {
  onBackToHome?: () => void
  onClose?: () => void
  onNavigateCustom?: () => void
}

const themeOptions = [
  { id: 'coral-mint', name: '珊瑚薄荷', color: '#ff7f87' },
  { id: 'mint', name: '薄荷海青', color: '#2f9f93' },
  { id: 'coral', name: '暖珊瑚红', color: '#e85f6d' },
  { id: 'peach', name: '蜜桃暖杏', color: '#fb923c' },
  { id: 'violet', name: '梦幻粉紫', color: '#a78bfa' },
  { id: 'sky', name: '晴空冰蓝', color: '#38bdf8' },
] as const

let nextOrderSeq = 1001
function generateOrderNumber() {
  nextOrderSeq += 1
  return `WP-PET-2026-${nextOrderSeq}`
}

export function PetGallery({ onBackToHome, onClose, onNavigateCustom }: PetGalleryProps) {
  const handleClose = onClose || onBackToHome

  // 核心多层级视图状态：'all' 全景展馆 | 'author' 作者独立展馆
  const [galleryView, setGalleryView] = useState<'all' | 'author'>('all')
  const [activeAuthorId, setActiveAuthorId] = useState<string | null>(null)

  // 筛选与搜索
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // 详情弹窗 (Level 2)
  const [selectedPet, setSelectedPet] = useState<GalleryPet | null>(null)
  const [selectedActionIndex, setSelectedActionIndex] = useState(0)

  // 1对1私聊画师联系卡弹窗 (免在线付费通道，直连画师与自行付款)
  const [contactArtist, setContactArtist] = useState<PetAuthor | null>(null)

  // 家宠定制与创作者提交弹窗
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false)
  const [customPetName, setCustomPetName] = useState('')
  const [customPetType, setCustomPetType] = useState('cat')
  const [customPetActions, setCustomPetActions] = useState('伸懒腰、踩奶、打盹、歪头')
  const [customOwnerEmail, setCustomOwnerEmail] = useState('')
  const [customPhotos, setCustomPhotos] = useState<string[]>([])
  const [customOrderNumber, setCustomOrderNumber] = useState<string | null>(null)

  // 交互提示与复制状态
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  // 主题与收藏持久化
  const [theme, setTheme] = useState<string>(() => {
    return localStorage.getItem('windowpet-gallery-theme') || 'coral-mint'
  })
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem('windowpet-gallery-favs')
      return stored ? new Set(JSON.parse(stored)) : new Set(['jiyi', 'nuonuo', 'fox', 'maicuijiao'])
    } catch {
      return new Set(['jiyi', 'nuonuo', 'fox', 'maicuijiao'])
    }
  })


  // 切换主题
  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme)
    localStorage.setItem('windowpet-gallery-theme', newTheme)
  }

  // 收藏切换
  const toggleFavorite = (e: React.MouseEvent, petId: string) => {
    e.stopPropagation()
    setFavorites((prev) => {
      const next = new Set(prev)
      if (next.has(petId)) {
        next.delete(petId)
        showToast('已取消收藏')
      } else {
        next.add(petId)
        showToast('已加入我的最爱 ❤️')
      }
      localStorage.setItem('windowpet-gallery-favs', JSON.stringify(Array.from(next)))
      return next
    })
  }

  const showToast = (msg: string) => {
    setToastMessage(msg)
  }

  useEffect(() => {
    if (!toastMessage) return
    const timer = setTimeout(() => setToastMessage(null), 3200)
    return () => clearTimeout(timer)
  }, [toastMessage])

  // 隐藏 ICP 备案号浮条
  useEffect(() => {
    const icp = document.querySelector<HTMLElement>('.site-icp-filing')
    if (!icp) return
    const prevDisplay = icp.style.display
    icp.style.display = 'none'
    return () => {
      icp.style.display = prevDisplay
    }
  }, [])

  // 全量在馆伙伴均直接免费开放导入
  const isPetUnlocked = (_pet: GalleryPet) => true

  // 复制兑换码
  const handleCopyCode = (e: React.MouseEvent, code: string, petName: string) => {
    e.stopPropagation()
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(code)
      showToast(`🎉 兑换码 ${code} 已复制！在桌面端粘贴即可激活【${petName}】`)
      setTimeout(() => setCopiedCode(null), 2500)
    })
  }

  // DeepLink 一键协议导入
  const handleDeepLinkImport = (pet: GalleryPet) => {
    const deepLinkUrl = `windowpet://import?pet=${encodeURIComponent(pet.id)}&code=${encodeURIComponent(pet.redeemCode)}&name=${encodeURIComponent(pet.name)}`
    window.open(deepLinkUrl, '_self')
    showToast(`🚀 正在呼叫 WindowPet 桌面客户端导入【${pet.name}】...`)
    navigator.clipboard.writeText(pet.redeemCode)
  }

  // 跳转进入作者专属独立展馆 (Level 3)
  const openAuthorProfile = (authorId: string) => {
    setSelectedPet(null)
    setActiveAuthorId(authorId)
    setGalleryView('author')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // 返回展馆全景 (Level 1)
  const closeAuthorProfile = () => {
    setGalleryView('all')
    setActiveAuthorId(null)
  }

  // 打开宠物详情 (Level 2)
  const openPetDetail = (pet: GalleryPet) => {
    setSelectedPet(pet)
    setSelectedActionIndex(0)
  }

  const closePetDetail = () => {
    setSelectedPet(null)
  }

  // 当前选中的作者对象
  const activeAuthor: PetAuthor | null = useMemo(() => {
    if (!activeAuthorId) return null
    return galleryAuthors[activeAuthorId] || null
  }, [activeAuthorId])

  // 当前作者旗下的专属作品列表
  const authorPets = useMemo(() => {
    if (!activeAuthorId) return []
    return galleryPets.filter((p) => p.authorId === activeAuthorId)
  }, [activeAuthorId])

  // 全景过滤角色列表
  const filteredPets = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return galleryPets.filter((pet) => {
      const matchCat =
        selectedCategory === 'all' ||
        (selectedCategory === 'favorite' ? favorites.has(pet.id) : pet.category === selectedCategory)
      if (!matchCat) return false

      if (!q) return true
      return (
        pet.name.toLowerCase().includes(q) ||
        pet.enName.toLowerCase().includes(q) ||
        pet.authorName.toLowerCase().includes(q) ||
        pet.authorHandle.toLowerCase().includes(q) ||
        pet.workType.toLowerCase().includes(q) ||
        pet.folderName.toLowerCase().includes(q) ||
        pet.traits.some((t) => t.toLowerCase().includes(q)) ||
        pet.tagline.toLowerCase().includes(q)
      )
    })
  }, [searchQuery, selectedCategory, favorites])

  const producerOrder = ['official', 'chestnut', 'mino', 'hoshino', 'wildspirit', 'memelab'] as const

  // 按制作人直接分栏编组
  const groupedPetsByProducer = useMemo(() => {
    const groups: { author: PetAuthor; pets: GalleryPet[] }[] = []
    for (const authorId of producerOrder) {
      const author = galleryAuthors[authorId]
      if (!author) continue
      const pets = filteredPets.filter((p) => p.authorId === authorId)
      if (pets.length > 0) {
        groups.push({ author, pets })
      }
    }
    return groups
  }, [filteredPets])

  // 家宠定制模拟上传
  const handlePhotoUploadMock = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const fileNames = Array.from(files).map((f) => f.name)
      setCustomPhotos((prev) => [...prev, ...fileNames])
      showToast(`📸 成功添加 ${files.length} 张宠物萌照！`)
    }
  }

  const handleSubmitCustomPet = (e: React.FormEvent) => {
    e.preventDefault()
    if (!customPetName.trim()) {
      showToast('请填写毛孩子的昵称')
      return
    }
    if (!customOwnerEmail.trim()) {
      showToast('请填写接收兑换码的邮箱')
      return
    }
    const orderNo = generateOrderNumber()
    setCustomOrderNumber(orderNo)
    showToast(`🎉 预约成功！定制工单号：${orderNo}`)
  }

  // ESC 关闭处理
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (contactArtist) {
          setContactArtist(null)
        } else if (selectedPet) {
          closePetDetail()
        } else if (isCustomModalOpen) {
          setIsCustomModalOpen(false)
        } else if (galleryView === 'author') {
          closeAuthorProfile()
        } else if (handleClose) {
          handleClose()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [contactArtist, selectedPet, isCustomModalOpen, galleryView, handleClose])

  return (
    <div className="gallery-page-container" data-gallery-theme={theme}>
      {/* 顶部导航 Header */}
      <header className="gallery-header">
        <div className="gallery-header-left">
          <div className="gallery-logo-brand" onClick={closeAuthorProfile} style={{ cursor: 'pointer' }}>
            <PawPrint size={22} color="var(--brand)" />
            <span>WindowPet</span>
            <span className="gallery-logo-badge">小鼻嘎展馆 · 精选创作者伙伴</span>
          </div>
        </div>

        <div className="gallery-header-right">
          {/* 搜索框 */}
          <div className="gallery-search-box">
            <Search className="gallery-search-icon" size={16} />
            <input
              type="text"
              className="gallery-search-input"
              placeholder="搜索角色或创作者：吉伊、米诺、柴犬、星野..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                if (galleryView === 'author') setGalleryView('all')
              }}
            />
            {searchQuery && (
              <button
                className="gallery-search-clear"
                type="button"
                onClick={() => setSearchQuery('')}
                aria-label="清空搜索"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* 快捷通道按钮：爱宠定制 */}
          <button
            type="button"
            className="gallery-nav-action-btn gallery-nav-custom-btn"
            onClick={() => {
              if (onNavigateCustom) {
                onNavigateCustom()
              } else {
                setIsCustomModalOpen(true)
              }
            }}
            title="定制自家的猫猫狗狗等毛孩子到电脑桌面"
          >
            <Camera size={15} />
            <span>爱宠定制</span>
          </button>

          {/* 8色主题色调色盘 */}
          <div className="gallery-theme-palette" title="选择界面主题色">
            {themeOptions.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`gallery-theme-dot ${theme === t.id ? 'is-active' : ''}`}
                style={{ backgroundColor: t.color }}
                onClick={() => handleThemeChange(t.id)}
                aria-label={t.name}
              />
            ))}
          </div>

          {/* 返回首页按钮 */}
          {handleClose && (
            <button
              type="button"
              className="gallery-lightbox-close-btn"
              onClick={handleClose}
              title="返回官网首页"
              aria-label="返回官网首页"
            >
              <Home size={15} />
              <span>返回首页</span>
            </button>
          )}
        </div>
      </header>

      {/* 主体布局 */}
      <div className="gallery-body-layout">
        {/* 左侧分类侧边栏 */}
        <aside className="gallery-sidebar">
          <div className="gallery-sidebar-sticky">
            <div className="gallery-sidebar-title">画风专区分类</div>
            <div className="gallery-sidebar-chips-wrap">
              {galleryCategories.map((cat) => {
                const isActive = galleryView === 'all' && selectedCategory === cat.id
                return (
                  <button
                    key={cat.id}
                    type="button"
                    className={`gallery-cat-chip ${isActive ? 'is-active' : ''}`}
                    onClick={() => {
                      setGalleryView('all')
                      setActiveAuthorId(null)
                      setSelectedCategory(cat.id)
                    }}
                  >
                    <span className="gallery-cat-chip-icon">
                      {cat.id === 'all' && <PawPrint size={15} />}
                      {cat.id === 'official' && <Sparkles size={15} />}
                      {cat.id === 'home' && <Home size={15} />}
                      {cat.id === 'anime' && <Heart size={15} />}
                      {cat.id === 'nature' && <PawPrint size={15} />}
                      {cat.id === 'fun' && <Sparkles size={15} />}
                    </span>
                    <span>{cat.label}</span>
                    <span className="gallery-cat-count">{cat.count}</span>
                  </button>
                )
              })}

              <button
                type="button"
                className={`gallery-cat-chip ${galleryView === 'all' && selectedCategory === 'favorite' ? 'is-active' : ''}`}
                onClick={() => {
                  setGalleryView('all')
                  setActiveAuthorId(null)
                  setSelectedCategory('favorite')
                }}
              >
                <span className="gallery-cat-chip-icon">
                  <Heart size={15} fill={galleryView === 'all' && selectedCategory === 'favorite' ? 'currentColor' : 'none'} />
                </span>
                <span>我的收藏</span>
                <span className="gallery-cat-count">{favorites.size}</span>
              </button>
            </div>

            {/* 创作者专属小展馆专栏 (点击直达作者个人主页) */}
            <div className="gallery-author-filter-wrap">
              <div className="gallery-sidebar-title" style={{ marginTop: '16px', marginBottom: '8px' }}>
                创作者独立展馆
              </div>
              <div className="gallery-author-chips-wrap">
                <button
                  type="button"
                  className={`gallery-author-chip ${galleryView === 'all' && !activeAuthorId ? 'is-active' : ''}`}
                  onClick={closeAuthorProfile}
                >
                  <span>全景大展馆</span>
                </button>
                {Object.values(galleryAuthors).map((auth) => {
                  const isAuthorActive = galleryView === 'author' && activeAuthorId === auth.id
                  return (
                    <button
                      key={auth.id}
                      type="button"
                      className={`gallery-author-chip ${isAuthorActive ? 'is-active' : ''}`}
                      onClick={() => openAuthorProfile(auth.id)}
                      title={`进入【${auth.name}】的专属展馆`}
                    >
                      <span className="author-chip-name">{auth.name}</span>
                      <small
                        className="author-chip-badge"
                        style={isAuthorActive ? { background: auth.badgeColor, color: '#fff' } : undefined}
                      >
                        {auth.badge}
                      </small>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* 侧边栏功能入口卡片：爱宠专属定制 */}
            <button
              type="button"
              className="gallery-sidebar-action-card custom-action-card"
              onClick={() => {
                if (onNavigateCustom) {
                  onNavigateCustom()
                } else {
                  setIsCustomModalOpen(true)
                }
              }}
            >
              <div className="sidebar-action-icon">
                <Camera size={18} />
              </div>
              <div className="sidebar-action-text">
                <strong>定制自家毛孩子</strong>
                <span>生活照 1 对 1 手绘 · 专属神态还原</span>
              </div>
            </button>

            <div className="gallery-sidebar-banner">
              <strong>💡 增删无忧 · 秒级唤回</strong>
              <span>
                桌面端右键角色即可随时【从桌面收回】；想念时随时回到展馆，点击【一键导入】即可秒级召唤！
              </span>
            </div>
          </div>
        </aside>

        {/* 右侧主内容区域 */}
        <main className="gallery-main-content">
          {/* ======================= Tier 3: 作者独立主页 (Author Profile View) ======================= */}
          {galleryView === 'author' && activeAuthor ? (
            <div className="author-profile-container">
              {/* 顶部面包屑与返回栏 */}
              <div className="author-profile-topbar">
                <button type="button" className="author-back-btn" onClick={closeAuthorProfile}>
                  <ArrowLeft size={16} />
                  <span>返回展馆全景大厅</span>
                </button>
                <span className="author-crumb-divider">/</span>
                <span className="author-crumb-title">{activeAuthor.name} 的个人创作展馆</span>
              </div>

              {/* 作者专属巨幅 Hero 卡片 */}
              <div className="author-profile-hero">
                <div
                  className="author-hero-banner-strip"
                  style={{ background: activeAuthor.bannerGradient }}
                />
                <div className="author-hero-content-wrap">
                  <div className="author-hero-main-row">
                    <div className="author-hero-avatar-box">
                      <div
                        className="author-large-avatar"
                        style={{ background: activeAuthor.badgeColor }}
                      >
                        {activeAuthor.initial}
                      </div>
                    </div>
                    <div className="author-hero-info-box">
                      <div className="author-name-badge-row">
                        <h2>{activeAuthor.name}</h2>
                        <span
                          className="author-badge-pill"
                          style={{ backgroundColor: activeAuthor.badgeColor }}
                        >
                          {activeAuthor.badge}
                        </span>
                        <span className="author-handle-text">{activeAuthor.handle}</span>
                      </div>
                      <p className="author-role-subtitle">{activeAuthor.role}</p>
                    </div>

                    <div className="author-hero-metrics-strip">
                      <div className="author-metric-box">
                        <strong>{activeAuthor.followers.toLocaleString()}</strong>
                        <span>关注者</span>
                      </div>
                      <div className="author-metric-box">
                        <strong>{activeAuthor.likes.toLocaleString()}</strong>
                        <span>获得点赞</span>
                      </div>
                      <div className="author-metric-box">
                        <strong>{authorPets.length}</strong>
                        <span>已上架伙伴</span>
                      </div>
                    </div>
                  </div>

                  <blockquote className="author-hero-bio-quote">
                    “{activeAuthor.bio}”
                  </blockquote>

                  <div className="author-hero-tags-row">
                    {activeAuthor.tags.map((tag) => (
                      <span key={tag} className="author-hero-tag-pill">
                        #{tag}
                      </span>
                    ))}
                  </div>

                  {/* 若作者开放定制约稿，展示约稿专属卡片 */}
                  {activeAuthor.acceptCustom && (
                    <div className="author-commission-callout">
                      <div className="commission-callout-icon">
                        <Camera size={20} />
                      </div>
                      <div className="commission-callout-text">
                        <strong>🎨 该作者开放 1 对 1 私宠生活照手绘定制约稿</strong>
                        <p>{activeAuthor.customNotice}</p>
                      </div>
                      <button
                        type="button"
                        className="commission-callout-btn"
                        onClick={() => {
                          if (onNavigateCustom) {
                            onNavigateCustom()
                          } else {
                            setIsCustomModalOpen(true)
                          }
                        }}
                      >
                        <span>预约该作者定制</span>
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* 作者作品展厅列表 */}
              <div className="author-works-section">
                <div className="author-works-header">
                  <div>
                    <h3>{activeAuthor.name} 创作的全部伙伴 ({authorPets.length} 款)</h3>
                    <p>全部伙伴免注册免登录，免费一键直接导入；如需专属定制，可直接私聊画师沟通与自行付款！</p>
                  </div>
                </div>

                {authorPets.length === 0 ? (
                  <div className="gallery-empty">
                    <Info size={40} />
                    <h3>该作者暂时还没有上架作品</h3>
                    <p>新角色正在切帧打磨中，敬请期待！</p>
                  </div>
                ) : (
                  <div className="gallery-minimal-grid">
                    {authorPets.map((pet) => {
                      const unlocked = isPetUnlocked(pet)
                      return (
                        <article
                          key={pet.id}
                          className="gallery-minimal-card"
                          onClick={() => openPetDetail(pet)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => e.key === 'Enter' && openPetDetail(pet)}
                          title={`点击查看【${pet.name}】的详细动作与导入`}
                        >
                          <div className="minimal-card-stage">
                            <img
                              src={`${import.meta.env.BASE_URL}${pet.animatedWebp || pet.image}`}
                              alt={pet.name}
                              className="minimal-card-img"
                              loading="lazy"
                            />
                            {unlocked && (
                              <span className="minimal-card-unlocked-dot" title="已拥有">
                                ✓
                              </span>
                            )}
                          </div>

                          <div className="minimal-card-info">
                            <span className="minimal-card-name">{pet.name}</span>
                            <span className="minimal-card-action">
                              动作：{pet.actions[0]?.label || '专属动作'}
                            </span>
                          </div>
                        </article>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* ======================= Tier 1: 全景大展馆 (All Gallery View) ======================= */
            <>
              {/* Banner 头部 */}
              <section className="gallery-hero-banner">
                <div className="gallery-hero-text">
                  <h1>小鼻嘎展馆 · 角色图鉴</h1>
                  <p>
                    汇聚知名画师与工坊切帧创作的 21 款精品桌面伙伴。无需注册账号，支持免登录即买即用，点击创作者名可直达其专属展馆！
                  </p>
                </div>
                <div className="gallery-hero-badge-strip">
                  <div className="gallery-hero-metric">
                    <strong>{galleryPets.length}</strong>
                    <span>在馆伙伴</span>
                  </div>
                  <div className="gallery-hero-metric">
                    <strong>6 位</strong>
                    <span>特邀制作人</span>
                  </div>
                  <div className="gallery-hero-metric">
                    <strong>免登录</strong>
                    <span>扫码即付即导</span>
                  </div>
                </div>
              </section>

              {/* 制作人分类区块列表 */}
              {groupedPetsByProducer.length === 0 ? (
                <div className="gallery-empty">
                  <Info size={40} />
                  <h3>没有找到符合条件的角色</h3>
                  <p>换个关键词试试，或者切换到【全部作品】专区。</p>
                </div>
              ) : (
                <div className="gallery-producers-stream">
                  {groupedPetsByProducer.map(({ author, pets }) => (
                    <section className="gallery-producer-section" key={author.id}>
                      {/* 制作人标题栏：直接写“制作人：XXX”，排版简约横排 */}
                      <div className="gallery-producer-header">
                        <div className="gallery-producer-avatar" style={{ background: author.badgeColor }}>
                          {author.initial}
                        </div>
                        <div className="gallery-producer-title-wrap">
                          <div className="gallery-producer-main-title">
                            <h2>制作人：{author.name}</h2>
                            <span className="gallery-producer-badge" style={{ borderColor: author.badgeColor, color: author.badgeColor }}>
                              {author.badge}
                            </span>
                          </div>
                          <span className="gallery-producer-subtitle">{author.role} · {pets.length} 款角色</span>
                        </div>
                        {author.acceptCustom && (
                          <button
                            type="button"
                            className="gallery-producer-custom-tag"
                            onClick={() => setContactArtist(author)}
                            title={`私聊画师【${author.name}】沟通爱宠专属定制，双方自行付款`}
                          >
                            <MessageSquare size={13} />
                            <span>💬 私聊画师定制</span>
                          </button>
                        )}
                      </div>

                      {/* 极简宠物卡片网格：只放宠物动效 + 名称 + 动作 */}
                      <div className="gallery-minimal-grid">
                        {pets.map((pet) => {
                          const unlocked = isPetUnlocked(pet)
                          return (
                            <article
                              key={pet.id}
                              className="gallery-minimal-card"
                              onClick={() => openPetDetail(pet)}
                              role="button"
                              tabIndex={0}
                              onKeyDown={(e) => e.key === 'Enter' && openPetDetail(pet)}
                              title={`点击查看【${pet.name}】的详细动作与导入`}
                            >
                              {/* 宠物动效展示区 */}
                              <div className="minimal-card-stage">
                                <img
                                  src={`${import.meta.env.BASE_URL}${pet.animatedWebp || pet.image}`}
                                  alt={pet.name}
                                  className="minimal-card-img"
                                  loading="lazy"
                                />
                                {unlocked && (
                                  <span className="minimal-card-unlocked-dot" title="已拥有">
                                    ✓
                                  </span>
                                )}
                              </div>

                              {/* 极简文字：名称 + 动作 */}
                              <div className="minimal-card-info">
                                <span className="minimal-card-name">{pet.name}</span>
                                <span className="minimal-card-action">
                                  动作：{pet.actions[0]?.label || '专属动作'}
                                </span>
                              </div>
                            </article>
                          )
                        })}
                      </div>
                    </section>
                  ))}
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* ======================= Tier 2: 沉浸式详情弹窗 (Modal) ======================= */}
      {selectedPet && (
        <div className="gallery-modal-backdrop" onClick={closePetDetail}>
          <div className="gallery-modal" onClick={(e) => e.stopPropagation()}>
            <button className="gallery-modal-close" type="button" onClick={closePetDetail} title="关闭">
              <X size={18} />
            </button>

            <div className="gallery-modal-body">
              {/* 弹窗左侧大舞台 */}
              <div className="gallery-modal-stage">
                <div className="gallery-stage-avatar-wrap">
                  <img
                    src={`${import.meta.env.BASE_URL}${selectedPet.image}`}
                    alt={selectedPet.name}
                    className="gallery-stage-avatar"
                  />
                </div>

                {/* 动作切换器 */}
                {selectedPet.actions.length > 0 && (
                  <div className="gallery-action-selector">
                    {selectedPet.actions.map((act, idx) => (
                      <button
                        key={act.id}
                        type="button"
                        className={`gallery-action-chip ${selectedActionIndex === idx ? 'is-active' : ''}`}
                        onClick={() => setSelectedActionIndex(idx)}
                      >
                        {act.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* 弹窗右侧详细档案 */}
              <div className="gallery-modal-info">
                <div className="gallery-info-head">
                  <div className="gallery-detail-title-row">
                    <h2>
                      <span>{selectedPet.name}</span>
                      <span className="gallery-card-en">{selectedPet.enName}</span>
                      <span className="gallery-worktype-tag">{selectedPet.workType}</span>
                    </h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <button
                        type="button"
                        className={`gallery-fav-btn ${favorites.has(selectedPet.id) ? 'active' : ''}`}
                        onClick={(e) => toggleFavorite(e, selectedPet.id)}
                        title={favorites.has(selectedPet.id) ? '取消收藏' : '加入我的最爱'}
                        style={{
                          background: 'rgba(239, 68, 68, 0.08)',
                          border: '1px solid rgba(239, 68, 68, 0.2)',
                          borderRadius: '8px',
                          padding: '6px 12px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          cursor: 'pointer',
                          color: favorites.has(selectedPet.id) ? '#ef4444' : '#64748b',
                          fontSize: '13px',
                          fontWeight: 600,
                        }}
                      >
                        <Heart
                          size={15}
                          fill={favorites.has(selectedPet.id) ? '#ef4444' : 'none'}
                          color={favorites.has(selectedPet.id) ? '#ef4444' : 'currentColor'}
                        />
                        <span>{favorites.has(selectedPet.id) ? '已收藏' : '收藏'}</span>
                      </button>
                      <div className="detail-price-pill" style={{ background: 'rgba(47, 159, 147, 0.1)', color: '#2f9f93', borderColor: 'rgba(47, 159, 147, 0.25)' }}>
                        免费开放
                      </div>
                    </div>
                  </div>

                  {/* 创作者专属互动名片 (可一键跳往作者主页) */}
                  {galleryAuthors[selectedPet.authorId] && (
                    <div className="detail-author-interactive-card">
                      <div className="detail-author-card-left">
                        <div
                          className="detail-author-avatar-circle"
                          style={{ background: galleryAuthors[selectedPet.authorId].badgeColor }}
                        >
                          {galleryAuthors[selectedPet.authorId].initial}
                        </div>
                        <div className="detail-author-card-meta">
                          <div className="detail-author-name-wrap">
                            <strong>{galleryAuthors[selectedPet.authorId].name}</strong>
                            <span
                              className="detail-author-badge"
                              style={{ backgroundColor: galleryAuthors[selectedPet.authorId].badgeColor }}
                            >
                              {galleryAuthors[selectedPet.authorId].badge}
                            </span>
                          </div>
                          <span className="detail-author-handle">
                            {galleryAuthors[selectedPet.authorId].handle} · 粉丝 {galleryAuthors[selectedPet.authorId].followers.toLocaleString()}
                          </span>
                        </div>
                      </div>

                      <button
                        type="button"
                        className="detail-author-jump-btn"
                        onClick={() => openAuthorProfile(selectedPet.authorId)}
                        title={`进入【${galleryAuthors[selectedPet.authorId].name}】的个人独立展馆`}
                      >
                        <span>进 ta 的主页</span>
                        <ArrowRight size={13} />
                      </button>
                    </div>
                  )}

                  <div className="gallery-info-tagline">{selectedPet.tagline}</div>
                </div>

                <p className="gallery-info-desc">{selectedPet.description}</p>

                {/* 当前选中动作说明 */}
                {selectedPet.actions[selectedActionIndex] && (
                  <div className="gallery-card-quote">
                    <strong>动作【{selectedPet.actions[selectedActionIndex].label}】：</strong>
                    {selectedPet.actions[selectedActionIndex].description}
                  </div>
                )}

                {/* 参数指标 */}
                <div className="gallery-modal-stats">
                  {selectedPet.stats.map(([val, lbl]) => (
                    <div key={lbl} className="gallery-stat-box">
                      <strong>{val.startsWith('￥') || val.startsWith('¥') ? '免费开放' : val}</strong>
                      <span>{val.startsWith('￥') || val.startsWith('¥') ? '开源畅享' : lbl}</span>
                    </div>
                  ))}
                </div>

                {/* 正版与交付保障说明 */}
                <div className="gallery-copyright-notice">
                  <ShieldCheck size={18} color="#2563eb" />
                  <div>
                    <strong>正版切帧与终身可用保障：</strong>
                    <span>
                      本角色由创作者【{selectedPet.authorName}】精心切帧制作与调校。无需注册账号，授权后与您的 Windows 设备永久绑定，支持随软件更新并享受后续动作扩展包！
                    </span>
                  </div>
                </div>

                {/* 增删无忧机制提示 */}
                <div className="gallery-modal-workflow-tip">
                  <Info size={16} />
                  <div>
                    <strong>自由收回与重新召唤：</strong>
                    在电脑桌面右键该宠物选择【从桌面收回此宠物】即可随时移出；想念它时随时回到展馆点击【一键导入到桌面】，1 秒重新召回！
                  </div>
                </div>

                {/* 核心操作区：全量伙伴免费开放，支持一键导入与私聊画师 */}
                <div className="gallery-integration-panel">
                  <div className="gallery-integration-title">
                    <strong>
                      <Sparkles size={16} />
                      全量在馆伙伴免费开放 · 免登录直接激活
                    </strong>
                    <span className="gallery-card-en">100% 永久开源</span>
                  </div>

                  <div className="gallery-code-display">
                    <span className="gallery-code-text">{selectedPet.redeemCode}</span>
                    <button
                      type="button"
                      className="gallery-btn-sm"
                      onClick={(e) => handleCopyCode(e, selectedPet.redeemCode, selectedPet.name)}
                    >
                      {copiedCode === selectedPet.redeemCode ? <Check size={14} /> : <Copy size={14} />}
                      <span>{copiedCode === selectedPet.redeemCode ? '已复制' : '复制备用码'}</span>
                    </button>
                  </div>

                  <div className="gallery-integration-buttons">
                    <button
                      type="button"
                      className="gallery-cta-primary gallery-cta-unlocked"
                      onClick={() => handleDeepLinkImport(selectedPet)}
                      title="点击通过浏览器唤醒 Windows 客户端自动导入"
                    >
                      <Zap size={18} />
                      <span>一键导入到桌面客户端</span>
                    </button>

                    <button
                      type="button"
                      className="gallery-cta-secondary"
                      onClick={(e) => handleCopyCode(e, selectedPet.redeemCode, selectedPet.name)}
                    >
                      <Copy size={16} />
                      <span>复制离线识别码</span>
                    </button>

                    {selectedPet.authorId !== 'official' && (
                      <button
                        type="button"
                        className="gallery-cta-chat-btn"
                        onClick={() => {
                          const author = galleryAuthors[selectedPet.authorId]
                          if (author) setContactArtist(author)
                        }}
                        title="私聊画师沟通爱宠专属定制，双方自行协商付款"
                      >
                        <MessageSquare size={16} />
                        <span>💬 私聊画师约稿 (自行付款)</span>
                      </button>
                    )}
                  </div>

                  <p className="gallery-integration-hint">
                    <Info size={14} />
                    WindowPet 平台永久免费开源，不设任何在线付费门槛。如需爱宠专属定制请直接私聊画师 1 对 1 沟通，双方自行协商付款，透明无套路！
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ======================= 私聊画师联系卡 (Artist Direct Chat Modal) ======================= */}
      {contactArtist && (
        <div className="gallery-modal-backdrop" onClick={() => setContactArtist(null)}>
          <div className="gallery-modal artist-contact-modal" onClick={(e) => e.stopPropagation()}>
            <button className="gallery-modal-close" type="button" onClick={() => setContactArtist(null)} title="关闭">
              <X size={18} />
            </button>

            <div className="artist-contact-header">
              <div className="artist-contact-badge">
                <MessageSquare size={15} />
                <span>1 对 1 私聊沟通 · 平台零抽成</span>
              </div>
              <h2>私聊画师【{contactArtist.name}】</h2>
              <p>WindowPet 平台不设在线付费抽成。请直接与画师 1 对 1 私聊商议定制细节，双方自行商定付款！</p>
            </div>

            <div className="artist-contact-body">
              <div className="artist-contact-card">
                <div className="artist-contact-avatar-box" style={{ background: contactArtist.bannerGradient }}>
                  <span>{contactArtist.initial}</span>
                </div>
                <div className="artist-contact-info">
                  <div className="artist-name-row">
                    <h3>{contactArtist.name}</h3>
                    <span className="artist-handle-tag">{contactArtist.handle}</span>
                  </div>
                  <span className="artist-contact-role">{contactArtist.role}</span>
                  <p className="artist-contact-bio">{contactArtist.bio}</p>
                  <div className="artist-contact-tags">
                    {contactArtist.tags.map((tag) => (
                      <span key={tag} className="artist-contact-tag">#{tag}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="artist-contact-methods">
                <div className="contact-method-item is-primary">
                  <div className="contact-method-left">
                    <div className="contact-method-icon">
                      <QqIcon size={20} />
                    </div>
                    <div>
                      <strong>官方定制联络群（找画师私聊）</strong>
                      <span>进群可直接私聊【{contactArtist.name}】或 @画师 沟通定制细节与报价</span>
                    </div>
                  </div>
                  <div className="contact-method-actions">
                    <button
                      type="button"
                      className="contact-copy-btn"
                      onClick={() => {
                        navigator.clipboard.writeText('422616922')
                        showToast(`已复制官方群号 422616922！进群直接私聊【${contactArtist.name}】`)
                      }}
                    >
                      <Copy size={14} />
                      <span>复制群号 422616922</span>
                    </button>
                    <a
                      href="https://qm.qq.com/q/cYlRBbvuda"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="contact-direct-link"
                    >
                      <span>一键进群私聊</span>
                    </a>
                  </div>
                </div>

                <div className="contact-tips-box">
                  <strong>💡 双方私聊定制流程与付款提示：</strong>
                  <ul>
                    <li>1. 准备 1~3 张爱宠清晰生活照（坐姿、站姿或趴卧全身照最佳）；</li>
                    <li>2. 告诉画师爱宠名字与特征小神态（如歪头、踩奶、打哈欠、看鼠标视线跟随）；</li>
                    <li>3. <strong>双方自行商议工期与付款</strong>（微信/支付宝等直接转账给画师，无平台抽成差价）；</li>
                    <li>4. 画师交付后由官方引擎一键封装，终身永久拥有唯一角色安装包！</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="artist-contact-footer">
              <button
                type="button"
                className="gallery-btn-secondary"
                onClick={() => setContactArtist(null)}
              >
                关闭
              </button>
              {onNavigateCustom && (
                <button
                  type="button"
                  className="gallery-btn-primary"
                  onClick={() => {
                    setContactArtist(null)
                    onNavigateCustom()
                  }}
                >
                  <span>前往爱宠定制工坊查看案例</span>
                  <ArrowRight size={14} />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ======================= 家宠定制预约弹窗 (CustomPetModal) ======================= */}
      {isCustomModalOpen && (
        <div className="gallery-modal-backdrop" onClick={() => setIsCustomModalOpen(false)}>
          <div className="gallery-modal custom-order-modal" onClick={(e) => e.stopPropagation()}>
            <button className="gallery-modal-close" type="button" onClick={() => setIsCustomModalOpen(false)}>
              <X size={18} />
            </button>

            <div className="custom-modal-header">
              <div className="custom-modal-icon">
                <Camera size={24} />
              </div>
              <div>
                <h2>家宠专属定制通道</h2>
                <p>拍下自家宠物的真实生活照片，由特邀画师 1 对 1 切帧制作，生成专属桌面角色！</p>
              </div>
            </div>

            {customOrderNumber ? (
              <div className="custom-order-success">
                <div className="success-icon-wrap">
                  <Check size={36} color="#16a34a" />
                </div>
                <h3>预约工单已生成！</h3>
                <div className="success-order-box">
                  <span>工单预约号：</span>
                  <strong>{customOrderNumber}</strong>
                </div>
                <p>
                  我们已接收到关于【{customPetName}】的定制需求与照片信息。
                  制作完成后，专属兑换码与角色包将第一时间发送至 <strong>{customOwnerEmail}</strong>。
                </p>
                <div className="success-note">
                  💡 交付后您可以在桌面端直接兑换；也可在桌面右键随时移除或在展馆随时重新唤回！
                </div>
                <button
                  type="button"
                  className="gallery-cta-primary"
                  onClick={() => {
                    setCustomOrderNumber(null)
                    setIsCustomModalOpen(false)
                  }}
                >
                  完成并返回展馆
                </button>
              </div>
            ) : (
              <form className="custom-order-form" onSubmit={handleSubmitCustomPet}>
                <div className="form-group-row">
                  <div className="form-group">
                    <label>毛孩子昵称 *</label>
                    <input
                      type="text"
                      required
                      placeholder="例如：波波、奶黄包、咕咕"
                      value={customPetName}
                      onChange={(e) => setCustomPetName(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>宠物品种 *</label>
                    <select value={customPetType} onChange={(e) => setCustomPetType(e.target.value)}>
                      <option value="cat">🐱 猫咪 (英短/美短/布偶/田园等)</option>
                      <option value="dog">🐶 狗狗 (柴犬/柯基/金毛/泰迪等)</option>
                      <option value="hamster">🐹 仓鼠 / 荷兰猪 / 龙猫</option>
                      <option value="rabbit">🐰 兔兔</option>
                      <option value="other">🦜 鸟类 / 异宠</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>📸 上传生活萌照 (建议 3~5 张正面、侧面、打盹姿态)</label>
                  <div className="photo-upload-dropzone">
                    <Upload size={24} className="upload-icon" />
                    <p>点击选择或拖拽宠物生活照至此处</p>
                    <span className="upload-sub">支持 PNG、JPG、WebP，清晰抓拍更佳</span>
                    <input
                      type="file"
                      multiple
                      accept="image/*"
                      className="photo-file-input"
                      onChange={handlePhotoUploadMock}
                    />
                  </div>

                  {customPhotos.length > 0 && (
                    <div className="uploaded-photos-list">
                      {customPhotos.map((name, idx) => (
                        <span key={idx} className="photo-chip">
                          📷 {name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label>期望动作愿望</label>
                  <input
                    type="text"
                    placeholder="例如：踩奶、伸懒腰、摇尾巴、好奇歪头"
                    value={customPetActions}
                    onChange={(e) => setCustomPetActions(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>接收兑换码的邮箱 *</label>
                  <input
                    type="email"
                    required
                    placeholder="your-email@example.com"
                    value={customOwnerEmail}
                    onChange={(e) => setCustomOwnerEmail(e.target.value)}
                  />
                </div>

                <div className="custom-order-footer">
                  <button type="button" className="gallery-btn-sm" onClick={() => setIsCustomModalOpen(false)}>
                    取消
                  </button>
                  <button type="submit" className="gallery-cta-primary">
                    <Send size={16} />
                    <span>提交定制预约需求</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* 浮动 Toast 提示 */}
      {toastMessage && (
        <div className="gallery-toast" role="status">
          <Sparkles size={16} />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  )
}
