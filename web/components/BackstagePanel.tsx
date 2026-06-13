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
  const [collapsed, setCollapsed] = useState(false)
  const { status, turn, agents } = useSessionStore()

  const activeCount = agents.filter(a => a.status === 'active').length
  const mutedCount = agents.filter(a => a.status === 'muted').length

  return (
    <div className="border-t border-gold/20 bg-navy-900/95 backdrop-blur-sm">
      <div className="px-6 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-parchment/40">
          <span className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${
              status === 'running' ? 'bg-green-400 animate-pulse' :
              status === 'paused' ? 'bg-yellow-400' : 'bg-red-400'
            }`} />
            {status === 'running' ? 'Canlı' : status === 'paused' ? 'Duraklatıldı' : 'Sonlandı'}
          </span>
          <span>Tur {turn}</span>
          <span>{activeCount} aktif{mutedCount > 0 ? `, ${mutedCount} susturulmuş` : ''}</span>
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-parchment/40 hover:text-parchment/60 transition-colors text-sm"
        >
          {collapsed ? '▲ Paneli Aç' : '▼ Paneli Kapat'}
        </button>
      </div>

      {!collapsed && (
        <div className="px-6 pb-4 space-y-3">
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
