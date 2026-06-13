'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createSession, listSessions, type SessionListItem } from '@/lib/api'

export default function HomePage() {
  const router = useRouter()
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => {})
  }, [])

  const handleStart = async () => {
    if (!topic.trim()) return
    setLoading(true)
    setError('')
    try {
      const session = await createSession(topic.trim())
      router.push(`/session/${session.id}`)
    } catch {
      setError('Oturum başlatılamadı. Backend çalışıyor mu?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-xl">
        <div className="text-center mb-12">
          <h1 className="font-serif text-4xl tracking-widest text-gold uppercase mb-2">
            Konsilisyum
          </h1>
          <p className="font-serif text-parchment/50 italic text-sm">
            Yaşayan Fikir Meclisi
          </p>
          <div className="gold-divider mt-6" />
        </div>

        <div className="space-y-4">
          <div>
            <label className="block font-serif text-sm text-parchment/60 mb-2">
              Tartışma konusu
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleStart()}
              placeholder="Yapay zeka eğitimi geleceği nasıl şekillendirir?"
              className="input-classic w-full"
              autoFocus
            />
          </div>

          <button
            onClick={handleStart}
            disabled={loading || !topic.trim()}
            className="btn-gold w-full disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {loading ? 'Başlatılıyor...' : 'Konsili Başlat'}
          </button>

          {error && (
            <p className="text-red-400 text-sm font-serif text-center">{error}</p>
          )}
        </div>

        {sessions.length > 0 && (
          <div className="mt-12">
            <div className="gold-divider mb-6" />
            <h2 className="font-serif text-sm text-parchment/40 uppercase tracking-widest mb-4">
              Geçmiş Oturumlar
            </h2>
            <div className="space-y-2">
              {sessions.slice(0, 5).map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between p-3 bg-navy-800/50 rounded-lg border border-gold/10 hover:border-gold/30 transition-colors cursor-pointer"
                  onClick={() => router.push(`/session/${s.id}`)}
                >
                  <div>
                    <span className="text-parchment/80 font-serif text-sm">
                      {s.name || 'İsimsiz oturum'}
                    </span>
                    <span className="text-parchment/30 text-xs ml-3">
                      Tur: {s.turn_count}
                    </span>
                  </div>
                  <span className="text-parchment/20 text-xs">
                    {s.created_at?.slice(0, 16)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-12 text-center">
          <div className="flex items-center justify-center gap-4 text-parchment/20 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-atlas" /> Atlas
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-mira" /> Mira
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-kaan" /> Kaan
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
