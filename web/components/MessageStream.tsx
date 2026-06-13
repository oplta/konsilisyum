'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { useSessionStore } from '@/hooks/useWebSocket'
import MessageCard from './MessageCard'

export default function MessageStream() {
  const { messages, typingAgent, systemMessage, userScrolledUp, setUserScrolledUp } =
    useSessionStore()
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [newMessageCount, setNewMessageCount] = useState(0)
  const lastMessageCount = useRef(messages.length)

  useEffect(() => {
    if (!userScrolledUp && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
      setNewMessageCount(0)
    } else if (messages.length > lastMessageCount.current) {
      setNewMessageCount(prev => prev + (messages.length - lastMessageCount.current))
    }
    lastMessageCount.current = messages.length
  }, [messages, typingAgent, userScrolledUp])

  const handleScroll = useCallback(() => {
    if (!containerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100
    setUserScrolledUp(!isAtBottom)
    if (isAtBottom) {
      setNewMessageCount(0)
    }
  }, [setUserScrolledUp])

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    setNewMessageCount(0)
    setUserScrolledUp(false)
  }

  return (
    <div className="flex-1 relative overflow-hidden">
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-full overflow-y-auto px-6 py-4 space-y-3 scroll-smooth"
      >
        {messages.length === 0 && !typingAgent && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-4xl mb-4 animate-pulse">🏛️</div>
              <p className="text-parchment/30 font-serif italic">
                Tartışma başlıyor...
              </p>
              <p className="text-parchment/20 font-serif text-xs mt-2">
                Ajanlar hazırlanıyor
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageCard key={`${msg.turn}-${msg.speaker}-${i}`} message={msg} />
        ))}

        {typingAgent && (
          <div className="flex items-center gap-2 px-4 py-3 text-gold/60 text-sm font-serif bg-navy-800/30 rounded-lg border border-gold/10">
            <span className="animate-pulse">▌</span>
            <span>{typingAgent} düşünüyor...</span>
          </div>
        )}

        {systemMessage && (
          <div className="mx-4 p-3 bg-gold/5 border border-gold/20 rounded-lg text-sm text-gold/80 font-serif">
            {systemMessage}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {newMessageCount > 0 && userScrolledUp && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 bg-gold/20 text-gold border border-gold/30 rounded-full px-4 py-2 text-sm font-serif hover:bg-gold/30 transition-all shadow-lg"
        >
          ↓ {newMessageCount} yeni mesaj
        </button>
      )}
    </div>
  )
}
