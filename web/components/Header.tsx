'use client'

import { useRouter } from 'next/navigation'
import { useSessionStore } from '@/hooks/useWebSocket'

export default function Header() {
  const { topic, status, turn, connectionStatus } = useSessionStore()
  const router = useRouter()

  const statusConfig: Record<string, { color: string; label: string; pulse: boolean }> = {
    running: { color: 'text-green-400', label: 'CANLI', pulse: true },
    paused: { color: 'text-yellow-400', label: 'DURAKLATILDI', pulse: false },
    ended: { color: 'text-red-400', label: 'SONA ERDI', pulse: false },
    connecting: { color: 'text-parchment/40', label: 'BAGLANIYOR', pulse: true },
  }

  const config = statusConfig[status] || statusConfig.connecting
  const isConnected = connectionStatus === 'connected'

  return (
    <header className="px-6 py-4 glass-panel sticky top-0 z-10 border-b border-gold/10">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/')}
            className="group flex items-center gap-3"
          >
            <span className="text-2xl opacity-40 group-hover:opacity-80 transition-opacity">🏛️</span>
            <span className="font-display text-xl text-gold tracking-wider group-hover:text-gold-light transition-colors">
              KONSİLİSYUM
            </span>
          </button>
          {topic && (
            <>
              <span className="text-gold/20 text-2xl font-light">|</span>
              <span className="text-parchment/60 text-sm font-body italic max-w-md truncate">
                {topic}
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2 bg-navy-800/50 rounded-full px-4 py-1.5 border border-gold/10">
            <span className="text-parchment/40 text-xs font-display">TUR</span>
            <span className="text-parchment font-display text-lg">{turn}</span>
          </div>

          <div className={`flex items-center gap-2 ${config.color}`}>
            <span className={`w-2.5 h-2.5 rounded-full bg-current ${config.pulse ? 'animate-pulse' : ''}`} />
            <span className="text-xs font-display tracking-wider">{config.label}</span>
          </div>

          {!isConnected && (
            <div className="flex items-center gap-2 text-red-400/70 text-xs bg-red-900/20 px-3 py-1 rounded-full border border-red-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400/70 animate-pulse" />
              <span className="font-display">Bağlantı yok</span>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
