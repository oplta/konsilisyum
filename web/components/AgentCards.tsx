'use client'

import { useSessionStore } from '@/hooks/useWebSocket'

export default function AgentCards() {
  const { agents, typingAgent } = useSessionStore()

  const activeAgents = agents.filter(a => a.status !== 'removed')

  return (
    <div className="px-6 py-3">
      <div className="flex gap-3 overflow-x-auto pb-1">
        {activeAgents.map((agent) => {
          const isTyping = typingAgent === agent.name
          const isMuted = agent.status === 'muted'

          return (
            <div
              key={agent.name}
              className={`relative min-w-[140px] rounded-lg p-3 transition-all duration-300 ${
                isTyping
                  ? 'bg-navy-700/80 scale-105'
                  : 'bg-navy-800/60'
              } ${isMuted ? 'opacity-50' : ''}`}
              style={{
                borderLeft: `3px solid ${agent.color}`,
                boxShadow: isTyping ? `0 0 20px ${agent.color}33` : undefined,
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`w-2.5 h-2.5 rounded-full transition-all ${
                    isTyping ? 'animate-pulse scale-125' : ''
                  }`}
                  style={{ backgroundColor: isMuted ? '#666' : agent.color }}
                />
                <span className="font-serif text-sm font-medium text-parchment">
                  {agent.name}
                </span>
              </div>

              <div className="text-xs text-parchment/50 mb-1">{agent.role}</div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-parchment/30">
                  {agent.turn_count} tur
                </span>
                {isMuted && (
                  <span className="text-yellow-500/70 text-[10px]">SUSTURULMUŞ</span>
                )}
              </div>

              {isTyping && (
                <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-ping"
                  style={{ backgroundColor: agent.color }}
                />
              )}
            </div>
          )
        })}

        {activeAgents.length === 0 && (
          <div className="text-parchment/30 font-serif text-sm italic py-2">
            Aktif ajan yok. Kontrol panelinden ajan ekleyin.
          </div>
        )}
      </div>
    </div>
  )
}
