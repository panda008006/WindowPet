import { useState } from 'react'
import {
  Check,
  Copy,
  Cpu,
  Download,
  Home,
  MessageCircle,
  Palette,
  ShieldCheck,
  Sparkles,
  Wrench,
} from 'lucide-react'
import './subpages.css'

interface FaqPageProps {
  onBackToHome?: () => void
  onOpenCustom?: () => void
  onOpenGallery?: () => void
}

const qqGroupUrl = 'https://qm.qq.com/q/cYlRBbvuda'
const githubRepoUrl = 'https://github.com/panda008006/WindowPet'
const releaseInstallerHref = 'https://github.com/panda008006/WindowPet/releases/download/v1.0.32/WindowPet_Setup_v1.0.32.exe'

export function FaqPage({ onBackToHome, onOpenCustom, onOpenGallery }: FaqPageProps) {
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

  const faqGroups = [
    {
      id: 'security',
      title: '安装、安全与系统兼容',
      icon: ShieldCheck,
      iconColor: '#126ad6',
      items: [
        {
          q: '为什么初次运行 Windows SmartScreen 会弹出“未知发布者”的安全提示？',
          a: '这是微软 Windows 系统对所有新发布程序的标准常规提示。商业机构的 EV 企业数字代码签名证书每年需花费数千至上万元。WindowPet 是一款由个人发起的 100% 纯净开源软件，代码全量在 GitHub 开源接受全球开发者审计，绝无任何恶意后门或窃取行为。首次运行时，只需点击窗口上的【更多信息】➔【仍要运行】即可正常开启，完全绿色安全。',
          highlight: '💡 开源保障：可以在 GitHub 上查看每一行公开源码与 Release 二进制 SHA-256 校验和。',
        },
        {
          q: '会被 360、火绒或腾讯电脑管家等安全软件拦截或误报吗？',
          a: 'WindowPet 采用绿色免写入系统注册表机制，不劫持任何系统核心文件。大部分杀毒软件均能正常放行。若极少数杀毒软件偶发拦截，是由于未签名的可执行文件触发了启发式防御规则，直接选择【信任并允许运行】即可。',
        },
        {
          q: '软件运行需要联网吗？会偷偷上传我的隐私数据或键盘记录吗？',
          a: '绝不！WindowPet 是一款 100% 本地运行的桌面程序。软件核心功能（角色渲染、待办便签、番茄闹钟）全程完全离线工作，没有任何后台上传键盘输入、剪贴板记录或麦克风监听的代码逻辑，请放心使用。',
        },
        {
          q: '支持哪些操作系统？有支持苹果 macOS 或 Linux 的计划吗？',
          a: '目前版本已针对 64 位 Windows 10 与 Windows 11 进行了深度原生适配（支持全屏无边框置顶与高分屏 DPI 自适应）。苹果 macOS 与 Linux 原生移植版已进入开源社区规划阶段，有进展会在官方 QQ 群与 GitHub 第一时间同步。',
        },
      ],
    },
    {
      id: 'performance',
      title: '电脑性能与游戏防干扰',
      icon: Cpu,
      iconColor: '#059669',
      items: [
        {
          q: '长期常驻在桌面边上，会占用大量电脑内存或导致卡顿吗？',
          a: '完全不会！WindowPet 经过了极致的轻量化性能调优。在日常空闲挂机状态下，内存占用仅约 30MB~50MB，CPU 占用率低于 0.3%，甚至远低于开启一个空白浏览器标签页的资源开销。即使在 8GB 内存的老旧办公电脑上也能丝滑常驻。',
        },
        {
          q: '玩《黑神话》《英雄联盟》《原神》《CS2》等大型游戏时会冲突或掉帧吗？',
          a: '零冲突、零掉帧！WindowPet 拥有智能全屏避让机制。当您进入独占全屏游戏模式时，桌宠会自动暂停非必要动画并降低刷新率，不遮挡游戏视窗准星，不抢占鼠标焦点，保障您的竞技游戏毫无干扰。',
        },
        {
          q: '笔记本电脑用电池供电时挂着，会严重加速耗电吗？',
          a: '由于采用 GPU 硬件加速轻量渲染与事件驱动休眠机制，当鼠标没有移至桌宠上方且无闹钟触发时，渲染管线几乎处于静默休眠状态，对笔记本续航的影响微乎其微。',
        },
      ],
    },
    {
      id: 'characters',
      title: '角色图鉴、版权与爱宠定制',
      icon: Palette,
      iconColor: '#7c3aed',
      items: [
        {
          q: '获取小鼻嘎展馆里的角色需要登录账号吗？如何购买与导入？',
          a: '无需注册或登录任何账号！WindowPet 采用极简免登录付费与即时导入机制：官方创研看板角色完全免费；特邀独立画师与工坊创研角色可直接扫码支付（￥3.9~￥9.9），付款后系统自动永久授权并呼叫客户端一键导入桌面端，即买即玩。',
        },
        {
          q: '展馆里的角色是由哪些作者制作的？如何找到心仪作者的作品？',
          a: '展馆由 WindowPet 创研所、独立家宠插画师（米诺画画中）、动漫概念画师（星野光年漫研所）、自然生灵画师（自然漫步客）以及特邀定制工坊等多位知名作者联合呈现。点击任意角色卡片或详情中的【查看作者主页】，即可进入该作者的个人独立展馆，浏览其创作的全部专属角色，并支持 1 对 1 定制约稿沟通！',
        },
        {
          q: '如何把自家的真实毛孩子（猫咪/狗狗）定制成桌面专属宠物？',
          a: '点击顶部导航栏【爱宠定制】，只需提供 1~3 张爱宠真实生活照，平台特邀独立插画师会 1 对 1 量身手绘并设计专属互动动作。加入官方交流群（422616922）即可快速预约画师。',
        },
      ],
    },
    {
      id: 'troubleshooting',
      title: '日常操作技巧与疑难排查',
      icon: Wrench,
      iconColor: '#d97706',
      items: [
        {
          q: '宠物不小心被我拖拽到屏幕边缘外看不到了，怎么找回？',
          a: '不用慌张！在 Windows 屏幕右下角的系统托盘区域，找到 WindowPet 的小爪子托盘图标 ➔ 点击鼠标右键 ➔ 选择【重置宠物位置至屏幕正中央】，小宠物就会立刻回到视野中心。',
        },
        {
          q: '怎么让桌宠随 Windows 开机自动启动？',
          a: '在小宠物身上点击鼠标右键 ➔ 打开【控制台设置】 ➔ 勾选【随 Windows 开机自动启动】即可生效。',
        },
        {
          q: '更换新电脑或重装系统后，原来的角色包和便签记录怎么迁移？',
          a: 'WindowPet 采用绿色便携架构。所有角色数据与便签均保存在软件安装根目录下的 `pets/` 与 `data/` 文件夹中。只需将整个 WindowPet 文件夹拷贝至新电脑即可无缝继承所有角色与历史配置！',
        },
      ],
    },
  ]

  return (
    <div className="page-view-pane">
      <div className="subpage-container">
        {/* 顶部 Hero */}
        <header className="subpage-hero">
          <span className="eyebrow">HELP CENTER & FAQ · 常见问题解答</span>
          <h1>解答你关心的一切使用与安全疑问</h1>
          <p className="subpage-lead">
            开源代码透明可查、超低内存消耗承诺、杀毒误报技术释疑、多屏多系统无缝适配。
            打消顾虑，安心让桌面小萌宠陪伴你的每一天。
          </p>

          <div className="subpage-hero-actions">
            <a
              className="primary-download"
              href={releaseInstallerHref}
              download="WindowPet_Setup_v1.0.32.exe"
              style={{ padding: '12px 28px', fontSize: '15px' }}
            >
              <Download size={18} />
              <span>免费下载正式版 (50MB)</span>
            </a>

            <button
              type="button"
              className="secondary-action"
              onClick={handleCopyQq}
              style={{ padding: '12px 22px', fontSize: '14px' }}
            >
              {copiedQq ? <Check size={16} color="#059669" /> : <Copy size={16} />}
              <span>{copiedQq ? '群号 422616922 已复制！' : '官方 QQ 交流群：422616922'}</span>
            </button>

            {onOpenCustom && (
              <button
                type="button"
                className="secondary-action"
                onClick={onOpenCustom}
                style={{ padding: '12px 22px', fontSize: '14px' }}
              >
                <Sparkles size={16} />
                <span>了解爱宠定制服务</span>
              </button>
            )}

            {onOpenGallery && (
              <button
                type="button"
                className="secondary-action"
                onClick={onOpenGallery}
                style={{ padding: '12px 22px', fontSize: '14px' }}
              >
                <Sparkles size={16} />
                <span>浏览小鼻嘎展馆</span>
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

        {/* 四大分类 FAQ 列表 */}
        <div className="faq-categories-grid">
          {faqGroups.map((group) => {
            const GroupIcon = group.icon
            return (
              <section key={group.id}>
                <div className="faq-group-title">
                  <GroupIcon size={24} color={group.iconColor} />
                  <span>{group.title}</span>
                </div>

                <div className="faq-list">
                  {group.items.map((item, idx) => (
                    <article className="subpage-card faq-item" key={idx}>
                      <div className="faq-question">
                        <div className="faq-q-badge">Q</div>
                        <h3>{item.q}</h3>
                      </div>
                      <div className="faq-answer">
                        <p>{item.a}</p>
                        {item.highlight && (
                          <div className="faq-highlight-box">
                            {item.highlight}
                          </div>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )
          })}
        </div>

        {/* 底部求助与反馈卡片 */}
        <div className="subpage-cta-box">
          <div>
            <h3>还有其他使用疑问，或发现了程序 Bug？</h3>
            <p>欢迎加入官方交流群直接与开发者对话，或在 GitHub 提交 Issue 建议，我们每天都在关注。</p>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <a
              className="primary-download"
              href={qqGroupUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', textDecoration: 'none' }}
            >
              <MessageCircle size={18} />
              <span>加入官方 QQ 交流群</span>
            </a>
            <a
              className="secondary-action"
              href={githubRepoUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', textDecoration: 'none' }}
            >
              <span>GitHub 反馈 Issues</span>
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
