/* eslint-disable react-refresh/only-export-components */
import { useEffect, useMemo, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Camera,
  Check,
  Copy,
  Eye,
  Film,
  Flame,
  Heart,
  Info,
  Layers,
  MessageSquare,
  PawPrint,
  Search,
  Send,
  Sparkles,
  Upload,
  Video,
  X,
  Zap,
  QrCode,
} from 'lucide-react'
import { galleryCategories, galleryPets, galleryAuthors, type GalleryPet, type PetAuthor } from './galleryData'
import { QqIcon, BilibiliIcon, DouyinIcon } from './CreatorAvatars'
import './gallery.css'

export const authorOrder = ['anime', 'nagano', 'memelab', 'storybook', 'furry'] as const

interface PetGalleryProps {
  onBackToHome?: () => void
  onClose?: () => void
  onNavigateCustom?: () => void
  onNavigateSubmit?: () => void
}

let nextOrderSeq = 1001
function generateOrderNumber() {
  nextOrderSeq += 1
  return `WP-PET-2026-${nextOrderSeq}`
}

export function PetGallery({ onBackToHome, onClose, onNavigateCustom, onNavigateSubmit }: PetGalleryProps) {
  const handleClose = onClose || onBackToHome

  // 核心多层级视图状态：'all' 全景展馆 | 'author' 作者独立展馆
  const [galleryView, setGalleryView] = useState<'all' | 'author'>('all')
  const [activeAuthorId, setActiveAuthorId] = useState<string | null>(null)

  // 筛选与搜索 (默认进入热门推荐)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('hot')

  // 详情弹窗 (Level 2)
  const [selectedPet, setSelectedPet] = useState<GalleryPet | null>(null)
  const [selectedActionIndex, setSelectedActionIndex] = useState(0)

  // 1对1私聊画师联系卡弹窗 (免在线付费通道，直连画师与自行付款)
  const [contactArtist, setContactArtist] = useState<PetAuthor | null>(null)
  const [viewingRewardQr, setViewingRewardQr] = useState<{
    qrUrl: string
    authorName: string
    petName: string
  } | null>(null)

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
  const [theme] = useState<string>(() => {
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

  // 弹窗打开时提升容器层级，防止被顶部固定导航栏遮挡点击
  useEffect(() => {
    const isModalOpen = Boolean(selectedPet || contactArtist || isCustomModalOpen)
    const parentPane = document.querySelector<HTMLElement>('.gallery-view-pane')
    if (parentPane) {
      if (isModalOpen) {
        parentPane.classList.add('has-active-modal')
      } else {
        parentPane.classList.remove('has-active-modal')
      }
    }
    return () => {
      document.querySelector<HTMLElement>('.gallery-view-pane')?.classList.remove('has-active-modal')
    }
  }, [selectedPet, contactArtist, isCustomModalOpen])

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

  // 分类实时数量统计 (全部/热门/转头猫/高帧动画/真实毛孩/轻量GIF)
  const categoryCounts = useMemo(() => {
    return {
      all: galleryPets.length,
      hot: galleryPets.filter((p) => p.isHot).length,
      tracking: galleryPets.filter((p) => p.funcType === 'tracking').length,
      animated: galleryPets.filter((p) => p.funcType === 'animated').length,
      realpet: galleryPets.filter((p) => p.funcType === 'realpet').length,
      gif: galleryPets.filter((p) => p.funcType === 'gif').length,
    }
  }, [])

  // 全景过滤角色列表 (支持热门/全部/功能专区/收藏)
  const filteredPets = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return galleryPets.filter((pet) => {
      let matchCat = false
      if (selectedCategory === 'all') {
        matchCat = true
      } else if (selectedCategory === 'hot') {
        matchCat = Boolean(pet.isHot)
      } else if (selectedCategory === 'favorite') {
        matchCat = favorites.has(pet.id)
      } else {
        matchCat = pet.funcType === selectedCategory
      }
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

  // 统一响应式标准卡片 (人物形象 ➔ 角色中文名 ➔ 一键导入)
  const renderUnifiedPetCard = (pet: GalleryPet) => {
    const isFav = favorites.has(pet.id)


    return (
      <article
        key={pet.id}
        className="unified-pet-card"
        onClick={() => openPetDetail(pet)}
        title={`点击查看【${pet.name}】动作详情与试玩`}
      >
        <div className="unified-card-topbar">
          <span />
          <button
            type="button"
            className={`unified-card-fav-btn ${isFav ? 'is-fav' : ''}`}
            onClick={(e) => toggleFavorite(e, pet.id)}
            title={isFav ? '已收藏' : '加入收藏'}
          >
            <Heart
              size={14}
              fill={isFav ? '#ef4444' : 'none'}
              color={isFav ? '#ef4444' : 'currentColor'}
            />
          </button>
        </div>

        {/* 1. 人物居中形象动图 */}
        <div className="unified-card-stage">
          <img
            src={`${import.meta.env.BASE_URL}${pet.animatedWebp || pet.image}`}
            alt={pet.name}
            className="unified-card-sprite"
            loading="lazy"
          />
        </div>

        {/* 2. 角色名 + 创作者宣传 (B站/抖音) */}
        <div className="unified-card-meta">
          <h3 className="unified-card-name">{pet.name}</h3>
          <div className="unified-card-en">{pet.enName || pet.folderName}</div>
        </div>

        {/* 3. 一键导入按钮 */}
        <div className="unified-card-actions">
          <button
            type="button"
            className="unified-card-import-btn"
            onClick={(e) => {
              e.stopPropagation()
              handleDeepLinkImport(pet)
            }}
            title={`一键导入【${pet.name}】到桌面端`}
          >
            <Zap size={14} />
            <span>一键导入</span>
          </button>
        </div>
      </article>
    )
  }

  return (
    <div className="gallery-page-container" data-gallery-theme={theme}>
      {/* 主体布局 */}
      <div className="gallery-body-layout">
        {/* 左侧分类侧边栏 */}
        <aside className="gallery-sidebar">
          <div className="gallery-sidebar-sticky">
            <div className="gallery-sidebar-title">按功能分类</div>
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
                      {cat.id === 'hot' && <Flame size={15} />}
                      {cat.id === 'all' && <Layers size={15} />}
                      {cat.id === 'tracking' && <Eye size={15} />}
                      {cat.id === 'animated' && <Video size={15} />}
                      {cat.id === 'realpet' && <PawPrint size={15} />}
                      {cat.id === 'gif' && <Film size={15} />}
                    </span>
                    <span>{cat.label}</span>
                    <span className="gallery-cat-count">
                      {categoryCounts[cat.id as keyof typeof categoryCounts] ?? cat.count}
                    </span>
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
                人气创作者
              </div>
              <div className="gallery-author-chips-wrap">
                <button
                  type="button"
                  className={`gallery-author-chip ${galleryView === 'all' && !activeAuthorId ? 'is-active' : ''}`}
                  onClick={closeAuthorProfile}
                >
                  <span>全部作者</span>
                </button>
                {authorOrder.map((authId) => {
                  const auth = galleryAuthors[authId]
                  if (!auth) return null
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
                    </button>
                  )
                })}
              </div>
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
                <span className="author-crumb-title">{activeAuthor.name} 的作品展馆</span>
                <span className="gallery-stream-count" style={{ marginLeft: 'auto' }}>
                  共 {authorPets.length} 款小鼻嘎
                </span>
              </div>

              {/* 统一响应式大网格展示该作者角色 */}
              <div className="unified-pet-grid">
                {authorPets.map((pet) => renderUnifiedPetCard(pet))}
              </div>
            </div>
          ) : (
            /* ======================= Tier 1: 全景大展馆 (All Gallery View) ======================= */
            <>
              <div className="gallery-stream-header">
                <div className="gallery-stream-title">
                  <h2>
                    {searchQuery.trim()
                      ? `搜索结果: "${searchQuery.trim()}"`
                      : galleryCategories.find((c) => c.id === selectedCategory)?.label ||
                        (selectedCategory === 'favorite' ? '我的收藏' : '全部小鼻嘎')}
                  </h2>

                  {/* 搜索框移至“热门推荐”等分类标题后面 */}
                  <div className="gallery-search-box">
                    <Search className="gallery-search-icon" size={16} />
                    <input
                      type="text"
                      className="gallery-search-input"
                      placeholder="搜索角色或创作者：自嘲熊、吉伊、Dora、狐狸..."
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
                </div>

                {/* 右侧创作者投稿入口 */}
                {onNavigateSubmit && (
                  <button
                    type="button"
                    className="gallery-stream-submit-btn"
                    onClick={onNavigateSubmit}
                    title="进入创作者投稿中心，投稿你的自制桌宠"
                  >
                    <Upload size={16} />
                    <span>创作者投稿</span>
                  </button>
                )}
              </div>

              {filteredPets.length === 0 ? (
                <div className="gallery-empty">
                  <Info size={40} />
                  <h3>没有找到符合条件的角色</h3>
                  <p>换个关键词试试，或者切换左侧分类。</p>
                </div>
              ) : (
                <div className="unified-pet-grid">
                  {filteredPets.map((pet) => renderUnifiedPetCard(pet))}
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
              {/* 弹窗左侧大舞台：动作生动演示 */}
              <div className="gallery-modal-stage">
                <div className="gallery-stage-avatar-wrap">
                  <img
                    src={`${import.meta.env.BASE_URL}${selectedPet.actions[selectedActionIndex]?.preview || selectedPet.animatedWebp || selectedPet.image}`}
                    alt={selectedPet.name}
                    className="gallery-stage-avatar"
                  />
                  <div className="stage-live-badge">
                    <span className="live-pulsing-dot" />
                    <span>{selectedPet.actions[selectedActionIndex]?.label || '待机呼吸'} · 动态演示</span>
                  </div>
                </div>

                {/* 动作切换器 (精选展示，轻量流畅) */}
                {selectedPet.actions.length > 0 && (
                  <div className="gallery-action-selector">
                    {selectedPet.actions.slice(0, 6).map((act, idx) => (
                      <button
                        key={act.id}
                        type="button"
                        className={`gallery-action-chip ${selectedActionIndex === idx ? 'is-active' : ''}`}
                        onClick={() => setSelectedActionIndex(idx)}
                        title={act.description}
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
                      {selectedPet.enName && <small className="gallery-detail-en">{selectedPet.enName}</small>}
                    </h2>
                    <button
                      type="button"
                      onClick={(e) => toggleFavorite(e, selectedPet.id)}
                      className={`gallery-fav-btn ${favorites.has(selectedPet.id) ? 'active' : ''}`}
                      style={{
                        background: 'rgba(239, 68, 68, 0.08)',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: '8px',
                        padding: '6px 14px',
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
                  </div>
                </div>

                {/* 角色生动简介 */}
                <p className="gallery-info-desc">{selectedPet.description}</p>

                {/* 当前选中动作说明 */}
                {selectedPet.actions[selectedActionIndex] && (
                  <div className="gallery-card-quote">
                    <strong>🐾 动作【{selectedPet.actions[selectedActionIndex].label}】：</strong>
                    <span>{selectedPet.actions[selectedActionIndex].description}</span>
                  </div>
                )}

                {/* 创作者专属互动名片 (包含 B站、抖音、QQ群 与 宣传) */}
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
                          <span className="creator-role-tag">认证创作者</span>
                        </div>
                        <span className="detail-author-handle">
                          {galleryAuthors[selectedPet.authorId].bio}
                        </span>
                      </div>
                    </div>

                    {/* 创作者社交账号快速关注与宣传 (B站 / 抖音 / QQ群) */}
                    <div className="detail-author-social-row">
                      {galleryAuthors[selectedPet.authorId].bilibili && (
                        <a
                          href="https://www.bilibili.com"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="author-social-link bili"
                          title={`前往 B站 关注 ${galleryAuthors[selectedPet.authorId].name}`}
                        >
                          <BilibiliIcon size={14} />
                          <span>B站: {galleryAuthors[selectedPet.authorId].bilibili}</span>
                        </a>
                      )}
                      {galleryAuthors[selectedPet.authorId].douyin && (
                        <span
                          className="author-social-link douyin"
                          title={`抖音号: ${galleryAuthors[selectedPet.authorId].douyin}`}
                        >
                          <DouyinIcon size={14} />
                          <span>抖音: {galleryAuthors[selectedPet.authorId].douyin}</span>
                        </span>
                      )}
                      {galleryAuthors[selectedPet.authorId].qqGroup && (
                        <a
                          href="https://qm.qq.com/q/aCrzrRQkqA"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="author-social-link qq"
                          title={`加入作者官方交流群: ${galleryAuthors[selectedPet.authorId].qqGroup}`}
                        >
                          <QqIcon size={13} />
                          <span>QQ群: {galleryAuthors[selectedPet.authorId].qqGroup}</span>
                        </a>
                      )}
                      {/* 创作者收款码 / 投喂占位 */}
                      <button
                        type="button"
                        className="author-social-link reward-qr"
                        onClick={() => setViewingRewardQr({
                          qrUrl: selectedPet.rewardQrCode || (galleryAuthors[selectedPet.authorId] && galleryAuthors[selectedPet.authorId].rewardQrCode) || 'artist_group_qr.jpg',
                          authorName: (galleryAuthors[selectedPet.authorId] && galleryAuthors[selectedPet.authorId].name) || selectedPet.authorName,
                          petName: selectedPet.name,
                        })}
                        title={`点击查看创作者收款码`}
                      >
                        <QrCode size={13} />
                        <span>💰 创作者收款码</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* 核心操作区：简洁明快，一键导入 */}
                <div className="gallery-integration-panel">
                  <div className="gallery-integration-buttons">
                    <button
                      type="button"
                      className="gallery-cta-primary"
                      onClick={() => handleDeepLinkImport(selectedPet)}
                      title="点击通过浏览器唤醒 Windows 客户端自动导入"
                    >
                      <Zap size={18} />
                      <span>一键导入到桌面端</span>
                    </button>

                    <button
                      type="button"
                      className="gallery-cta-secondary"
                      onClick={(e) => handleCopyCode(e, selectedPet.redeemCode, selectedPet.name)}
                      title="点击复制离线识别码"
                    >
                      {copiedCode === selectedPet.redeemCode ? <Check size={16} /> : <Copy size={16} />}
                      <span>{copiedCode === selectedPet.redeemCode ? '已复制导入码' : `离线码: ${selectedPet.redeemCode}`}</span>
                    </button>
                  </div>
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
                        navigator.clipboard.writeText('536254840')
                        showToast(`已复制官方群号 536254840！进群直接私聊【${contactArtist.name}】`)
                      }}
                    >
                      <Copy size={14} />
                      <span>复制群号 536254840</span>
                    </button>
                    <a
                      href="https://qm.qq.com/q/aCrzrRQkqA"
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

      
      {/* ======================= 创作者收款码查看弹窗 (点击打开，没有就算了) ======================= */}
      {viewingRewardQr && (
        <div className="gallery-modal-backdrop reward-qr-backdrop" onClick={() => setViewingRewardQr(null)}>
          <div className="reward-qr-modal" onClick={(e) => e.stopPropagation()}>
            <button
              className="gallery-modal-close"
              type="button"
              onClick={() => setViewingRewardQr(null)}
              title="关闭"
            >
              <X size={18} />
            </button>
            <div className="reward-qr-modal-header">
              <span className="reward-qr-modal-badge">☕ 创作者赞赏激励</span>
              <h3>支持 {viewingRewardQr.authorName} 的创作</h3>
              <p>喜欢【{viewingRewardQr.petName}】吗？给创作者投喂一杯咖啡，激励产出更多神仙动作与新角色吧！</p>
            </div>
            <div className="reward-qr-modal-body">
              <div className="reward-qr-img-wrap">
                <img
                  src={viewingRewardQr.qrUrl.startsWith('http') || viewingRewardQr.qrUrl.startsWith('data:') ? viewingRewardQr.qrUrl : `${import.meta.env.BASE_URL}${viewingRewardQr.qrUrl}`}
                  alt={`${viewingRewardQr.authorName} 收款码`}
                  className="reward-qr-modal-img"
                />
              </div>
              <div className="reward-qr-modal-tip">
                <span>✨ 小家伙今天吃饱饱啦 · 你的喜欢与陪伴就是最好的支持！</span>
              </div>
            </div>
            <div className="reward-qr-modal-footer">
              <button
                type="button"
                className="reward-qr-modal-close-btn"
                onClick={() => setViewingRewardQr(null)}
              >
                我知道啦
              </button>
            </div>
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
