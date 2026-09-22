import { useEffect, useMemo, useState } from 'react'
import {
  Camera,
  Check,
  Code2,
  Copy,
  Download,
  ExternalLink,
  Heart,
  Home,
  Info,
  Layers,
  PawPrint,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from 'lucide-react'
import { galleryCategories, galleryPets, galleryAuthors, type GalleryPet } from './galleryData'
import './gallery.css'

interface PetGalleryProps {
  onBackToHome?: () => void
  onClose?: () => void
}

const themeOptions = [
  { id: 'klein', name: '靛蓝', color: '#3559d8' },
  { id: 'violet', name: '紫罗兰', color: '#7c3aed' },
  { id: 'teal', name: '黛绿', color: '#0d9488' },
  { id: 'amber', name: '蜜橙', color: '#ea580c' },
  { id: 'rose', name: '玫红', color: '#e11d48' },
  { id: 'pink', name: '樱粉', color: '#db2777' },
  { id: 'yellow', name: '赤金', color: '#d97706' },
  { id: 'zinc', name: '石墨', color: '#27272a' },
] as const

let nextOrderSeq = 1001
function generateOrderNumber() {
  nextOrderSeq += 1
  return `WP-PET-2026-${nextOrderSeq}`
}

export function PetGallery({ onBackToHome, onClose }: PetGalleryProps) {
  const handleClose = onClose || onBackToHome
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all')
  const [selectedPet, setSelectedPet] = useState<GalleryPet | null>(null)
  const [selectedActionIndex, setSelectedActionIndex] = useState(0)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  // 弹窗状态：家宠定制预约弹窗 & 创作者开源平台弹窗
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false)
  const [isCreatorModalOpen, setIsCreatorModalOpen] = useState(false)
  const [creatorActiveTab, setCreatorActiveTab] = useState<'guide' | 'submit'>('guide')

  // 家宠定制表单状态
  const [customPetName, setCustomPetName] = useState('')
  const [customPetType, setCustomPetType] = useState('cat')
  const [customPetActions, setCustomPetActions] = useState('伸懒腰、踩奶、打盹、歪头')
  const [customOwnerEmail, setCustomOwnerEmail] = useState('')
  const [customDeliveryMode, setCustomDeliveryMode] = useState<'private' | 'public'>('private')
  const [customPhotos, setCustomPhotos] = useState<string[]>([])
  const [customOrderNumber, setCustomOrderNumber] = useState<string | null>(null)

  // 创作者提交表单状态
  const [submitAuthorName, setSubmitAuthorName] = useState('')
  const [submitAuthorLink, setSubmitAuthorLink] = useState('')
  const [submitPetName, setSubmitPetName] = useState('')
  const [submitPetLicense, setSubmitPetLicense] = useState('CC-BY-4.0')
  const [submitPetDesc, setSubmitPetDesc] = useState('')
  const [submitFileAttached, setSubmitFileAttached] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)

  const [theme, setTheme] = useState<string>(() => {
    return localStorage.getItem('windowpet-gallery-theme') || 'klein'
  })
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem('windowpet-gallery-favs')
      return stored ? new Set(JSON.parse(stored)) : new Set(['jiyi', 'nuonuo', 'fox', 'maicuijiao'])
    } catch {
      return new Set(['jiyi', 'nuonuo', 'fox', 'maicuijiao'])
    }
  })

  // 切换主题时持久化
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

  // 弹出 Toast
  const showToast = (msg: string) => {
    setToastMessage(msg)
  }

  useEffect(() => {
    if (!toastMessage) return
    const timer = setTimeout(() => setToastMessage(null), 3200)
    return () => clearTimeout(timer)
  }, [toastMessage])

  // 展馆模式下隐藏主站右下角 ICP 备案号浮条，返回主页时自动还原
  useEffect(() => {
    const icp = document.querySelector<HTMLElement>('.site-icp-filing')
    if (!icp) return
    const prevDisplay = icp.style.display
    icp.style.display = 'none'
    return () => {
      icp.style.display = prevDisplay
    }
  }, [])

  // 复制兑换码
  const handleCopyCode = (e: React.MouseEvent, code: string, petName: string) => {
    e.stopPropagation()
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(code)
      showToast(`🎉 兑换码 ${code} 已复制！在桌面端粘贴即可解锁【${petName}】`)
      setTimeout(() => setCopiedCode(null), 2500)
    })
  }

  // 核心功能 (a)：一键唤醒导入桌面客户端
  const handleDeepLinkImport = (pet: GalleryPet) => {
    const deepLinkUrl = `windowpet://import?pet=${encodeURIComponent(pet.id)}&code=${encodeURIComponent(pet.redeemCode)}&name=${encodeURIComponent(pet.name)}`
    
    // 触发系统 URL 协议唤醒
    window.open(deepLinkUrl, '_self')
    
    showToast(`🚀 正在呼叫 WindowPet 桌面端导入【${pet.name}】...`)
    
    // 兜底复制
    navigator.clipboard.writeText(pet.redeemCode)
  }

  // 过滤结果
  const filteredPets = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return galleryPets.filter((pet) => {
      const matchCat =
        selectedCategory === 'all' ||
        (selectedCategory === 'favorite' ? favorites.has(pet.id) : pet.category === selectedCategory)
      if (!matchCat) return false

      const matchAuthor = selectedAuthor === 'all' || pet.authorId === selectedAuthor
      if (!matchAuthor) return false

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
  }, [searchQuery, selectedCategory, selectedAuthor, favorites])

  // 打开详情
  const openPetDetail = (pet: GalleryPet) => {
    setSelectedPet(pet)
    setSelectedActionIndex(0)
  }

  // 关闭详情
  const closePetDetail = () => {
    setSelectedPet(null)
  }

  // 处理家宠定制照片模拟上传
  const handlePhotoUploadMock = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const fileNames = Array.from(files).map((f) => f.name)
      setCustomPhotos((prev) => [...prev, ...fileNames])
      showToast(`📸 成功添加 ${files.length} 张宠物萌照！`)
    }
  }

  // 提交家宠定制预约
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

  // 提交创作者角色作品
  const handleSubmitCreatorWork = (e: React.FormEvent) => {
    e.preventDefault()
    if (!submitPetName.trim() || !submitAuthorName.trim()) {
      showToast('请填写角色名称与创作者昵称')
      return
    }
    setSubmitSuccess(true)
    showToast(`🌟 作品【${submitPetName}】提交成功！感谢共建小鼻嘎开源生态`)
  }

  // 监听 ESC 键关闭弹窗
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (selectedPet) {
          closePetDetail()
        } else if (isCustomModalOpen) {
          setIsCustomModalOpen(false)
        } else if (isCreatorModalOpen) {
          setIsCreatorModalOpen(false)
        } else if (handleClose) {
          handleClose()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedPet, isCustomModalOpen, isCreatorModalOpen, handleClose])

  return (
    <div className="gallery-page-container" data-gallery-theme={theme}>
      {/* 顶部导航 Header */}
      <header className="gallery-header">
        <div className="gallery-header-left">
          <div className="gallery-logo-brand">
            <PawPrint size={22} color="var(--brand)" />
            <span>WindowPet</span>
            <span className="gallery-logo-badge">小鼻嘎展馆 · 全 24 款萌宠</span>
          </div>
        </div>

        <div className="gallery-header-right">
          {/* 搜索框 */}
          <div className="gallery-search-box">
            <Search className="gallery-search-icon" size={16} />
            <input
              type="text"
              className="gallery-search-input"
              placeholder="搜索角色：吉伊、柴犬、家宠、fox..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
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

          {/* 快捷通道按钮：家宠定制 & 创作者开源计划 */}
          <button
            type="button"
            className="gallery-nav-action-btn gallery-nav-custom-btn"
            onClick={() => {
              setSelectedCategory('home')
              setIsCustomModalOpen(true)
            }}
            title="定制自家的猫猫狗狗等毛孩子到电脑桌面"
          >
            <Camera size={15} />
            <span>家宠定制</span>
          </button>

          <button
            type="button"
            className="gallery-nav-action-btn gallery-nav-creator-btn"
            onClick={() => setIsCreatorModalOpen(true)}
            title="WindowPet 角色制作开源规范与作品提交"
          >
            <Code2 size={15} />
            <span>开源计划</span>
          </button>

          {/* 8色主题色调色盘 (仿 VibeHub) */}
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
            <div className="gallery-sidebar-title">角色图鉴分类</div>
            <div className="gallery-sidebar-chips-wrap">
              {galleryCategories.map((cat) => {
                const isActive = selectedCategory === cat.id
                return (
                  <button
                    key={cat.id}
                    type="button"
                    className={`gallery-cat-chip ${isActive ? 'is-active' : ''}`}
                    onClick={() => {
                      setSelectedCategory(cat.id)
                      setSelectedAuthor('all')
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
                className={`gallery-cat-chip ${selectedCategory === 'favorite' ? 'is-active' : ''}`}
                onClick={() => {
                  setSelectedCategory('favorite')
                  setSelectedAuthor('all')
                }}
              >
                <span className="gallery-cat-chip-icon">
                  <Heart size={15} fill={selectedCategory === 'favorite' ? 'currentColor' : 'none'} />
                </span>
                <span>我的收藏</span>
                <span className="gallery-cat-count">{favorites.size}</span>
              </button>
            </div>

            {/* 创作者筛选专栏 */}
            <div className="gallery-author-filter-wrap">
              <div className="gallery-sidebar-title" style={{ marginTop: '16px', marginBottom: '8px' }}>
                创作者专栏
              </div>
              <div className="gallery-author-chips-wrap">
                <button
                  type="button"
                  className={`gallery-author-chip ${selectedAuthor === 'all' ? 'is-active' : ''}`}
                  onClick={() => setSelectedAuthor('all')}
                >
                  <span>全部创作者</span>
                </button>
                {Object.values(galleryAuthors).map((auth) => (
                  <button
                    key={auth.id}
                    type="button"
                    className={`gallery-author-chip ${selectedAuthor === auth.id ? 'is-active' : ''}`}
                    onClick={() => {
                      setSelectedAuthor(auth.id)
                      setSelectedCategory('all')
                    }}
                    title={auth.bio}
                  >
                    <span className="author-chip-name">{auth.name}</span>
                    <small className="author-chip-badge">{auth.badge}</small>
                  </button>
                ))}
              </div>
            </div>

            {/* 侧边栏功能入口卡片：家宠专属定制 */}
            <button
              type="button"
              className="gallery-sidebar-action-card custom-action-card"
              onClick={() => {
                setSelectedCategory('home')
                setIsCustomModalOpen(true)
              }}
            >
              <div className="sidebar-action-icon">
                <Camera size={18} />
              </div>
              <div className="sidebar-action-text">
                <strong>定制自家毛孩子</strong>
                <span>拍照上传 · 专属神态还原</span>
              </div>
            </button>

            {/* 侧边栏功能入口卡片：创作者开源计划 */}
            <button
              type="button"
              className="gallery-sidebar-action-card creator-action-card"
              onClick={() => setIsCreatorModalOpen(true)}
            >
              <div className="sidebar-action-icon">
                <Code2 size={18} />
              </div>
              <div className="sidebar-action-text">
                <strong>角色开源共创计划</strong>
                <span>提供制作指引 · 欢迎民间投稿</span>
              </div>
              <Sparkles size={14} className="sidebar-action-badge" />
            </button>

            <div className="gallery-sidebar-banner">
              <strong>💡 随时随地 增删无忧</strong>
              <span>
                电脑端桌面上对宠物点击右键即可随时【收回宠物】；想念它时随时回到本展馆，点击【一键导入到桌面】即可秒级召唤！
              </span>
            </div>
          </div>
        </aside>

        {/* 右侧主内容网格 */}
        <main className="gallery-main-content">
          {/* Banner 头部 */}
          <section className="gallery-hero-banner">
            <div className="gallery-hero-text">
              <h1>小鼻嘎展馆 · 角色图鉴</h1>
              <p>探索 21 款精选桌面伙伴（含真实家宠与民间共创），支持一键唤醒导入桌面，或复制公开兑换码随心解锁！</p>
            </div>
            <div className="gallery-hero-badge-strip">
              <div className="gallery-hero-metric">
                <strong>21</strong>
                <span>全收录伙伴</span>
              </div>
              <div className="gallery-hero-metric">
                <strong>100%</strong>
                <span>免登录兑换</span>
              </div>
              <div className="gallery-hero-metric">
                <strong>开源</strong>
                <span>民间共创支持</span>
              </div>
            </div>
          </section>

          {/* 当选中“家宠”分类时，展示专属定制说明大 Banner */}
          {selectedCategory === 'home' && (
            <section className="custom-pet-spotlight-banner">
              <div className="spotlight-left">
                <div className="spotlight-badge">
                  <Camera size={15} />
                  <span>家宠专属定制通道</span>
                </div>
                <h2>想把自家的毛孩子做成电脑桌宠吗？</h2>
                <p>
                  只需拍 3~5 张爱宠日常生活照（正面发呆、侧面玩耍、伸懒腰抓拍）上传至后台。
                  我们将通过专业切帧工作流还原它的可爱神态与专属互动！
                  制作完成后，通过专属兑换码发送至您的邮箱，也可在展馆公开展出。
                </p>
                
                <div className="spotlight-steps">
                  <div className="spotlight-step-item">
                    <span className="step-num">1</span>
                    <span>手机拍萌照</span>
                  </div>
                  <span className="spotlight-step-arrow">→</span>
                  <div className="spotlight-step-item">
                    <span className="step-num">2</span>
                    <span>上传定制需求</span>
                  </div>
                  <span className="spotlight-step-arrow">→</span>
                  <div className="spotlight-step-item">
                    <span className="step-num">3</span>
                    <span>工坊转绘切帧</span>
                  </div>
                  <span className="spotlight-step-arrow">→</span>
                  <div className="spotlight-step-item">
                    <span className="step-num">4</span>
                    <span>邮箱领码/导入桌面</span>
                  </div>
                </div>

                <div className="spotlight-cta-row">
                  <button
                    type="button"
                    className="spotlight-cta-btn"
                    onClick={() => setIsCustomModalOpen(true)}
                  >
                    <Upload size={16} />
                    <span>立即上传照片预约定制</span>
                  </button>
                  <span className="spotlight-cta-hint">
                    💡 在电脑端右键即可随时关闭/收回宠物，想念时随时来这里一键重新召唤！
                  </span>
                </div>
              </div>

              <div className="spotlight-right-tags">
                <div className="spotlight-feature-card">
                  <strong>🔒 专属私密交付</strong>
                  <p>定制的兑换码只发到您的私人邮箱，专属于您一个人的桌面独家陪伴。</p>
                </div>
                <div className="spotlight-feature-card">
                  <strong>🌟 官网入馆陈列</strong>
                  <p>可选将您的爱宠上架至【家宠】专区，让全网用户一起吸宠互动！</p>
                </div>
              </div>
            </section>
          )}

          {/* 角色卡片网格 */}
          {filteredPets.length === 0 ? (
            <div className="gallery-empty">
              <Info size={40} />
              <h3>没有找到符合条件的小鼻嘎</h3>
              <p>换个关键词试试，或者切换到【全部小鼻嘎】分类。</p>
            </div>
          ) : (
            <div className="gallery-grid">
              {filteredPets.map((pet) => {
                const isFav = favorites.has(pet.id)
                const isHomePet = pet.category === 'home'
                return (
                  <article
                    key={pet.id}
                    className={`gallery-card ${isHomePet ? 'is-home-pet-card' : ''}`}
                    onClick={() => openPetDetail(pet)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && openPetDetail(pet)}
                  >
                    {/* 卡片头 */}
                    <div className="gallery-card-header">
                      <div className="gallery-card-title-group">
                        <h3>
                          <span>{pet.name}</span>
                          <span className="gallery-worktype-tag">{pet.workType}</span>
                        </h3>
                        <div className="gallery-card-meta-line">
                          <span className="gallery-card-en">{pet.enName}</span>
                          <span className="gallery-author-pill">🎨 {pet.authorName}</span>
                        </div>
                      </div>
                      <button
                        type="button"
                        className={`gallery-fav-btn ${isFav ? 'is-fav' : ''}`}
                        onClick={(e) => toggleFavorite(e, pet.id)}
                        title={isFav ? '已收藏' : '收藏'}
                      >
                        <Heart size={18} fill={isFav ? '#ef4444' : 'none'} color={isFav ? '#ef4444' : 'currentColor'} />
                      </button>
                    </div>

                    {/* 台词 Quote (VibeHub 风格) */}
                    <blockquote className="gallery-card-quote">
                      {pet.tagline}
                    </blockquote>

                    {/* 动作预览区 */}
                    <div className="gallery-card-preview">
                      <img
                        src={`${import.meta.env.BASE_URL}${pet.image}`}
                        alt={pet.name}
                        className="gallery-card-img"
                        loading="lazy"
                      />
                    </div>

                    {/* 标签 */}
                    <div className="gallery-card-tags">
                      {pet.traits.slice(0, 3).map((t) => (
                        <span key={t} className="gallery-card-tag">
                          {t}
                        </span>
                      ))}
                    </div>

                    {/* 增删无忧提示 */}
                    <div className="gallery-card-summon-tip">
                      <span>💡 右键随时收回 · 展馆一键导回</span>
                    </div>

                    {/* 底部兑换码与操作 */}
                    <div className="gallery-card-footer">
                      <span className="gallery-redeem-badge" title="官方公开兑换码">
                        <Sparkles size={12} />
                        {pet.redeemCode}
                      </span>
                      <div className="gallery-card-actions">
                        <button
                          type="button"
                          className="gallery-btn-sm"
                          onClick={(e) => handleCopyCode(e, pet.redeemCode, pet.name)}
                          title="复制兑换码"
                        >
                          {copiedCode === pet.redeemCode ? <Check size={13} /> : <Copy size={13} />}
                          <span>{copiedCode === pet.redeemCode ? '已复制' : '复制码'}</span>
                        </button>
                        <button
                          type="button"
                          className="gallery-btn-sm gallery-btn-primary-sm"
                          onClick={() => openPetDetail(pet)}
                        >
                          <span>档案</span>
                        </button>
                      </div>
                    </div>
                  </article>
                )
              })}
            </div>
          )}
        </main>
      </div>

      {/* 沉浸式详情弹窗 (Modal) */}
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
                  <h2>
                    <span>{selectedPet.name}</span>
                    <span className="gallery-card-en">{selectedPet.enName}</span>
                    <span className="gallery-worktype-tag">{selectedPet.workType}</span>
                  </h2>
                  <div className="gallery-author-box">
                    <span className="gallery-author-label">创作者：</span>
                    <strong className="gallery-author-name">{selectedPet.authorName}</strong>
                    <span className="gallery-author-handle">{selectedPet.authorHandle}</span>
                    <span className="gallery-license-tag">协议：{selectedPet.license}</span>
                  </div>
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
                      <strong>{val}</strong>
                      <span>{lbl}</span>
                    </div>
                  ))}
                </div>

                {/* 社区创作与避风港保护原则免责说明 */}
                <div className="gallery-copyright-notice">
                  <ShieldCheck size={18} color="#2563eb" />
                  <div>
                    <strong>社区创作与避风港保护原则：</strong>
                    <span>
                      本形象属于【{selectedPet.workType}】，由民间创作者自发上传分享，遵循《{selectedPet.license}》。仅供个人非商用桌面美化与技术交流，非 WindowPet 官方商业角色。若权利人认为本作品侵犯了您的合法权益，请联系我们（邮箱/QQ群），核实后将在 24 小时内即刻执行下架处理。
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

                {/* 核心互通操作区：一键唤醒导入 + 复制码 */}
                <div className="gallery-integration-panel">
                  <div className="gallery-integration-title">
                    <strong>
                      <Sparkles size={16} /> 官方公开兑换码（免费）
                    </strong>
                    <span className="gallery-card-en">免登录直接使用</span>
                  </div>

                  <div className="gallery-code-display">
                    <span className="gallery-code-text">{selectedPet.redeemCode}</span>
                    <button
                      type="button"
                      className="gallery-btn-sm"
                      onClick={(e) => handleCopyCode(e, selectedPet.redeemCode, selectedPet.name)}
                    >
                      {copiedCode === selectedPet.redeemCode ? <Check size={14} /> : <Copy size={14} />}
                      <span>{copiedCode === selectedPet.redeemCode ? '已复制' : '一键复制'}</span>
                    </button>
                  </div>

                  <div className="gallery-integration-buttons">
                    <button
                      type="button"
                      className="gallery-cta-primary"
                      onClick={() => handleDeepLinkImport(selectedPet)}
                      title="点击通过浏览器唤醒 Windows 客户端自动导入"
                    >
                      <ExternalLink size={18} />
                      <span>一键导入到桌面</span>
                    </button>

                    <button
                      type="button"
                      className="gallery-cta-secondary"
                      onClick={(e) => handleCopyCode(e, selectedPet.redeemCode, selectedPet.name)}
                    >
                      <Copy size={16} />
                      <span>复制兑换码</span>
                    </button>
                  </div>

                  <p className="gallery-integration-hint">
                    <Info size={14} />
                    桌面端打开【兑换角色】窗口，直接粘贴上述兑换码，无需登录即可激活！
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 家宠定制预约弹窗 (CustomPetModal) */}
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
                <p>拍下自家宠物的真实生活照片，由 WindowPet 创作者工坊切帧制作，生成专属角色！</p>
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
                  我们已接收到关于【{customPetName}】的定制信息与照片需求。
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

                <div className="form-group-row">
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

                  <div className="form-group">
                    <label>交付方式偏好</label>
                    <select
                      value={customDeliveryMode}
                      onChange={(e) => setCustomDeliveryMode(e.target.value as 'private' | 'public')}
                    >
                      <option value="private">🔒 专属私密交付（仅发到邮箱，独家陪伴）</option>
                      <option value="public">🌟 展馆公开陈列（上架到展馆家宠区，供大家吸宠）</option>
                    </select>
                  </div>
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

      {/* 创作者开放平台 / 角色开源计划弹窗 (CreatorModal) */}
      {isCreatorModalOpen && (
        <div className="gallery-modal-backdrop" onClick={() => setIsCreatorModalOpen(false)}>
          <div className="gallery-modal creator-hub-modal" onClick={(e) => e.stopPropagation()}>
            <button className="gallery-modal-close" type="button" onClick={() => setIsCreatorModalOpen(false)}>
              <X size={18} />
            </button>

            <div className="creator-modal-header">
              <div className="creator-modal-icon">
                <Code2 size={24} />
              </div>
              <div>
                <h2>WindowPet 角色设计开源计划</h2>
                <p>全面开放角色制作规范！欢迎民间画师、建模师与 AI 创作者一起共建小鼻嘎宇宙。</p>
              </div>
            </div>

            <div className="creator-modal-tabs">
              <button
                type="button"
                className={`creator-tab-btn ${creatorActiveTab === 'guide' ? 'is-active' : ''}`}
                onClick={() => setCreatorActiveTab('guide')}
              >
                <Layers size={16} />
                <span>制作规范与开源工具</span>
              </button>
              <button
                type="button"
                className={`creator-tab-btn ${creatorActiveTab === 'submit' ? 'is-active' : ''}`}
                onClick={() => setCreatorActiveTab('submit')}
              >
                <Upload size={16} />
                <span>提交我的角色作品</span>
              </button>
            </div>

            {creatorActiveTab === 'guide' ? (
              <div className="creator-tab-content">
                <div className="creator-guide-grid">
                  <div className="guide-card">
                    <div className="guide-card-icon">1</div>
                    <h4>动作规格与画布</h4>
                    <p>
                      支持 128x128、192x192 或 256x256 透明 PNG/WebP 序列帧。保持中心对齐与一致的接触地面。
                    </p>
                  </div>

                  <div className="guide-card">
                    <div className="guide-card-icon">2</div>
                    <h4>内置 AI 制作套件</h4>
                    <p>
                      WindowPet 自带《AI角色制作工作流》（位于项目 <code>AI角色制作</code> 目录），支持豆包/即梦图生图与自动批量切片。
                    </p>
                  </div>

                  <div className="guide-card">
                    <div className="guide-card-icon">3</div>
                    <h4>asset.json 骨骼配置</h4>
                    <p>
                      声明 <code>idle</code>、<code>drag</code>、<code>tumble</code> 等触发器动作。简单直观，即写即用。
                    </p>
                  </div>

                  <div className="guide-card">
                    <div className="guide-card-icon">4</div>
                    <h4>全网展馆入驻</h4>
                    <p>
                      通过审核的作品将永久陈列于【小鼻嘎展馆】，并附带创作者个人主页与社交账号署名！
                    </p>
                  </div>
                </div>

                <div className="creator-download-box">
                  <div>
                    <strong>开源脚手架与规范包</strong>
                    <p>包含 asset.json 标准模板、动作帧切片示意图与 Python 校验脚本</p>
                  </div>
                  <button
                    type="button"
                    className="gallery-cta-secondary"
                    onClick={() => {
                      showToast('已复制 AI 角色制作套件目录路径：AI角色制作/AI角色制作完整指引_Doubao.md')
                    }}
                  >
                    <Download size={16} />
                    <span>获取制作脚手架</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="creator-tab-content">
                {submitSuccess ? (
                  <div className="creator-submit-success">
                    <div className="success-icon-wrap">
                      <Check size={36} color="#16a34a" />
                    </div>
                    <h3>作品已提交！</h3>
                    <p>
                      感谢创作者 <strong>{submitAuthorName}</strong> 投递的【{submitPetName}】！
                      审核通过后将上架至【小鼻嘎展馆】，并提供一键导入和专属公开码。
                    </p>
                    <button
                      type="button"
                      className="gallery-cta-primary"
                      onClick={() => {
                        setSubmitSuccess(false)
                        setIsCreatorModalOpen(false)
                      }}
                    >
                      完成
                    </button>
                  </div>
                ) : (
                  <form className="creator-submit-form" onSubmit={handleSubmitCreatorWork}>
                    <div className="form-group-row">
                      <div className="form-group">
                        <label>角色名称 *</label>
                        <input
                          type="text"
                          required
                          placeholder="例如：机甲小兔、咖啡企鹅"
                          value={submitPetName}
                          onChange={(e) => setSubmitPetName(e.target.value)}
                        />
                      </div>

                      <div className="form-group">
                        <label>创作者昵称 *</label>
                        <input
                          type="text"
                          required
                          placeholder="您的画师/开发者名称"
                          value={submitAuthorName}
                          onChange={(e) => setSubmitAuthorName(e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="form-group-row">
                      <div className="form-group">
                        <label>个人主页 / GitHub / B站</label>
                        <input
                          type="url"
                          placeholder="https://..."
                          value={submitAuthorLink}
                          onChange={(e) => setSubmitAuthorLink(e.target.value)}
                        />
                      </div>

                      <div className="form-group">
                        <label>开源许可协议</label>
                        <select value={submitPetLicense} onChange={(e) => setSubmitPetLicense(e.target.value)}>
                          <option value="CC-BY-4.0">知识共享 CC-BY 4.0 (允许使用并保留署名)</option>
                          <option value="MIT">MIT License (完全自由开源)</option>
                          <option value="CC0">CC0 (公有领域，无任何限制)</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-group">
                      <label>角色简介与灵感故事</label>
                      <textarea
                        rows={3}
                        placeholder="简单介绍一下你的角色设计灵感、有哪些好玩的互动动作..."
                        value={submitPetDesc}
                        onChange={(e) => setSubmitPetDesc(e.target.value)}
                      />
                    </div>

                    <div className="form-group">
                      <label>上传角色包 (.wpet 或动作帧 ZIP)</label>
                      <div
                        className="photo-upload-dropzone"
                        onClick={() => setSubmitFileAttached(true)}
                        style={{ cursor: 'pointer' }}
                      >
                        <Upload size={22} className="upload-icon" />
                        <p>{submitFileAttached ? '已选择角色资源包 (.zip/.wpet)' : '点击上传打包好的角色文件'}</p>
                      </div>
                    </div>

                    <div className="custom-order-footer">
                      <button type="button" className="gallery-btn-sm" onClick={() => setIsCreatorModalOpen(false)}>
                        取消
                      </button>
                      <button type="submit" className="gallery-cta-primary">
                        <Send size={16} />
                        <span>提交审核入馆</span>
                      </button>
                    </div>
                  </form>
                )}
              </div>
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
