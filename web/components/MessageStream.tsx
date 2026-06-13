'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { useSessionStore } from '@/hooks/useWebSocket'
import MessageCard from './MessageCard'

export default function MessageStream() {
  const { messages, typingAgent, systemMessage, userScrolledUp, setUserScrolledUp, agents } =
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
        className="h-full overflow-y-auto px-8 py-6 space-y-4 scroll-smooth"
      >
        {messages.length === 0 && !typingAgent && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center slide-up">
              <div className="text-6xl mb-6 opacity-30 animate-pulse">🏛️</div>
              <p className="font-display text-xl text-parchment/40 tracking-wide mb-2">
                Tartışma Başlıyor
              </p>
              <p className="font-body text-parchment/25 text-sm italic">
                Ajanlar toplanıyor ve hazırlanıyor...
              </p>
              <div className="mt-8 flex items-center justify-center gap-2">
                <span className="w-2 h-2 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: '0s' }} />
                <span className="w-2 h-2 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: '0.2s' }} />
                <span className="w-2 h-2 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageCard 
            key={`${msg.turn}-${msg.speaker}-${i}`} 
            message={msg} 
            isNew={i === messages.length - 1}
          />
        ))}

        {typingAgent && (
          <div className="flex items-center gap-3 px-6 py-4 text-gold/70 text-sm font-body bg-navy-800/40 rounded-xl border border-gold/15 backdrop-blur-sm slide-up">
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full bg-gold/60 animate-bounce" style={{ animationDelay: '0s' }} />
              <span className="w-2 h-2 rounded-full bg-gold/60 animate-bounce" style={{ animationDelay: '0.15s' }} />
              <span className="w-2 h-2 rounded-full bg-gold/60 animate-bounce" style={{ animationDelay: '0.3s' }} />
            </div>
            <span className="font-display tracking-wide">
              {typingAgent}
            </span>
            <span className="text-parchment/40 italic">
              {agents.find(a => a.name === typingAgent)?.style || 'düşünüyor...'}
            </span>
          </div>
        )}

        {systemMessage && (
          <div className="mx-6 p-5 bg-gold/5 border border-gold/25 rounded-xl text-sm text-gold/90 font-body slide-up backdrop-blur-sm">
            <div className="flex items-start gap-3">
              <span className="text-lg">💬</span>
              <span>{systemMessage}</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {newMessageCount > 0 && userScrolledUp && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-6 right-6 btn-gold rounded-full px-5 py-3 shadow-2xl slide-up flex items-center gap-2"
        >
          <span>↓</span>
          <span>{newMessageCount} yeni mesaj</span>
        </button>
      )}
    </div>
  )
}
