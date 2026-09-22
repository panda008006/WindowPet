import {
  Camera,
  Sparkles,
  Gift,
  HeartHandshake,
  CheckCircle2,
  ArrowLeft,
  ShieldCheck,
  Clock,
  Cpu,
  Layers,
} from 'lucide-react'

interface CustomPetStudioProps {
  onBackToHome: () => void
  onExploreModels?: () => void
}

export function CustomPetStudio({ onBackToHome, onExploreModels }: CustomPetStudioProps) {
  return (
    <div className="custom-studio-page">
      <div className="custom-studio-container">
        {/* 返回按钮与顶条 */}
        <div className="custom-studio-topbar">
          <button type="button" className="custom-back-btn" onClick={onBackToHome}>
            <ArrowLeft size={16} />
            <span>返回主页</span>
          </button>
          {onExploreModels && (
            <button type="button" className="custom-link-btn" onClick={onExploreModels}>
              <span>去逛逛模型库 (24款)</span>
              <Layers size={14} />
            </button>
          )}
        </div>

        {/* Hero 标题区 */}
        <header className="custom-studio-hero">
          <span className="custom-eyebrow">CUSTOM PET STUDIO / 专属毛孩子桌面化</span>
          <h1>把自家毛孩子，做进电脑桌面陪伴你</h1>
          <p className="custom-hero-desc">
            不只是现成的动漫角色！提供 1~3 张爱宠清晰生活照（猫咪、狗狗、龙猫、鹦鹉），
            专业动作设计 + 风格化提取，生成专属 Windows 陪伴桌宠。每一次敲键盘、看屏幕，爱宠都在身边。
          </p>
        </header>

        {/* 3 步定制流程 */}
        <section className="custom-steps-grid">
          <article className="custom-step-card">
            <div className="custom-step-num">01</div>
            <div className="custom-step-icon-box tone-coral">
              <Camera size={26} />
            </div>
            <h3>提供生活照</h3>
            <p>
              准备 1~3 张爱宠清晰的全身照（站立、坐姿或正面趴卧），提取毛色花纹、斑块、瞳色与标志性外观特征。
            </p>
            <ul className="custom-step-points">
              <li><CheckCircle2 size={15} /> 站立 / 趴卧正面清晰照</li>
              <li><CheckCircle2 size={15} /> 标志性毛色斑点与五官特征</li>
              <li><CheckCircle2 size={15} /> 支持猫、狗、异宠等所有品类</li>
            </ul>
          </article>

          <article className="custom-step-card">
            <div className="custom-step-num">02</div>
            <div className="custom-step-icon-box tone-mint">
              <Sparkles size={26} />
            </div>
            <h3>动作与性格定制</h3>
            <p>
              挑选喜欢的动作风格与性格习惯：日常发呆、桌面散步、打瞌睡、踩奶、敲键盘陪加班，甚至定制专属小玩具互动。
            </p>
            <ul className="custom-step-points">
              <li><CheckCircle2 size={15} /> 5 款以上独创互动动作</li>
              <li><CheckCircle2 size={15} /> 专属道具响应（毛线球/骨头/逗猫棒）</li>
              <li><CheckCircle2 size={15} /> 到点定时互动提醒</li>
            </ul>
          </article>

          <article className="custom-step-card">
            <div className="custom-step-num">03</div>
            <div className="custom-step-icon-box tone-blue">
              <Gift size={26} />
            </div>
            <h3>专属安装包交付</h3>
            <p>
              生成独一无二的专属角色兑换码与离线安装包。双击即可在 WindowPet 中召唤自家毛孩子常驻桌面，永久陪伴。
            </p>
            <ul className="custom-step-points">
              <li><CheckCircle2 size={15} /> 专属兑换码，一键导入使用</li>
              <li><CheckCircle2 size={15} /> 私密专属归属，支持独立保存备份</li>
              <li><CheckCircle2 size={15} /> 永久有效，跟随软件终身升级</li>
            </ul>
          </article>
        </section>

        {/* 4 种定制类型展示 */}
        <section className="custom-showcase-section">
          <h2>支持定制的毛孩子类型</h2>
          <div className="custom-types-grid">
            <div className="custom-type-card">
              <span className="custom-type-emoji">🐱</span>
              <strong>猫咪专属伴侣</strong>
              <p>趴在任务栏打瞌睡、踩奶、被羽毛逗弄、偶尔跳起来抓光标，安静治愈。</p>
            </div>
            <div className="custom-type-card">
              <span className="custom-type-emoji">🐶</span>
              <strong>狗狗元气搭档</strong>
              <p>欢快摇尾巴、桌面跑圈、叼骨头等待、工作满 45 分钟提醒你喝水休息。</p>
            </div>
            <div className="custom-type-card">
              <span className="custom-type-emoji">🐹</span>
              <strong>异宠小精灵</strong>
              <p>仓鼠捧坚果、龙猫发呆、鹦鹉跳舞挥翅、小兔子咀嚼，独具可爱个性。</p>
            </div>
            <div className="custom-type-card">
              <span className="custom-type-emoji">🕊️</span>
              <strong>天使毛孩子留存</strong>
              <p>为去往汪星/喵星的天使毛孩子留一份永远在屏幕上奔跑的生动记忆。</p>
            </div>
          </div>
        </section>

        {/* 预约卡片 */}
        <section className="custom-booking-card">
          <div className="custom-booking-content">
            <div className="custom-booking-badge">
              <ShieldCheck size={16} />
              <span>官方担保 · 满意后再交付</span>
            </div>
            <h2>想给自家毛孩子定制独一无二的专属桌宠？</h2>
            <p>
              官方交流群现已开放预约通道。提供透明制作进度预览，支持动态小样确认，满意后再最终交付。
            </p>
            <div className="custom-booking-features">
              <div>
                <Clock size={16} />
                <span>3~5 个工作日交付</span>
              </div>
              <div>
                <Cpu size={16} />
                <span>极简占用（仅约 30MB）</span>
              </div>
              <div>
                <ShieldCheck size={16} />
                <span>100% 绿色安全无广告</span>
              </div>
            </div>
          </div>

          <div className="custom-booking-action">
            <a
              className="custom-primary-btn"
              href="https://qm.qq.com/q/cYlRBbvuda"
              target="_blank"
              rel="noopener noreferrer"
            >
              <HeartHandshake size={20} />
              <span>立即预约爱宠定制 / 进群交流</span>
            </a>
            <button type="button" className="custom-secondary-btn" onClick={onBackToHome}>
              返回主页
            </button>
          </div>
        </section>

        {/* 常见问题 */}
        <section className="custom-faq-section">
          <h2>爱宠定制常见问题 (FAQ)</h2>
          <div className="custom-faq-grid">
            <article className="custom-faq-item">
              <strong>Q: 定制出来的角色会公开给其他人使用吗？</strong>
              <p>默认完全私密！交付的兑换码与数据包仅归您本人所有。如果您希望分享给朋友或授权官方收录，才会公开展示。</p>
            </article>
            <article className="custom-faq-item">
              <strong>Q: 放在桌面上会影响办公或打游戏吗？</strong>
              <p>完全不会。WindowPet 支持一键穿透点击（鼠标点击直接穿透到背后窗口）、快捷键随时隐藏、置顶/贴底调整，绝不挡视线。</p>
            </article>
            <article className="custom-faq-item">
              <strong>Q: 电脑性能低能跑得动吗？</strong>
              <p>WindowPet 专为极速轻量优化，内存占用低至约 30MB，CPU 占用率低于 0.5%，轻薄本和老旧电脑也能丝滑运行。</p>
            </article>
            <article className="custom-faq-item">
              <strong>Q: 如果日后软件更新，定制的角色还能用吗？</strong>
              <p>可以！角色包采用统一的规范标准格式，WindowPet 软件未来所有大版本更新均保证 100% 向下兼容。</p>
            </article>
          </div>
        </section>

        {/* 页脚 */}
        <footer className="page-bottom-footer custom-footer">
          <span>© 2026 WindowPet Open Source Community · 永久开源免费</span>
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noreferrer">
            桂ICP备2026009615号-2
          </a>
        </footer>
      </div>
    </div>
  )
}
