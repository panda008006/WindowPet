import { useState } from 'react'
import {
  Camera,
  Gift,
  HeartHandshake,
  Home,
  Palette,
  Sparkles,
  ArrowRight,
  HelpCircle,
  Copy,
  Check,
  MessageSquare,
  Volume2,
  Download,
  Heart,
  Award,
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
  tag: string
  img: string
  note: string
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
    }, 3000)
  }

  const handleCopyQq = () => {
    try {
      navigator.clipboard.writeText('422616922')
      setCopiedQq(true)
      showToast('官方定制直通群号 422616922 已复制到剪贴板！')
      setTimeout(() => setCopiedQq(false), 2400)
    } catch {
      // ignore
    }
  }

  const handleDeepLink = (code: string, petName: string) => {
    const deepLinkUrl = `windowpet://import?code=${encodeURIComponent(code)}&name=${encodeURIComponent(petName)}`
    window.open(deepLinkUrl, '_self')
    showToast(`🚀 正在呼叫 WindowPet 桌面端自动装载【${petName}】...（若未弹出请使用下方备用码）`)
    try {
      navigator.clipboard.writeText(code)
    } catch {
      // ignore
    }
  }

  // 小汪生全部动作配置
  const xiaoWangActions: Record<
    XiaoWangActionKey,
    { label: string; anim: string; desc: string; frames: number; tag: string }
  > = {
    idle: {
      label: '伴读待机 · 吐舌笑',
      anim: `${import.meta.env.BASE_URL}pets/xiaowang-idle.webp`,
      desc: '96 帧平稳呼吸循化，咧开小嘴灿烂大笑，双耳微动。放在工位屏幕边，一眼就治愈！',
      frames: 96,
      tag: '静音伴读 · 呼吸微笑',
    },
    click: {
      label: '撒欢互动 · 狂奔扑腾',
      anim: `${import.meta.env.BASE_URL}pets/xiaowang-click.webp`,
      desc: '96 帧大步狂奔扑腾，短腿生风，身体侧身飞跃，真实还原狗狗听到零食开心的撒欢步态！',
      frames: 96,
      tag: '点击撒欢 · 短腿飞奔',
    },
    drag: {
      label: '悬空拖拽 · 超人起飞',
      anim: `${import.meta.env.BASE_URL}pets/xiaowang-drag.webp`,
      desc: '96 帧四爪离地腾空跃起，鼠标抓取拖拽时像小狗超人一样悬空飞扑蹬腿求抱抱！',
      frames: 96,
      tag: '悬空拖拽 · 飞狗起飞',
    },
  }

  // 小汪生真实爱宠写真明信片堆
  const postcards: PostcardItem[] = [
    {
      id: 'p1',
      title: '小汪生 · 天使微笑',
      tag: '📸 待机神态',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-1-smile.png`,
      note: '真实柯基犬生活照切帧 · 每天开机对你灿烂咧嘴笑',
      actionKey: 'idle',
      rotation: '-2.5deg',
    },
    {
      id: 'p2',
      title: '小汪生 · 撒欢狂奔',
      tag: '🏃‍♂️ 奔跑动作',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-3-running.png`,
      note: '实录跑动步态切帧 · 小短腿在屏幕底栏嗒嗒快跑',
      actionKey: 'click',
      rotation: '2deg',
    },
    {
      id: 'p3',
      title: '小汪生 · 腾空飞跃',
      tag: '🚀 悬空起飞',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-5-flying.png`,
      note: '鼠标拖拽起飞抓拍 · 悬空蹬动短腿求抱抱',
      actionKey: 'drag',
      rotation: '-1.8deg',
    },
    {
      id: 'p4',
      title: '小汪生 · 歪头眨眼',
      tag: '💖 萌态抓拍',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-2-happy.png`,
      note: '生活照神采还原 · 好奇歪头与耳朵小晃动',
      actionKey: 'idle',
      rotation: '2.4deg',
    },
    {
      id: 'p5',
      title: '小汪生 · 扑腾玩耍',
      tag: '🐾 互动命中',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-4-pounce.png`,
      note: '逗弄道具即时反馈 · 扑腾翻滚捉桌面蝴蝶',
      actionKey: 'click',
      rotation: '-2.2deg',
    },
    {
      id: 'p6',
      title: '小汪生 · 治愈小太阳',
      tag: '✨ 永久相伴',
      img: `${import.meta.env.BASE_URL}pets/xiaowang/postcard-6-airborne.png`,
      note: '独一无二的生命印记 · 把真实爱宠做进电脑屏幕',
      actionKey: 'drag',
      rotation: '1.5deg',
    },
  ]

  // 画师分栏展示
  const artistChains = [
    {
      id: 'chestnut',
      name: '@糖炒栗子',
      initial: '栗',
      badge: '特邀主理',
      role: '特邀定制主理人 · 真实毛发专精',
      desc: '资深宠物肖像画师，擅长眼神微动作追踪与毛流感精绘。鼠标晃到哪里，爱宠就机敏地看到哪里。',
      tags: ['真实毛发', '25帧视线跟随', '微表情打呼噜', '猫犬专精'],
      status: '● 开放约稿中（工期约 3~5 天）',
      cases: [
        {
          id: 'maicuijiao',
          title: '田园橘猫 · 麦脆角',
          img: `${import.meta.env.BASE_URL}pets/jiyi-action-waving.webp`,
          resultTag: '25帧毛发微表情',
          redeemCode: 'WPX-2026-JIYI',
        },
        {
          id: 'snowball',
          title: '纯种布偶 · 雪球',
          img: `${import.meta.env.BASE_URL}pets/cat.png`,
          resultTag: '视线跟随+呼噜踩奶',
          redeemCode: 'WPX-2026-CAT',
        },
      ],
    },
    {
      id: 'mino',
      name: '@米诺画画中',
      initial: '米',
      badge: '金牌画师',
      role: '金牌宠物动态画师 · 治愈微表情专精',
      desc: '擅长捕捉爱宠标志性萌态（歪头杀、飞机耳、打哈欠），动作生动传神。',
      tags: ['治愈微表情', '生动神态', 'Q萌神形兼备'],
      status: '● 开放约稿中（工期约 2~4 天）',
      cases: [
        {
          id: 'huanhuan',
          title: '短腿柯基 · 欢欢',
          img: `${import.meta.env.BASE_URL}pets/dog.png`,
          resultTag: '扭臀+摇尾小跳',
          redeemCode: 'WPX-2026-DOG',
        },
        {
          id: 'moyu-fox',
          title: '赤狐小皮皮',
          img: `${import.meta.env.BASE_URL}pets/fox.png`,
          resultTag: '翻白眼打哈欠',
          redeemCode: 'WPX-2026-FOX',
        },
      ],
    },
  ]

  const customFaqs = [
    {
      q: '定制我家毛孩子需要准备哪些资料？',
      a: '只需准备 1~3 张爱宠在充足光线下的清晰生活照（建议包含正面坐姿、站立或趴卧全身照），并简单告知画师毛孩子的名字、品种与平时最萌的标志性小动作（如爱歪头、爱踩奶、贪睡等）即可。',
    },
    {
      q: '定制的工期大概需要多久？流程是怎样的？',
      a: '通常完整工期为 2~5 个工作日。流程包含：① 进群沟通确认风格与动作；② 画师提供线稿与关键动作预览；③ 验收确认细节；④ 官方技术引擎封装打包交付专属安装文件。',
    },
    {
      q: '交付后是一只怎样的软件？以后换电脑还能用吗？',
      a: '交付的是专门为您生成的独立专属安装包（仅几十MB）及配套的角色资源包（.pet）。双击即可常驻电脑桌面，且该角色永久属于您，未来更换新电脑或重装系统只需重新解压即可永久使用。',
    },
    {
      q: '定制费用如何支付？平台会抽取中介提成吗？',
      a: '平台 100% 永久免费开源，绝不收取任何中介抽成！用户与画师直接 1 对 1 私聊沟通定制细节与工期，双方自行协商付款（微信/支付宝等直接转账给画师）。平台只提供中立的切帧与技术封装支持，零差价、零套路！',
    },
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
        {/* 顶部 Hero */}
        <header className="subpage-hero">
          <span className="eyebrow pink-eyebrow">
            <Sparkles size={14} />
            <span>CUSTOM PET STUDIO · 真实毛孩子专属定制</span>
          </span>
          <h1>把自家的毛孩子，做进电脑桌面陪伴你</h1>
          <p className="subpage-lead">
            不只是现成的动漫角色！提供 1~3 张自家族宠真实生活照，
            纯手工 1 对 1 精细切帧 + 288 帧全套生动动作 + 官方轻量引擎封装。
            每一次敲键盘看屏幕，自家的毛孩子都在你身边摇尾巴~
          </p>

          <div className="subpage-hero-actions">
            <a
              className="primary-download pink-primary-btn"
              href={qqGroupUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ padding: '12px 28px', fontSize: '15px' }}
            >
              <HeartHandshake size={18} />
              <span>立即预约爱宠定制 / 进群私聊</span>
            </a>

            <button
              type="button"
              className="secondary-action pink-secondary-btn"
              onClick={handleCopyQq}
              style={{ padding: '12px 22px', fontSize: '14px' }}
            >
              {copiedQq ? <Check size={16} color="#ff6b81" /> : <Copy size={16} />}
              <span>{copiedQq ? '群号 422616922 已复制！' : '复制官方群号：422616922'}</span>
            </button>

            {onOpenGallery && (
              <button
                type="button"
                className="secondary-action pink-secondary-btn"
                onClick={onOpenGallery}
                style={{ padding: '12px 22px', fontSize: '14px' }}
              >
                <Sparkles size={16} />
                <span>逛逛小鼻嘎展馆</span>
              </button>
            )}

            {onBackToHome && (
              <button
                type="button"
                className="secondary-action pink-secondary-btn"
                onClick={onBackToHome}
                style={{ padding: '12px 22px', fontSize: '14px' }}
              >
                <Home size={16} />
                <span>返回官网首页</span>
              </button>
            )}
          </div>
        </header>

        {/* =========================================================================
            核心王牌：小汪生 · 真实毛孩子手作写真明信片大赏 + 全部动作交互舞台
            ========================================================================= */}
        <section className="xiaowang-showcase-section">
          <div className="subpage-section-header text-center">
            <span className="subpage-section-badge pink-badge">
              <Heart size={14} fill="#ff6b81" color="#ff6b81" />
              <span>OFFICIAL MASTERPIECE · 官方唯一手工实拍定制示范</span>
            </span>
            <h2>真实宠物定制代表作：《小汪生》写真明信片</h2>
            <p>
              打开就像铺满一整张桌子的漂亮明信片！
              由作者唯一倾心纯手工实拍抠图调校，完整收录待机吐舌、撒欢狂奔、悬空起飞全部生动动作。
            </p>
          </div>

          {/* 1. 明信片写真大赏 (Postcard Desk Wall) */}
          <div className="xiaowang-postcard-wall" aria-label="小汪生真实宠物明信片大赏">
            {postcards.map((p) => {
              const isActive = activeXiaoWangAction === p.actionKey
              return (
                <div
                  key={p.id}
                  className={`xiaowang-postcard-card ${isActive ? 'is-active-card' : ''}`}
                  style={{ transform: `rotate(${p.rotation})` }}
                  onClick={() => {
                    setActiveXiaoWangAction(p.actionKey)
                    showToast(`✨ 已联动切换至【${xiaoWangActions[p.actionKey].label}】动作演示！`)
                  }}
                  role="button"
                  tabIndex={0}
                  title={`点击查看【${p.title}】动态演示`}
                >
                  {/* 顶部樱花粉和纸胶带装饰 */}
                  <div className="postcard-washi-tape" />

                  {/* 右上角复古粉色邮票 */}
                  <div className="postcard-stamp">
                    <span className="stamp-text">WindowPet</span>
                    <span className="stamp-num">No.{p.id.replace('p', '0')}</span>
                  </div>

                  {/* 真实照片相框 */}
                  <div className="postcard-photo-frame">
                    <img src={p.img} alt={p.title} className="postcard-photo-img" loading="lazy" />
                    <span className="postcard-tag-pill">{p.tag}</span>
                  </div>

                  {/* 手写风标题与文字 */}
                  <div className="postcard-caption">
                    <div className="postcard-title-row">
                      <strong className="postcard-title">{p.title}</strong>
                      <span className="postcard-date">2026.08 · 手作实切</span>
                    </div>
                    <p className="postcard-note">{p.note}</p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* 2. 小汪生全部动作动态演示交互舞台 (Live Actions Stage) */}
          <div className="xiaowang-interactive-stage-card">
            <div className="stage-left-avatar-zone">
              <div className="stage-avatar-glow-ring">
                <img
                  key={activeXiaoWangAction}
                  src={xiaoWangActions[activeXiaoWangAction].anim}
                  alt={`小汪生 ${xiaoWangActions[activeXiaoWangAction].label} 实时演示`}
                  className="stage-live-avatar-img"
                />
              </div>

              <div className="stage-audio-badge">
                <Volume2 size={14} color="#ff6b81" />
                <span>实录音源配套 · 奔跑喘气与欢快汪汪声</span>
              </div>
            </div>

            <div className="stage-right-control-zone">
              <div className="stage-control-header">
                <div className="stage-pet-title-row">
                  <h3>小汪生 · 真实柯基毛孩子</h3>
                  <span className="stage-author-pill">
                    <Award size={13} color="#ff6b81" />
                    <span>作者唯一手工示范作</span>
                  </span>
                </div>
                <p className="stage-pet-intro">
                  “全套 288 帧生活视频逐帧切帧，100% 还原真实毛孩子的表情与动作反馈。
                  自家族宠的每一次撒欢与陪伴，都可以在电脑桌面上永久定格。”
                </p>
              </div>

              {/* 动作切换标签组 */}
              <div className="stage-action-tabs" aria-label="切换小汪生动作">
                <span className="action-tabs-label">点击切换动作体验：</span>
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

              {/* 当前动作详情提示 */}
              <div className="stage-current-action-tip">
                <strong>当前播放动作细节：</strong>
                <span>{xiaoWangActions[activeXiaoWangAction].desc}</span>
              </div>

              {/* 核心操作按钮组 */}
              <div className="stage-action-cta-group">
                <button
                  type="button"
                  className="stage-import-pet-btn"
                  onClick={() => handleDeepLink('WPX-2026-XIAOWANG', '小汪')}
                  title="直接将小汪生一键导入桌面软件常驻陪伴"
                >
                  <Download size={16} />
                  <span>免费将【小汪生】导入桌面客户端</span>
                </button>

                <button
                  type="button"
                  className="stage-custom-my-pet-btn"
                  onClick={() => {
                    handleCopyQq()
                    showToast('已复制官方群号 422616922！进群直接私聊定制自家的真实毛孩子~')
                  }}
                  title="预约定制自家族宠，双方自行私聊付款"
                >
                  <HeartHandshake size={16} />
                  <span>我也想定做我家的毛孩子 (私聊自行付款)</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================================
            特邀画师专栏（极简横向分栏，纯粉色主题）
            ========================================================================= */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge pink-badge">
              <Palette size={14} />
              <span>VERIFIED ARTISTS & STYLES</span>
            </span>
            <h2>特邀合作画师作品案例</h2>
            <p>简约浏览体验：按制作人分栏呈现，外部仅展示宠物与动作，清爽直观。</p>
          </div>

          <div className="gallery-producers-stream">
            {artistChains.map((artist) => (
              <section className="gallery-producer-section pink-producer-card" key={artist.id}>
                {/* 制作人标题栏：直接写“制作人：XXX” */}
                <div className="gallery-producer-header">
                  <div className="gallery-producer-avatar pink-producer-avatar">
                    {artist.initial}
                  </div>
                  <div className="gallery-producer-title-wrap">
                    <div className="gallery-producer-main-title">
                      <h2>制作人：{artist.name}</h2>
                      <span className="gallery-producer-badge pink-badge">
                        {artist.badge}
                      </span>
                    </div>
                    <span className="gallery-producer-subtitle">{artist.role} · {artist.status}</span>
                  </div>

                  <div className="producer-action-group">
                    <button
                      type="button"
                      className="gallery-producer-custom-tag pink-chat-btn"
                      onClick={() => {
                        handleCopyQq()
                        showToast(`已复制官方群号 422616922！进群可直接私聊【${artist.name}】沟通定制与自行付款~`)
                      }}
                      title="私聊画师沟通爱宠定制，双方自行付款"
                    >
                      <MessageSquare size={13} />
                      <span>💬 私聊画师 (自行付款)</span>
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

                {/* 极简宠物卡片网格 */}
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
                        <span className="minimal-card-action">
                          动作：{c.resultTag}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </section>

        {/* =========================================================================
            四步极简定制流程（纯粉色）
            ========================================================================= */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge pink-badge">
              <Sparkles size={14} />
              <span>SIMPLE 4-STEP PROCESS</span>
            </span>
            <h2>四步极简定制，毛孩子跃然桌面</h2>
            <p>从真实生活照到桌面灵动伙伴，标准化专业流程，透明省心。</p>
          </div>

          <div className="custom-steps-grid">
            <article className="subpage-card custom-step-card pink-step-card">
              <div className="custom-step-number pink-step-number">01</div>
              <div className="custom-step-icon pink-step-icon">
                <Camera size={24} />
              </div>
              <h3>01. 提供真实生活照</h3>
              <p>
                准备 1~3 张爱宠在充足光线下的正面坐姿、站立或特写全身照。告知画师爱宠的花斑特征（白手套、眼线、花纹）与平时最可爱的神态。
              </p>
            </article>

            <article className="subpage-card custom-step-card pink-step-card">
              <div className="custom-step-number pink-step-number">02</div>
              <div className="custom-step-icon pink-step-icon">
                <Palette size={24} />
              </div>
              <h3>02. 挑选动作与互动风格</h3>
              <p>
                可自由挑选 3~5 组专属动作：日常打盹、看鼠标摇尾巴、敲键盘陪加班、羽毛逗弄、伸懒腰等，甚至融入爱宠专属小玩具。
              </p>
            </article>

            <article className="subpage-card custom-step-card pink-step-card">
              <div className="custom-step-number pink-step-number">03</div>
              <div className="custom-step-icon pink-step-icon">
                <Sparkles size={24} />
              </div>
              <h3>03. 画师 1 对 1 绘制精修</h3>
              <p>
                特邀独立画师量身绘制关键帧并合成平滑动画序列，提供预览样张，支持细节打磨调整，直到您完全满意为止。
              </p>
            </article>

            <article className="subpage-card custom-step-card pink-step-card">
              <div className="custom-step-number pink-step-number">04</div>
              <div className="custom-step-icon pink-step-icon">
                <Gift size={24} />
              </div>
              <h3>04. 专属安装包交付</h3>
              <p>
                WindowPet 官方引擎技术打包，生成独一无二的专属安装程序及资源包。双击即刻召唤毛孩子常驻桌面，永久陪伴。
              </p>
            </article>
          </div>
        </section>

        {/* =========================================================================
            定制答疑 FAQ（纯粉色）
            ========================================================================= */}
        <section style={{ marginBottom: '40px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge pink-badge">
              <HelpCircle size={14} />
              <span>FAQ</span>
            </span>
            <h2>爱宠定制常见问题</h2>
            <p>了解定制流程、工期安排、零抽成与交付保障细节。</p>
          </div>

          <div className="faq-list">
            {customFaqs.map((faq, idx) => (
              <article className="subpage-card faq-item pink-faq-card" key={idx}>
                <div className="faq-question">
                  <div className="faq-q-badge pink-q-badge">Q</div>
                  <h3>{faq.q}</h3>
                </div>
                <div className="faq-answer">
                  <p>{faq.a}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* 底部 CTA 预约横幅 */}
        <div className="subpage-cta-box pink-cta-box">
          <div>
            <h3>想给自家毛孩子定制专属电脑桌面陪伴？</h3>
            <p>官方交流群现已开放预约通道，透明工期与进度跟踪，双方直接私聊自行付款，平台零抽成！</p>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <a
              className="primary-download pink-primary-btn"
              href={qqGroupUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', textDecoration: 'none' }}
            >
              <HeartHandshake size={18} />
              <span>立即进群预约定制</span>
              <ArrowRight size={16} />
            </a>
          </div>
        </div>

        {/* 底部版权 */}
        <footer className="subpage-footer">
          <span>© 2026 WindowPet · 小鼻嘎开源社区 · 永久免费</span>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
            桂ICP备2026009615号-2
          </a>
        </footer>
      </div>
    </div>
  )
}
