'use client'

import type { Message } from '@/stores/sessionStore'

interface MessageCardProps {
  message: Message
}

export default function MessageCard({ message }: MessageCardProps) {
  return (
    <div
      className="group relative pl-4 py-3 pr-4 bg-navy-800/40 rounded-r-lg hover:bg-navy-800/60 transition-colors"
      style={{ borderLeft: `3px solid ${message.color}` }}
    >
      <div className="flex items-baseline gap-3 mb-2">
        <span
          className="font-serif text-sm font-semibold"
          style={{ color: message.color }}
        >
          {message.speaker}
        </span>
        <span className="text-xs text-parchment/30 font-serif">
          {message.role}
        </span>
        <span className="text-xs text-parchment/20 ml-auto font-mono">
          #{message.turn}
        </span>
      </div>
      <p className="font-serif text-sm text-parchment/85 leading-relaxed whitespace-pre-wrap">
        {message.content}
      </p>
    </div>
  )
}
