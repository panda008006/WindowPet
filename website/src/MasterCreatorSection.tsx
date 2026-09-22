import { useState } from 'react'
import { Award, Camera, Check, Copy, HeartHandshake, ShieldCheck, Sparkles, Video, Zap } from 'lucide-react'

const qqGroupUrl = 'https://qm.qq.com/q/cYlRBbvuda'

interface MasterCreatorSectionProps {
  onNavigateCustom?: () => void
  onNavigateGallery?: () => void
}

export function MasterCreatorSection({ onNavigateCustom, onNavigateGallery }: MasterCreatorSectionProps) {
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

  const hallOfFamePets = [
    {
      code: 'WP-MASTER-001',
      name: '纯种布偶 · 雪球',
      avatar: `${import.meta.env.BASE_URL}pets/cat.png`,
      honor: '首位入驻星历宠星',
      action: '25帧视线跟随+踩奶',
      tag: '专属金冠封号',
    },
    {
      code: 'WP-MASTER-002',
      name: '柯基小短腿 · 欢欢',
      avatar: `${import.meta.env.BASE_URL}pets/dog.png`,
      honor: '工位治愈模范生',
      action: '扭臀摇尾+扑腾',
      tag: '专属金冠封号',
    },
    {
      code: 'WP-MASTER-003',
      name: '摸鱼怨种柴柴',
      avatar: `${import.meta.env.BASE_URL}pets/fox.png`,
      honor: '打工人精神代言',
      action: '翻白眼打哈欠叹气',
      tag: '专属金冠封号',
    },
  ]

  return (
    <div className="master-creator-section-card">
      <div className="master-creator-header">
        <div className="master-creator-badge-row">
          <span className="master-founder-badge">
            <Sparkles size={14} />
            <span>FOUNDER STUDIO · 官方主理人专栏</span>
          </span>
          <span className="master-open-source-tag">100% 永久免费开源 · 无商业套路</span>
        </div>

        <h2>我一直在首页，把你的毛孩子做进电脑桌面</h2>
        <p className="master-creator-lead">
          WindowPet 的软件核心全量开源免费。如果你想让自家的真实爱宠（猫咪、狗狗、龙猫、小鸟）常驻屏幕，
          你可以直接找我进行 <strong>1 对 1 手工生活照定制</strong>。每一个经过我定制的角色，
          都将享有<strong>永久唯一的官方名号封存</strong>，给它一份在这个世界上独一无二的生命印记。
        </p>

        <div className="master-action-row">
          <a
            className="primary-download master-cta-btn"
            href={qqGroupUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            <HeartHandshake size={17} />
            <span>预约博主定制 / 进群直聊</span>
          </a>

          <button
            type="button"
            className="secondary-action master-copy-btn"
            onClick={handleCopyQq}
          >
            {copiedQq ? <Check size={16} color="#059669" /> : <Copy size={16} />}
            <span>{copiedQq ? '官方群号已复制！' : '复制官方群号：422616922'}</span>
          </button>

          {onNavigateCustom && (
            <button
              type="button"
              className="secondary-action master-more-btn"
              onClick={onNavigateCustom}
            >
              <Camera size={16} />
              <span>了解定制流程与规范</span>
            </button>
          )}
        </div>
      </div>

      {/* 核心价值三大支柱 */}
      <div className="master-pillars-grid">
        <div className="master-pillar-item">
          <div className="pillar-icon" style={{ background: 'rgba(232, 95, 109, 0.12)', color: '#e85f6d' }}>
            <Award size={22} />
          </div>
          <div className="pillar-text">
            <strong>官方永久名号封号（星历认证）</strong>
            <p>
              每一个定制角色在交付专属安装包的同时，都会在 WindowPet 官网星历档案中永久储存唯一编号（如 <code>WP-MASTER-001</code>），赋予它在这个世界上的专属名份。
            </p>
          </div>
        </div>

        <div className="master-pillar-item">
          <div className="pillar-icon" style={{ background: 'rgba(47, 159, 147, 0.12)', color: '#2f9f93' }}>
            <Zap size={22} />
          </div>
          <div className="pillar-text">
            <strong>纯手工生活照切帧（1 对 1 神态还原）</strong>
            <p>
              提供 1~3 张生活照，由博主纯手工提炼标志性微表情（踩奶、打哈欠、叹气、歪头），25 帧丝滑动作，杜绝机械化千篇一律。
            </p>
          </div>
        </div>

        <div className="master-pillar-item">
          <div className="pillar-icon" style={{ background: 'rgba(59, 130, 246, 0.12)', color: '#2563eb' }}>
            <Video size={22} />
          </div>
          <div className="pillar-text">
            <strong>高清实况借力展示 · 本地轻量零负担</strong>
            <p>
              担心高质量视频占用服务器？高清演示实况直接挂载在 B 站与社交平台，软件本地运行切帧仅几百 KB，电脑零卡顿、换机随心用！
            </p>
          </div>
        </div>
      </div>

      {/* 已封存的星历名人堂样例 */}
      <div className="master-hall-of-fame">
        <div className="hall-header">
          <div className="hall-title">
            <ShieldCheck size={16} color="#e85f6d" />
            <span>已获得官方永久名号封存的爱宠代表</span>
          </div>
          {onNavigateGallery && (
            <button
              type="button"
              className="hall-link-btn"
              onClick={onNavigateGallery}
            >
              <span>进入小鼻嘎展馆浏览更多 →</span>
            </button>
          )}
        </div>

        <div className="hall-grid">
          {hallOfFamePets.map((p) => (
            <div className="hall-pet-card" key={p.code}>
              <div className="hall-pet-avatar-wrap">
                <img src={p.avatar} alt={p.name} className="hall-pet-avatar" />
                <span className="hall-crown-tag">{p.tag}</span>
              </div>
              <div className="hall-pet-meta">
                <span className="hall-code">{p.code}</span>
                <strong>{p.name}</strong>
                <small className="hall-honor">{p.honor}</small>
                <span className="hall-action-tag">动作：{p.action}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
