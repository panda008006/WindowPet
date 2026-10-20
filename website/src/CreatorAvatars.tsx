/* eslint-disable react-refresh/only-export-components */
// 官方二次元画师与工坊专属头像与社交图标组件

// 1. 宇痕丶 头像 (完全对标截图：深蓝动漫发型、红色大眼、白色领口)
export function YuhenAvatar() {
  return (
    <svg viewBox="0 0 100 100" width="66" height="66" className="blogger-avatar-svg">
      <circle cx="50" cy="50" r="48" fill="#f8fafc" />
      <circle cx="50" cy="50" r="44" fill="#ede9fe" fillOpacity="0.4" />
      
      {/* 蓝黑深发底 */}
      <circle cx="50" cy="48" r="32" fill="#1e1b4b" />
      <path d="M 20 48 Q 14 34 26 24 Q 40 18 50 18 Q 60 18 74 24 Q 86 34 80 48 Z" fill="#1e1b4b" />
      <path d="M 16 52 Q 10 68 20 74" stroke="#1e1b4b" strokeWidth="6" fill="none" strokeLinecap="round" />
      <path d="M 84 52 Q 90 68 80 74" stroke="#1e1b4b" strokeWidth="6" fill="none" strokeLinecap="round" />

      {/* 脸部 */}
      <ellipse cx="50" cy="54" rx="27" ry="25" fill="#fff1f2" />

      {/* 动漫碎刘海 */}
      <path d="M 22 42 Q 32 58 36 46 Q 44 60 50 44 Q 56 60 64 46 Q 68 58 78 42 Z" fill="#1e1b4b" />

      {/* 标志性鲜红动漫大眼 */}
      <ellipse cx="38" cy="54" rx="5.5" ry="7" fill="#dc2626" />
      <ellipse cx="62" cy="54" rx="5.5" ry="7" fill="#dc2626" />
      <circle cx="36" cy="52" r="2.5" fill="#ffffff" />
      <circle cx="60" cy="52" r="2.5" fill="#ffffff" />
      <circle cx="40" cy="57" r="1.2" fill="#ffffff" />
      <circle cx="64" cy="57" r="1.2" fill="#ffffff" />

      {/* 脸颊微红 */}
      <ellipse cx="31" cy="61" rx="5" ry="2" fill="#f43f5e" fillOpacity="0.35" />
      <ellipse cx="69" cy="61" rx="5" ry="2" fill="#f43f5e" fillOpacity="0.35" />

      {/* 微笑 */}
      <path d="M 47 62 Q 50 65 53 62" stroke="#991b1b" strokeWidth="1.8" fill="none" strokeLinecap="round" />

      {/* 白衬衫领 */}
      <path d="M 32 78 Q 50 72 68 78 L 74 96 Q 50 100 26 96 Z" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1.5" />
      <path d="M 45 76 L 50 84 L 55 76 Z" fill="#e2e8f0" />
    </svg>
  )
}

// 2. Candya (糖炒栗子) 头像 (双丸子发髻、星饰、甜美笑脸)
export function CandyaAvatar() {
  return (
    <svg viewBox="0 0 100 100" width="66" height="66" className="blogger-avatar-svg">
      <circle cx="50" cy="50" r="48" fill="#fff5f7" />
      <circle cx="50" cy="50" r="44" fill="#fed7aa" fillOpacity="0.25" />
      
      <circle cx="20" cy="42" r="16" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="2" />
      <circle cx="80" cy="42" r="16" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="2" />
      <circle cx="20" cy="42" r="12" fill="#e2e8f0" />
      <circle cx="80" cy="42" r="12" fill="#e2e8f0" />
      <path d="M 12 42 Q 10 56 16 62" stroke="#fda4af" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M 88 42 Q 90 56 84 62" stroke="#fda4af" strokeWidth="3" fill="none" strokeLinecap="round" />

      <ellipse cx="50" cy="52" rx="28" ry="26" fill="#fff1f2" />

      <path d="M 24 44 Q 50 30 76 44 Q 68 54 50 50 Q 32 54 24 44 Z" fill="#94a3b8" />
      <path d="M 28 42 Q 35 48 38 42" stroke="#64748b" strokeWidth="1.5" fill="none" />
      <path d="M 62 42 Q 65 48 72 42" stroke="#64748b" strokeWidth="1.5" fill="none" />

      <path d="M 22 36 Q 50 24 78 36" stroke="#fda4af" strokeWidth="4" fill="none" strokeLinecap="round" />
      <path d="M 26 34 Q 50 22 74 34" stroke="#ffffff" strokeWidth="2" strokeDasharray="3,3" fill="none" />

      <polygon
        points="50,18 52,24 58,25 53,29 55,35 50,31 45,35 47,29 42,25 48,24"
        fill="#fbbf24"
        stroke="#f59e0b"
        strokeWidth="1"
      />

      <ellipse cx="38" cy="53" rx="5.5" ry="7" fill="#475569" />
      <ellipse cx="62" cy="53" rx="5.5" ry="7" fill="#475569" />
      <circle cx="36" cy="51" r="2.5" fill="#ffffff" />
      <circle cx="60" cy="51" r="2.5" fill="#ffffff" />
      <circle cx="40" cy="56" r="1.2" fill="#ffffff" />
      <circle cx="64" cy="56" r="1.2" fill="#ffffff" />

      <ellipse cx="32" cy="59" rx="5" ry="2.5" fill="#fb7185" fillOpacity="0.45" />
      <ellipse cx="68" cy="59" rx="5" ry="2.5" fill="#fb7185" fillOpacity="0.45" />

      <path d="M 47 59 Q 50 63 53 59" stroke="#e11d48" strokeWidth="1.8" fill="none" strokeLinecap="round" />

      <path d="M 32 78 Q 50 72 68 78 L 74 96 Q 50 100 26 96 Z" fill="#334155" />
      <path d="M 42 75 L 50 84 L 58 75 Z" fill="#ffffff" />
      <circle cx="50" cy="85" r="3" fill="#fb7185" />

      <rect x="74" y="66" width="12" height="15" rx="3" fill="#ffedd5" stroke="#ea580c" strokeWidth="1.2" />
      <rect x="78" y="60" width="3" height="7" fill="#f97316" />
      <circle cx="80" cy="74" r="1.5" fill="#78350f" />
      <circle cx="83" cy="76" r="1.5" fill="#78350f" />
    </svg>
  )
}

// 3. Nagano酱 头像 (粉色双马尾、星星发夹、画本)
export function NaganoAvatar() {
  return (
    <svg viewBox="0 0 100 100" width="66" height="66" className="blogger-avatar-svg">
      <circle cx="50" cy="50" r="48" fill="#fff0f5" />
      <circle cx="50" cy="50" r="44" fill="#fbcfe8" fillOpacity="0.35" />
      
      <circle cx="22" cy="46" r="15" fill="#f472b6" stroke="#db2777" strokeWidth="1.5" />
      <circle cx="78" cy="46" r="15" fill="#f472b6" stroke="#db2777" strokeWidth="1.5" />
      <path d="M 16 46 Q 14 62 22 70" stroke="#f472b6" strokeWidth="6" fill="none" strokeLinecap="round" />
      <path d="M 84 46 Q 86 62 78 70" stroke="#f472b6" strokeWidth="6" fill="none" strokeLinecap="round" />

      <ellipse cx="50" cy="52" rx="28" ry="26" fill="#fff1f2" />

      <path d="M 24 44 Q 50 28 76 44 Q 68 56 50 50 Q 32 56 24 44 Z" fill="#ec4899" />

      <polygon
        points="32,32 34,36 38,37 35,40 36,44 32,42 28,44 29,40 26,37 30,36"
        fill="#fde047"
        stroke="#eab308"
        strokeWidth="1"
      />

      <ellipse cx="38" cy="53" rx="5.5" ry="7" fill="#0284c7" />
      <ellipse cx="62" cy="53" rx="5.5" ry="7" fill="#0284c7" />
      <circle cx="36" cy="51" r="2.5" fill="#ffffff" />
      <circle cx="60" cy="51" r="2.5" fill="#ffffff" />
      <circle cx="40" cy="56" r="1.2" fill="#ffffff" />
      <circle cx="64" cy="56" r="1.2" fill="#ffffff" />

      <ellipse cx="31" cy="59" rx="5" ry="2.5" fill="#f43f5e" fillOpacity="0.4" />
      <ellipse cx="69" cy="59" rx="5" ry="2.5" fill="#f43f5e" fillOpacity="0.4" />

      <path d="M 47 59 Q 50 63 53 59" stroke="#e11d48" strokeWidth="1.8" fill="none" strokeLinecap="round" />

      <path d="M 32 78 Q 50 72 68 78 L 72 96 Q 50 100 28 96 Z" fill="#f472b6" />
      <rect x="42" y="76" width="16" height="20" rx="3" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1.5" />
      <path d="M 46 82 Q 50 79 54 82" stroke="#f43f5e" strokeWidth="1.5" fill="none" />
    </svg>
  )
}

// 4. 整活大队 头像 (潮酷像素墨镜、柴犬耳、连帽衫)
export function MemeLabAvatar() {
  return (
    <svg viewBox="0 0 100 100" width="66" height="66" className="blogger-avatar-svg">
      <circle cx="50" cy="50" r="48" fill="#fef3c7" />
      <circle cx="50" cy="50" r="44" fill="#fed7aa" fillOpacity="0.35" />

      <polygon points="26,38 20,18 40,28" fill="#f59e0b" stroke="#d97706" strokeWidth="1.5" />
      <polygon points="74,38 80,18 60,28" fill="#f59e0b" stroke="#d97706" strokeWidth="1.5" />
      <polygon points="27,34 23,23 36,29" fill="#fef3c7" />
      <polygon points="73,34 77,23 64,29" fill="#fef3c7" />

      <ellipse cx="50" cy="54" rx="29" ry="26" fill="#fef08a" />

      <rect x="25" y="44" width="23" height="13" fill="#0f172a" />
      <rect x="52" y="44" width="23" height="13" fill="#0f172a" />
      <rect x="48" y="48" width="4" height="4" fill="#0f172a" />
      <rect x="27" y="46" width="4" height="4" fill="#ffffff" />
      <rect x="54" y="46" width="4" height="4" fill="#ffffff" />

      <path d="M 44 64 Q 50 70 58 63" stroke="#b45309" strokeWidth="2.5" fill="none" strokeLinecap="round" />

      <path d="M 28 80 Q 50 72 72 80 L 78 98 Q 50 102 22 98 Z" fill="#0284c7" />
      <path d="M 45 78 L 50 86 L 55 78 Z" fill="#ffffff" />
    </svg>
  )
}

// 5. 阿秋与绘本屋 头像 (复古贝雷帽、童趣围裙、企鹅插画)
export function StorybookAvatar() {
  return (
    <svg viewBox="0 0 100 100" width="66" height="66" className="blogger-avatar-svg">
      <circle cx="50" cy="50" r="48" fill="#e0f2fe" />
      <circle cx="50" cy="50" r="44" fill="#bae6fd" fillOpacity="0.35" />

      {/* 棕色复古画家贝雷帽 */}
      <ellipse cx="50" cy="28" rx="34" ry="14" fill="#b45309" />
      <circle cx="50" cy="18" r="3" fill="#78350f" />

      <ellipse cx="50" cy="54" rx="27" ry="25" fill="#fff1f2" />

      {/* 棕发齐刘海 */}
      <path d="M 24 44 Q 50 32 76 44 Q 68 54 50 50 Q 32 54 24 44 Z" fill="#78350f" />

      {/* 温暖棕色大眼睛 */}
      <ellipse cx="38" cy="54" rx="5.5" ry="7" fill="#78350f" />
      <ellipse cx="62" cy="54" rx="5.5" ry="7" fill="#78350f" />
      <circle cx="36" cy="52" r="2.5" fill="#ffffff" />
      <circle cx="60" cy="52" r="2.5" fill="#ffffff" />

      {/* 腮红与微笑 */}
      <ellipse cx="31" cy="61" rx="5" ry="2.5" fill="#fb7185" fillOpacity="0.4" />
      <ellipse cx="69" cy="61" rx="5" ry="2.5" fill="#fb7185" fillOpacity="0.4" />
      <path d="M 47 62 Q 50 65 53 62" stroke="#b45309" strokeWidth="1.8" fill="none" strokeLinecap="round" />

      {/* 蓝色工装背带画袍 */}
      <path d="M 30 78 Q 50 72 70 78 L 74 98 Q 50 102 26 98 Z" fill="#0284c7" />
      <path d="M 42 76 L 50 85 L 58 76 Z" fill="#ffffff" />
    </svg>
  )
}

// 腾讯 QQ 官方矢量图标
export function QqIcon({ size = 13 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" fill="currentColor">
      <path d="M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 685.8 128 512 128S257.5 262.2 261.9 447.9c-28.4 70.8-46.7 113.9-62.7 165.3-34 109.5-23 154.8-14.6 155.8 18 2.2 70.1-82.4 70.1-82.4 0 49 25.2 112.9 79.9 159.6-38.1 48-77.8 77.2-77.8 77.2 4.9 4.9 31.9 7.8 70.8-12.7 54.8 28.3 118.8 44.3 184.4 44.3s129.6-16 184.4-44.3c38.9 20.5 65.9 17.6 70.8 12.7 0 0-39.7-29.2-77.8-77.2 54.7-46.7 79.9-110.6 79.9-159.6 0 0 52.1 84.6 70.1 82.4 8.5-1 19.5-46.3-14.4-155.8z" />
    </svg>
  )
}

// Bilibili 官方小电视图标
export function BilibiliIcon({ size = 13 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.813 4.653h.854c1.51 0 2.733 1.224 2.733 2.734v9.98c0 1.51-1.223 2.734-2.733 2.734H5.333c-1.51 0-2.733-1.224-2.733-2.734V7.387c0-1.51 1.223-2.734 2.733-2.734h.854L4.86 3.125a.8.8 0 0 1 1.13-1.13l2.4 2.4a.8.8 0 0 1 .235.56v.058h6.75v-.058a.8.8 0 0 1 .235-.56l2.4-2.4a.8.8 0 1 1 1.13 1.13l-1.327 1.528zM8.5 10.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm7 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z" />
    </svg>
  )
}

// 抖音 官方音符图标
export function DouyinIcon({ size = 13 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.589 6.686a4.793 4.793 0 0 1-3.77-4.245V2h-3.445v13.672a2.896 2.896 0 0 1-2.887 2.887 2.896 2.896 0 0 1-2.888-2.887 2.896 2.896 0 0 1 2.888-2.887c.394 0 .766.082 1.107.228V9.526a6.34 6.34 0 0 0-1.107-.098C5.975 9.428 3 12.403 3 15.885c0 3.482 2.975 6.457 6.489 6.457 3.514 0 6.489-2.975 6.489-6.457V8.528a8.21 8.21 0 0 0 4.611 1.403V6.686h-1z" />
    </svg>
  )
}

// 根据 authorId 渲染对应头像
export function renderCreatorAvatar(authorId: string) {
  switch (authorId) {
    case 'anime':
      return <YuhenAvatar />
    case 'nagano':
      return <NaganoAvatar />
    case 'memelab':
      return <MemeLabAvatar />
    case 'storybook':
      return <StorybookAvatar />
    case 'furry':
    case 'candya':
    default:
      return <CandyaAvatar />
  }
}
