import { useState } from 'react'
import {
  Camera,
  Gift,
  HeartHandshake,
  Home,
  Palette,
  Sparkles,
  ArrowRight,
  Copy,
  Check,
  MessageSquare,
  Volume2,
  Download,
  Heart,
} from 'lucide-react'
import './subpages.css'

interface CustomPetPageProps {
  onBackToHome?: () => void
  onOpenGallery?: () => void
}

const qqGroupUrl = 'https://qm.qq.com/q/cYlRBbvuda'

type XiaoWangActionKey = 'idle' | 'click' | 'drag'

interface PostcardItem {
  id: string
  title: string
  img: string
  actionKey: XiaoWangActionKey
  rotation: string
}

export function CustomPetPage({ onBackToHome, onOpenGallery }: CustomPetPageProps) {
  const [copiedQq, setCopiedQq] = useState(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [activeXiaoWangAction, setActiveXiaoWangAction] = useState<XiaoWangActionKey>('idle')

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => {
      setToastMessage(null)
    }, 2800)
  }

  const handleCopyQq = () => {
    try {
      navigator.clipboard.writeText('422616922')
      setCopiedQq(true)
      showToast('官方定制直通群号 422616922 已复制！')
      setTimeout(() => setCopiedQq(false), 2400)
    } catch {
      // ignore
    }
  }

  const handleDeepLink = (code: string, petName: string) => {
    const deepLinkUrl = `windowpet://import?code=${encodeURIComponent(code)}&name=${encodeURIComponent(petName)}`
    window.open(deepLinkUrl, '_self')
    showToast(`🚀 正在呼叫 WindowPet 桌面端装载【${petName}】...`)
    try {
      navigator.clipboard.writeText(code)
    } catch {
      // ignore
    }
  }

  // 小汪生全部动作配置（极简定义）
  const xiaoWangActions: Record<
    XiaoWangActionKey,
    { label: string; anim: string; tag: string }
  > = {
    idle: {
      label: '伴读待机',
      anim: `${import.meta.env.BASE_URL}pets/xiaowang-idle.webp`,
      tag: '吐舌微笑',
    },
    click: {
      label: '欢快奔跑',
      anim: `${import.meta.env.BASE_URL}pets/xiaowang-click.webp`,
      tag: '短腿撒欢',
    },
    drag: {
      label: '悬空拖拽',
      anim: `${import.meta.env.BASE_URL}pets/xiaowang-drag.webp`,
      tag: '超人飞扑',
    },
  }

  // 小汪生真实写真明信片（极简纯粹，去除大段繁琐说明）
  const postcards: PostcardItem[] = [
    {
      id: 'p1',
      title: '吐舌笑',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-1-smile.png`,
      actionKey: 'idle',
      rotation: '-2.5deg',
    },
    {
      id: 'p2',
      title: '欢快跑',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-3-running.png`,
      actionKey: 'click',
      rotation: '2deg',
    },
    {
      id: 'p3',
      title: '超人飞',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-5-flying.png`,
      actionKey: 'drag',
      rotation: '-1.8deg',
    },
    {
      id: 'p4',
      title: '歪头杀',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-2-happy.png`,
      actionKey: 'idle',
      rotation: '2.4deg',
    },
    {
      id: 'p5',
      title: '捉蝴蝶',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-4-pounce.png`,
      actionKey: 'click',
      rotation: '-2.2deg',
    },
    {
      id: 'p6',
      title: '小太阳',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-6-airborne.png`,
      actionKey: 'drag',
      rotation: '1.5deg',
    },
  ]

  // 特邀画师极简作品
  const artistChains = [
    {
      id: 'chestnut',
      name: '@糖炒栗子',
      initial: '栗',
      role: '真实毛发专精',
      cases: [
        {
          id: 'maicuijiao',
          title: '田园橘猫 · 麦脆角',
          img: `${import.meta.env.BASE_URL}pets/jiyi-action-waving.webp`,
          redeemCode: 'WPX-2026-JIYI',
        },
        {
          id: 'snowball',
          title: '纯种布偶 · 雪球',
          img: `${import.meta.env.BASE_URL}pets/cat.png`,
          redeemCode: 'WPX-2026-CAT',
        },
      ],
    },
    {
      id: 'mino',
      name: '@米诺画画中',
      initial: '米',
      role: '灵动神态专精',
      cases: [
        {
          id: 'huanhuan',
          title: '短腿柯基 · 欢欢',
          img: `${import.meta.env.BASE_URL}pets/dog.png`,
          redeemCode: 'WPX-2026-DOG',
        },
        {
          id: 'moyu-fox',
          title: '赤狐小皮皮',
          img: `${import.meta.env.BASE_URL}pets/fox.png`,
          redeemCode: 'WPX-2026-FOX',
        },
      ],
    },
  ]

  // 极简 4 步流程
  const steps = [
    { num: '01', icon: Camera, title: '发生活照', desc: '1~2 张清晰爱宠照片' },
    { num: '02', icon: Palette, title: '选专属动作', desc: '待机、跑动、拖拽等' },
    { num: '03', icon: HeartHandshake, title: '私聊画师', desc: '群内 1对1 沟通，自行付款' },
    { num: '04', icon: Gift, title: '导入桌面', desc: '双击专属文件即刻陪伴' },
  ]

  return (
    <div className="page-view-pane custom-pet-page-pure-pink">
      {/* 浮动操作提示 */}
      {toastMessage && (
        <div className="gallery-toast-pill pink-toast-pill" role="status" aria-live="polite">
          <Sparkles size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      <div className="subpage-container">
        {/* 极简风 Hero */}
        <header className="subpage-hero" style={{ paddingBottom: '20px' }}>
          <span className="eyebrow pink-eyebrow custom-eyebrow-with-avatar">
            <span className="custom-hero-avatar-badge" title="小汪生">
              <img
                src={`${import.meta.env.BASE_URL}pets/xiaowang-avatar.png`}
                alt="小汪"
                className="custom-hero-avatar-img"
              />
            </span>
            <span>小汪生示范 · 爱宠专属定制</span>
          </span>
          <h1>把自家的毛孩子，做进电脑桌面</h1>
          <p className="subpage-lead" style={{ maxWidth: '620px', margin: '0 auto 20px auto' }}>
            给画师发几张生活照，纯手工切帧制作生动动作，让自家的毛孩子常驻桌面陪伴你。
          </p>

          <div className="subpage-hero-actions">
            <a
              className="primary-download pink-primary-btn"
              href={qqGroupUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ padding: '10px 24px', fontSize: '14.5px' }}
            >
              <HeartHandshake size={17} />
              <span>进群私聊约稿</span>
            </a>

            <button
              type="button"
              className="secondary-action pink-secondary-btn"
              onClick={handleCopyQq}
              style={{ padding: '10px 20px', fontSize: '14px' }}
            >
              {copiedQq ? <Check size={15} color="#ff6b81" /> : <Copy size={15} />}
              <span>{copiedQq ? '已复制群号 422616922' : 'QQ群：422616922'}</span>
            </button>

            {onOpenGallery && (
              <button
                type="button"
                className="secondary-action pink-secondary-btn"
                onClick={onOpenGallery}
                style={{ padding: '10px 20px', fontSize: '14px' }}
              >
                <Sparkles size={15} />
                <span>小鼻嘎展馆</span>
              </button>
            )}

            {onBackToHome && (
              <button
                type="button"
                className="secondary-action pink-secondary-btn"
                onClick={onBackToHome}
                style={{ padding: '10px 20px', fontSize: '14px' }}
              >
                <Home size={15} />
                <span>返回首页</span>
              </button>
            )}
          </div>
        </header>

        {/* =========================================================================
            小汪生 · 真实写真明信片与全部动作交互舞台
            ========================================================================= */}
        <section className="xiaowang-showcase-section">
          <div className="subpage-section-header text-center" style={{ marginBottom: '22px' }}>
            <span className="subpage-section-badge pink-badge">
              <Heart size={14} fill="#ff6b81" color="#ff6b81" />
              <span>OFFICIAL SHOWCASE</span>
            </span>
            <h2>代表作：《小汪生》写真与动作</h2>
            <p>作者为自家柯基实拍手工制作，点击明信片可切换下方动作。</p>
          </div>

          {/* 1. 明信片写真（极简无繁琐长文） */}
          <div className="xiaowang-postcard-wall" aria-label="小汪生写真明信片">
            {postcards.map((p) => {
              const isActive = activeXiaoWangAction === p.actionKey
              return (
                <div
                  key={p.id}
                  className={`xiaowang-postcard-card ${isActive ? 'is-active-card' : ''}`}
                  style={{ transform: `rotate(${p.rotation})` }}
                  onClick={() => {
                    setActiveXiaoWangAction(p.actionKey)
                    showToast(`✨ 切换至【${xiaoWangActions[p.actionKey].label}】动作`)
                  }}
                  role="button"
                  tabIndex={0}
                  title={`点击查看【${p.title}】动态演示`}
                >
                  <div className="postcard-washi-tape" />
                  <div className="postcard-stamp">
                    <span className="stamp-text">WindowPet</span>
                    <span className="stamp-num">No.{p.id.replace('p', '0')}</span>
                  </div>
                  <div className="postcard-photo-frame">
                    <img src={p.img} alt={p.title} className="postcard-photo-img" loading="lazy" />
                  </div>
                  <div className="postcard-caption" style={{ alignItems: 'center', marginTop: '10px' }}>
                    <strong className="postcard-title" style={{ fontSize: '14px', color: '#4a2830' }}>
                      小汪 · {p.title}
                    </strong>
                  </div>
                </div>
              )
            })}
          </div>

          {/* 2. 小汪生全部动作动态演示舞台 */}
          <div className="xiaowang-interactive-stage-card">
            <div className="stage-left-avatar-zone">
              <div className="stage-avatar-glow-ring">
                <img
                  key={activeXiaoWangAction}
                  src={xiaoWangActions[activeXiaoWangAction].anim}
                  alt={`小汪生 ${xiaoWangActions[activeXiaoWangAction].label}`}
                  className="stage-live-avatar-img"
                />
              </div>

              <div className="stage-audio-badge">
                <Volume2 size={14} color="#ff6b81" />
                <span>实录音源 · 奔跑喘气与汪汪声</span>
              </div>
            </div>

            <div className="stage-right-control-zone">
              <div className="stage-control-header">
                <div className="stage-pet-title-row">
                  <h3>小汪生 · 柯基毛孩子</h3>
                  <span className="stage-author-pill">
                    <Heart size={13} fill="#ff6b81" color="#ff6b81" />
                    <span>纯手工示范作</span>
                  </span>
                </div>
              </div>

              {/* 动作切换按钮组 */}
              <div className="stage-action-tabs" aria-label="切换小汪生动作">
                <div className="action-tab-button-group">
                  {(Object.keys(xiaoWangActions) as XiaoWangActionKey[]).map((key) => {
                    const action = xiaoWangActions[key]
                    const isActive = activeXiaoWangAction === key
                    return (
                      <button
                        key={key}
                        type="button"
                        className={`stage-action-btn ${isActive ? 'is-active' : ''}`}
                        onClick={() => {
                          setActiveXiaoWangAction(key)
                          showToast(`切换动作：【${action.label}】`)
                        }}
                      >
                        <strong>{action.label}</strong>
                        <small>{action.tag}</small>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* 极简使用说明 */}
              <div className="xiaowang-minimal-license-hint">
                <span className="hint-icon">💡</span>
                <span>《小汪生》支持个人在桌面端免费使用，非完全开源角色，请勿商用哦~</span>
              </div>

              {/* 核心操作按钮 */}
              <div className="stage-action-cta-group">
                <button
                  type="button"
                  className="stage-import-pet-btn"
                  onClick={() => handleDeepLink('WPX-2026-XIAOWANG', '小汪')}
                  title="免费将小汪生一键导入桌面端"
                >
                  <Download size={16} />
                  <span>免费将【小汪生】导入桌面</span>
                </button>

                <button
                  type="button"
                  className="stage-custom-my-pet-btn"
                  onClick={() => {
                    handleCopyQq()
                    showToast('已复制官方群号 422616922！进群直接私聊定制自家的毛孩子~')
                  }}
                  title="预约定制自家族宠，双方自行私聊付款"
                >
                  <HeartHandshake size={16} />
                  <span>我也想定制自家的毛孩子</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================================
            极简 4 步定制流程
            ========================================================================= */}
        <section style={{ marginBottom: '46px' }}>
          <div className="subpage-section-header text-center" style={{ marginBottom: '20px' }}>
            <span className="subpage-section-badge pink-badge">
              <Sparkles size={14} />
              <span>SIMPLE PROCESS</span>
            </span>
            <h2>四步极简定制流程</h2>
            <p>省心省事，画师 1 对 1 手绘切帧，直接交付专属安装文件。</p>
          </div>

          <div className="custom-minimal-steps-grid">
            {steps.map((s) => {
              const IconComp = s.icon
              return (
                <div key={s.num} className="custom-minimal-step-item">
                  <div className="step-num-badge">{s.num}</div>
                  <div className="step-icon-wrap">
                    <IconComp size={20} color="#ff6b81" />
                  </div>
                  <h4>{s.title}</h4>
                  <p>{s.desc}</p>
                </div>
              )
            })}
          </div>
        </section>

        {/* =========================================================================
            特邀画师作品（极简呈现）
            ========================================================================= */}
        <section style={{ marginBottom: '46px' }}>
          <div className="subpage-section-header text-center" style={{ marginBottom: '20px' }}>
            <span className="subpage-section-badge pink-badge">
              <Palette size={14} />
              <span>ARTIST SHOWCASE</span>
            </span>
            <h2>画师合作案例</h2>
            <p>真实毛孩子定制作品展示，进群可直接 1 对 1 私聊画师约稿与付款。</p>
          </div>

          <div className="gallery-producers-stream">
            {artistChains.map((artist) => (
              <section className="gallery-producer-section pink-producer-card" key={artist.id}>
                <div className="gallery-producer-header">
                  <div className="gallery-producer-avatar pink-producer-avatar">
                    {artist.initial}
                  </div>
                  <div className="gallery-producer-title-wrap">
                    <div className="gallery-producer-main-title">
                      <h2>制作人：{artist.name}</h2>
                    </div>
                    <span className="gallery-producer-subtitle">{artist.role}</span>
                  </div>

                  <div className="producer-action-group">
                    <button
                      type="button"
                      className="gallery-producer-custom-tag pink-chat-btn"
                      onClick={() => {
                        handleCopyQq()
                        showToast(`已复制群号 422616922！进群可私聊【${artist.name}】沟通定制与付款~`)
                      }}
                      title="私聊画师沟通爱宠定制，双方自行付款"
                    >
                      <MessageSquare size={13} />
                      <span>私聊画师</span>
                    </button>
                    <a
                      href={qqGroupUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="producer-direct-chat-link pink-direct-link"
                      title="一键进群私聊画师"
                    >
                      进群私聊
                    </a>
                  </div>
                </div>

                <div className="gallery-minimal-grid">
                  {artist.cases.map((c) => (
                    <article
                      key={c.id}
                      className="gallery-minimal-card pink-card-hover"
                      onClick={() => handleDeepLink(c.redeemCode, c.title)}
                      role="button"
                      tabIndex={0}
                      title={`点击通过桌面端一键导入【${c.title}】`}
                    >
                      <div className="minimal-card-stage">
                        <img
                          src={c.img}
                          alt={c.title}
                          className="minimal-card-img"
                          loading="lazy"
                        />
                      </div>
                      <div className="minimal-card-info">
                        <span className="minimal-card-name">{c.title}</span>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </section>

        {/* 底部极简预约横幅 */}
        <div className="subpage-cta-box pink-cta-box">
          <div>
            <h3>想给自家毛孩子定制专属桌面陪伴？</h3>
            <p>进群直接私聊画师，双方自行付款，平台永久免费零抽成。</p>
          </div>
          <div>
            <a
              className="primary-download pink-primary-btn"
              href={qqGroupUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '11px 24px', textDecoration: 'none' }}
            >
              <HeartHandshake size={17} />
              <span>立即进群私聊约稿</span>
              <ArrowRight size={15} />
            </a>
          </div>
        </div>

        {/* 底部极简版权 */}
        <footer className="subpage-footer" style={{ marginTop: '40px' }}>
          <span>© 2026 WindowPet · 小鼻嘎开源社区 · 永久免费</span>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
            桂ICP备2026009615号-2
          </a>
        </footer>
      </div>
    </div>
  )
}
