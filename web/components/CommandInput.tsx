'use client'

import { useState, type KeyboardEvent } from 'react'

interface CommandInputProps {
  onSendMessage: (message: string) => void
  onSendCommand: (cmd: string, args?: Record<string, string>) => void
}

export default function CommandInput({ onSendMessage, onSendCommand }: CommandInputProps) {
  const [value, setValue] = useState('')
  const [isCommand, setIsCommand] = useState(false)

  const handleChange = (newValue: string) => {
    setValue(newValue)
    setIsCommand(newValue.startsWith('/'))
  }

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed) return

    if (trimmed.startsWith('/')) {
      const parts = trimmed.slice(1).split(/\s+/)
      const cmd = parts[0]
      const rest = parts.slice(1).join(' ')

      const argsMap: Record<string, string[]> = {
        say: ['message'],
        ask: ['agent', 'message'],
        topic: ['topic'],
        spawn: ['definition'],
        kick: ['agent'],
        mute: ['agent'],
        unmute: ['agent'],
        think: ['message'],
        edit: ['agent', 'field', 'value'],
        export: ['format'],
        load: ['file'],
        role: ['role'],
      }

      const argKeys = argsMap[cmd]
      if (argKeys && rest) {
        if (argKeys.length === 1) {
          onSendCommand(cmd, { [argKeys[0]]: rest })
        } else {
          const restParts = rest.split(/\s+/)
          const args: Record<string, string> = {}
          argKeys.forEach((key, i) => {
            if (key === 'message' || key === 'definition' || key === 'topic') {
              args[key] = restParts.slice(i).join(' ')
            } else {
              args[key] = restParts[i] || ''
            }
          })
          onSendCommand(cmd, args)
        }
      } else {
        onSendCommand(cmd)
      }
    } else {
      onSendMessage(trimmed)
    }

    setValue('')
    setIsCommand(false)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <input
          type="text"
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Mesaj yaz veya /komut gir..."
          className={`input-classic w-full pr-20 ${
            isCommand ? 'border-gold/50 text-gold' : ''
          }`}
        />
        {isCommand && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-gold/60 font-display tracking-wider">
            KOMUT
          </span>
        )}
      </div>
      <button
        onClick={handleSubmit}
        disabled={!value.trim()}
        className="btn-gold whitespace-nowrap disabled:opacity-30 disabled:cursor-not-allowed px-5"
      >
        Gönder
      </button>
    </div>
  )
}
