import React, { useState, useMemo, useRef } from 'react'
import {
  Sparkles,
  Send,
  Flame,
  Heart,
  ArrowLeft,
  Compass,
  Palette,
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
  claimedCount?: number
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
    claimedCount: 1,
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
    claimedCount: 1,
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
    claimedCount: 1,
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
    claimedCount: 1,
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

type FilterType = 'xiaobiga' | 'claimed'

/**
 * 7日心愿海交错布局算法：
 * 保证近7天高票角色泡泡最大、最突出；
 * 同时将大泡泡、小泡泡和中泡泡自然错落穿插，形成极具生命力的海洋泡泡星系图景。
 */
function distributeOceanBubbles(items: WishBubble[]): WishBubble[] {
  if (items.length <= 4) return items
  // 按7日票数降序排序
  const sorted = [...items].sort((a, b) => b.votes - a.votes)

  const big: WishBubble[] = []
  const medium: WishBubble[] = []
  const small: WishBubble[] = []

  const total = sorted.length
  const bigCutoff = Math.max(3, Math.floor(total * 0.22)) // 前排约 5~6 个大泡泡
  const medCutoff = Math.floor(total * 0.55) // 中排约 8~9 个中泡泡

  sorted.forEach((item, index) => {
    if (index < bigCutoff) {
      big.push(item)
    } else if (index < medCutoff) {
      medium.push(item)
    } else {
      small.push(item)
    }
  })

  // 错落编排：大泡泡作为视觉核心锚点，周边有机穿插小泡泡与中泡泡
  const result: WishBubble[] = []
  let bIdx = 0
  let mIdx = 0
  let sIdx = 0

  while (bIdx < big.length || mIdx < medium.length || sIdx < small.length) {
    if (bIdx < big.length) result.push(big[bIdx++])
    if (sIdx < small.length) result.push(small[sIdx++])
    if (mIdx < medium.length) result.push(medium[mIdx++])
    if (sIdx < small.length) result.push(small[sIdx++])
  }

  return result
}

export function WantedPetPage({ onBackToHome, onOpenGallery, onOpenCustom }: WantedPetPageProps) {
  const [bubbles, setBubbles] = useState<WishBubble[]>(initialBubbles)
  const [inputText, setInputText] = useState('')
  const [activeFilter, setActiveFilter] = useState<FilterType>('xiaobiga')
  const [toastMsg, setToastMsg] = useState<string | null>(null)
  const [poppingId, setPoppingId] = useState<string | null>(null)
  const [isArtistMode, setIsArtistMode] = useState(false)

  // 用户个人投票记录：每个角色限投 20 次，可投多个不同角色
  const [userVotes, setUserVotes] = useState<Record<string, number>>(() => {
    try {
      const saved = localStorage.getItem('windowpet_wish_votes_map')
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  })

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

  // 投票点赞 +1 (单角色限 20 票，多角色不限)
  const handleVote = (id: string, name: string) => {
    const currentCount = userVotes[id] || 0
    if (currentCount >= 20) {
      showToast(`💖 您已为【${name}】投满 20 票心愿啦！心意满满，去为其他心仪角色投出宝贵一票吧~`)
      return
    }

    const nextCount = currentCount + 1
    const updatedVotes = { ...userVotes, [id]: nextCount }
    setUserVotes(updatedVotes)
    try {
      localStorage.setItem('windowpet_wish_votes_map', JSON.stringify(updatedVotes))
    } catch {
      // ignore
    }

    setPoppingId(id)
    setBubbles((prev) =>
      prev.map((b) => (b.id === id ? { ...b, votes: b.votes + 1 } : b))
    )
    showToast(`🎉 为【${name}】许愿 +1！(您已投 ${nextCount}/20 票) 泡泡又膨胀了一圈~`)
    setTimeout(() => setPoppingId(null), 600)
  }

  // 画师认领制作：认领人数加 1 并点亮制作状态
  const handleClaimPet = (id: string, name: string) => {
    setPoppingId(id)
    let newClaimCount = 1
    setBubbles((prev) =>
      prev.map((b) => {
        if (b.id !== id) return b
        const prevCount = b.claimedCount || (b.claimedBy ? 1 : 0)
        newClaimCount = prevCount + 1
        return {
          ...b,
          claimedCount: newClaimCount,
          claimedBy: b.claimedBy || '社区画师',
        }
      })
    )
    showToast(`🎨 感谢画师老师认领【${name}】！认领人数已加 1（当前已有 ${newClaimCount} 位画师认领制作），期待早日上线！`)
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

  // 计算7日热度排行（1-indexed）
  const voteRanks = useMemo(() => {
    const sorted = [...bubbles].sort((a, b) => b.votes - a.votes)
    const map: Record<string, number> = {}
    sorted.forEach((b, idx) => {
      map[b.id] = idx + 1
    })
    return map
  }, [bubbles])

  // 过滤后的泡泡列表
  const filteredBubbles = useMemo(() => {
    if (activeFilter === 'claimed') {
      return bubbles.filter((b) => Boolean(b.claimedBy) || Boolean(b.claimedCount && b.claimedCount > 0))
    }
    // 默认 'xiaobiga'：近7天热度心愿海，高呼声大泡泡与小泡泡自然错落呈现
    return distributeOceanBubbles(bubbles)
  }, [bubbles, activeFilter])

  // 计算最大票数，用于动态等比缩放
  const maxVotes = useMemo(() => {
    return Math.max(...bubbles.map((b) => b.votes), 1)
  }, [bubbles])

  return (
    <div className="wanted-page-wrapper">
      {/* 顶部极简快捷导航（tabs 放置在左侧，与返回首页成组） */}
      <header className="wanted-topbar">
        <div className="wanted-topbar-left">
          <button type="button" className="wanted-back-btn" onClick={onBackToHome}>
            <ArrowLeft size={16} />
            <span>返回首页</span>
          </button>

          <div className="wanted-topbar-tabs">
            <button
              type="button"
              className={`wanted-filter-pill ${activeFilter === 'xiaobiga' ? 'is-active' : ''}`}
              onClick={() => setActiveFilter('xiaobiga')}
              title="7日心愿热度榜 · 大小泡泡自然错落涌动"
            >
              <span>🐾 小鼻嘎</span>
            </button>
            <button
              type="button"
              className={`wanted-filter-pill ${activeFilter === 'claimed' ? 'is-active' : ''}`}
              onClick={() => setActiveFilter('claimed')}
              title="画师已认领角色"
            >
              <Palette size={13} color="#2f9f93" />
              <span>画师已领</span>
            </button>
          </div>
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

      {/* 主界面主体：心愿海洋与角色气泡天空（去除冗余大标题与说明段落，直接进入灵动泡泡海） */}
      <main className="wanted-main-stage">

        {/* 画师入驻与心愿认领状态栏 (放置在气泡海洋上方，一目了然且永不被底部输入框遮挡) */}
        <div className="wanted-artist-callout">
          <div className="callout-left">
            {isArtistMode ? (
              <div className="callout-artist-mode-active">
                <span className="callout-live-dot" />
                <span>
                  <strong>画师认领模式生效中：</strong>点击下方任意角色的气泡，即可认领该心愿（认领画师数 +1 并点亮制作进度）！
                </span>
              </div>
            ) : (
              <div className="callout-artist-mode-idle">
                <Palette size={16} color="#2f9f93" />
                <span>
                  <strong>画师心愿认领：</strong>点击右侧【我是画师】，即可开启认领模式并点亮您想制作的角色~
                </span>
              </div>
            )}
          </div>

          <div className="callout-right-actions">
            <button
              type="button"
              className={`callout-artist-btn ${isArtistMode ? 'is-artist-active' : ''}`}
              onClick={() => {
                setIsArtistMode((prev) => !prev)
                if (!isArtistMode) {
                  showToast('🎨 已开启【画师认领模式】！现在点击下方任意角色的气泡，即可认领该角色（认领数加 1）~')
                } else {
                  showToast('已退出画师认领模式，恢复普通心愿投票。')
                }
              }}
              title={isArtistMode ? '点击退出画师认领模式' : '点击开启画师认领模式'}
            >
              <Palette size={14} />
              <span>{isArtistMode ? '✓ 画师认领中 (点击退出)' : '我是画师，认领心愿'}</span>
            </button>

            {onOpenCustom && (
              <button
                type="button"
                className="callout-secondary-custom-btn"
                onClick={onOpenCustom}
                title="前往爱宠定制专区"
              >
                <span>爱宠定制专区 →</span>
              </button>
            )}
          </div>
        </div>

        {/* 气泡天空与海洋 */}
        <div className={`wanted-bubbles-ocean ${isArtistMode ? 'is-artist-mode' : ''}`}>
          {filteredBubbles.map((b, idx) => {
            const rank = voteRanks[b.id] || 99
            // 尺寸计算：7天热度自然映射（大泡泡最膨胀至 152px，小泡泡精巧 82px，错落有致）
            const ratio = Math.min(1, Math.max(0, b.votes / maxVotes))
            const sizePx = Math.round(82 + Math.pow(ratio, 0.82) * 70)
            const isPopping = poppingId === b.id
            const myVote = userVotes[b.id] || 0
            const claimCount = b.claimedCount || (b.claimedBy ? 1 : 0)

            return (
              <div
                key={b.id}
                className={`ocean-bubble-node bubble-float-drift-${(idx % 6) + 1} ${
                  isPopping ? 'is-heart-bouncing' : ''
                } ${isArtistMode ? 'is-artist-interactive' : ''}`}
                style={{
                  width: `${sizePx}px`,
                  height: `${sizePx}px`,
                  background: b.gradient,
                  boxShadow: isArtistMode
                    ? `0 10px 30px rgba(16, 185, 129, 0.4), inset 0 -4px 12px rgba(0,0,0,0.06), inset 0 4px 12px rgba(255,255,255,0.85)`
                    : `0 10px 30px ${b.glowColor}, inset 0 -4px 12px rgba(0,0,0,0.06), inset 0 4px 12px rgba(255,255,255,0.85)`,
                  color: b.textColor,
                }}
                onClick={() => (isArtistMode ? handleClaimPet(b.id, b.name) : handleVote(b.id, b.name))}
                title={
                  isArtistMode
                    ? `[画师认领模式] 点击认领【${b.name}】制作 (认领画师数 +1，当前: ${claimCount} 位)`
                    : `点击为【${b.name}】投出宝贵心愿票 (当前: ${b.votes} 票，您已投: ${myVote}/20 票)`
                }
                role="button"
                tabIndex={0}
              >
                {/* 7日热度前三甲冠亚季军徽标与超高呼声火苗 */}
                {rank === 1 && (
                  <span className="ocean-rank-crown" title="近7天热度 Top 1 · 呼声最高！">
                    👑 Top 1
                  </span>
                )}
                {rank === 2 && (
                  <span className="ocean-rank-crown is-rank-2" title="近7天热度 Top 2">
                    🥈 Top 2
                  </span>
                )}
                {rank === 3 && (
                  <span className="ocean-rank-crown is-rank-3" title="近7天热度 Top 3">
                    🥉 Top 3
                  </span>
                )}
                {rank > 3 && b.isHot && (
                  <span className="ocean-hot-badge" title="7日呼声超高！">
                    <Flame size={12} fill="#ef4444" color="#ef4444" />
                  </span>
                )}

                {/* 画师模式悬浮引导 */}
                {isArtistMode && (
                  <span className="ocean-artist-claim-pill" title="点击即可认领制作">
                    + 认领
                  </span>
                )}

                <span className="ocean-bubble-title">{b.name}</span>

                <div className="ocean-bubble-stat">
                  <Heart size={11} fill="currentColor" />
                  <span>{b.votes}</span>
                </div>

                {claimCount > 0 && (
                  <span
                    className="ocean-claimed-tag"
                    title={`已有 ${claimCount} 位画师认领制作`}
                  >
                    ✓ 制作中 ({claimCount}画师)
                  </span>
                )}
              </div>
            )
          })}
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
