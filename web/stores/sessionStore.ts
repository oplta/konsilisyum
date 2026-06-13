import { create } from 'zustand'

export interface Agent {
  name: string
  role: string
  goal: string
  blind_spot: string
  style: string
  trigger: string
  color: string
  status: string
  turn_count: number
  last_turn: number
}

export interface Message {
  turn: number
  speaker: string
  role: string
  content: string
  color: string
  reply_to?: string | null
  mentions?: string[]
}

interface SessionStore {
  sessionId: string | null
  topic: string
  status: 'running' | 'paused' | 'ended' | 'connecting'
  turn: number
  agents: Agent[]
  messages: Message[]
  typingAgent: string | null
  systemMessage: string | null
  analysisResult: { kind: string; content: string } | null
  connectionStatus: 'connected' | 'disconnected' | 'connecting'
  userScrolledUp: boolean

  setSessionId: (id: string) => void
  setTopic: (topic: string) => void
  setStatus: (status: SessionStore['status']) => void
  setTurn: (turn: number) => void
  setAgents: (agents: Agent[]) => void
  addMessage: (msg: Message) => void
  setTypingAgent: (agent: string | null) => void
  setSystemMessage: (msg: string | null) => void
  setAnalysisResult: (result: { kind: string; content: string } | null) => void
  setConnectionStatus: (status: SessionStore['connectionStatus']) => void
  setUserScrolledUp: (v: boolean) => void
  reset: () => void
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessionId: null,
  topic: '',
  status: 'connecting',
  turn: 0,
  agents: [],
  messages: [],
  typingAgent: null,
  systemMessage: null,
  analysisResult: null,
  connectionStatus: 'connecting',
  userScrolledUp: false,

  setSessionId: (id) => set({ sessionId: id }),
  setTopic: (topic) => set({ topic }),
  setStatus: (status) => set({ status }),
  setTurn: (turn) => set({ turn }),
  setAgents: (agents) => set({ agents }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setTypingAgent: (agent) => set({ typingAgent: agent }),
  setSystemMessage: (msg) => set({ systemMessage: msg }),
  setAnalysisResult: (result) => set({ analysisResult: result }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setUserScrolledUp: (v) => set({ userScrolledUp: v }),
  reset: () => set({
    sessionId: null,
    topic: '',
    status: 'connecting',
    turn: 0,
    agents: [],
    messages: [],
    typingAgent: null,
    systemMessage: null,
    analysisResult: null,
    connectionStatus: 'connecting',
    userScrolledUp: false,
  }),
}))
