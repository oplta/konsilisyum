'use client'

import { useState } from 'react'
import CommandInput from './CommandInput'
import QuickCommands from './QuickCommands'
import { useSessionStore } from '@/hooks/useWebSocket'

interface BackstagePanelProps {
  onSendMessage: (message: string) => void
  onSendCommand: (cmd: string, args?: Record<string, string>) => void
}

export default function BackstagePanel({ onSendMessage, onSendCommand }: BackstagePanelProps) {
  const [expanded, setExpanded] = useState(true)
  const { status, turn, agents } = useSessionStore()

  const activeCount = agents.filter(a => a.status === 'active').length
  const mutedCount = agents.filter(a => a.status === 'muted').length

  return (
    <div className="glass-panel border-t border-gold/15 relative z-20">
      <div className="px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              status === 'running' ? 'bg-green-400 animate-pulse shadow-lg shadow-green-400/50' :
              status === 'paused' ? 'bg-yellow-400' : 'bg-red-400'
            }`} />
            <span className="font-display text-parchment/50 tracking-wider">
              {status === 'running' ? 'CANLI' : status === 'paused' ? 'DURAKLATILDI' : 'SONLANDI'}
            </span>
          </div>
          <div className="h-4 w-px bg-gold/20" />
          <span className="font-mono text-parchment/40">
            Tur <span className="text-parchment/60">{turn}</span>
          </span>
          <div className="h-4 w-px bg-gold/20" />
          <span className="font-body text-parchment/40">
            <span className="text-parchment/60">{activeCount}</span> aktif
            {mutedCount > 0 && <>, <span className="text-parchment/60">{mutedCount}</span> susturulmuş</>}
          </span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-parchment/40 hover:text-gold/80 transition-colors text-xs font-display tracking-wider flex items-center gap-1"
        >
          <span>{expanded ? '▼' : '▲'}</span>
          <span>{expanded ? 'Küçült' : 'Genişlet'}</span>
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-3 space-y-2 slide-up">
          <QuickCommands onSendCommand={onSendCommand} />
          <CommandInput
            onSendMessage={onSendMessage}
            onSendCommand={onSendCommand}
          />
        </div>
      )}
    </div>
  )
}
