export interface SeatedAuthorFigureProps {
  authorId: string
  authorName: string
  role?: string
  greeting?: string
  badgeColor?: string
  accentColor?: string
  className?: string
}

export function SeatedAuthorFigure({
  authorId,
  authorName,
  role,
  greeting,
  badgeColor = '#e85f6d',
  className = '',
}: SeatedAuthorFigureProps) {
  // 默认寄语配置
  const defaultGreetings: Record<string, string> = {
    nagano: '欢迎来到我的手作小屋！筐里全是我一笔一画勾出来的治愈小生灵，点击进去就能把玩所有动作哦~',
    storybook: '翻开复古绘本，童年回忆都在这里。坐在小板凳上，把这筐软萌朋友交给你啦！',
    memelab: '工位太枯燥？这筐高能梗宠专治打工内耗，看中哪个直接点开，魔性动效保证让你笑出声！',
    furry: '每一只毛孩子都有独特的呼吸与眼神。在这只收纳筐里，我为你封存了最真实的温度。',
    anime: '星辰原画绘梦完成！次元画板前的角色都装在展筐里了，挑选你的专属番剧搭档吧！',
    chestnut: '这里是我承接的家宠写生作品筐，真实毛发展开，点击即可查看每位毛孩子的专属档案~',
    mino: '捕捉毛孩子拆家与卖萌的绝版神态，全手绘帧动效，欢迎开箱检阅！',
  }

  const currentGreeting = greeting || defaultGreetings[authorId] || '欢迎光临我的作品展筐，全部伙伴免登录免费下载，点击即可查看全套动作！'

  return (
    <div className={`seated-author-stage ${className}`} data-author-id={authorId}>
      {/* 顶部/侧边生动寄语对话气泡 */}
      <div className="seated-author-bubble">
        <div className="bubble-author-title">
          <span className="bubble-author-dot" style={{ backgroundColor: badgeColor }} />
          <strong>{authorName}</strong>
          {role && <span className="bubble-author-role">{role}</span>}
        </div>
        <p className="bubble-author-quote">“{currentGreeting}”</p>
        <div className="bubble-pointer" />
      </div>

      {/* 坐姿画师核心矢量插画 (Seated Creator Figure) */}
      <div className="seated-figure-wrapper">
        {/* 坐垫/画师凳子 */}
        <div className="seated-stool-shadow" />

        {/* 1. Nagano酱 (软萌粉系双马尾坐姿，手抱画本，双腿垂晃) */}
        {authorId === 'nagano' && (
          <svg className="seated-svg-figure nagano-figure" viewBox="0 0 180 200" width="180" height="200" fill="none">
            {/* 凳子/坐垫 */}
            <ellipse cx="90" cy="155" rx="46" ry="14" fill="#ffd1d8" stroke="#f472b6" strokeWidth="2.5" />
            <rect x="58" y="155" width="8" height="35" rx="4" fill="#fbcfe8" />
            <rect x="114" y="155" width="8" height="35" rx="4" fill="#fbcfe8" />

            {/* 垂坐的小腿与小鞋子 (带 feet-swing 动画) */}
            <g className="seated-legs-group">
              {/* 左腿与鞋 */}
              <g className="leg-left">
                <path d="M72 135 L68 170" stroke="#fda4af" strokeWidth="10" strokeLinecap="round" />
                <ellipse cx="66" cy="174" rx="9" ry="6" fill="#fb7185" />
                <circle cx="68" cy="173" r="2.5" fill="#ffffff" />
              </g>
              {/* 右腿与鞋 */}
              <g className="leg-right">
                <path d="M108 135 L112 170" stroke="#fda4af" strokeWidth="10" strokeLinecap="round" />
                <ellipse cx="114" cy="174" rx="9" ry="6" fill="#fb7185" />
                <circle cx="112" cy="173" r="2.5" fill="#ffffff" />
              </g>
            </g>

            {/* 躯干 (粉色蓬蓬针织毛衣) */}
            <path
              d="M62 95 Q54 135 68 142 Q90 146 112 142 Q126 135 118 95 Z"
              fill="#ffe4e6"
              stroke="#fb7185"
              strokeWidth="2.5"
            />
            {/* 毛衣罗纹领口 */}
            <path d="M74 95 Q90 102 106 95" stroke="#fb7185" strokeWidth="3" fill="none" strokeLinecap="round" />

            {/* 双手抱着的迷你速写本 (上画有吉伊的小脸) */}
            <g className="sketchbook-group">
              <rect x="68" y="105" width="44" height="32" rx="4" fill="#ffffff" stroke="#e11d48" strokeWidth="2" transform="rotate(-3 90 120)" />
              {/* 速写本上的小吉伊涂鸦 */}
              <circle cx="85" cy="119" r="6" fill="#fff1f2" stroke="#fb7185" strokeWidth="1.2" />
              <circle cx="83" cy="118" r="1" fill="#881337" />
              <circle cx="87" cy="118" r="1" fill="#881337" />
              <path d="M84 121 Q85 122.5 86 121" stroke="#881337" strokeWidth="0.8" fill="none" />
              <path d="M96 114 L104 114 M96 118 L103 118 M96 122 L101 122" stroke="#fda4af" strokeWidth="1.5" strokeLinecap="round" />
              {/* 小手手握着画本 */}
              <circle cx="68" cy="120" r="5" fill="#ffe4e6" stroke="#fb7185" strokeWidth="1.5" />
              <circle cx="112" cy="118" r="5" fill="#ffe4e6" stroke="#fb7185" strokeWidth="1.5" />
            </g>

            {/* 头部与发型 */}
            <circle cx="90" cy="65" r="30" fill="#fff5f5" stroke="#fb7185" strokeWidth="2.5" />
            {/* 柔软棕栗色双马尾 */}
            <path d="M60 62 C45 75 42 105 52 115 C56 110 58 85 64 72 Z" fill="#9a3412" />
            <path d="M120 62 C135 75 138 105 128 115 C124 110 122 85 116 72 Z" fill="#9a3412" />
            {/* 刘海 */}
            <path d="M62 62 Q75 45 90 45 Q105 45 118 62 Q105 58 90 59 Q75 58 62 62 Z" fill="#9a3412" />
            {/* 可爱兔耳发箍 */}
            <path d="M72 45 Q66 18 76 22 Q82 28 80 44" fill="#fecdd3" stroke="#e11d48" strokeWidth="2" />
            <path d="M108 45 Q114 18 104 22 Q98 28 100 44" fill="#fecdd3" stroke="#e11d48" strokeWidth="2" />

            {/* 萌系面部 (圆圆水汪汪大眼睛、红晕、微笑) */}
            <ellipse cx="80" cy="68" rx="3.5" ry="5" fill="#4c0519" />
            <circle cx="81.5" cy="66" r="1.5" fill="#ffffff" />
            <ellipse cx="100" cy="68" rx="3.5" ry="5" fill="#4c0519" />
            <circle cx="101.5" cy="66" r="1.5" fill="#ffffff" />
            {/* 腮红 */}
            <ellipse cx="73" cy="74" rx="4.5" ry="2.5" fill="#fda4af" opacity="0.8" />
            <ellipse cx="107" cy="74" rx="4.5" ry="2.5" fill="#fda4af" opacity="0.8" />
            {/* 微笑 */}
            <path d="M87 73 Q90 77 93 73" stroke="#be123c" strokeWidth="1.8" fill="none" strokeLinecap="round" />
          </svg>
        )}

        {/* 2. 阿秋与绘本屋 (复古背带裤童年画家，坐着捧大绘本) */}
        {authorId === 'storybook' && (
          <svg className="seated-svg-figure storybook-figure" viewBox="0 0 180 200" width="180" height="200" fill="none">
            {/* 木墩坐凳 */}
            <ellipse cx="90" cy="155" rx="44" ry="13" fill="#fed7aa" stroke="#c2410c" strokeWidth="2.5" />
            <rect x="58" y="155" width="64" height="32" rx="3" fill="#ffedd5" stroke="#ea580c" strokeWidth="2" />
            <path d="M72 165 C85 167 95 163 110 166" stroke="#fb923c" strokeWidth="1.5" />

            {/* 垂坐腿部与复古小皮鞋 */}
            <g className="seated-legs-group">
              <g className="leg-left">
                <path d="M74 135 L70 170" stroke="#0284c7" strokeWidth="11" strokeLinecap="round" />
                <ellipse cx="67" cy="175" rx="9" ry="6" fill="#78350f" />
                <rect x="63" y="172" width="8" height="4" rx="2" fill="#d97706" />
              </g>
              <g className="leg-right">
                <path d="M106 135 L110 170" stroke="#0284c7" strokeWidth="11" strokeLinecap="round" />
                <ellipse cx="113" cy="175" rx="9" ry="6" fill="#78350f" />
                <rect x="109" y="172" width="8" height="4" rx="2" fill="#d97706" />
              </g>
            </g>

            {/* 背带裤与黄色内衬衬衫 */}
            <path d="M64 96 L116 96 L112 142 L68 142 Z" fill="#0284c7" stroke="#0369a1" strokeWidth="2.5" />
            <path d="M74 96 L74 135 M106 96 L106 135" stroke="#bae6fd" strokeWidth="3" />
            {/* 衬衫黄色袖口与领子 */}
            <circle cx="74" cy="115" r="2.5" fill="#fde047" />
            <circle cx="106" cy="115" r="2.5" fill="#fde047" />

            {/* 捧着的复古童话大绘本 (绘有企鹅妹小剪影) */}
            <g className="storybook-open-book">
              <path d="M62 110 Q90 116 90 135 Q62 130 62 110 Z" fill="#e0f2fe" stroke="#0284c7" strokeWidth="1.8" />
              <path d="M118 110 Q90 116 90 135 Q118 130 118 110 Z" fill="#e0f2fe" stroke="#0284c7" strokeWidth="1.8" />
              {/* 绘本封皮 */}
              <path d="M58 112 Q90 120 122 112" stroke="#d97706" strokeWidth="3" fill="none" strokeLinecap="round" />
              {/* 迷你企鹅涂鸦 */}
              <ellipse cx="78" cy="120" rx="4" ry="6" fill="#0f172a" />
              <ellipse cx="78" cy="121" rx="2.5" ry="4" fill="#ffffff" />
              <polygon points="76,120 80,120 78,122" fill="#ea580c" />
              {/* 手手托着绘本 */}
              <circle cx="62" cy="122" r="5" fill="#fed7aa" />
              <circle cx="118" cy="122" r="5" fill="#fed7aa" />
            </g>

            {/* 脑袋与深蓝画家贝雷帽 */}
            <circle cx="90" cy="66" r="28" fill="#fff7ed" stroke="#ea580c" strokeWidth="2.2" />
            {/* 贝雷帽 */}
            <ellipse cx="90" cy="46" rx="34" ry="16" fill="#0369a1" />
            <circle cx="90" cy="36" r="3.5" fill="#0284c7" />
            {/* 棕色蓬松卷发 */}
            <path d="M64 56 Q56 72 64 82 Q70 65 74 60" fill="#78350f" />
            <path d="M116 56 Q124 72 116 82 Q110 65 106 60" fill="#78350f" />

            {/* 暖暖的笑脸 */}
            <path d="M78 68 Q81 65 84 68" stroke="#78350f" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            <path d="M96 68 Q99 65 102 68" stroke="#78350f" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            <ellipse cx="74" cy="74" rx="4" ry="2" fill="#fb923c" opacity="0.7" />
            <ellipse cx="106" cy="74" rx="4" ry="2" fill="#fb923c" opacity="0.7" />
            <path d="M87 75 Q90 79 93 75" stroke="#c2410c" strokeWidth="2" fill="none" strokeLinecap="round" />
          </svg>
        )}

        {/* 3. 整活大队 (潮酷像素墨镜，盘腿坐在高能懒人沙发上，旁边转动 oiiai) */}
        {authorId === 'memelab' && (
          <svg className="seated-svg-figure memelab-figure" viewBox="0 0 180 200" width="180" height="200" fill="none">
            {/* 黄色高能懒人沙发 / 坐包 */}
            <ellipse cx="90" cy="150" rx="52" ry="22" fill="#fef08a" stroke="#ca8a04" strokeWidth="3" />
            <path d="M46 142 Q38 120 54 110 Q70 125 58 145" fill="#fde047" />
            <path d="M134 142 Q142 120 126 110 Q110 125 122 145" fill="#fde047" />

            {/* 盘腿坐姿 (Cross-legged) */}
            <path d="M56 148 Q90 162 124 148" stroke="#475569" strokeWidth="16" strokeLinecap="round" />
            <ellipse cx="54" cy="148" rx="8" ry="6" fill="#f59e0b" />
            <ellipse cx="126" cy="148" rx="8" ry="6" fill="#f59e0b" />

            {/* 黑色电竞潮牌卫衣 */}
            <path d="M60 95 L120 95 L114 140 L66 140 Z" fill="#1e293b" stroke="#0f172a" strokeWidth="2" />
            {/* 卫衣胸前迷因表情符号 */}
            <text x="90" y="122" textAnchor="middle" fill="#facc15" fontSize="13" fontWeight="bold">
              ⚡MEME
            </text>

            {/* 手里端着机械键盘 / 游戏手柄 */}
            <g className="gamepad-group">
              <rect x="70" y="126" width="40" height="18" rx="5" fill="#334155" stroke="#f59e0b" strokeWidth="2" />
              <circle cx="78" cy="135" r="3" fill="#22c55e" />
              <circle cx="86" cy="135" r="3" fill="#ef4444" />
              <circle cx="98" cy="135" r="2.5" fill="#38bdf8" />
              <circle cx="104" cy="135" r="2.5" fill="#facc15" />
            </g>

            {/* 旁边悬浮的小 oiiai 旋转猫 */}
            <g className="floating-mini-meme">
              <circle cx="145" cy="85" r="14" fill="#fbbf24" stroke="#d97706" strokeWidth="1.8" />
              <polygon points="135,76 140,68 143,76" fill="#d97706" />
              <polygon points="147,76 150,68 155,76" fill="#d97706" />
              <circle cx="140" cy="84" r="1.5" fill="#000" />
              <circle cx="150" cy="84" r="1.5" fill="#000" />
              <ellipse cx="145" cy="89" rx="3" ry="1.5" fill="#ef4444" />
              <text x="145" y="110" textAnchor="middle" fill="#ea580c" fontSize="9" fontWeight="bold">
                OIIAI~
              </text>
            </g>

            {/* 脑袋与鸭舌帽 */}
            <circle cx="90" cy="65" r="28" fill="#fef08a" stroke="#ca8a04" strokeWidth="2" />
            {/* 反戴黑色潮流鸭舌帽 */}
            <path d="M64 54 C64 38 116 38 116 54 Z" fill="#0f172a" />
            <rect x="52" y="52" width="22" height="7" rx="3" fill="#334155" transform="rotate(-15 63 55)" />

            {/* 潮酷像素风大墨镜 (Thug Life Glasses) */}
            <g className="pixel-shades">
              <rect x="68" y="62" width="18" height="12" fill="#09090b" stroke="#ffffff" strokeWidth="1" />
              <rect x="94" y="62" width="18" height="12" fill="#09090b" stroke="#ffffff" strokeWidth="1" />
              <rect x="86" y="66" width="8" height="4" fill="#09090b" />
              <rect x="70" y="64" width="3" height="3" fill="#ffffff" />
              <rect x="96" y="64" width="3" height="3" fill="#ffffff" />
            </g>
            {/* 歪嘴得意的坏笑 */}
            <path d="M84 82 Q93 86 98 80" stroke="#ca8a04" strokeWidth="2.5" fill="none" strokeLinecap="round" />
          </svg>
        )}

        {/* 4. 糖炒栗子 (毛茸茸自然庄园主理人，扎丸子头，盘腿坐在草绿毛毯上，抱着小猫画素描) */}
        {authorId === 'furry' && (
          <svg className="seated-svg-figure furry-figure" viewBox="0 0 180 200" width="180" height="200" fill="none">
            {/* 柔软墨绿地毯与毛绒蒲团 */}
            <ellipse cx="90" cy="154" rx="54" ry="18" fill="#bbf7d0" stroke="#16a34a" strokeWidth="2.5" />
            <ellipse cx="90" cy="150" rx="44" ry="12" fill="#dcfce7" />

            {/* 盘坐姿态 */}
            <path d="M58 142 Q90 156 122 142" stroke="#15803d" strokeWidth="14" strokeLinecap="round" />
            <ellipse cx="56" cy="144" rx="7" ry="5" fill="#f59e0b" />
            <ellipse cx="124" cy="144" rx="7" ry="5" fill="#f59e0b" />

            {/* 亚麻棉麻工坊围裙 */}
            <path d="M64 96 L116 96 L112 138 L68 138 Z" fill="#86efac" stroke="#16a34a" strokeWidth="2" />
            {/* 围裙兜兜，里面插着彩色铅笔 */}
            <rect x="74" y="116" width="32" height="18" rx="3" fill="#dcfce7" stroke="#15803d" strokeWidth="1.5" />
            <line x1="78" y1="112" x2="78" y2="120" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" />
            <line x1="84" y1="110" x2="84" y2="120" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" />
            <line x1="90" y1="113" x2="90" y2="120" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" />

            {/* 膝头依偎着的软乎白色小猫咪 (布偶雪球的原型) */}
            <g className="lap-kitten">
              <ellipse cx="90" cy="134" rx="14" ry="9" fill="#ffffff" stroke="#94a3b8" strokeWidth="1.5" />
              <polygon points="82,126 86,120 89,126" fill="#cbd5e1" />
              <polygon points="91,126 94,120 98,126" fill="#cbd5e1" />
              <circle cx="86" cy="132" r="1.5" fill="#0284c7" />
              <circle cx="94" cy="132" r="1.5" fill="#0284c7" />
              <path d="M89 135 L91 135" stroke="#f43f5e" strokeWidth="1.2" strokeLinecap="round" />
            </g>

            {/* 手里拿着的木质速写画板 */}
            <g className="sketch-easel-mini">
              <rect x="110" y="98" width="22" height="30" rx="3" fill="#fed7aa" stroke="#c2410c" strokeWidth="1.5" transform="rotate(12 121 113)" />
              <line x1="114" y1="106" x2="126" y2="106" stroke="#9a3412" strokeWidth="1.2" />
              <circle cx="110" cy="120" r="4.5" fill="#ffe4e6" />
            </g>

            {/* 脑袋、温暖栗色丸子头 */}
            <circle cx="90" cy="65" r="28" fill="#fef3c7" stroke="#d97706" strokeWidth="2" />
            {/* 顶部的可爱大丸子头 */}
            <circle cx="90" cy="34" r="14" fill="#78350f" />
            <circle cx="90" cy="34" r="16" fill="none" stroke="#f59e0b" strokeWidth="2" strokeDasharray="3 3" />
            {/* 栗色刘海与碎发 */}
            <path d="M64 62 Q75 48 90 48 Q105 48 116 62 Q105 56 90 56 Q75 56 64 62 Z" fill="#78350f" />

            {/* 治愈温和的杏仁笑眼 */}
            <path d="M76 68 Q81 63 86 68" stroke="#78350f" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            <path d="M94 68 Q99 63 104 68" stroke="#78350f" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            <ellipse cx="73" cy="74" rx="4" ry="2" fill="#f87171" opacity="0.6" />
            <ellipse cx="107" cy="74" rx="4" ry="2" fill="#f87171" opacity="0.6" />
            <path d="M87 75 Q90 79 93 75" stroke="#b45309" strokeWidth="2" fill="none" strokeLinecap="round" />
          </svg>
        )}

        {/* 5. 星野光年 (次元原画师，身披星辰披肩，手握发光电磁笔与数位屏) */}
        {authorId === 'anime' && (
          <svg className="seated-svg-figure anime-figure" viewBox="0 0 180 200" width="180" height="200" fill="none">
            {/* 科技感发光转椅 */}
            <ellipse cx="90" cy="156" rx="46" ry="14" fill="#ddd6fe" stroke="#7c3aed" strokeWidth="2.5" />
            <path d="M66 156 L58 185 M114 156 L122 185" stroke="#a78bfa" strokeWidth="4" strokeLinecap="round" />

            {/* 垂坐腿部与酷黑长筒靴 */}
            <g className="seated-legs-group">
              <g className="leg-left">
                <path d="M72 135 L68 172" stroke="#6d28d9" strokeWidth="11" strokeLinecap="round" />
                <ellipse cx="66" cy="176" rx="9" ry="6" fill="#1e1b4b" />
                <circle cx="68" cy="174" r="2" fill="#c084fc" />
              </g>
              <g className="leg-right">
                <path d="M108 135 L112 172" stroke="#6d28d9" strokeWidth="11" strokeLinecap="round" />
                <ellipse cx="114" cy="176" rx="9" ry="6" fill="#1e1b4b" />
                <circle cx="112" cy="174" r="2" fill="#c084fc" />
              </g>
            </g>

            {/* 星空紫黑斗篷风衣 */}
            <path d="M58 95 Q48 135 66 142 Q90 146 114 142 Q132 135 122 95 Z" fill="#4c1d95" stroke="#7c3aed" strokeWidth="2.5" />
            {/* 斗篷内衬星空金边 */}
            <path d="M72 95 L90 135 L108 95" stroke="#fbbf24" strokeWidth="2" fill="none" />

            {/* 发光数位屏与数位笔 */}
            <g className="tablet-group">
              <rect x="68" y="112" width="44" height="28" rx="4" fill="#0f172a" stroke="#8b5cf6" strokeWidth="2" />
              {/* 屏幕上的发光光标与波形 */}
              <path d="M74 126 L82 120 L88 130 L102 118" stroke="#38bdf8" strokeWidth="2" fill="none" />
              <circle cx="102" cy="118" r="3" fill="#ec4899" />
              {/* 右手持发光电磁笔 */}
              <line x1="108" y1="110" x2="100" y2="120" stroke="#f472b6" strokeWidth="3" strokeLinecap="round" />
              <circle cx="110" cy="110" r="4.5" fill="#fbcfe8" />
            </g>

            {/* 脑袋与银紫渐变次元发型 */}
            <circle cx="90" cy="65" r="28" fill="#fdf4ff" stroke="#a21caf" strokeWidth="2" />
            {/* 银紫色飘逸长发 */}
            <path d="M58 60 C48 78 46 108 58 120 C64 100 66 80 72 68 Z" fill="#a855f7" />
            <path d="M122 60 C132 78 134 108 122 120 C116 100 114 80 108 68 Z" fill="#a855f7" />
            {/* 呆毛与星形发夹 */}
            <path d="M90 42 Q96 22 108 28" stroke="#c084fc" strokeWidth="3" fill="none" strokeLinecap="round" />
            <polygon points="76,46 78,52 84,52 79,56 81,62 76,58 71,62 73,56 68,52 74,52" fill="#fbbf24" />

            {/* 闪烁的星空眼眸 */}
            <ellipse cx="79" cy="68" rx="4" ry="5.5" fill="#581c87" />
            <polygon points="79,66 80,68 82,68 80,70 81,72 79,71 77,72 78,70 76,68 78,68" fill="#ffffff" />
            <ellipse cx="101" cy="68" rx="4" ry="5.5" fill="#581c87" />
            <polygon points="101,66 102,68 104,68 102,70 103,72 101,71 99,72 100,70 98,68 100,68" fill="#ffffff" />
            <ellipse cx="72" cy="74" rx="4" ry="2" fill="#f472b6" opacity="0.6" />
            <ellipse cx="108" cy="74" rx="4" ry="2" fill="#f472b6" opacity="0.6" />
            <path d="M87 75 Q90 78 93 75" stroke="#701a75" strokeWidth="2" fill="none" strokeLinecap="round" />
          </svg>
        )}

        {/* 默认通配 / 特邀定制画师形象 (通用优雅坐姿插画师) */}
        {!['nagano', 'storybook', 'memelab', 'furry', 'anime'].includes(authorId) && (
          <svg className="seated-svg-figure default-figure" viewBox="0 0 180 200" width="180" height="200" fill="none">
            <ellipse cx="90" cy="155" rx="46" ry="14" fill="#ffd1d8" stroke="#f472b6" strokeWidth="2" />
            <g className="seated-legs-group">
              <path d="M72 135 L68 170" stroke="#fda4af" strokeWidth="10" strokeLinecap="round" />
              <ellipse cx="66" cy="174" rx="9" ry="6" fill="#fb7185" />
              <path d="M108 135 L112 170" stroke="#fda4af" strokeWidth="10" strokeLinecap="round" />
              <ellipse cx="114" cy="174" rx="9" ry="6" fill="#fb7185" />
            </g>
            <path d="M64 96 Q56 135 68 142 Q90 146 112 142 Q124 135 116 96 Z" fill="#ffe4e6" stroke="#fb7185" strokeWidth="2" />
            <rect x="70" y="108" width="40" height="28" rx="4" fill="#ffffff" stroke="#f43f5e" strokeWidth="1.5" />
            <circle cx="90" cy="65" r="28" fill="#fff5f5" stroke="#fb7185" strokeWidth="2" />
            <circle cx="90" cy="36" r="12" fill="#9a3412" />
            <path d="M66 60 Q90 48 114 60" fill="#9a3412" />
            <ellipse cx="80" cy="68" rx="3.5" ry="5" fill="#4c0519" />
            <circle cx="81.5" cy="66" r="1.5" fill="#ffffff" />
            <ellipse cx="100" cy="68" rx="3.5" ry="5" fill="#4c0519" />
            <circle cx="101.5" cy="66" r="1.5" fill="#ffffff" />
            <path d="M87 74 Q90 78 93 74" stroke="#be123c" strokeWidth="1.8" fill="none" strokeLinecap="round" />
          </svg>
        )}
      </div>
    </div>
  )
}
