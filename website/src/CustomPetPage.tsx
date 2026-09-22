import { useState } from 'react'
import {
  Camera,
  CheckCircle2,
  Gift,
  HeartHandshake,
  Home,
  Palette,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
  Copy,
  Check,
} from 'lucide-react'
import './subpages.css'

interface CustomPetPageProps {
  onBackToHome?: () => void
  onOpenGallery?: () => void
}

const qqGroupUrl = 'https://qm.qq.com/q/cYlRBbvuda'

export function CustomPetPage({ onBackToHome, onOpenGallery }: CustomPetPageProps) {
  const [copiedQq, setCopiedQq] = useState(false)

  const handleCopyQq = () => {
    try {
      navigator.clipboard.writeText('422616922')
      setCopiedQq(true)
      setTimeout(() => setCopiedQq(false), 2400)
    } catch {
      // ignore
    }
  }

  const artists = [
    {
      id: 'chestnut',
      name: '@糖炒栗子',
      studio: '糖炒栗子定制工坊',
      initial: '栗',
      gradient: 'linear-gradient(135deg, #ff7675, #fab1a0)',
      tagColor: '#e11d48',
      styleTitle: '25帧视线跟随 / 真实毛发质感',
      desc: '资深宠物肖像画师，擅长猫咪狗狗眼神微动作追踪与毛流感精绘。鼠标晃到哪里，爱宠就机敏地看到哪里，神态栩栩如生。',
      tags: ['真实毛发', '25帧视线跟随', '微表情打呼噜', '猫犬专精'],
      status: '● 开放约稿中（工期约 3~5 天）',
      works: '代表作【麦脆角摇头猫】、【布偶猫雪球】',
    },
    {
      id: 'mino',
      name: '@米诺画画中',
      studio: '米诺治愈工坊',
      initial: '米',
      gradient: 'linear-gradient(135deg, #00cec9, #81ecec)',
      tagColor: '#0d9488',
      styleTitle: '日系治愈 Q 版 / 软萌像素风',
      desc: '重度猫狗铲屎官，擅长将现实宠物的憨态与花斑特征提取为极具治愈感的萌系形象。踩奶、伸懒腰、打瞌睡动作一应俱全。',
      tags: ['治愈Q版', '软萌像素', '踩奶互动', '异宠可接'],
      status: '● 开放约稿中（工期约 2~4 天）',
      works: '代表作【小柴犬阿黄】、【豚鼠布布】、【金渐层圆圆】',
    },
    {
      id: 'hoshino',
      name: '@星野同人漫研社',
      studio: '星野创作组',
      initial: '星',
      gradient: 'linear-gradient(135deg, #6c5ce7, #a29bfe)',
      tagColor: '#7c3aed',
      styleTitle: '二次元拟人 / 专属连携演出',
      desc: '脑洞大开的动漫社创作者，擅长把毛孩子打造成动漫伴侣！设计专属敲小鼓、弹吉他、或配合主人打字疯狂摇晃的魔性动作。',
      tags: ['动漫拟人', '连携乐器合奏', '打工怨种搭子', '限量接单'],
      status: '● 开放约稿中（每月限量 5 单）',
      works: '代表作【猫耳少女萌化】、【魔性合奏乐手】',
    },
    {
      id: 'memelab',
      name: '@整活大队 MemeLab',
      studio: 'MemeLab 创意室',
      initial: 'M',
      gradient: 'linear-gradient(135deg, #fdcb6e, #ffeaa7)',
      tagColor: '#d35400',
      styleTitle: '幽默沙雕表情包 / 狂暴打字搭子',
      desc: '专治上班无聊！将爱宠的沙雕丑照与表情包制作成桌宠，陪你上班疯狂敲键盘或在屏幕边上发呆叹气，喜感直接拉满。',
      tags: ['沙雕表情包', '狂暴敲键盘', '打工怨种', '随缘接单'],
      status: '● 开放约稿中（随缘接单）',
      works: '代表作【疯狂敲键盘猫】、【摸鱼怨种柴】',
    },
  ]

  const showcaseCases = [
    {
      title: '田园橘猫 · 麦脆角',
      artist: '@糖炒栗子',
      img: `${import.meta.env.BASE_URL}pets/jiyi-action-waving.webp`,
      desc: '主人提供 2 张阳台晒太阳生活照。提取了特征性的山字纹与琥珀色大眼睛，定制了鼠标跟随、趴睡发呆与按爪印 3 个动作。',
      tag: '真实毛发定制',
    },
    {
      title: '柴犬 · 阿黄',
      artist: '@米诺画画中',
      img: `${import.meta.env.BASE_URL}pets/fox-action-waving.webp`,
      desc: '主人提供歪头杀正脸照。还原了标志性的豆豆眉和白胸脯，加入了点击摇尾巴、接飞盘和小憩 3 组互动。',
      tag: '治愈手绘定制',
    },
    {
      title: '垂耳兔 · 糯米团',
      artist: '@米诺画画中',
      img: `${import.meta.env.BASE_URL}pets/dora-action-waving.webp`,
      desc: '还原灰白色软糯绒毛与大长耳朵。双击可喂食胡萝卜，在屏幕任务栏边缘趴着咀嚼，安静治愈不挡屏幕。',
      tag: '软萌像素定制',
    },
  ]

  const customFaqs = [
    {
      q: '定制我家毛孩子需要准备哪些资料？',
      a: '只需准备 1~3 张爱宠在明亮光线下的清晰生活照（建议包含正面坐姿、站立或趴卧全身照），并简单告知画师毛孩子的名字、品种与平时最萌的标志性小动作（如爱歪头、爱踩奶、贪睡等）即可。',
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
  ]

  return (
    <div className="page-view-pane">
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

        {/* 特邀驻站合作画师团 */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header" style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <span className="subpage-section-badge">
                <ShieldCheck size={14} />
                <span>INDEPENDENT CREATORS</span>
              </span>
              <h2>特邀驻站合作画师团 · 多元风格随心选</h2>
              <p>平台特邀多位知名独立插画师与像素创作者，一对一承接生活照私宠约稿定制。</p>
            </div>
            <span style={{ fontSize: '0.82rem', color: '#126ad6', background: 'rgba(36, 119, 255, 0.08)', padding: '4px 12px', borderRadius: '999px', fontWeight: 650 }}>
              画师直约 · 平台提供中立技术支持
            </span>
          </div>

          <div className="custom-artists-grid">
            {artists.map((artist) => (
              <article className="subpage-card custom-artist-card" key={artist.id}>
                <div className="custom-artist-head">
                  <div className="custom-artist-avatar" style={{ background: artist.gradient }}>
                    {artist.initial}
                  </div>
                  <div className="custom-artist-meta">
                    <strong>{artist.name}</strong>
                    <small style={{ color: artist.tagColor }}>{artist.styleTitle}</small>
                  </div>
                </div>

                <p className="custom-artist-desc">{artist.desc}</p>

                <div className="custom-artist-tags">
                  {artist.tags.map((tag) => (
                    <span className="custom-artist-tag" key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="custom-artist-footer">
                  <span className="custom-artist-status">{artist.status}</span>
                  <small style={{ color: '#718ea8' }}>{artist.studio}</small>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* 经典案例预览 */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <CheckCircle2 size={14} />
              <span>REAL SHOWCASE</span>
            </span>
            <h2>定制案例欣赏 · 从生活照到桌面伙伴</h2>
            <p>看看其他宠友将自家毛孩子做进电脑桌面的真实效果。</p>
          </div>

          <div className="custom-showcase-grid">
            {showcaseCases.map((item) => (
              <article className="subpage-card custom-showcase-item" key={item.title}>
                <img src={item.img} alt={item.title} className="custom-showcase-pet-img" />
                <div className="custom-showcase-info">
                  <h4>{item.title}</h4>
                  <p>{item.desc}</p>
                  <div className="custom-showcase-tags">
                    <span style={{ color: '#126ad6', fontWeight: 700 }}>🎨 {item.artist}</span>
                    <span style={{ color: '#059669', background: 'rgba(5, 150, 105, 0.1)', padding: '1px 6px', borderRadius: '4px' }}>
                      {item.tag}
                    </span>
                  </div>
                </div>
              </article>
            ))}
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
