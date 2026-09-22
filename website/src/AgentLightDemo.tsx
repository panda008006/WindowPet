import { useState } from 'react'

type AgentState = 'idle' | 'running' | 'error'

const stateConfigs: Record<AgentState, {
  color: string
  glow: string
  label: string
  message: string
}> = {
  idle: {
    color: '#10b981',
    glow: 'rgba(16, 185, 129, 0.65)',
    label: '🟢 伴读就绪',
    message: '正在安静陪你敲键盘~ (●\'◡\'●)',
  },
  running: {
    color: '#3b82f6',
    glow: 'rgba(59, 130, 246, 0.65)',
    label: '🔵 协同运行中',
    message: '正在协同 AI 运行任务中，马上就好！✨',
  },
  error: {
    color: '#ef4444',
    glow: 'rgba(239, 68, 68, 0.7)',
    label: '🔴 报错警示',
    message: '检测到终端报错或异常，快看一下！⚠️',
  },
}

export function AgentLightDemo() {
  const [currentState, setCurrentState] = useState<AgentState>('running')
  const config = stateConfigs[currentState]

  return (
    <div className="agent-light-demo-compact">
      <div className="agent-stage-wrapper">
        {/* 智能说话气泡 */}
        <div className="agent-bubble-container" key={currentState}>
          <div className="agent-speech-bubble" style={{ borderColor: `${config.color}60` }}>
            <p className="agent-bubble-text">{config.message}</p>
          </div>
          <div className="agent-bubble-arrow" />
        </div>

        {/* 头顶三色指示灯 */}
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
            alt="WindowPet 萌宠"
            className="agent-pet-img"
          />
        </div>
      </div>

      {/* 极简切换三色灯状态 */}
      <div className="agent-toggle-buttons">
        <button
          type="button"
          className={`agent-btn ${currentState === 'idle' ? 'is-active is-green' : ''}`}
          onClick={() => setCurrentState('idle')}
        >
          🟢 静音伴读
        </button>

        <button
          type="button"
          className={`agent-btn ${currentState === 'running' ? 'is-active is-blue' : ''}`}
          onClick={() => setCurrentState('running')}
        >
          🔵 智能体运行
        </button>

        <button
          type="button"
          className={`agent-btn ${currentState === 'error' ? 'is-active is-red' : ''}`}
          onClick={() => setCurrentState('error')}
        >
          🔴 报错提醒
        </button>
      </div>
    </div>
  )
}
