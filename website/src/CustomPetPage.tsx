import { useState } from 'react'
import {
  Camera,
  Gift,
  HeartHandshake,
  Palette,
  Sparkles,
  ArrowRight,
  Copy,
  Check,
  MessageSquare,
  Volume2,
  Download,
  Heart,
  Award,
  HelpCircle,
} from 'lucide-react'
import './subpages.css'

interface CustomPetPageProps {
  onBackToHome?: () => void
  onOpenGallery?: () => void
}

const qqGroupUrl = 'https://qm.qq.com/q/aCrzrRQkqA'
const qqGroupNumber = '536254840'
const artistGroupNumber = '1074892989'

interface PetActionConfig {
  label: string
  anim: string
  tag: string
  desc: string
}

interface CustomPetCase {
  id: string
  name: string
  species: string
  tag: string
  badgeNum: string
  previewImg: string
  rotation: string
  note: string
  description: string
  author: string
  soundNote: string
  redeemCode: string
  defaultAction: string
  actions: Record<string, PetActionConfig>
}

// 6 款用户指定的专属定制角色 (糯米飞飞、小汪生、橘圆圆、芝士小短腿、柠萌笑笑、高西地)
const customPets: CustomPetCase[] = [
  {
    id: 'sugarglider',
    name: '糯米飞飞',
    species: '白化蜜袋鼯 · 小飞鼠',
    tag: '🐿️ 软萌异宠 · 飞扑滑翔',
    badgeNum: 'No.01',
    previewImg: `${import.meta.env.BASE_URL}pets/sugarglider-custom-transparent.png`,
    rotation: '-2.2deg',
    note: '大眼萌态与张臂滑翔飞扑 · 像小精灵一样轻巧停在屏幕边沿',
    description: '以真实白化蜜袋鼯为原型的桌面异宠伙伴。拥有水汪汪的大眼睛与标志性的飞膜，开机时在屏幕底栏嚼着小饼干探头探脑，鼠标抓取时会张开小爪爪在屏幕上快乐滑翔！',
    author: '异宠写生工坊 · 特邀示范',
    soundNote: '实录轻音 · 细微吧唧嘴声与欢快扇耳声',
    redeemCode: 'WPX-2026-SUGARGLIDER',
    defaultAction: 'idle',
    actions: {
      idle: {
        label: '捧饼伴读',
        anim: `${import.meta.env.BASE_URL}pets/sugarglider-transparent-idle.webp`,
        tag: '大眼嚼嚼',
        desc: '两只小手抱着小饼干吧唧嘴，大黑眼睛水汪汪注视屏幕，耳朵欢快抖动。',
      },
      click: {
        label: '张臂飞扑',
        anim: `${import.meta.env.BASE_URL}pets/sugarglider-transparent-click.webp`,
        tag: '飞膜滑翔',
        desc: '轻戳一下张开小爪飞膜向前滑翔飞扑，敏捷又呆萌。',
      },
      drag: {
        label: '悬空抱抱',
        anim: `${import.meta.env.BASE_URL}pets/sugarglider-transparent-drag.webp`,
        tag: '悬空蹬腿',
        desc: '鼠标拖拽悬空时张开飞膜蹬腿求抱抱，像一朵轻盈的小蒲公英。',
      },
    },
  },
  {
    id: 'xiaowang',
    name: '小汪生',
    species: '手作比熊 · 纯真小狗',
    tag: '🐶 手作写真 · 治愈汪汪',
    badgeNum: 'No.02',
    previewImg: `${import.meta.env.BASE_URL}pets/xiaowang-custom-transparent.png`,
    rotation: '2.0deg',
    note: '羊毛毡纯手工真实生活照切帧 · 每天开机对你灿烂咧嘴笑',
    description: 'WindowPet 官方手作定制旗舰示范作。作者精心手作羊毛毡比熊犬并由真实狗狗生活照切帧，完整收录 288 帧吐舌微笑、撒欢狂奔、悬空起飞全部生动反馈。',
    author: '手作工坊 · 官方唯一实拍示范',
    soundNote: '实录音源 · 奔跑喘气与欢快汪汪声',
    redeemCode: 'WPX-2026-XIAOWANG',
    defaultAction: 'idle',
    actions: {
      idle: {
        label: '伴读待机',
        anim: `${import.meta.env.BASE_URL}pets/xiaowang-idle.webp`,
        tag: '吐舌微笑',
        desc: '96 帧平稳呼吸循环，咧开小嘴灿烂大笑，双耳微动。放在工位屏幕边，一眼就治愈！',
      },
      click: {
        label: '撒欢狂奔',
        anim: `${import.meta.env.BASE_URL}pets/xiaowang-click.webp`,
        tag: '短腿撒欢',
        desc: '96 帧大步狂奔扑腾，短腿生风，身体侧身飞跃，真实还原狗狗听到零食开心的撒欢步态！',
      },
      drag: {
        label: '悬空起飞',
        anim: `${import.meta.env.BASE_URL}pets/xiaowang-drag.webp`,
        tag: '超人起飞',
        desc: '96 帧四爪离地腾空跃起，鼠标抓取拖拽时像小狗超人一样悬空飞扑蹬腿求抱抱。',
      },
    },
  },
  {
    id: 'goldencat',
    name: '橘圆圆',
    species: '金渐层大胖猫 · 圆脸大胖橘',
    tag: '🐱 动效小橘猫 · 金渐层肥橘',
    badgeNum: 'No.03',
    previewImg: `${import.meta.env.BASE_URL}pets/chubby-custom-transparent.png`,
    rotation: '-1.6deg',
    note: '圆头大脸盘子金渐层生活写生 · 趴在任务栏打盹踩奶晃尾巴',
    description: '圆滚滚的大包子脸英短金渐层大胖橘猫，性格慵懒粘人。平时端坐在桌面角部微闭眼睛打瞌睡，鼠标划过时会晃悠蓬松大粗尾巴，沉稳治愈。',
    author: '猫咪写生社 · 纯手绘动画组',
    soundNote: '实录猫音 · 低频治愈呼噜声与轻声喵呜',
    redeemCode: 'WPX-2026-CHUBBY',
    defaultAction: 'idle',
    actions: {
      idle: {
        label: '端坐伴读',
        anim: `${import.meta.env.BASE_URL}pets/chubby-transparent-idle.webp`,
        tag: '微动眨眼',
        desc: '英短金渐层大脸盘子端坐在桌角，毛茸茸胸脯随呼吸轻微律动，温柔眨眼。',
      },
      click: {
        label: '歪头呼噜',
        anim: `${import.meta.env.BASE_URL}pets/chubby-transparent-click.webp`,
        tag: '呼噜踩奶',
        desc: '被轻戳一下舒服地眯起眼睛，发出低频治愈呼噜声并轻蹭屏幕。',
      },
      drag: {
        label: '拎起大橘',
        anim: `${import.meta.env.BASE_URL}pets/chubby-transparent-drag.webp`,
        tag: '肉嘟嘟悬空',
        desc: '鼠标轻提起沉甸甸的肥橘，四只毛爪自然下垂，胖嘟嘟超有份量。',
      },
    },
  },
  {
    id: 'munchkincat',
    name: '芝士小短腿',
    species: '曼赤肯矮脚猫 · 橘白软糖',
    tag: '🐾 动效小橘猫 · 曼赤肯短腿',
    badgeNum: 'No.04',
    previewImg: `${import.meta.env.BASE_URL}pets/munchkin-custom-transparent.png`,
    rotation: '2.4deg',
    note: '曼赤肯短腿小猫生动切帧 · 走两步小短腿倒腾欢快，软萌治愈',
    description: '软糯可爱的矮脚橘白小猫，全套生动多帧动画。底栏小碎步走起路来像小马达一样倒腾，尾巴轻摇，带有两抹萌萌的小红晕，让人忍不住想上手捏一捏。',
    author: '萌宠动画社 · 短腿猫专精',
    soundNote: '实录幼猫音 · 软糯奶音喵喵叫',
    redeemCode: 'WPX-2026-MUNCHKIN',
    defaultAction: 'idle',
    actions: {
      idle: {
        label: '短腿站立',
        anim: `${import.meta.env.BASE_URL}pets/munchkin-transparent-idle.webp`,
        tag: '摇尾晃头',
        desc: '曼赤肯短腿橘白小猫乖巧站立，尾巴自然轻晃，神态好奇鲜活。',
      },
      click: {
        label: '开怀小跳',
        anim: `${import.meta.env.BASE_URL}pets/munchkin-transparent-click.webp`,
        tag: '欢喜雀跃',
        desc: '被鼠标点中时小短腿欢快蹬跳，眼睛笑成两条可爱的月牙缝。',
      },
      drag: {
        label: '提溜扑腾',
        anim: `${import.meta.env.BASE_URL}pets/munchkin-transparent-drag.webp`,
        tag: '短腿划水',
        desc: '悬空被提起来时两条小短前爪像划水一样轻快扑腾，可爱爆棚。',
      },
    },
  },
  {
    id: 'gecko',
    name: '柠萌笑笑',
    species: '微笑豹纹守宫 · 柠檬小蜥蜴',
    tag: '🦎 手工爬宠 · 永远在微笑的小可爱',
    badgeNum: 'No.05',
    previewImg: `${import.meta.env.BASE_URL}pets/gecko-custom-transparent.png`,
    rotation: '-1.8deg',
    note: '肥嘟嘟尾巴与标志性微笑唇 · 陪伴放空打字不打扰的安静桌面新宠',
    description: '专为异宠与爬宠爱好者打造的微笑守宫。拥有漂亮的柠檬黄豹纹斑点与肥嘟嘟的储能大尾巴。安静不吵闹，手持暖心标牌静静趴在屏幕底沿，是打字写代码时最治愈的无声守护者。',
    author: '守宫写生屋 · 异宠手作团队',
    soundNote: '零分贝静音伴读 · 绝对不干扰专注工作与学习',
    redeemCode: 'WPX-2026-GECKO',
    defaultAction: 'idle',
    actions: {
      idle: {
        label: '定点趴卧',
        anim: `${import.meta.env.BASE_URL}pets/gecko-transparent-idle.webp`,
        tag: '静音放空',
        desc: '静静趴在屏幕底沿发呆放空，手持 YOU CAN DO IT 标牌，眼睛好奇注视着光标。',
      },
      click: {
        label: '吐舌眨眼',
        anim: `${import.meta.env.BASE_URL}pets/gecko-transparent-click.webp`,
        tag: '微笑吐舌',
        desc: '轻点一下歪头吐出粉嫩小舌头，标志性微笑唇微微翘起，萌感爆棚。',
      },
      drag: {
        label: '悬空吸附',
        anim: `${import.meta.env.BASE_URL}pets/gecko-transparent-drag.webp`,
        tag: '吸盘腾空',
        desc: '小吸盘爪爪张开悬空提溜，憨态可掬在屏幕空中漫步，随时吸附停留。',
      },
    },
  },
  {
    id: 'westie',
    name: '高西地',
    species: '雪白立耳 · 西高地白梗犬',
    tag: '🐕 真实萌犬 · 高西地小狗',
    badgeNum: 'No.06',
    previewImg: `${import.meta.env.BASE_URL}pets/westie-custom-transparent.png`,
    rotation: '1.6deg',
    note: '黑纽扣小鼻子与雪白立耳 · 真实西高地白梗写生，欢快小碎步常驻桌角',
    description: '根据真实西高地白梗写生复刻的桌面伙伴。雪白的毛发、天然呆萌的圆黑鼻头与精神奕奕的小立耳。鼠标一动它就欢快摇尾巴，把家里的狗狗随时趴在工作台。',
    author: '真实萌犬写生工坊 · 特邀画师',
    soundNote: '实录犬声 · 快乐轻快小狗喘息与短尾摇摆',
    redeemCode: 'WPX-2026-WESTIE',
    defaultAction: 'idle',
    actions: {
      idle: {
        label: '趴趴发呆',
        anim: `${import.meta.env.BASE_URL}pets/westie-transparent-idle.webp`,
        tag: '守候桌角',
        desc: '趴在桌角静静守候，两只圆溜溜小黑眼睛机敏转动，忠诚温和。',
      },
      click: {
        label: '开心摇尾',
        anim: `${import.meta.env.BASE_URL}pets/westie-transparent-click.webp`,
        tag: '欢快摇尾',
        desc: '戳它一下耳朵立刻竖起，像看到小零食一样欢快摇尾巴，极具互动感。',
      },
      drag: {
        label: '提溜腾空',
        anim: `${import.meta.env.BASE_URL}pets/westie-transparent-drag.webp`,
        tag: '抱起腾空',
        desc: '抱起毛孩子换个位置，四爪自然悬空等待落地，憨厚乖巧。',
      },
    },
  },
]

// 特邀画师案例 (3位画师，每位画师展示 2 款角色，刚好对应 6 款定制角色)
const artistChains = [
  {
    id: 'chestnut',
    name: '@糖炒栗子',
    initial: '栗',
    role: '猫咪写生与高帧动效专精 · 视线追踪画师',
    cases: [
      {
        id: 'goldencat',
        title: '橘圆圆 · 金渐层大胖橘',
        img: `${import.meta.env.BASE_URL}pets/chubby-custom-transparent.png`,
        redeemCode: 'WPX-2026-CHUBBY',
      },
      {
        id: 'munchkincat',
        title: '芝士小短腿 · 曼赤肯矮脚',
        img: `${import.meta.env.BASE_URL}pets/munchkin-custom-transparent.png`,
        redeemCode: 'WPX-2026-MUNCHKIN',
      },
    ],
  },
  {
    id: 'mino',
    name: '@米诺画画中',
    initial: '米',
    role: '灵动神态专精 · Q萌家宠与异宠写生画师',
    cases: [
      {
        id: 'westie',
        title: '高西地 · 西高地白梗',
        img: `${import.meta.env.BASE_URL}pets/westie-custom-transparent.png`,
        redeemCode: 'WPX-2026-WESTIE',
      },
      {
        id: 'sugarglider',
        title: '糯米飞飞 · 白化蜜袋鼯',
        img: `${import.meta.env.BASE_URL}pets/sugarglider-custom-transparent.png`,
        redeemCode: 'WPX-2026-SUGARGLIDER',
      },
    ],
  },
  {
    id: 'shougong',
    name: '@手工坊主阿暖',
    initial: '暖',
    role: '纯手工手作生活照切帧与爬宠定制主理人',
    cases: [
      {
        id: 'xiaowang',
        title: '小汪生 · 手作羊毛毡比熊',
        img: `${import.meta.env.BASE_URL}pets/xiaowang-custom-transparent.png`,
        redeemCode: 'WPX-2026-XIAOWANG',
      },
      {
        id: 'gecko',
        title: '柠萌笑笑 · 微笑豹纹守宫',
        img: `${import.meta.env.BASE_URL}pets/gecko-custom-transparent.png`,
        redeemCode: 'WPX-2026-GECKO',
      },
    ],
  },
]

// 四步极简定制流程 (4 个大图标)
const steps = [
  { num: '01', icon: Camera, title: '发生活照', desc: '准备 1~3 张爱宠清晰生活照与花纹特征' },
  { num: '02', icon: Palette, title: '选专属动作', desc: '自由挑选待机、跑动、拖拽、特殊习性动作' },
  { num: '03', icon: HeartHandshake, title: '私聊画师', desc: '群内与画师 1 对 1 沟通需求，双方自行结算' },
  { num: '04', icon: Gift, title: '导入桌面', desc: '生成专属安装包与兑换码，双击即刻召唤相伴' },
]

// 定制常见问题
const faqs = [
  {
    q: '定制一只毛孩子大概需要多久？',
    a: '通常工期为 3~5 天。画师 1 对 1 逐帧切帧或手绘动画序列，完成后生成专属安装文件或离线兑换码直接交付。',
  },
  {
    q: '为什么做出来的动作这么生动灵动？',
    a: '我们基于 WindowPet 独家轻量透明动效引擎，支持待机呼吸微动、鼠标左键点击互动和悬空长按拖拽多套完整动作生态，100% 还原真实神韵。',
  },
  {
    q: '平台收费吗？双方如何付款？',
    a: 'WindowPet 官方平台与引擎永久免费开源零抽成！您在官方交流群内直接与画师 1 对 1 沟通细节与工期，双方自行私聊结算，透明省心。',
  },
  {
    q: '我是画手/独立设计师，想入驻接单或提交作品，如何加入？',
    a: `非常欢迎！请加入专属【Windowpet 画手群：${artistGroupNumber}】。群内提供官方切帧规范、动作模板包与入驻指引，可以直接对接约稿用户，优秀作品可直接登载入驻官网！`,
  },
]

export function CustomPetPage(_props: CustomPetPageProps) {
  const [copiedQq, setCopiedQq] = useState(false)
  const [copiedArtistQq, setCopiedArtistQq] = useState(false)
  const [showQrModal, setShowQrModal] = useState(false)
  const [copiedCode, setCopiedCode] = useState(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  // 当前选中的定制角色 (默认选中小汪生)
  const [activePetId, setActivePetId] = useState<string>('xiaowang')
  const [activeActionKey, setActiveActionKey] = useState<string>('idle')

  const activePet = customPets.find((p) => p.id === activePetId) || customPets[1]
  const currentAction = activePet.actions[activeActionKey] || activePet.actions[activePet.defaultAction]

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => {
      setToastMessage(null)
    }, 3000)
  }

  const handleCopyQq = () => {
    try {
      navigator.clipboard.writeText(qqGroupNumber)
      setCopiedQq(true)
      showToast(`官方定制直通群号 ${qqGroupNumber} 已复制到剪贴板！`)
      setTimeout(() => setCopiedQq(false), 2400)
    } catch {
      // ignore
    }
  }

  const handleCopyArtistQq = () => {
    try {
      navigator.clipboard.writeText(artistGroupNumber)
      setCopiedArtistQq(true)
      showToast(`画手群号 ${artistGroupNumber} 已复制到剪贴板！`)
      setTimeout(() => setCopiedArtistQq(false), 2400)
    } catch {
      showToast(`画手群号：${artistGroupNumber}`)
    }
  }

  const handleCopyCode = (code: string, petName: string) => {
    try {
      navigator.clipboard.writeText(code)
      setCopiedCode(true)
      showToast(`已复制【${petName}】离线兑换码：${code}，打开客户端点击“兑换角色”即可召唤！`)
      setTimeout(() => setCopiedCode(false), 2400)
    } catch {
      // ignore
    }
  }

  const handleDeepLink = (code: string, petName: string, petId?: string) => {
    const params = new URLSearchParams()
    if (petId) params.append('pet', petId)
    if (code) params.append('code', code)
    if (petName) params.append('name', petName)
    const deepLinkUrl = `windowpet://import?${params.toString()}`
    window.open(deepLinkUrl, '_self')
    showToast(`🚀 正在呼叫 WindowPet 桌面端自动装载【${petName}】...（若未弹出已为您复制备用码：${code}）`)
    try {
      navigator.clipboard.writeText(code)
    } catch {
      // ignore
    }
  }

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
        {/* =========================================================================
            顶部 Hero (纯粉色温馨风格) - 去除冗余的返回首页与逛逛展馆按钮，保留核心定制私聊
            ========================================================================= */}
        <header className="subpage-hero" style={{ paddingBottom: '24px' }}>
          <span className="eyebrow pink-eyebrow custom-eyebrow-with-avatar">
            <span className="custom-hero-avatar-badge" title="小汪生">
              <img
                src={`${import.meta.env.BASE_URL}pets/xiaowang-avatar.png`}
                alt="小汪"
                className="custom-hero-avatar-img"
              />
            </span>
            <span>CUSTOM PET STUDIO · 真实毛孩子专属定制</span>
          </span>
          <h1>把自家的毛孩子，做进电脑桌面</h1>
          <p className="subpage-lead" style={{ maxWidth: '660px', margin: '0 auto 24px auto' }}>
            不只是现成的动漫伙伴！发送 1~3 张自家族宠真实生活照，纯手作 1:1 精细切帧，全套生动多帧动效，让自家的毛孩子在工位屏幕边永远陪伴你~
          </p>

          <div className="subpage-hero-actions">
            <a
              className="primary-download pink-primary-btn"
              href={qqGroupUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ padding: '11px 26px', fontSize: '15px' }}
            >
              <HeartHandshake size={18} />
              <span>立即预约爱宠定制 / 进群私聊</span>
            </a>

            <button
              type="button"
              className="secondary-action pink-secondary-btn"
              onClick={handleCopyQq}
              style={{ padding: '11px 22px', fontSize: '14px' }}
            >
              {copiedQq ? <Check size={16} color="#ff6b81" /> : <Copy size={16} />}
              <span>{copiedQq ? `群号 ${qqGroupNumber} 已复制！` : `复制官方群号：${qqGroupNumber}`}</span>
            </button>
          </div>
        </header>

        {/* =========================================================================
            核心展示：6 个很大的写真明信片大框 + 实时动作交互舞台
            ========================================================================= */}
        <section className="xiaowang-showcase-section">
          <div className="subpage-section-header text-center" style={{ marginBottom: '24px' }}>
            <span className="subpage-section-badge pink-badge">
              <Heart size={14} fill="#ff6b81" color="#ff6b81" />
              <span>OFFICIAL SHOWCASE · 真实毛孩子定制代表作大赏</span>
            </span>
            <h2>精选定制代表作：6 款专属毛孩子写真明信片</h2>
            <p>
              铺满桌面的手作与家宠写真明信片！涵盖小飞鼠、手作小汪生、动效小橘猫、守宫蜥蜴与西高地萌犬，点击明信片切换下方动作舞台，一键免费导入桌面端畅玩！
            </p>
          </div>

          {/* 1. 6 个很大的写真明信片大框 (3 列 x 2 行) */}
          <div className="xiaowang-postcard-wall" aria-label="爱宠定制 6 款角色明信片大赏">
            {customPets.map((p) => {
              const isActive = activePetId === p.id
              return (
                <div
                  key={p.id}
                  className={`xiaowang-postcard-card ${isActive ? 'is-active-card' : ''}`}
                  style={{ transform: `rotate(${p.rotation})` }}
                  onClick={() => {
                    setActivePetId(p.id)
                    setActiveActionKey(p.defaultAction)
                    showToast(`✨ 已联动切换至【${p.name}】动态舞台！`)
                  }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      setActivePetId(p.id)
                      setActiveActionKey(p.defaultAction)
                    }
                  }}
                  title={`点击查看【${p.name}】动态动作演示`}
                >
                  {/* 顶部樱花粉和纸胶带装饰 */}
                  <div className="postcard-washi-tape" />

                  {/* 右上角复古粉色邮票 */}
                  <div className="postcard-stamp">
                    <span className="stamp-text">WindowPet</span>
                    <span className="stamp-num">{p.badgeNum}</span>
                  </div>

                  {/* 真实照片 / 动效精灵相框 */}
                  <div className="postcard-photo-frame">
                    <img
                      src={p.previewImg}
                      alt={p.name}
                      className="postcard-photo-img"
                      style={{ objectFit: 'contain', padding: '10px' }}
                    />
                    <span className="postcard-tag-pill">{p.tag}</span>
                  </div>

                  {/* 手写风标题与说明 */}
                  <div className="postcard-caption">
                    <div className="postcard-title-row">
                      <strong className="postcard-title">{p.name}</strong>
                      <span className="postcard-date">{p.species}</span>
                    </div>
                    <p className="postcard-note">{p.note}</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                      <span style={{ fontSize: '11px', color: '#ff6b81', fontWeight: 700 }}>
                        兑换码：{p.redeemCode}
                      </span>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                        {isActive ? '● 当前正在演示' : '点击切换舞台'}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* 2. 实时全动作动态演示交互舞台 (Live Actions Stage) */}
          <div className="xiaowang-interactive-stage-card">
            <div className="stage-left-avatar-zone">
              <div className="stage-avatar-glow-ring">
                <img
                  key={`${activePet.id}-${activeActionKey}`}
                  src={currentAction.anim}
                  alt={`${activePet.name} ${currentAction.label} 实时演示`}
                  className="stage-live-avatar-img"
                />
              </div>

              <div className="stage-audio-badge">
                <Volume2 size={14} color="#ff6b81" />
                <span>{activePet.soundNote}</span>
              </div>
            </div>

            <div className="stage-right-control-zone">
              <div className="stage-control-header">
                <div className="stage-pet-title-row">
                  <h3>{activePet.name} · {activePet.species}</h3>
                  <span className="stage-author-pill">
                    <Award size={13} color="#ff6b81" />
                    <span>{activePet.author}</span>
                  </span>
                </div>
                <p className="stage-pet-intro">
                  {activePet.description}
                </p>
              </div>

              {/* 动作切换标签组 */}
              <div className="stage-action-tabs" aria-label={`切换${activePet.name}动作`}>
                <span className="action-tabs-label">点击切换动作体验：</span>
                <div className="action-tab-button-group">
                  {Object.keys(activePet.actions).map((key) => {
                    const action = activePet.actions[key]
                    const isActive = activeActionKey === key
                    return (
                      <button
                        key={key}
                        type="button"
                        className={`stage-action-btn ${isActive ? 'is-active' : ''}`}
                        onClick={() => {
                          setActiveActionKey(key)
                          showToast(`已切换至【${activePet.name} · ${action.label}】动作演示！`)
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
                <span>
                  《{activePet.name}》支持在 WindowPet 桌面端永久免费导入使用，非完全开源角色，请勿商用哦~
                </span>
              </div>

              {/* 核心操作按钮 */}
              <div className="stage-action-cta-group">
                <button
                  type="button"
                  className="stage-import-pet-btn"
                  onClick={() => handleDeepLink(activePet.redeemCode, activePet.name, activePet.id)}
                  title={`免费将【${activePet.name}】一键导入桌面端`}
                >
                  <Download size={16} />
                  <span>免费将【{activePet.name}】导入桌面</span>
                </button>

                <button
                  type="button"
                  className="stage-import-pet-btn"
                  style={{ background: '#fff', color: '#ff4757', border: '1.5px solid #ffccd4' }}
                  onClick={() => handleCopyCode(activePet.redeemCode, activePet.name)}
                  title="复制离线兑换码"
                >
                  {copiedCode ? <Check size={16} color="#ff4757" /> : <Copy size={16} color="#ff4757" />}
                  <span>复制离线码 ({activePet.redeemCode})</span>
                </button>

                <button
                  type="button"
                  className="stage-custom-my-pet-btn"
                  onClick={() => {
                    handleCopyQq()
                    showToast(`已复制官方群号 ${qqGroupNumber}！进群可直接私聊画师定制自家的毛孩子~`)
                  }}
                  title="预约定制自家毛孩子，双方自行私聊付款"
                >
                  <HeartHandshake size={16} />
                  <span>我也想定制自家的毛孩子</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================================
            极简 4 步定制流程 (4 个醒目的大图标)
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
                    <IconComp size={24} color="#ff6b81" />
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
                        showToast(`已复制群号 ${qqGroupNumber}！进群可私聊【${artist.name}】沟通定制与付款~`)
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
                      onClick={() => handleDeepLink(c.redeemCode, c.title, c.id)}
                      role="button"
                      tabIndex={0}
                      title={`点击通过桌面端一键导入【${c.title}】`}
                    >
                      <div className="minimal-card-stage">
                        <img
                          src={c.img}
                          alt={c.title}
                          className="minimal-card-img"
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

        {/* =========================================================================
            画手 / 动作设计师入驻招募计划
            ========================================================================= */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header text-center" style={{ marginBottom: '24px' }}>
            <span className="subpage-section-badge pink-badge">
              <Sparkles size={14} />
              <span>JOIN AS CREATOR</span>
            </span>
            <h2>画手 & 动作设计师招募计划</h2>
            <p>零抽成入驻 WindowPet，把你的手绘灵感与毛孩子做进千万用户的电脑桌面！</p>
          </div>

          <div
            style={{
              background: 'linear-gradient(135deg, #ffffff 0%, #fffbfb 100%)',
              border: '1.5px solid #ffe3e7',
              borderRadius: '24px',
              padding: '36px 32px',
              boxShadow: '0 12px 36px rgba(255, 117, 140, 0.08)',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '36px',
              alignItems: 'center',
            }}
          >
            {/* 左侧说明与权益 */}
            <div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 14px',
                  background: '#fff0f3',
                  borderRadius: '20px',
                  color: '#ff4d6d',
                  fontSize: '13px',
                  fontWeight: 700,
                  marginBottom: '14px',
                }}
              >
                <Palette size={15} />
                <span>诚邀插画师 · 动效设计师 · 黏土手作娘 · 像素画师入驻</span>
              </div>
              <h3 style={{ fontSize: '24px', color: '#2b2d42', margin: '0 0 14px', fontWeight: 850 }}>
                你有精湛画工，我们提供舞台与零抽成客源
              </h3>
              <p style={{ fontSize: '14.5px', color: '#6c757d', lineHeight: 1.7, margin: '0 0 24px' }}>
                无论是为爱宠主人量身定制 1 对 1 动效角色，还是上架你原创的萌系 IP，加入 WindowPet 画手大家庭，创作价值直接变现。
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '28px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '8px',
                      background: '#ffe5ec',
                      color: '#ff4d6d',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      fontWeight: 800,
                      fontSize: '13px',
                    }}
                  >
                    01
                  </div>
                  <div>
                    <strong style={{ fontSize: '14.5px', color: '#2b2d42', display: 'block', marginBottom: '2px' }}>
                      平台永久 0% 零抽成
                    </strong>
                    <span style={{ fontSize: '13px', color: '#6c757d', lineHeight: 1.5 }}>
                      用户进群直接私聊你约稿沟通，稿酬双方自行微信/支付宝结算，平台不扣取任何中介差价。
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '8px',
                      background: '#e0f2fe',
                      color: '#0284c7',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      fontWeight: 800,
                      fontSize: '13px',
                    }}
                  >
                    02
                  </div>
                  <div>
                    <strong style={{ fontSize: '14.5px', color: '#2b2d42', display: 'block', marginBottom: '2px' }}>
                      官网与桌面端永久署名推荐
                    </strong>
                    <span style={{ fontSize: '13px', color: '#6c757d', lineHeight: 1.5 }}>
                      定制优秀案例直接登载官网爱宠定制专区、画师专栏与桌面端置顶推荐位，让更多人认识你的风格。
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '8px',
                      background: '#fef3c7',
                      color: '#d97706',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      fontWeight: 800,
                      fontSize: '13px',
                    }}
                  >
                    03
                  </div>
                  <div>
                    <strong style={{ fontSize: '14.5px', color: '#2b2d42', display: 'block', marginBottom: '2px' }}>
                      免费提供切帧规范与动作引擎模板
                    </strong>
                    <span style={{ fontSize: '13px', color: '#6c757d', lineHeight: 1.5 }}>
                      进群直接领取透明免抠切帧规范、标准动作模板包与一键打包调试工具，新手画手也能轻松上手。
                    </span>
                  </div>
                </div>
              </div>

              {/* 操作按钮区 */}
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px' }}>
                <button
                  type="button"
                  className="primary-download pink-primary-btn"
                  onClick={handleCopyArtistQq}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '11px 22px' }}
                >
                  {copiedArtistQq ? <Check size={16} /> : <Copy size={16} />}
                  <span>{copiedArtistQq ? '画手群号已复制！' : `复制画手群号：${artistGroupNumber}`}</span>
                </button>
                <button
                  type="button"
                  className="secondary-action"
                  onClick={() => setShowQrModal(true)}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '10px 18px', background: '#ffffff', border: '1px solid #dee2e6', borderRadius: '12px', color: '#495057', fontSize: '13.5px', fontWeight: 650, cursor: 'pointer' }}
                >
                  <span>查看群二维码</span>
                </button>
              </div>
            </div>

            {/* 右侧画手群二维码展示卡片 */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                background: '#ffffff',
                border: '1.5px solid #f1f3f5',
                borderRadius: '22px',
                padding: '24px 20px',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.05)',
                textAlign: 'center',
                maxWidth: '280px',
                margin: '0 auto',
              }}
            >
              <div
                style={{
                  borderRadius: '16px',
                  overflow: 'hidden',
                  border: '1px solid #f0f0f0',
                  cursor: 'pointer',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
                  transition: 'transform 0.2s ease',
                }}
                onClick={() => setShowQrModal(true)}
                title="点击放大查看"
              >
                <img
                  src={`${import.meta.env.BASE_URL}artist_group_qr.jpg`}
                  alt="Windowpet 画手群 二维码"
                  style={{ width: '100%', maxWidth: '220px', height: 'auto', display: 'block' }}
                />
              </div>
              <div style={{ marginTop: '16px' }}>
                <div style={{ fontSize: '16px', fontWeight: 800, color: '#2b2d42', marginBottom: '4px' }}>
                  Windowpet 画手群
                </div>
                <div style={{ fontSize: '14px', color: '#ff4d6d', fontWeight: 800, marginBottom: '6px' }}>
                  群号：{artistGroupNumber}
                </div>
                <p style={{ fontSize: '12px', color: '#868e96', margin: 0 }}>
                  打开手机 QQ 扫一扫加入，进群领取动作切帧规范与模板包
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================================
            常见问题 FAQ
            ========================================================================= */}
        <section style={{ marginBottom: '46px' }}>
          <div className="subpage-section-header text-center" style={{ marginBottom: '20px' }}>
            <span className="subpage-section-badge pink-badge">
              <HelpCircle size={14} />
              <span>FAQ</span>
            </span>
            <h2>爱宠定制常见问题</h2>
            <p>了解定制流程、工期安排、零抽成与交付保障细节。</p>
          </div>

          <div style={{ maxWidth: '820px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                style={{
                  background: '#ffffff',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  border: '1.5px solid rgba(255, 182, 193, 0.4)',
                  boxShadow: '0 4px 14px rgba(216, 75, 107, 0.06)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span
                    style={{
                      background: '#ff6b81',
                      color: '#fff',
                      width: '22px',
                      height: '22px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      fontWeight: 800,
                    }}
                  >
                    Q
                  </span>
                  <h4 style={{ margin: 0, fontSize: '15px', color: '#2d3436', fontWeight: 750 }}>{faq.q}</h4>
                </div>
                <p style={{ margin: '0 0 0 32px', fontSize: '13px', color: '#636e72', lineHeight: 1.6 }}>{faq.a}</p>
              </div>
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
          <span>© 2026 WindowPet · 治愈系桌面伴侣</span>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
            桂ICP备2026009615号-2
          </a>
        </footer>
      </div>

      {/* 画手群专属二维码放大弹窗 */}
      {showQrModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
            zIndex: 99999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
          onClick={() => setShowQrModal(false)}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '24px',
              padding: '24px 20px 20px',
              maxWidth: '340px',
              width: '100%',
              textAlign: 'center',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.25)',
              border: '1px solid #f1f3f5',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ borderRadius: '16px', overflow: 'hidden', border: '1px solid #f0f0f0', marginBottom: '16px' }}>
              <img
                src={`${import.meta.env.BASE_URL}artist_group_qr.jpg`}
                alt="Windowpet 画手群 二维码"
                style={{ width: '100%', display: 'block' }}
              />
            </div>
            <div style={{ fontSize: '16.5px', fontWeight: 800, color: '#2b2d42', marginBottom: '4px' }}>
              Windowpet 画手群
            </div>
            <div style={{ fontSize: '14px', color: '#ff4d6d', fontWeight: 800, marginBottom: '12px' }}>
              群号：{artistGroupNumber}
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                type="button"
                onClick={handleCopyArtistQq}
                style={{
                  padding: '9px 18px',
                  background: '#fff0f3',
                  color: '#ff4d6d',
                  border: '1px solid #ffd6de',
                  borderRadius: '16px',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                {copiedArtistQq ? <Check size={14} /> : <Copy size={14} />}
                <span>{copiedArtistQq ? '已复制！' : '复制群号'}</span>
              </button>
              <button
                type="button"
                onClick={() => setShowQrModal(false)}
                style={{
                  padding: '9px 20px',
                  background: '#f1f3f5',
                  color: '#495057',
                  border: 'none',
                  borderRadius: '16px',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
