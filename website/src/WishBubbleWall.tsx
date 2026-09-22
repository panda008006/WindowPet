import { useState, useMemo } from 'react'
import { Sparkles, Send, Flame, Heart, CheckCircle2 } from 'lucide-react'

interface WishBubble {
  id: string
  name: string
  votes: number
  gradient: string
  textColor: string
  glowColor: string
  isHot?: boolean
  claimedBy?: string
}

const initialBubbles: WishBubble[] = [
  {
    id: 'b1',
    name: '线条小狗',
    votes: 89,
    gradient: 'radial-gradient(circle at 30% 30%, #fff0f2 0%, #ffccd2 60%, #ff9aa2 100%)',
    textColor: '#991b1b',
    glowColor: 'rgba(255, 154, 162, 0.45)',
    isHot: true,
  },
  {
    id: 'b2',
    name: '纯种布偶 · 雪球',
    votes: 76,
    gradient: 'radial-gradient(circle at 30% 30%, #f0fdf9 0%, #ccfbf1 60%, #5eead4 100%)',
    textColor: '#115e59',
    glowColor: 'rgba(94, 234, 212, 0.45)',
    isHot: true,
    claimedBy: '糖炒栗子定制工坊',
  },
  {
    id: 'b3',
    name: '摸鱼怨种柴柴',
    votes: 68,
    gradient: 'radial-gradient(circle at 30% 30%, #fffbeb 0%, #fef3c7 60%, #fcd34d 100%)',
    textColor: '#854d0e',
    glowColor: 'rgba(252, 211, 77, 0.45)',
    isHot: true,
    claimedBy: '米诺画画中',
  },
  {
    id: 'b4',
    name: '卡比兽',
    votes: 53,
    gradient: 'radial-gradient(circle at 30% 30%, #eff6ff 0%, #dbeafe 60%, #93c5fd 100%)',
    textColor: '#1e40af',
    glowColor: 'rgba(147, 197, 253, 0.45)',
  },
  {
    id: 'b5',
    name: '可达鸭',
    votes: 49,
    gradient: 'radial-gradient(circle at 30% 30%, #fefce8 0%, #fef9c3 60%, #fde047 100%)',
    textColor: '#713f12',
    glowColor: 'rgba(253, 224, 71, 0.45)',
  },
  {
    id: 'b6',
    name: '乌萨奇兔兔',
    votes: 44,
    gradient: 'radial-gradient(circle at 30% 30%, #faf5ff 0%, #f3e8ff 60%, #d8b4fe 100%)',
    textColor: '#581c87',
    glowColor: 'rgba(216, 180, 254, 0.45)',
    claimedBy: '星野光年漫研所',
  },
  {
    id: 'b7',
    name: '水豚卡皮巴拉',
    votes: 38,
    gradient: 'radial-gradient(circle at 30% 30%, #fff7ed 0%, #ffedd5 60%, #fdba74 100%)',
    textColor: '#7c2d12',
    glowColor: 'rgba(253, 186, 116, 0.45)',
  },
  {
    id: 'b8',
    name: '原神锅巴',
    votes: 34,
    gradient: 'radial-gradient(circle at 30% 30%, #fff1f2 0%, #ffe4e6 60%, #fda4af 100%)',
    textColor: '#881337',
    glowColor: 'rgba(253, 164, 175, 0.45)',
  },
  {
    id: 'b9',
    name: '帕鲁小电猫',
    votes: 28,
    gradient: 'radial-gradient(circle at 30% 30%, #ecfeff 0%, #cffafe 60%, #67e8f9 100%)',
    textColor: '#155e75',
    glowColor: 'rgba(103, 232, 249, 0.45)',
  },
  {
    id: 'b10',
    name: '豚鼠小鼻嘎',
    votes: 25,
    gradient: 'radial-gradient(circle at 30% 30%, #f0fdf4 0%, #dcfce7 60%, #86efac 100%)',
    textColor: '#14532d',
    glowColor: 'rgba(134, 239, 172, 0.45)',
    claimedBy: '官方创研所',
  },
]

const colorPalettes = [
  { gradient: 'radial-gradient(circle at 30% 30%, #fff0f2 0%, #ffccd2 60%, #ff9aa2 100%)', textColor: '#991b1b', glowColor: 'rgba(255, 154, 162, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #f0fdf9 0%, #ccfbf1 60%, #5eead4 100%)', textColor: '#115e59', glowColor: 'rgba(94, 234, 212, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #eff6ff 0%, #dbeafe 60%, #93c5fd 100%)', textColor: '#1e40af', glowColor: 'rgba(147, 197, 253, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #faf5ff 0%, #f3e8ff 60%, #d8b4fe 100%)', textColor: '#581c87', glowColor: 'rgba(216, 180, 254, 0.5)' },
  { gradient: 'radial-gradient(circle at 30% 30%, #fff7ed 0%, #ffedd5 60%, #fdba74 100%)', textColor: '#7c2d12', glowColor: 'rgba(253, 186, 116, 0.5)' },
]

export function WishBubbleWall({ onNavigateCustom }: { onNavigateCustom?: () => void }) {
  const [bubbles, setBubbles] = useState<WishBubble[]>(initialBubbles)
  const [inputText, setInputText] = useState('')
  const [toastMsg, setToastMsg] = useState<string | null>(null)
  const [recentlyPoppedId, setRecentlyPoppedId] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToastMsg(msg)
    setTimeout(() => setToastMsg(null), 2800)
  }

  // 投票点赞 +1
  const handleVote = (id: string, name: string) => {
    setRecentlyPoppedId(id)
    setBubbles((prev) =>
      prev.map((b) => (b.id === id ? { ...b, votes: b.votes + 1 } : b))
    )
    showToast(`🎉 为【${name}】点赞 +1！泡泡又膨胀了一圈~`)
    setTimeout(() => setRecentlyPoppedId(null), 600)
  }

  // 提交新许愿（吐泡泡）
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = inputText.trim()
    if (!trimmed) return

    if (trimmed.length < 2 || trimmed.length > 14) {
      showToast('⚠️ 角色名称请控制在 2~14 个字以内哦')
      return
    }

    // 检查是否已经存在
    const existingIndex = bubbles.findIndex(
      (b) => b.name.toLowerCase() === trimmed.toLowerCase()
    )

    if (existingIndex >= 0) {
      const existing = bubbles[existingIndex]
      handleVote(existing.id, existing.name)
      setInputText('')
      return
    }

    // 新增气泡
    const pal = colorPalettes[bubbles.length % colorPalettes.length]
    const newBubble: WishBubble = {
      id: `custom-${Date.now()}`,
      name: trimmed,
      votes: 1,
      gradient: pal.gradient,
      textColor: pal.textColor,
      glowColor: pal.glowColor,
    }

    setBubbles((prev) => [newBubble, ...prev])
    setRecentlyPoppedId(newBubble.id)
    setInputText('')
    showToast(`✨ 成功吐出新泡泡【${trimmed}】！快拉朋友来把它顶大！`)
    setTimeout(() => setRecentlyPoppedId(null), 600)
  }

  // 计算最大票数，用于动态等比缩放气泡尺寸
  const maxVotes = useMemo(() => {
    return Math.max(...bubbles.map((b) => b.votes), 1)
  }, [bubbles])

  return (
    <div className="wish-bubble-wall-card">
      {toastMsg && (
        <div className="bubble-toast-pill" role="status">
          <Sparkles size={15} />
          <span>{toastMsg}</span>
        </div>
      )}

      <div className="bubble-wall-header">
        <div className="bubble-header-titles">
          <span className="bubble-eyebrow">
            <Sparkles size={14} />
            <span>COMMUNITY LIVE WISH POOL · 灵感疯狂吐泡泡</span>
          </span>
          <h3>想让什么角色住进桌面？打字让它吐出来！</h3>
          <p>
            谁的提议多，谁的泡泡就膨胀得最大！点击任意泡泡可直接 <strong>+1 助力</strong>，入驻画师与主理人会优先认领大泡泡切帧制作！
          </p>
        </div>

        {/* 输入吐泡泡栏 */}
        <form className="bubble-input-bar" onSubmit={handleSubmit}>
          <input
            type="text"
            className="bubble-input-field"
            placeholder="输入心仪的角色（如：线条小狗、可达鸭...）"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            maxLength={14}
          />
          <button type="submit" className="bubble-submit-btn">
            <Send size={15} />
            <span>吐个泡泡 🫧</span>
          </button>
        </form>
      </div>

      {/* 动态浮动泡泡舞台 */}
      <div className="bubble-stage-canvas">
        {bubbles.map((b, idx) => {
          // 尺寸映射：最小 75px，最大 135px
          const ratio = Math.min(1, Math.max(0, b.votes / maxVotes))
          const sizePx = Math.round(75 + ratio * 60)
          const isPopping = recentlyPoppedId === b.id

          return (
            <div
              key={b.id}
              className={`floating-bubble-item bubble-float-${(idx % 4) + 1} ${isPopping ? 'is-pop-bouncing' : ''}`}
              style={{
                width: `${sizePx}px`,
                height: `${sizePx}px`,
                background: b.gradient,
                boxShadow: `0 8px 24px ${b.glowColor}, inset 0 -4px 10px rgba(0,0,0,0.06), inset 0 4px 10px rgba(255,255,255,0.8)`,
                color: b.textColor,
              }}
              onClick={() => handleVote(b.id, b.name)}
              title={`点击为【${b.name}】投上宝贵 1 票 (当前: ${b.votes} 票)`}
              role="button"
              tabIndex={0}
            >
              {b.isHot && (
                <span className="bubble-hot-badge" title="超热门角色">
                  <Flame size={11} fill="#ef4444" color="#ef4444" />
                </span>
              )}

              <span className="bubble-name-text">{b.name}</span>
              <span className="bubble-vote-pill">
                <Heart size={10} fill="currentColor" />
                <span>{b.votes}</span>
              </span>

              {b.claimedBy && (
                <span className="bubble-claimed-tag" title={`已被画师【${b.claimedBy}】认领制作中`}>
                  ✓ 制作中
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* 底部画师联动与限额说明 */}
      <div className="bubble-wall-footer">
        <div className="bubble-footer-tips">
          <CheckCircle2 size={15} color="#10b981" />
          <span>
            <strong>防刷与审核机制：</strong>内置敏感词与频率限制，每个作者最多可认领 20 款入驻。绿色健康，人人可参与！
          </span>
        </div>

        {onNavigateCustom && (
          <button
            type="button"
            className="bubble-claim-btn"
            onClick={onNavigateCustom}
          >
            <span>🎨 我是画师，我要认领制作</span>
          </button>
        )}
      </div>
    </div>
  )
}
