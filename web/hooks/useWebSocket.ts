'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useSessionStore } from '@/stores/sessionStore'

export { useSessionStore }

export function useWebSocket(sessionId: string) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const store = useSessionStore

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    store.getState().setConnectionStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000'
    const ws = new WebSocket(`${protocol}//${host}/ws/session/${sessionId}`)

    ws.onopen = () => {
      store.getState().setConnectionStatus('connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'session_state':
          store.getState().setAgents(data.agents)
          store.getState().setTopic(data.topic)
          store.getState().setTurn(data.turn)
          store.getState().setStatus(data.status)
          break

        case 'agent_message':
          store.getState().addMessage({
            turn: data.turn,
            speaker: data.speaker,
            role: data.role,
            content: data.content,
            color: data.color,
            reply_to: data.reply_to,
            mentions: data.mentions,
          })
          store.getState().setTurn(data.turn)
          break

        case 'agent_typing':
          store.getState().setTypingAgent(data.agent)
          break

        case 'agent_done_typing':
          store.getState().setTypingAgent(null)
          break

        case 'status':
          store.getState().setStatus(data.status)
          store.getState().setTurn(data.turn)
          break

        case 'topic_changed':
          store.getState().setTopic(data.topic)
          break

        case 'agents_update':
          store.getState().setAgents(data.agents)
          break

        case 'summary':
          store.getState().setSystemMessage(`📋 Özet: ${data.content}`)
          break

        case 'analysis':
          store.getState().setAnalysisResult({ kind: data.kind, content: data.content })
          break

        case 'command_result':
          if (data.message) {
            store.getState().setSystemMessage(data.message)
          }
          break

        case 'error':
          store.getState().setSystemMessage(`⚠ ${data.message}`)
          break
      }
    }

    ws.onclose = (event) => {
      store.getState().setConnectionStatus('disconnected')
      if (event.code !== 4004) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      ws.close()
    }

    wsRef.current = ws
  }, [sessionId])

  const sendCommand = useCallback((cmd: string, args?: Record<string, string>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'command', cmd, args }))
    }
  }, [])

  const sendMessage = useCallback((message: string) => {
    sendCommand('say', { message })
  }, [sendCommand])

  useEffect(() => {
    store.getState().reset()
    connect()
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { sendCommand, sendMessage }
}
