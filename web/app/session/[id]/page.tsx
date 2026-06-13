'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useWebSocket, useSessionStore } from '@/hooks/useWebSocket'
import Header from '@/components/Header'
import AgentCards from '@/components/AgentCards'
import MessageStream from '@/components/MessageStream'
import BackstagePanel from '@/components/BackstagePanel'

function LoadingScreen() {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-navy-900">
      <div className="text-center slide-up">
        <div className="text-6xl mb-6 opacity-40">🏛️</div>
        <h1 className="font-display text-4xl tracking-wider text-gold mb-3">
          KONSİLİSYUM
        </h1>
        <div className="gold-divider my-6 max-w-xs mx-auto" />
        <p className="text-parchment/50 font-body italic mb-6">Konsil toplanıyor...</p>
        <div className="flex items-center justify-center gap-2">
          <span className="w-2 h-2 rounded-full bg-gold/50 animate-bounce" style={{ animationDelay: '0s' }} />
          <span className="w-2 h-2 rounded-full bg-gold/50 animate-bounce" style={{ animationDelay: '0.2s' }} />
          <span className="w-2 h-2 rounded-full bg-gold/50 animate-bounce" style={{ animationDelay: '0.4s' }} />
        </div>
      </div>
    </div>
  )
}

function ErrorScreen({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-navy-900">
      <div className="text-center max-w-md slide-up">
        <div className="text-5xl mb-6">⚠️</div>
        <h2 className="font-display text-2xl text-gold mb-3 tracking-wide">Bağlantı Hatası</h2>
        <div className="gold-divider my-4 max-w-xs mx-auto" />
        <p className="text-parchment/60 font-body text-sm mb-8">{message}</p>
        <button onClick={onRetry} className="btn-gold px-8 py-3">
          Tekrar Dene
        </button>
      </div>
    </div>
  )
}

export default function SessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { sendCommand, sendMessage } = useWebSocket(sessionId)
  const { setSessionId, setSystemMessage, connectionStatus } = useSessionStore()

  useEffect(() => {
    setSessionId(sessionId)
  }, [sessionId, setSessionId])

  useEffect(() => {
    if (connectionStatus === 'connected') {
      setIsLoading(false)
      setError(null)
    } else if (connectionStatus === 'disconnected') {
      const timeout = setTimeout(() => {
        setError('Sunucuya bağlanılamıyor. Backend çalışıyor mu?')
        setIsLoading(false)
      }, 5000)
      return () => clearTimeout(timeout)
    }
  }, [connectionStatus])

  const handleSendCommand = (cmd: string, args?: Record<string, string>) => {
    sendCommand(cmd, args)
    setSystemMessage(null)
  }

  const handleRetry = () => {
    setIsLoading(true)
    setError(null)
    window.location.reload()
  }

  if (error) {
    return <ErrorScreen message={error} onRetry={handleRetry} />
  }

  if (isLoading) {
    return <LoadingScreen />
  }

  return (
    <div className="h-screen flex flex-col bg-navy-900">
      <Header />
      <AgentCards />
      <div className="gold-divider" />
      <MessageStream />
      <BackstagePanel
        onSendMessage={(msg) => {
          sendMessage(msg)
          setSystemMessage(null)
        }}
        onSendCommand={handleSendCommand}
      />
    </div>
  )
}
