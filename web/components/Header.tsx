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
    <header className="px-6 py-3 bg-navy-900/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/')}
            className="font-serif text-xl tracking-widest text-gold uppercase hover:text-gold/80 transition-colors"
          >
            Konsilisyum
          </button>
          {topic && (
            <>
              <span className="text-gold/30">|</span>
              <span className="text-parchment/60 text-sm font-serif italic max-w-md truncate">
                {topic}
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-5 text-sm">
          <div className="flex items-center gap-2 bg-navy-800/50 rounded-full px-3 py-1">
            <span className="text-parchment/40 text-xs">Tur</span>
            <span className="text-parchment font-medium">{turn}</span>
          </div>

          <div className={`flex items-center gap-2 ${config.color}`}>
            <span className={`w-2 h-2 rounded-full bg-current ${config.pulse ? 'animate-pulse' : ''}`} />
            <span className="text-xs font-medium">{config.label}</span>
          </div>

          {!isConnected && (
            <div className="flex items-center gap-1 text-red-400/70 text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400/70" />
              Bağlantı yok
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
