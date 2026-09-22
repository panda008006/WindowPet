import React, { useState, useMemo, useRef } from 'react'
import {
  Sparkles,
  Send,
  Flame,
  Heart,
  CheckCircle2,
  ArrowLeft,
  Compass,
  Palette,
  Zap,
  MessageSquareHeart,
} from 'lucide-react'
import './wanted.css'

export interface WishBubble {
  id: string
  name: string
  votes: number
  category: 'anime' | 'animal' | 'game' | 'meme'
  gradient: string
  textColor: string
  glowColor: string
  isHot?: boolean
  claimedBy?: string
  createdAt?: string
}

const initialBubbles: WishBubble[] = [
  {
    id: 'b1',
    name: '线条小狗',
    votes: 156,
    category: 'meme',
    gradient: 'radial-gradient(circle at 30% 30%, #fff0f2 0%, #ffccd2 60%, #ff9aa2 100%)',
    textColor: '#991b1b',
    glowColor: 'rgba(255, 154, 162, 0.45)',
    isHot: true,
  },
  {
    id: 'b2',
    name: '水豚卡皮巴拉',
    votes: 142,
    category: 'animal',
    gradient: 'radial-gradient(circle at 30% 30%, #fff7ed 0%, #ffedd5 60%, #fdba74 100%)',
    textColor: '#7c2d12',
    glowColor: 'rgba(253, 186, 116, 0.45)',
    isHot: true,
  },
  {
    id: 'b3',
    name: '纯种布偶 · 雪球',
    votes: 128,
    category: 'animal',
    gradient: 'radial-gradient(circle at 30% 30%, #f0fdf9 0%, #ccfbf1 60%, #5eead4 100%)',
    textColor: '#115e59',
    glowColor: 'rgba(94, 234, 212, 0.45)',
    isHot: true,
    claimedBy: '糖炒栗子定制工坊',
  },
  {
    id: 'b4',
    name: '摸鱼怨种柴柴',
    votes: 119,
    category: 'animal',
    gradient: 'radial-gradient(circle at 30% 30%, #fffbeb 0%, #fef3c7 60%, #fcd34d 100%)',
    textColor: '#854d0e',
    glowColor: 'rgba(252, 211, 77, 0.45)',
    isHot: true,
    claimedBy: '米诺画画中',
  },
  {
    id: 'b5',
    name: '帕鲁小电猫',
    votes: 98,
    category: 'game',
    gradient: 'radial-gradient(circle at 30% 30%, #ecfeff 0%, #cffafe 60%, #67e8f9 100%)',
    textColor: '#155e75',
    glowColor: 'rgba(103, 232, 249, 0.45)',
    isHot: true,
  },
  {
    id: 'b6',
    name: '可达鸭',
    votes: 92,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #fefce8 0%, #fef9c3 60%, #fde047 100%)',
    textColor: '#713f12',
    glowColor: 'rgba(253, 224, 71, 0.45)',
    isHot: true,
  },
  {
    id: 'b7',
    name: '间谍过家家 · 邦德',
    votes: 85,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #f8fafc 0%, #e2e8f0 60%, #94a3b8 100%)',
    textColor: '#334155',
    glowColor: 'rgba(148, 163, 184, 0.45)',
    isHot: true,
  },
  {
    id: 'b8',
    name: '乌萨奇兔兔',
    votes: 79,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #faf5ff 0%, #f3e8ff 60%, #d8b4fe 100%)',
    textColor: '#581c87',
    glowColor: 'rgba(216, 180, 254, 0.45)',
    claimedBy: '星野光年漫研所',
  },
  {
    id: 'b9',
    name: '酷洛米',
    votes: 74,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #fdf4ff 0%, #fae8ff 60%, #f0abfc 100%)',
    textColor: '#701a75',
    glowColor: 'rgba(240, 171, 252, 0.45)',
  },
  {
    id: 'b10',
    name: '蜡笔小新 · 小白',
    votes: 71,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #f0fdf4 0%, #dcfce7 60%, #86efac 100%)',
    textColor: '#14532d',
    glowColor: 'rgba(134, 239, 172, 0.45)',
  },
  {
    id: 'b11',
    name: '卡比兽',
    votes: 66,
    category: 'game',
    gradient: 'radial-gradient(circle at 30% 30%, #eff6ff 0%, #dbeafe 60%, #93c5fd 100%)',
    textColor: '#1e40af',
    glowColor: 'rgba(147, 197, 253, 0.45)',
  },
  {
    id: 'b12',
    name: '原神 · 锅巴',
    votes: 62,
    category: 'game',
    gradient: 'radial-gradient(circle at 30% 30%, #fff1f2 0%, #ffe4e6 60%, #fda4af 100%)',
    textColor: '#881337',
    glowColor: 'rgba(253, 164, 175, 0.45)',
  },
  {
    id: 'b13',
    name: '豚鼠小鼻嘎',
    votes: 59,
    category: 'animal',
    gradient: 'radial-gradient(circle at 30% 30%, #f0fdf4 0%, #dcfce7 60%, #86efac 100%)',
    textColor: '#14532d',
    glowColor: 'rgba(134, 239, 172, 0.45)',
    claimedBy: '官方创研所',
  },
  {
    id: 'b14',
    name: '蛋黄哥',
    votes: 55,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #fffbeb 0%, #fef3c7 60%, #fde68a 100%)',
    textColor: '#92400e',
    glowColor: 'rgba(253, 230, 138, 0.45)',
  },
  {
    id: 'b15',
    name: '罗小黑',
    votes: 51,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #f5f3ff 0%, #ede9fe 60%, #c4b5fd 100%)',
    textColor: '#4c1d95',
    glowColor: 'rgba(196, 181, 253, 0.45)',
  },
  {
    id: 'b16',
    name: '皮卡丘',
    votes: 48,
    category: 'game',
    gradient: 'radial-gradient(circle at 30% 30%, #fefce8 0%, #fef08a 60%, #eab308 100%)',
    textColor: '#713f12',
    glowColor: 'rgba(234, 179, 8, 0.45)',
  },
  {
    id: 'b17',
    name: '海德薇猫头鹰',
    votes: 44,
    category: 'animal',
    gradient: 'radial-gradient(circle at 30% 30%, #f1f5f9 0%, #e2e8f0 60%, #cbd5e1 100%)',
    textColor: '#334155',
    glowColor: 'rgba(203, 213, 225, 0.45)',
  },
  {
    id: 'b18',
    name: '哆啦A梦',
    votes: 41,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #e0f2fe 0%, #bae6fd 60%, #38bdf8 100%)',
    textColor: '#0369a1',
    glowColor: 'rgba(56, 189, 248, 0.45)',
  },
  {
    id: 'b19',
    name: '企鹅家族 Pingu',
    votes: 38,
    category: 'meme',
    gradient: 'radial-gradient(circle at 30% 30%, #ecfeff 0%, #cffafe 60%, #22d3ee 100%)',
    textColor: '#155e75',
    glowColor: 'rgba(34, 211, 238, 0.45)',
  },
  {
    id: 'b20',
    name: '汤姆猫',
    votes: 35,
    category: 'meme',
    gradient: 'radial-gradient(circle at 30% 30%, #f8fafc 0%, #cbd5e1 60%, #94a3b8 100%)',
    textColor: '#1e293b',
    glowColor: 'rgba(148, 163, 184, 0.45)',
  },
  {
    id: 'b21',
    name: 'chiikawa 吉伊',
    votes: 33,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #fff1f2 0%, #fed7aa 60%, #fb923c 100%)',
    textColor: '#9a3412',
    glowColor: 'rgba(251, 146, 60, 0.45)',
  },
  {
    id: 'b22',
    name: '史努比',
    votes: 30,
    category: 'animal',
    gradient: 'radial-gradient(circle at 30% 30%, #fafafa 0%, #f4f4f5 60%, #e4e4e7 100%)',
    textColor: '#27272a',
    glowColor: 'rgba(228, 228, 231, 0.45)',
  },
  {
    id: 'b23',
    name: '龙猫',
    votes: 27,
    category: 'anime',
    gradient: 'radial-gradient(circle at 30% 30%, #f0fdf4 0%, #bbf7d0 60%, #4ade80 100%)',
    textColor: '#166534',
    glowColor: 'rgba(74, 222, 128, 0.45)',
  },
  {
    id: 'b24',
    name: '肥嘟嘟左卫门',
    votes: 24,
    category: 'meme',
    gradient: 'radial-gradient(circle at 30% 30%, #fff1f2 0%, #fecdd3 60%, #fb7185 100%)',
    textColor: '#9f1239',
    glowColor: 'rgba(251, 113, 133, 0.45)',
  },
]

const quickPromptChips = [
  '卡皮巴拉',
  '间谍过家家邦德',
  '酷洛米',
  '蛋黄哥',
  '罗小黑',
  '蜡笔小新小白',
  '波加曼',
  '帕鲁小电猫',
]

const colorPalettes = [
  { gradient: 'radial-gradient(circle at 30% 30%, #fff0f2 0%, #ffccd2 60%, #ff9aa2 100%)', textColor: '#991b1b', glowColor: 'rgba(255, 154, 162, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #f0fdf9 0%, #ccfbf1 60%, #5eead4 100%)', textColor: '#115e59', glowColor: 'rgba(94, 234, 212, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #eff6ff 0%, #dbeafe 60%, #93c5fd 100%)', textColor: '#1e40af', glowColor: 'rgba(147, 197, 253, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #faf5ff 0%, #f3e8ff 60%, #d8b4fe 100%)', textColor: '#581c87', glowColor: 'rgba(216, 180, 254, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #fff7ed 0%, #ffedd5 60%, #fdba74 100%)', textColor: '#7c2d12', glowColor: 'rgba(253, 186, 116, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #fefce8 0%, #fef9c3 60%, #fde047 100%)', textColor: '#713f12', glowColor: 'rgba(253, 224, 71, 0.5)' },
]

interface WantedPetPageProps {
  onBackToHome: () => void
  onOpenGallery?: () => void
  onOpenCustom?: () => void
}

type FilterType = 'all' | 'hot' | 'claimed' | 'new'

export function WantedPetPage({ onBackToHome, onOpenGallery, onOpenCustom }: WantedPetPageProps) {
  const [bubbles, setBubbles] = useState<WishBubble[]>(initialBubbles)
  const [inputText, setInputText] = useState('')
  const [activeFilter, setActiveFilter] = useState<FilterType>('all')
  const [toastMsg, setToastMsg] = useState<string | null>(null)
  const [poppingId, setPoppingId] = useState<string | null>(null)

  // 升腾冒起泡泡的核心动画状态 (Codex/Anti-gravity 物理升腾)
  const [ascendingBubble, setAscendingBubble] = useState<{
    id: string
    name: string
    gradient: string
    textColor: string
    glowColor: string
  } | null>(null)

  const inputRef = useRef<HTMLInputElement | null>(null)

  const showToast = (msg: string) => {
    setToastMsg(msg)
    setTimeout(() => setToastMsg(null), 3000)
  }

  // 投票点赞 +1
  const handleVote = (id: string, name: string) => {
    setPoppingId(id)
    setBubbles((prev) =>
      prev.map((b) => (b.id === id ? { ...b, votes: b.votes + 1 } : b))
    )
    showToast(`🎉 为【${name}】点赞 +1！泡泡又膨胀了一圈~`)
    setTimeout(() => setPoppingId(null), 600)
  }

  // 发送心愿：触发泡泡从底部升腾并填充到上方的动画
  const triggerSendWish = (rawText: string) => {
    const trimmed = rawText.trim()
    if (!trimmed) return

    if (trimmed.length < 2 || trimmed.length > 14) {
      showToast('⚠️ 角色名称请控制在 2~14 个字以内哦')
      return
    }

    // 检查是否已有该角色
    const existingIndex = bubbles.findIndex(
      (b) => b.name.toLowerCase() === trimmed.toLowerCase()
    )

    if (existingIndex >= 0) {
      const existing = bubbles[existingIndex]
      handleVote(existing.id, existing.name)
      setInputText('')
      return
    }

    // 选择配色
    const pal = colorPalettes[bubbles.length % colorPalettes.length]
    const newBubbleId = `custom-${Date.now()}`

    // 1. 启动底部冒起升腾动画！
    setAscendingBubble({
      id: newBubbleId,
      name: trimmed,
      gradient: pal.gradient,
      textColor: pal.textColor,
      glowColor: pal.glowColor,
    })

    setInputText('')

    // 2. 升腾飞入动画进行 950ms 后，正式“去填充”上方的泡泡海洋
    setTimeout(() => {
      const newBubble: WishBubble = {
        id: newBubbleId,
        name: trimmed,
        votes: 1,
        category: 'anime',
        gradient: pal.gradient,
        textColor: pal.textColor,
        glowColor: pal.glowColor,
        createdAt: '刚刚',
      }

      setBubbles((prev) => [newBubble, ...prev])
      setPoppingId(newBubbleId)
      setAscendingBubble(null)
      showToast(`✨ 成功吐出泡泡【${trimmed}】并填充入心愿海！快来给它顶大！`)
      setTimeout(() => setPoppingId(null), 800)
    }, 950)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    triggerSendWish(inputText)
  }

  // 快速标签点击
  const handleQuickChipClick = (chipText: string) => {
    triggerSendWish(chipText)
  }

  // 过滤后的泡泡列表
  const filteredBubbles = useMemo(() => {
    switch (activeFilter) {
      case 'hot':
        return [...bubbles].sort((a, b) => b.votes - a.votes)
      case 'claimed':
        return bubbles.filter((b) => Boolean(b.claimedBy))
      case 'new':
        return bubbles.filter((b) => b.id.startsWith('custom-'))
      default:
        return bubbles
    }
  }, [bubbles, activeFilter])

  // 计算最大票数，用于动态等比缩放
  const maxVotes = useMemo(() => {
    return Math.max(...bubbles.map((b) => b.votes), 1)
  }, [bubbles])

  return (
    <div className="wanted-page-wrapper">
      {/* 顶部轻量极简面包屑与快捷导航 */}
      <header className="wanted-topbar">
        <button type="button" className="wanted-back-btn" onClick={onBackToHome}>
          <ArrowLeft size={16} />
          <span>返回首页</span>
        </button>

        <div className="wanted-topbar-tabs">
          <button
            type="button"
            className={`wanted-filter-pill ${activeFilter === 'all' ? 'is-active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            <span>全部心愿 ({bubbles.length})</span>
          </button>
          <button
            type="button"
            className={`wanted-filter-pill ${activeFilter === 'hot' ? 'is-active' : ''}`}
            onClick={() => setActiveFilter('hot')}
          >
            <Flame size={13} fill={activeFilter === 'hot' ? '#ef4444' : 'none'} color="#ef4444" />
            <span>呼声最高</span>
          </button>
          <button
            type="button"
            className={`wanted-filter-pill ${activeFilter === 'claimed' ? 'is-active' : ''}`}
            onClick={() => setActiveFilter('claimed')}
          >
            <Palette size={13} color="#2f9f93" />
            <span>画师已认领</span>
          </button>
          {bubbles.some((b) => b.id.startsWith('custom-')) && (
            <button
              type="button"
              className={`wanted-filter-pill ${activeFilter === 'new' ? 'is-active' : ''}`}
              onClick={() => setActiveFilter('new')}
            >
              <Zap size={13} color="#e85f6d" />
              <span>社区最新提出</span>
            </button>
          )}
        </div>

        <div className="wanted-topbar-actions">
          {onOpenGallery && (
            <button type="button" className="wanted-ghost-link" onClick={onOpenGallery}>
              <Compass size={15} />
              <span>探索在馆角色</span>
            </button>
          )}
        </div>
      </header>

      {/* 顶部飘浮 Toast 提示 */}
      {toastMsg && (
        <div className="wanted-toast-pill" role="status">
          <Sparkles size={15} />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* 主界面主体：心愿海洋与角色气泡天空 */}
      <main className="wanted-main-stage">
        <div className="wanted-hero-header">
          <div className="wanted-badge-row">
            <span className="wanted-eyebrow-badge">
              <Sparkles size={14} />
              <span>COMMUNITY LIVE WISH OCEAN · 想要角色心愿海</span>
            </span>
            <span className="wanted-online-pill">
              <span className="wanted-green-dot" />
              <span>实时互动 · 灵感吐泡泡</span>
            </span>
          </div>

          <h1 className="wanted-page-title">想要什么角色住进桌面？打字让它冒出来！</h1>
          <p className="wanted-page-subtitle">
            输入任意你想在电脑桌面上见到的角色。谁的呼声高，谁的泡泡就膨胀得最大！
            入驻画师与主理人会根据心愿海的泡泡热度，优先切帧制作并免费上线~
          </p>
        </div>

        {/* 气泡天空与海洋 */}
        <div className="wanted-bubbles-ocean">
          {filteredBubbles.map((b, idx) => {
            // 尺寸计算：从 82px 到 152px 动态线性平滑膨胀
            const ratio = Math.min(1, Math.max(0, b.votes / maxVotes))
            const sizePx = Math.round(82 + ratio * 68)
            const isPopping = poppingId === b.id

            return (
              <div
                key={b.id}
                className={`ocean-bubble-node bubble-float-drift-${(idx % 6) + 1} ${
                  isPopping ? 'is-heart-bouncing' : ''
                }`}
                style={{
                  width: `${sizePx}px`,
                  height: `${sizePx}px`,
                  background: b.gradient,
                  boxShadow: `0 10px 30px ${b.glowColor}, inset 0 -4px 12px rgba(0,0,0,0.06), inset 0 4px 12px rgba(255,255,255,0.85)`,
                  color: b.textColor,
                }}
                onClick={() => handleVote(b.id, b.name)}
                title={`点击为【${b.name}】投出宝贵 1 票 (当前: ${b.votes} 票)`}
                role="button"
                tabIndex={0}
              >
                {b.isHot && (
                  <span className="ocean-hot-badge" title="呼声超高！">
                    <Flame size={12} fill="#ef4444" color="#ef4444" />
                  </span>
                )}

                <span className="ocean-bubble-title">{b.name}</span>

                <div className="ocean-bubble-stat">
                  <Heart size={11} fill="currentColor" />
                  <span>{b.votes}</span>
                </div>

                {b.claimedBy && (
                  <span className="ocean-claimed-tag" title={`已被【${b.claimedBy}】认领制作中`}>
                    ✓ 制作中
                  </span>
                )}
              </div>
            )
          })}
        </div>

        {/* 画师入驻呼吁底栏 */}
        <div className="wanted-artist-callout">
          <div className="callout-left">
            <CheckCircle2 size={16} color="#10b981" />
            <span>
              <strong>开源防刷保障：</strong>每个角色独立投票，防止重复刷屏；每个作者最多认领 20 款入驻。
            </span>
          </div>
          {onOpenCustom && (
            <button type="button" className="callout-artist-btn" onClick={onOpenCustom}>
              <Palette size={14} />
              <span>我是画师，认领心愿制作</span>
            </button>
          )}
        </div>
      </main>

      {/* 核心亮点：升腾冒起泡泡 (物理飞升动画并飞入上方心愿池填充) */}
      {ascendingBubble && (
        <div
          className="ascending-bubble-actor"
          style={{
            background: ascendingBubble.gradient,
            boxShadow: `0 0 32px 8px ${ascendingBubble.glowColor}`,
            color: ascendingBubble.textColor,
          }}
        >
          <div className="ascending-bubble-glow-ring" />
          <span className="ascending-bubble-text">{ascendingBubble.name}</span>
          <span className="ascending-bubble-meta">🫧 正在升腾注入心愿海...</span>
        </div>
      )}

      {/* 核心亮点：Codex / Anti-gravity 风格正中下方悬浮输入对话框 */}
      <div className="codex-floating-dock-container">
        {/* 悬浮输入框上方的灵感快捷微气泡 */}
        <div className="codex-dock-prompt-chips" aria-label="灵感快捷推荐">
          <span className="chips-label">
            <Sparkles size={12} />
            <span>快速填充：</span>
          </span>
          {quickPromptChips.map((chip) => (
            <button
              key={chip}
              type="button"
              className="codex-prompt-chip-btn"
              onClick={() => handleQuickChipClick(chip)}
            >
              <span>+ {chip}</span>
            </button>
          ))}
        </div>

        {/* 正中下方高质感悬浮毛玻璃对话框 */}
        <form className="codex-floating-dialog-bar" onSubmit={handleSubmit}>
          <div className="dialog-left-icon">
            <MessageSquareHeart size={19} color="#e85f6d" />
          </div>

          <input
            ref={inputRef}
            type="text"
            className="codex-dialog-input"
            placeholder="输入你想住进桌面的角色，按回车或点发送..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            maxLength={14}
            autoFocus
          />

          <button
            type="submit"
            className={`codex-dialog-send-btn ${inputText.trim().length > 0 ? 'is-active' : ''}`}
            disabled={!inputText.trim()}
            title="发送心愿，让泡泡冒上去！"
          >
            <Send size={16} />
            <span>吐出泡泡 🫧</span>
          </button>
        </form>

        <div className="codex-dock-footnote">
          <span>按回车即时升腾飞升 · 纯净开源 · 免登录人人可参与</span>
        </div>
      </div>
    </div>
  )
}
