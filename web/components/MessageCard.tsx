'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import { useSessionStore } from '@/hooks/useWebSocket'
import type { Message } from '@/stores/sessionStore'

interface MessageCardProps {
  message: Message
  isNew?: boolean
}

function processMentions(node: React.ReactNode, agents: any[]): React.ReactNode[] {
  return React.Children.toArray(node).flatMap((child) => {
    if (typeof child === 'string') {
      const parts = child.split(/(@\w+)/g)
      return parts.map((part, i) => {
        if (part.startsWith('@')) {
          const agentName = part.slice(1)
          const agent = agents.find(a => a.name === agentName)
          return (
            <span
              key={`m-${i}`}
              className="font-semibold px-1 rounded"
              style={{
                color: agent?.color || '#d4af37',
                backgroundColor: (agent?.color || '#d4af37') + '15'
              }}
            >
              {part}
            </span>
          )
        }
        return part
      })
    }
    return [child]
  })
}

export default function MessageCard({ message, isNew }: MessageCardProps) {
  const { messages, agents } = useSessionStore()

  const repliedMessage = message.reply_to 
    ? messages.find(m => m.turn === parseInt(message.reply_to!) || m.speaker === message.reply_to)
    : null

  const mentionedAgents = message.mentions || []

  return (
    <div
      className={`group relative pl-5 py-4 pr-5 bg-navy-800/30 rounded-r-xl hover:bg-navy-800/50 transition-all duration-300 ${
        isNew ? 'slide-up' : ''
      }`}
      style={{ 
        borderLeft: `4px solid ${message.color}`,
        boxShadow: `inset 4px 0 12px -4px ${message.color}20`
      }}
    >
      {repliedMessage && (
        <div className="mb-2 pl-3 py-1.5 pr-3 border-l-2 border-gold/20 bg-navy-800/20 rounded-r text-xs">
          <span className="text-parchment/40 font-body italic">
            ↩ {repliedMessage.speaker}: {repliedMessage.content.slice(0, 80)}...
          </span>
        </div>
      )}

      <div className="flex items-baseline gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: message.color }}
          />
          <span
            className="font-display text-sm font-semibold tracking-wide"
            style={{ color: message.color }}
          >
            {message.speaker}
          </span>
        </div>
        <span className="text-[11px] text-parchment/40 font-body italic">
          {message.role}
        </span>
        <span className="text-[11px] text-parchment/20 ml-auto font-mono bg-navy-800/50 px-2 py-0.5 rounded">
          #{message.turn}
        </span>
      </div>

      <div className="font-body text-[13px] text-parchment/90 leading-relaxed markdown-content">
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <p className="my-2">{processMentions(children, agents)}</p>
            ),
            li: ({ children }) => (
              <li className="ml-2">{processMentions(children, agents)}</li>
            ),
            strong: ({ children }) => <strong className="font-bold text-parchment">{children}</strong>,
            em: ({ children }) => <em className="italic text-parchment/80">{children}</em>,
            code: ({ children }) => <code className="bg-navy-700/50 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>,
            pre: ({ children }) => <pre className="bg-navy-700/50 p-3 rounded my-2 overflow-x-auto">{children}</pre>,
            ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
            h1: ({ children }) => <h1 className="text-lg font-bold text-parchment my-3">{children}</h1>,
            h2: ({ children }) => <h2 className="text-base font-bold text-parchment my-3">{children}</h2>,
            h3: ({ children }) => <h3 className="text-sm font-bold text-parchment my-2">{children}</h3>,
            blockquote: ({ children }) => <blockquote className="border-l-2 border-gold/30 pl-3 my-2 italic text-parchment/70">{children}</blockquote>,
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>

      {mentionedAgents.length > 0 && (
        <div className="mt-2 flex items-center gap-2 text-[11px] text-parchment/30">
          <span>📢</span>
          <span className="font-body italic">
            {mentionedAgents.join(', ')} hitap edildi
          </span>
        </div>
      )}

      <div 
        className="absolute top-0 right-0 w-16 h-16 opacity-0 group-hover:opacity-5 transition-opacity"
        style={{
          background: `radial-gradient(circle at top right, ${message.color}, transparent 70%)`
        }}
      />
    </div>
  )
}
