import { useState } from 'react'
import { Sparkles, Terminal, AlertTriangle, CheckCircle2 } from 'lucide-react'

type AgentState = 'idle' | 'running' | 'error'

const stateConfigs: Record<AgentState, {
  color: string
  glow: string
  label: string
  badge: string
  message: string
  agentName: string
}> = {
  idle: {
    color: '#10b981',
    glow: 'rgba(16, 185, 129, 0.6)',
    label: '🟢 伴读就绪',
    badge: 'READY',
    message: '代码环境已就绪，正在安静陪你敲键盘~ (●\'◡\'●)',
    agentName: '工作就绪 · 静音伴读',
  },
  running: {
    color: '#3b82f6',
    glow: 'rgba(59, 130, 246, 0.6)',
    label: '🔵 AI 运行中',
    badge: 'AGENT RUNNING',
    message: '正在协同 Codex / Gemini / DeepSeek / WorkBuddy 跑任务中，马上就好！✨',
    agentName: 'Codex / Gemini / DeepSeek 协同中',
  },
  error: {
    color: '#ef4444',
    glow: 'rgba(239, 68, 68, 0.65)',
    label: '🔴 报错提醒',
    badge: 'ALERT',
    message: '哎呀！终端检测到执行异常或语法错误，快去控制台看一下！⚠️',
    agentName: '终端异常 · 警示提醒',
  },
}

export function AgentLightDemo() {
  const [currentState, setCurrentState] = useState<AgentState>('running')
  const config = stateConfigs[currentState]

  return (
    <div className="agent-light-demo-card">
      <div className="agent-demo-header">
        <div className="agent-header-left">
          <Terminal size={16} color="#e85f6d" />
          <span>AI 编程智能体 · 极简头顶亮灯联动</span>
        </div>
        <span
          className="agent-state-pill"
          style={{ backgroundColor: `${config.color}15`, color: config.color, borderColor: `${config.color}40` }}
        >
          {config.badge}
        </span>
      </div>

      <div className="agent-stage-wrapper">
        {/* 智能说话气泡 */}
        <div className="agent-bubble-container" key={currentState}>
          <div className="agent-speech-bubble" style={{ borderColor: `${config.color}50` }}>
            <p className="agent-bubble-text">{config.message}</p>
            <span className="agent-bubble-sub">{config.agentName}</span>
          </div>
          <div className="agent-bubble-arrow" style={{ borderTopColor: '#ffffff' }} />
        </div>

        {/* 头顶三色呼吸指示灯 */}
        <div className="agent-head-light-assembly">
          <div
            className="agent-led-core"
            style={{
              backgroundColor: config.color,
              boxShadow: `0 0 16px 4px ${config.glow}`,
            }}
          />
          <div
            className="agent-led-ring"
            style={{ borderColor: config.color }}
          />
        </div>

        {/* 宠物主体 */}
        <div className="agent-pet-avatar">
          <img
            src={`${import.meta.env.BASE_URL}pets/cat.png`}
            alt="WindowPet AI 联动萌宠"
            className="agent-pet-img"
          />
        </div>
      </div>

      {/* 极简无脑一键切换测试栏 */}
      <div className="agent-control-bar">
        <span className="agent-control-title">点击切换模拟信号：</span>
        <div className="agent-toggle-buttons">
          <button
            type="button"
            className={`agent-btn ${currentState === 'idle' ? 'is-active is-green' : ''}`}
            onClick={() => setCurrentState('idle')}
          >
            <CheckCircle2 size={13} />
            <span>正常伴读</span>
          </button>

          <button
            type="button"
            className={`agent-btn ${currentState === 'running' ? 'is-active is-blue' : ''}`}
            onClick={() => setCurrentState('running')}
          >
            <Sparkles size={13} />
            <span>智能体运行</span>
          </button>

          <button
            type="button"
            className={`agent-btn ${currentState === 'error' ? 'is-active is-red' : ''}`}
            onClick={() => setCurrentState('error')}
          >
            <AlertTriangle size={13} />
            <span>报错警示</span>
          </button>
        </div>
      </div>

      <p className="agent-demo-note">
        💡 <strong>极简哲学：</strong>无需繁杂的动作，只需头顶一盏灯 + 说话气泡，0 负担秒懂 AI 状态！
      </p>
    </div>
  )
}
