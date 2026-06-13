'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createSession, listSessions, clearAllSessions, type SessionListItem } from '@/lib/api'

const suggestedTopics = [
  'Yapay zeka eğitimi geleceği nasıl şekillendirir?',
  'Şehirlerde sürdürülebilir yaşam mümkün mü?',
  'Teknoloji mi insanlık mı daha hızlı evriliyor?',
  'Demokrasi dijital çağda nasıl dönüşmeli?',
]

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

  const handleStart = async (selectedTopic?: string) => {
    const topicToUse = selectedTopic || topic
    if (!topicToUse.trim()) return
    setLoading(true)
    setError('')
    try {
      const session = await createSession(topicToUse.trim())
      router.push(`/session/${session.id}`)
    } catch {
      setError('Oturum başlatılamadı. Backend çalışıyor mu?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-16 slide-down">
          <div className="inline-block mb-6">
            <div className="text-6xl mb-4 opacity-20">🏛️</div>
          </div>
          <h1 className="font-display text-5xl md:text-6xl text-gold mb-3 tracking-wider">
            KONSİLİSYUM
          </h1>
          <div className="gold-divider my-8 max-w-md mx-auto" />
          <p className="font-body text-parchment/60 text-lg italic">
            Yaşayan Fikir Meclisi
          </p>
          <p className="font-body text-parchment/40 text-sm mt-2 max-w-md mx-auto">
            Farklı bakış açılarına sahip yapay zeka ajanları, senin seçtiğin konuda tartışıyor.
            İstediğin an dahil ol, yön ver.
          </p>
        </div>

        <div className="space-y-6 slide-up stagger-1">
          <div className="glass-panel rounded-xl p-8">
            <label className="block font-display text-sm text-gold/80 mb-3 tracking-wide">
              TARTIŞMA KONUSU
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleStart()}
              placeholder="Bir konu girin veya aşağıdakilerden seçin..."
              className="input-classic w-full text-lg"
              autoFocus
            />

            <button
              onClick={() => handleStart()}
              disabled={loading || !topic.trim()}
              className="btn-gold w-full mt-4 text-base disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⚙️</span>
                  Konsil Toplanıyor...
                </span>
              ) : (
                'Konsili Başlat'
              )}
            </button>

            {error && (
              <p className="text-red-400 text-sm font-body text-center mt-4 slide-up">{error}</p>
            )}
          </div>

          <div className="slide-up stagger-2">
            <p className="font-display text-xs text-parchment/40 uppercase tracking-widest mb-3 text-center">
              Konu Önerileri
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {suggestedTopics.map((t, i) => (
                <button
                  key={i}
                  onClick={() => handleStart(t)}
                  className="text-left p-3 rounded-lg bg-navy-800/20 border border-gold/10 hover:border-gold/30 hover:bg-navy-800/40 transition-all text-sm text-parchment/60 hover:text-parchment/90 font-body"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        {sessions.length > 0 && (
          <div className="mt-16 slide-up stagger-3">
            <div className="gold-divider mb-8" />
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-sm text-parchment/50 uppercase tracking-widest">
                Geçmiş Oturumlar
              </h2>
              <button
                onClick={async () => {
                  if (confirm('Tüm geçmiş sohbetler silinecek. Emin misiniz?')) {
                    await clearAllSessions()
                    setSessions([])
                  }
                }}
                className="text-xs text-red-400/50 hover:text-red-400 transition-colors font-body"
              >
                Tümünü Temizle
              </button>
            </div>
            <div className="space-y-2">
              {sessions.slice(0, 5).map((s, i) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between p-4 glass-panel rounded-lg hover:border-gold/30 transition-all cursor-pointer group"
                  onClick={() => router.push(`/session/${s.id}`)}
                  style={{ animationDelay: `${i * 0.05}s` }}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-gold/30 group-hover:text-gold/60 transition-colors">◆</span>
                    <div>
                      <span className="text-parchment/80 font-body text-sm block">
                        {s.name || 'İsimsiz oturum'}
                      </span>
                      <span className="text-parchment/30 text-xs">
                        {s.turn_count} tur
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-parchment/20 text-xs font-mono">
                      {s.created_at?.slice(0, 16)}
                    </span>
                    <span className="text-parchment/20 group-hover:text-gold/60 transition-colors">→</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-16 text-center slide-up stagger-4">
          <div className="gold-divider mb-8 max-w-xs mx-auto" />
          <div className="flex items-center justify-center gap-6 text-parchment/30 text-xs flex-wrap">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-atlas/60" />
              <span className="font-display tracking-wide">Atlas</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-mira/60" />
              <span className="font-display tracking-wide">Mira</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-kaan/60" />
              <span className="font-display tracking-wide">Kaan</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#a8e6cf99' }} />
              <span className="font-display tracking-wide">Nova</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ff8a5c99' }} />
              <span className="font-display tracking-wide">Zeynep</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
