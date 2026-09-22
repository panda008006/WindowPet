import {
  AlarmClock,
  CalendarCheck,
  Download,
  EyeOff,
  Feather,
  FolderSync,
  HelpCircle,
  Home,
  Keyboard,
  Layers,
  Monitor,
  MousePointerClick,
  Sparkles,
  Volume2,
} from 'lucide-react'
import './subpages.css'

interface TutorialPageProps {
  onBackToHome?: () => void
  onOpenGallery?: () => void
  onOpenFaq?: () => void
}

const releaseInstallerHref = 'https://github.com/panda008006/WindowPet/releases/download/v1.0.32/WindowPet_Setup_v1.0.32.exe'

export function TutorialPage({ onBackToHome, onOpenGallery, onOpenFaq }: TutorialPageProps) {
  return (
    <div className="page-view-pane">
      <div className="subpage-container">
        {/* 顶部 Hero */}
        <header className="subpage-hero">
          <span className="eyebrow">USER GUIDE & SHORTCUTS · 使用教程</span>
          <h1>一分钟玩转 WindowPet 桌面伙伴</h1>
          <p className="subpage-lead">
            从初次安装解压、鼠标桌面手势，到摸鱼防查老板键、备忘录闹钟联动与多屏管理，
            助你轻松掌握桌面小宠物的所有隐藏操作技巧！
          </p>

          <div className="subpage-hero-actions">
            <a
              className="primary-download"
              href={releaseInstallerHref}
              download="WindowPet_Setup_v1.0.32.exe"
              style={{ padding: '12px 28px', fontSize: '15px' }}
            >
              <Download size={18} />
              <span>下载安装包体验 (仅 50MB)</span>
            </a>

            {onOpenFaq && (
              <button
                type="button"
                className="secondary-action"
                onClick={onOpenFaq}
                style={{ padding: '12px 22px', fontSize: '14px' }}
              >
                <HelpCircle size={16} />
                <span>常见问题 FAQ</span>
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

        {/* 快捷键速查表 (高频核心) */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <Keyboard size={14} />
              <span>GLOBAL SHORTCUTS</span>
            </span>
            <h2>全局快捷键速查 · 摸鱼与效率神器</h2>
            <p>即使在运行其他全屏软件或打游戏时，这些快捷键也能全局随时响应。</p>
          </div>

          <div className="tutorial-chapter-grid">
            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#dc2626' }}>
                  <EyeOff size={22} />
                </div>
                <div>
                  <h3>防查老板键 · 一秒隐身</h3>
                  <span className="tutorial-key-pill">Ctrl + Shift + P</span>
                </div>
              </div>
              <p>
                老板或同事走近时，按下瞬间将桌面上的所有宠物和悬浮便签瞬间隐藏，不留任何痕迹；再次按下即可在原地完美还原唤醒！
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon" style={{ background: 'rgba(14, 165, 233, 0.1)', color: '#0284c7' }}>
                  <CalendarCheck size={22} />
                </div>
                <div>
                  <h3>呼出待办悬浮便签</h3>
                  <span className="tutorial-key-pill">Ctrl + Shift + Space</span>
                </div>
              </div>
              <p>
                随时唤醒屏幕边缘的轻量备忘录。输入临时待办事项、会议时间或待买清单，按回车即可吸附在桌面，再也不怕忘事。
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon" style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#7c3aed' }}>
                  <Volume2 size={22} />
                </div>
                <div>
                  <h3>全局静音切换</h3>
                  <span className="tutorial-key-pill">Ctrl + Shift + M</span>
                </div>
              </div>
              <p>
                在开会或需要极度专注时，一键静音所有角色互动叫声与到点提醒蜂鸣；重新开启后恢复可爱萌系反馈音效。
              </p>
            </article>
          </div>
        </section>

        {/* 鼠标手势与桌面互动技巧 */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <MousePointerClick size={14} />
              <span>MOUSE GESTURES</span>
            </span>
            <h2>鼠标手势与日常桌面互动</h2>
            <p>告别死板的静态贴图，像对待真实宠物一样与它互动。</p>
          </div>

          <div className="tutorial-chapter-grid">
            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon">
                  <MousePointerClick size={22} />
                </div>
                <h3>左键拖拽 & 边缘智能吸附</h3>
              </div>
              <p>
                鼠标左键按住萌宠即可拖拽至屏幕任意位置。拖动到屏幕边缘（左/右/任务栏上方）时，角色会自动识别吸附停靠，不遮挡日常网页或游戏窗口。
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon">
                  <Sparkles size={22} />
                </div>
                <h3>单双击触发专属特技</h3>
              </div>
              <p>
                单击宠物：暂停待机，萌宠会转过头向你挥手、眨眼或害羞；连续双击：触发专属特技（例如吉伊开启演唱会演奏、Dora 开心蹦跶跳跃、狐狸甩长尾巴）。
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon">
                  <Layers size={22} />
                </div>
                <h3>无级滚轮缩放尺寸</h3>
              </div>
              <p>
                按住键盘 <span className="tutorial-key-pill">Alt</span> 键的同时滑动鼠标滚轮，可无级调整小宠物体积（50% 迷你小挂件 ~ 200% 巨型萌兽随心变）。
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon">
                  <Feather size={22} />
                </div>
                <h3>右键工具箱 & 逗宠道具</h3>
              </div>
              <p>
                在小宠物身上点击鼠标右键，可以打开主控制面板，还可以从工具箱中拿出羽毛或逗猫棒逗弄它，宠物眼神会实时跟随鼠标轨迹扑打互动！
              </p>
            </article>
          </div>
        </section>

        {/* 桌面实用助手功能 */}
        <section style={{ marginBottom: '56px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <CalendarCheck size={14} />
              <span>PRODUCTIVITY TOOLS</span>
            </span>
            <h2>桌面效率助手 · 不只是可爱</h2>
            <p>将备忘录、定时番茄钟与健康提醒无缝融入日常工作流。</p>
          </div>

          <div className="tutorial-chapter-grid">
            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#059669' }}>
                  <CalendarCheck size={22} />
                </div>
                <h3>贴心备忘录 (Memo)</h3>
              </div>
              <p>
                打开右键菜单选择【备忘录】，可以创建多个置顶便签。支持便签贴在桌宠头顶或屏幕右下角，做完一项顺手点击打勾划掉，治好健忘症。
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#d97706' }}>
                  <AlarmClock size={22} />
                </div>
                <h3>番茄时钟 & 喝水起身提醒</h3>
              </div>
              <p>
                可设置 25/45 分钟专注工作周期。倒计时结束时，小宠物会用活泼动作（如挥动荧光棒或敲门敲玻璃动作）提醒你站起来活动颈椎、喝一杯温水。
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#2563eb' }}>
                  <Monitor size={22} />
                </div>
                <h3>多显示器自由跨屏</h3>
              </div>
              <p>
                完美支持双显示器与多屏幕扩展环境！直接按住宠物拖动即可跨屏移动，各屏幕 DPI 缩放自动无缝适配，想让它停在哪台显示器都可以。
              </p>
            </article>
          </div>

          <div className="tutorial-tip-box">
            <span style={{ fontSize: '1.2rem' }}>💡</span>
            <div>
              <strong>温馨提示：如何设置 Windows 开机自动启动？</strong>
              <div style={{ marginTop: '4px' }}>
                在宠物身上点击鼠标右键 ➔ 点击【控制台设置】 ➔ 勾选【随 Windows 开机自动启动】，以后每次打开电脑，爱宠都会在桌面上第一时间迎接你。
              </div>
            </div>
          </div>
        </section>

        {/* 展馆兑换码与外部模型导入 */}
        <section style={{ marginBottom: '40px' }}>
          <div className="subpage-section-header">
            <span className="subpage-section-badge">
              <FolderSync size={14} />
              <span>CUSTOM EXTENSION</span>
            </span>
            <h2>展馆兑换码使用与自定义模型导入</h2>
            <p>超 20 款民间共创角色轻松解锁，也支持导入专属自定义模型。</p>
          </div>

          <div className="tutorial-chapter-grid">
            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon">
                  <Sparkles size={22} />
                </div>
                <h3>使用小鼻嘎展馆公开兑换码</h3>
              </div>
              <p>
                在官网顶部【小鼻嘎展馆】中，每一款角色都附带了公开兑换码（如 <code>WPX-2026-JIYI</code>）。在网页上点击一键复制后，右键桌宠打开控制台 ➔ 粘贴兑换码 ➔ 即可瞬间下载并激活对应角色！
              </p>
            </article>

            <article className="subpage-card tutorial-card">
              <div className="tutorial-card-header">
                <div className="tutorial-card-icon">
                  <FolderSync size={22} />
                </div>
                <h3>导入自己制作的专属角色包</h3>
              </div>
              <p>
                如果您通过【爱宠定制】获得了专属角色包，或者自己制作了动作序列，只需将角色文件夹解压放入软件安装目录下的 <code>pets/</code> 文件夹内，重启软件或在控制台点击【刷新角色库】即可立刻加载。
              </p>
            </article>
          </div>
        </section>

        {/* 底部 CTA 卡片 */}
        <div className="subpage-cta-box">
          <div>
            <h3>准备好开启你的桌面陪伴之旅了吗？</h3>
            <p>轻量绿色安装包仅 50MB，永久开源免费，无任何弹窗广告。</p>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <a
              className="primary-download"
              href={releaseInstallerHref}
              download="WindowPet_Setup_v1.0.32.exe"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', textDecoration: 'none' }}
            >
              <Download size={18} />
              <span>免费下载 Windows 安装包</span>
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
