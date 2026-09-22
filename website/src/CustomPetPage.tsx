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
  Zap,
  Laptop,
  MessageSquare,
} from 'lucide-react'
import './subpages.css'

interface CustomPetPageProps {
  onBackToHome?: () => void
  onOpenGallery?: () => void
}

const qqGroupUrl = 'https://qm.qq.com/q/cYlRBbvuda'

export function CustomPetPage({ onBackToHome, onOpenGallery }: CustomPetPageProps) {
  const [copiedQq, setCopiedQq] = useState(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

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

  // 4 大画师链式圈圈展示（一个作者圆圈，下面圈一个案例，再下面圈一个案例）
  const artistChains = [
    {
      id: 'chestnut',
      name: '@糖炒栗子',
      shortName: '糖炒栗子',
      studio: '糖炒栗子定制工坊',
      initial: '栗',
      badge: '特邀主理',
      badgeColor: '#e11d48',
      role: '特邀定制主理人 · 真实毛发专精',
      desc: '资深宠物肖像画师，擅长眼神微动作追踪与毛流感精绘。鼠标晃到哪里，爱宠就机敏地看到哪里。',
      tags: ['真实毛发', '25帧视线跟随', '微表情打呼噜', '猫犬专精'],
      gradient: 'linear-gradient(135deg, #ff7f87, #e85f6d)',
      ringColor: '#e85f6d',
      status: '● 开放约稿中（工期约 3~5 天）',
      cases: [
        {
          id: 'maicuijiao',
          title: '田园橘猫 · 麦脆角',
          img: `${import.meta.env.BASE_URL}pets/jiyi-action-waving.webp`,
          sourceTag: '生活照阳台晒太阳',
          resultTag: '25帧毛发微表情',
          desc: '提取特征山字纹与琥珀色大眼，定制了视线跟随、趴睡发呆与按爪印 3 个动作。',
          redeemCode: 'WPX-2026-JIYI',
        },
        {
          id: 'snowball',
          title: '纯种布偶 · 雪球',
          img: `${import.meta.env.BASE_URL}pets/cat.png`,
          sourceTag: '蓝眼大围脖照片',
          resultTag: '视线跟随+呼噜踩奶',
          desc: '抓取布偶猫标志性海双八字脸与蓬松围脖，跟随鼠标歪头眨眼，屏幕边缘伸懒腰踩奶。',
          redeemCode: 'WPX-2026-CAT',
        },
      ],
    },
    {
      id: 'mino',
      name: '@米诺画画中',
      shortName: '米诺',
      studio: '米诺治愈工坊',
      initial: '米',
      badge: '家宠写生',
      badgeColor: '#2f9f93',
      role: '独立家宠插画师 · 日系Q版/像素风',
      desc: '重度猫狗双全铲屎官，擅长将宠物的憨态与花斑特征提取为极具治愈感的萌系形象。',
      tags: ['治愈Q版', '软萌像素', '踩奶互动', '异宠可接'],
      gradient: 'linear-gradient(135deg, #2f9f93, #57c7b8)',
      ringColor: '#2f9f93',
      status: '● 开放约稿中（工期约 2~4 天）',
      cases: [
        {
          id: 'xiaochai',
          title: '小柴犬 · 阿黄',
          img: `${import.meta.env.BASE_URL}pets/xiaochai.png`,
          sourceTag: '歪头杀正脸生活照',
          resultTag: '摇尾巴+接飞盘逗弄',
          desc: '还原标志性白肚皮与豆豆眉，加入点击欢快摇尾巴、丢飞盘互动与小憩打呼噜。',
          redeemCode: 'WPX-2026-XIAOCHAI',
        },
        {
          id: 'nuomi',
          title: '垂耳兔 · 糯米团',
          img: `${import.meta.env.BASE_URL}pets/dora-action-waving.webp`,
          sourceTag: '灰白软糯生活照',
          resultTag: '任务栏静音嚼胡萝卜',
          desc: '高度还原灰白兔耳，双击投喂胡萝卜，常驻在屏幕任务栏右下角安静咀嚼。',
          redeemCode: 'WPX-2026-DORA',
        },
      ],
    },
    {
      id: 'hoshino',
      name: '@星野光年漫研所',
      shortName: '星野',
      studio: '星野创作组',
      initial: '星',
      badge: '动漫拟人',
      badgeColor: '#fb7185',
      role: '动漫概念插画师 · 二次元拟人伴侣',
      desc: '把自家的毛孩子打造成动漫伴侣！设计专属敲小鼓、吉他伴奏或打字狂暴摇晃动作。',
      tags: ['动漫拟人', '连携乐器合奏', '打工怨种搭子', '限量接单'],
      gradient: 'linear-gradient(135deg, #a78bfa, #fb7185)',
      ringColor: '#a78bfa',
      status: '● 开放约稿中（每月限量 5 单）',
      cases: [
        {
          id: 'miaomiao',
          title: '猫耳伴侣 · 喵喵',
          img: `${import.meta.env.BASE_URL}pets/jiyi-action-concert.webp`,
          sourceTag: '三花猫生活照拟人',
          resultTag: '敲小鼓吉他合奏',
          desc: '将自家三花猫花斑融入动漫猫耳少女，跟随键盘敲击节奏弹奏吉他，带来专属治愈 BGM。',
          redeemCode: 'WPX-2026-MIAOMIAO',
        },
        {
          id: 'foxboy',
          title: '赤狐少年 · 小赤',
          img: `${import.meta.env.BASE_URL}pets/fox-action-waving.webp`,
          sourceTag: '赤狐抓拍生活图',
          resultTag: '屏幕边沿探头挥手',
          desc: '蓬松大尾巴随风轻晃，在任务栏上方露出半个小脑袋偷偷看你，点击害羞缩回再探出。',
          redeemCode: 'WPX-2026-FOX',
        },
      ],
    },
    {
      id: 'memelab',
      name: '@整活大队 MemeLab',
      shortName: 'MemeLab',
      studio: 'MemeLab 创意室',
      initial: 'M',
      badge: '趣味整活',
      badgeColor: '#f59e0b',
      role: '幽默动态设计师 · 狂暴打字/摸鱼搭子',
      desc: '专治工位无聊！将爱宠的沙雕丑照与表情包制作成桌面搭子，陪你上班疯狂敲键盘。',
      tags: ['沙雕表情包', '狂暴敲键盘', '打工怨种', '随缘接单'],
      gradient: 'linear-gradient(135deg, #fb923c, #f59e0b)',
      ringColor: '#fb923c',
      status: '● 开放约稿中（随缘接单）',
      cases: [
        {
          id: 'salarycat',
          title: '疯狂敲键盘猫',
          img: `${import.meta.env.BASE_URL}pets/salary_cat.png`,
          sourceTag: '打工怨种搞笑丑照',
          resultTag: '超高速打字残影冒烟',
          desc: '打工人专属解压！你打字越快它敲键盘越狠，键盘冒火星，还会随着按键抓狂拍桌。',
          redeemCode: 'WPX-2026-SALARYCAT',
        },
        {
          id: 'mochuchai',
          title: '摸鱼怨种柴柴',
          img: `${import.meta.env.BASE_URL}pets/fox.png`,
          sourceTag: '翻白眼搞怪生活照',
          resultTag: '任务栏打哈欠叹气',
          desc: '趴在任务栏边沿不停打哈欠、叹气与翻白眼，完美化身工位精神状态代言人。',
          redeemCode: 'WPX-2026-CHAI',
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
      q: '画师直约与官方平台之间是什么关系？会公开我的爱宠吗？',
      a: '默认交付为 100% 私人专享，绝不未经允许公开给任何第三方下载！平台提供中立的轻量运行引擎支持与动作标准规范，画师团队一对一为宠友绘制，透明安全。',
    },
    {
      q: '定制费用如何支付？平台会抽取中介提成吗？',
      a: '平台 100% 永久免费开源，绝不收取任何中介抽成！用户与画师直接 1 对 1 私聊沟通定制细节与工期，双方自行协商付款（微信/支付宝等直接转账给画师）。平台只提供中立的切帧与技术封装支持，零差价、零套路！',
    },
  ]

  return (
    <div className="page-view-pane">
      {/* 浮动操作提示 */}
      {toastMessage && (
        <div className="gallery-toast-pill" role="status" aria-live="polite">
          <Sparkles size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      <div className="subpage-container">
        {/* 顶部 Hero */}
        <header className="subpage-hero">
          <span className="eyebrow">CUSTOM PET STUDIO · 专属定制工坊</span>
          <h1>把自家的毛孩子，做进电脑桌面陪伴你</h1>
          <p className="subpage-lead">
            不只是现成的动漫角色！提供 1~3 张爱宠真实生活照（猫咪、狗狗、龙猫、鹦鹉），
            特邀知名独立插画师 1 对 1 量身手绘 + 25 帧丝滑动作设计 + 官方轻量引擎专属打包。
            每一次敲键盘、看屏幕，自家的毛孩子都在你身边。
          </p>

          <div className="subpage-hero-actions">
            <a
              className="primary-download"
              href={qqGroupUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ padding: '12px 28px', fontSize: '15px' }}
            >
              <HeartHandshake size={18} />
              <span>立即预约爱宠定制 / 进群直通</span>
            </a>

            <button
              type="button"
              className="secondary-action"
              onClick={handleCopyQq}
              style={{ padding: '12px 22px', fontSize: '14px' }}
            >
              {copiedQq ? <Check size={16} color="#059669" /> : <Copy size={16} />}
              <span>{copiedQq ? '群号 422616922 已复制！' : '复制官方群号：422616922'}</span>
            </button>

            {onOpenGallery && (
              <button
                type="button"
                className="secondary-action"
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
                className="secondary-action"
                onClick={onBackToHome}
                style={{ padding: '12px 22px', fontSize: '14px' }}
              >
                <Home size={16} />
                <span>返回官网首页</span>
              </button>
            )}
          </div>
        </header>

        {/* 核心特色：制作人横向分栏，直接写“制作人”，下面接着写他的角色 */}
        <section style={{ marginBottom: '64px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <Sparkles size={14} />
              <span>CUSTOM CREATORS & PETS</span>
            </span>
            <h2>制作人专属定制案例</h2>
            <p>简约浏览体验：按制作人分栏呈现，外部仅展示宠物与动作，清爽直观。</p>
          </div>

          <div className="gallery-producers-stream">
            {artistChains.map((artist) => (
              <section className="gallery-producer-section" key={artist.id}>
                {/* 制作人标题栏：直接写“制作人：XXX” */}
                <div className="gallery-producer-header">
                  <div className="gallery-producer-avatar" style={{ background: artist.gradient }}>
                    {artist.initial}
                  </div>
                  <div className="gallery-producer-title-wrap">
                    <div className="gallery-producer-main-title">
                      <h2>制作人：{artist.name}</h2>
                      <span className="gallery-producer-badge" style={{ borderColor: artist.ringColor, color: artist.ringColor }}>
                        {artist.badge}
                      </span>
                    </div>
                    <span className="gallery-producer-subtitle">{artist.role} · {artist.status}</span>
                  </div>

                  <div className="producer-action-group">
                    <button
                      type="button"
                      className="gallery-producer-custom-tag"
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
                      className="producer-direct-chat-link"
                      title="一键进群私聊画师"
                    >
                      进群私聊
                    </a>
                  </div>
                </div>

                {/* 极简宠物卡片网格：只放宠物动效 + 名称 + 动作 */}
                <div className="gallery-minimal-grid">
                  {artist.cases.map((c) => (
                    <article
                      key={c.id}
                      className="gallery-minimal-card"
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

        {/* 作者入驻与免登录一键直接导入机制图解 */}
        <section style={{ marginBottom: '64px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <Zap size={14} />
              <span>ZERO-LOGIN IMPORT & CREATOR ONBOARDING</span>
            </span>
            <h2>免登录直接导入 & 画师入驻机制图解</h2>
            <p>
              彻底免去繁琐的手机号注册与密码记忆！理解博主与主流桌面软件的“DeepLink 协议直接唤醒 + 备用识别码”双轨机制。
            </p>
          </div>

          <div className="import-mechanisms-grid">
            {/* 卡片 1：免登录直接导入与备用码原理 */}
            <article className="subpage-card import-mech-card">
              <div className="import-mech-head">
                <div className="import-mech-icon-wrap" style={{ background: 'rgba(232, 95, 109, 0.12)', color: '#e85f6d' }}>
                  <Laptop size={24} />
                </div>
                <div>
                  <h3>网站如何直接把宠物导入本地软件？</h3>
                  <small style={{ color: '#57c7b8', fontWeight: 700 }}>系统级 DeepLink 协议唤醒 + 备用口令码</small>
                </div>
              </div>

              <div className="import-mech-steps">
                <div className="import-mech-step-item">
                  <div className="step-badge-num">1</div>
                  <div>
                    <strong>点导入自动唤醒（原生系统协议）</strong>
                    <p>
                      我们在 Windows 系统中注册了专属协议头 <code>windowpet://import</code>。当你在网页上点击【一键导入】时，Edge 或 Chrome 浏览器会自动弹出确认框：
                      <span className="dialog-mockup">“是否打开 WindowPet？/ 在其他应用中打开”</span>
                      点击【确定/允许】，本地软件立刻被唤醒并无感装载！
                    </p>
                  </div>
                </div>

                <div className="import-mech-step-item">
                  <div className="step-badge-num">2</div>
                  <div>
                    <strong>0 账号登录负担，免去一切繁琐验证</strong>
                    <p>
                      无论是展馆中的公共伙伴还是画师定制交付的专属角色，一律免注册账号、免手机验证码，点开即刻直接导入桌面，离线永久使用！
                    </p>
                  </div>
                </div>

                <div className="import-mech-step-item">
                  <div className="step-badge-num">3</div>
                  <div>
                    <strong>备用识别码双轨保险（复制粘贴秒导）</strong>
                    <p>
                      如果用户的浏览器安全级别过高拦截了自动弹窗，网页会同步显示 12 位口令识别码（如 <code>WPX-2026-JIYI</code>）。
                      只需在本地软件右键托盘 ➜ 选择【兑换/导入伙伴】粘贴该码，同样 1 秒完成下载装载，两套方案互为保险！
                    </p>
                  </div>
                </div>
              </div>
            </article>

            {/* 卡片 2：画师如何入驻与自动化打包 */}
            <article className="subpage-card import-mech-card">
              <div className="import-mech-head">
                <div className="import-mech-icon-wrap" style={{ background: 'rgba(47, 159, 147, 0.12)', color: '#2f9f93' }}>
                  <Palette size={24} />
                </div>
                <div>
                  <h3>画师如何入驻？宠物如何传到软件里？</h3>
                  <small style={{ color: '#e85f6d', fontWeight: 700 }}>画师只管画图，官方工具一键切帧打包</small>
                </div>
              </div>

              <div className="import-mech-steps">
                <div className="import-mech-step-item">
                  <div className="step-badge-num">A</div>
                  <div>
                    <strong>画师零代码创作（提供 18 格主精灵图）</strong>
                    <p>
                      画师完全不需要懂编程！画师只需按官方规范画出待机（idle）、点击（click）、悬空拖拽（drag）共 18 格 PNG 切片或一张大图纸。
                    </p>
                  </div>
                </div>

                <div className="import-mech-step-item">
                  <div className="step-badge-num">B</div>
                  <div>
                    <strong>官方自动化工具 1 秒切帧打包</strong>
                    <p>
                      使用项目中现成的 <code>build_character_from_sheet.py</code> 脚本，自动网格分割、去除纯色底、标准化尺寸并生成 <code>asset.json</code>，打包成几兆大小的 <code>.pet</code> 资源包。
                    </p>
                  </div>
                </div>

                <div className="import-mech-step-item">
                  <div className="step-badge-num">C</div>
                  <div>
                    <strong>云端分发与作者专属展馆上架</strong>
                    <p>
                      将打包好的角色发布至静态资源库，系统自动分配专属兑换口令码，并生成画师的个人专属主页与作品集。
                      用户一键点击即可秒速拉取并常驻桌面！
                    </p>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>

        {/* 四步极简定制流程 */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <Sparkles size={14} />
              <span>SIMPLE 4-STEP PROCESS</span>
            </span>
            <h2>四步极简定制，毛孩子跃然桌面</h2>
            <p>从生活照到桌面灵动伙伴，标准化专业流程，透明省心。</p>
          </div>

          <div className="custom-steps-grid">
            <article className="subpage-card custom-step-card">
              <div className="custom-step-number">01</div>
              <div className="custom-step-icon" style={{ background: 'rgba(239, 68, 68, 0.12)', color: '#dc2626' }}>
                <Camera size={24} />
              </div>
              <h3>01. 提供真实生活照</h3>
              <p>
                准备 1~3 张爱宠在充足光线下的正面坐姿、站立或特写全身照。告知画师爱宠的花斑特征（白手套、眼线、花纹）与平时最可爱的神态。
              </p>
            </article>

            <article className="subpage-card custom-step-card">
              <div className="custom-step-number">02</div>
              <div className="custom-step-icon" style={{ background: 'rgba(14, 165, 233, 0.12)', color: '#0284c7' }}>
                <Palette size={24} />
              </div>
              <h3>02. 挑选动作与互动风格</h3>
              <p>
                可自由挑选 3~5 组专属动作：日常打盹、看鼠标摇尾巴、敲键盘陪加班、羽毛逗弄、伸懒腰等，甚至融入爱宠专属小玩具。
              </p>
            </article>

            <article className="subpage-card custom-step-card">
              <div className="custom-step-number">03</div>
              <div className="custom-step-icon" style={{ background: 'rgba(139, 92, 246, 0.12)', color: '#7c3aed' }}>
                <Sparkles size={24} />
              </div>
              <h3>03. 画师 1 对 1 绘制精修</h3>
              <p>
                特邀独立画师量身绘制关键帧并合成平滑动画序列，提供预览样张，支持细节打磨调整，直到您完全满意为止。
              </p>
            </article>

            <article className="subpage-card custom-step-card">
              <div className="custom-step-number">04</div>
              <div className="custom-step-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#059669' }}>
                <Gift size={24} />
              </div>
              <h3>04. 专属安装包交付</h3>
              <p>
                WindowPet 官方引擎技术打包，生成独一无二的专属安装程序及资源包。双击即刻召唤毛孩子常驻桌面，永久陪伴。
              </p>
            </article>
          </div>
        </section>

        {/* 定制答疑 FAQ */}
        <section style={{ marginBottom: '40px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <HelpCircle size={14} />
              <span>FAQ</span>
            </span>
            <h2>爱宠定制常见问题</h2>
            <p>了解定制流程、工期安排与交付保障细节。</p>
          </div>

          <div className="faq-list">
            {customFaqs.map((faq, idx) => (
              <article className="subpage-card faq-item" key={idx}>
                <div className="faq-question">
                  <div className="faq-q-badge">Q</div>
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
        <div className="subpage-cta-box">
          <div>
            <h3>想给自家毛孩子定制专属电脑桌面陪伴？</h3>
            <p>官方交流群现已开放预约通道，透明工期与进度跟踪，支持验收满意后再交付。</p>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <a
              className="primary-download"
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
          <span>© 2026 WindowPet Open Source Community · 永久开源免费</span>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
            桂ICP备2026009615号-2
          </a>
        </footer>
      </div>
    </div>
  )
}
