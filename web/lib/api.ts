const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface CreateSessionResponse {
  id: string
  name: string
  topic: string
  status: string
  turn: number
  agents: Array<{
    name: string
    role: string
    color: string
    status: string
    turn_count: number
  }>
}

export interface SessionListItem {
  id: string
  name: string
  created_at: string
  turn_count: number
  status: string
}

export async function createSession(topic: string): Promise<CreateSessionResponse> {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic }),
  })
  if (!res.ok) throw new Error('Oturum oluşturulamadı')
  return res.json()
}

export async function listSessions(): Promise<SessionListItem[]> {
  const res = await fetch(`${API_BASE}/api/sessions`)
  if (!res.ok) throw new Error('Oturumlar listelenemedi')
  return res.json()
}

export async function getSession(id: string): Promise<CreateSessionResponse> {
  const res = await fetch(`${API_BASE}/api/sessions/${id}`)
  if (!res.ok) throw new Error('Oturum bulunamadı')
  return res.json()
}
