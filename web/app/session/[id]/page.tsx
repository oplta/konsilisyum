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
      <div className="text-center">
        <h1 className="font-serif text-3xl tracking-widest text-gold uppercase mb-4 animate-pulse">
          Konsilisyum
        </h1>
        <p className="text-parchment/40 font-serif italic">Bağlanılıyor...</p>
      </div>
    </div>
  )
}

function ErrorScreen({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-navy-900">
      <div className="text-center max-w-md">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="font-serif text-xl text-gold mb-2">Bağlantı Hatası</h2>
        <p className="text-parchment/60 font-serif text-sm mb-6">{message}</p>
        <button onClick={onRetry} className="btn-gold">
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
