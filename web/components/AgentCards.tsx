'use client'

import { useState } from 'react'
import { useSessionStore } from '@/hooks/useWebSocket'
import type { Agent } from '@/stores/sessionStore'

const AGENT_ICONS: Record<string, string> = {
  Atlas: '🗺️',
  Mira: '🔮',
  Kaan: '⚔️',
  Nova: '🚀',
  Zeynep: '🌍',
}

function getAgentIcon(name: string): string {
  return AGENT_ICONS[name] || '🎭'
}

function AgentProfileModal({ agent, onClose }: { agent: Agent; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 scale-in" onClick={onClose}>
      <div className="glass-panel rounded-2xl p-8 w-[550px] shadow-2xl slide-up" onClick={e => e.stopPropagation()}>
        <div className="flex items-start gap-4 mb-6">
          <div 
            className="w-16 h-16 rounded-xl flex items-center justify-center text-3xl"
            style={{ 
              backgroundColor: agent.color + '20',
              border: `2px solid ${agent.color}40`
            }}
          >
            {getAgentIcon(agent.name)}
          </div>
          <div className="flex-1">
            <h2 className="font-display text-2xl tracking-wide" style={{ color: agent.color }}>
              {agent.name}
            </h2>
            <p className="text-parchment/60 font-body italic">{agent.role}</p>
            <div className="flex items-center gap-3 mt-2 text-xs">
              <span className="px-2 py-1 rounded-full bg-navy-700/50 text-parchment/50">
                {agent.turn_count} tur konuştu
              </span>
              <span className={`px-2 py-1 rounded-full ${
                agent.status === 'active' ? 'bg-green-500/20 text-green-400' :
                agent.status === 'muted' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {agent.status === 'active' ? '● Aktif' : agent.status === 'muted' ? '○ Susturulmuş' : '✕ Çıkarıldı'}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="text-parchment/40 hover:text-parchment text-xl">✕</button>
        </div>

        <div className="gold-divider mb-6" />

        <div className="space-y-5">
          <div>
            <h3 className="font-display text-xs text-gold/70 uppercase tracking-widest mb-2">Amaç</h3>
            <p className="text-parchment/80 font-body text-sm leading-relaxed">{agent.goal}</p>
          </div>

          <div>
            <h3 className="font-display text-xs text-gold/70 uppercase tracking-widest mb-2">Kör Nokta</h3>
            <p className="text-parchment/80 font-body text-sm leading-relaxed">{agent.blind_spot}</p>
          </div>

          <div>
            <h3 className="font-display text-xs text-gold/70 uppercase tracking-widest mb-2">Konuşma Stili</h3>
            <p className="text-parchment/80 font-body text-sm leading-relaxed">{agent.style}</p>
          </div>

          <div>
            <h3 className="font-display text-xs text-gold/70 uppercase tracking-widest mb-2">Tetikleyici</h3>
            <p className="text-parchment/80 font-body text-sm leading-relaxed">{agent.trigger}</p>
          </div>
        </div>

        <div className="gold-divider mt-6 mb-4" />

        <div className="flex items-center justify-between text-xs text-parchment/30">
          <span>Son konuşma: Tur {agent.last_turn || 'Henüz konuşmadı'}</span>
          <span style={{ color: agent.color }}>■</span>
        </div>
      </div>
    </div>
  )
}

export default function AgentCards() {
  const { agents, typingAgent, turn } = useSessionStore()
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)

  const activeAgents = agents.filter(a => a.status !== 'removed')

  return (
    <>
      <div className="px-6 py-4">
        <div className="flex gap-4 overflow-x-auto pb-2">
          {activeAgents.map((agent, index) => {
            const isTyping = typingAgent === agent.name
            const isMuted = agent.status === 'muted'
            const turnsSinceLastSpoke = agent.last_turn > 0 ? turn - agent.last_turn : null

            return (
              <div
                key={agent.name}
                onClick={() => setSelectedAgent(agent)}
                className={`agent-card relative min-w-[140px] max-w-[160px] cursor-pointer slide-down ${
                  isTyping ? 'glow' : ''
                } ${isMuted ? 'opacity-40' : ''}`}
                style={{ 
                  animationDelay: `${index * 0.1}s`,
                  borderLeft: `3px solid ${agent.color}`,
                  boxShadow: isTyping ? `0 0 20px ${agent.color}40, inset 0 0 15px ${agent.color}10` : undefined,
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="relative">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg transition-all ${
                        isTyping ? 'animate-pulse scale-110' : ''
                      }`}
                      style={{ 
                        backgroundColor: isMuted ? '#33333380' : agent.color + '20',
                        border: `1px solid ${isMuted ? '#666' : agent.color}40`
                      }}
                    >
                      {getAgentIcon(agent.name)}
                    </div>
                    {isTyping && (
                      <span 
                        className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-ping"
                        style={{ backgroundColor: agent.color, opacity: 0.6 }}
                      />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="font-display text-sm font-semibold text-parchment tracking-wide block truncate">
                      {agent.name}
                    </span>
                    <span className="text-[10px] text-parchment/50 font-body italic block truncate">
                      {agent.role}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[10px] pt-2 border-t border-gold/10">
                  <span className="text-parchment/40 font-mono">
                    {agent.turn_count} tur
                  </span>
                  {isMuted && (
                    <span className="text-yellow-500/70 font-display tracking-wider">
                      SUSTURULMUŞ
                    </span>
                  )}
                  {isTyping && (
                    <span className="text-gold/80 font-display tracking-wider animate-pulse">
                      YAZIYOR
                    </span>
                  )}
                  {!isMuted && !isTyping && turnsSinceLastSpoke !== null && turnsSinceLastSpoke > 0 && (
                    <span className="text-parchment/30">
                      {turnsSinceLastSpoke} tur önce
                    </span>
                  )}
                </div>
              </div>
            )
          })}

          {activeAgents.length === 0 && (
            <div className="text-parchment/30 font-body text-sm italic py-2">
              Aktif ajan yok. Kontrol panelinden ajan ekleyin.
            </div>
          )}
        </div>
      </div>

      {selectedAgent && (
        <AgentProfileModal agent={selectedAgent} onClose={() => setSelectedAgent(null)} />
      )}
    </>
  )
}
