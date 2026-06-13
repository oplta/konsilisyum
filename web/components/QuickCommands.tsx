'use client'

import { useState, useCallback, useEffect } from 'react'
import { useSessionStore } from '@/hooks/useWebSocket'

interface QuickCommandsProps {
  onSendCommand: (cmd: string, args?: Record<string, string>) => void
}

export default function QuickCommands({ onSendCommand }: QuickCommandsProps) {
  const { status, agents, analysisResult, setAnalysisResult } = useSessionStore()
  const [showTopicDialog, setShowTopicDialog] = useState(false)
  const [showSpawnDialog, setShowSpawnDialog] = useState(false)
  const [showAskDialog, setShowAskDialog] = useState(false)
  const [showAgentMenu, setShowAgentMenu] = useState<string | null>(null)
  const [topicValue, setTopicValue] = useState('')
  const [spawnValue, setSpawnValue] = useState('')
  const [askAgent, setAskAgent] = useState('')
  const [askMessage, setAskMessage] = useState('')

  const isPaused = status === 'paused'

  const handleTogglePause = useCallback(() => {
    onSendCommand(isPaused ? 'resume' : 'pause')
  }, [isPaused, onSendCommand])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'p':
            e.preventDefault()
            handleTogglePause()
            break
          case 's':
            e.preventDefault()
            onSendCommand('summary')
            break
          case 'k':
            e.preventDefault()
            setShowTopicDialog(true)
            break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleTogglePause, onSendCommand])

  const activeAgents = agents.filter(a => a.status === 'active')
  const mutedAgents = agents.filter(a => a.status === 'muted')

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center">
        <div className="flex gap-1 bg-navy-800/50 rounded-lg p-1">
          <button
            onClick={handleTogglePause}
            className={`px-4 py-2 rounded-md text-sm font-serif transition-all ${
              isPaused
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
            }`}
          >
            {isPaused ? '▶ Devam' : '⏸ Duraklat'}
          </button>
        </div>

        <div className="w-px h-6 bg-gold/20" />

        <div className="flex gap-1 bg-navy-800/50 rounded-lg p-1">
          <button onClick={() => onSendCommand('summary')} className="btn-gold text-xs">
            📋 Özet
          </button>
          <button onClick={() => onSendCommand('decisions')} className="btn-gold text-xs">
            ✓ Kararlar
          </button>
          <button onClick={() => onSendCommand('actions')} className="btn-gold text-xs">
            → Eylemler
          </button>
          <button onClick={() => onSendCommand('map')} className="btn-gold text-xs">
            ⊞ Harita
          </button>
        </div>

        <div className="w-px h-6 bg-gold/20" />

        <button onClick={() => setShowTopicDialog(true)} className="btn-gold text-xs">
          📌 Konu
        </button>
        <button onClick={() => setShowAskDialog(true)} className="btn-gold text-xs">
          💬 Sor
        </button>
        <button onClick={() => setShowSpawnDialog(true)} className="btn-gold text-xs">
          + Ajan
        </button>

        {agents.length > 0 && (
          <>
            <div className="w-px h-6 bg-gold/20" />
            <div className="relative">
              <button
                onClick={() => setShowAgentMenu(showAgentMenu ? null : 'menu')}
                className="btn-gold text-xs"
              >
                👥 Yönet ▾
              </button>
              {showAgentMenu && (
                <div className="absolute bottom-full mb-2 left-0 bg-navy-800 border border-gold/30 rounded-lg shadow-xl min-w-[200px] z-50">
                  <div className="p-2 space-y-1">
                    {activeAgents.map(agent => (
                      <div key={agent.name} className="flex items-center justify-between p-2 hover:bg-navy-700/50 rounded">
                        <span className="text-parchment text-sm flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: agent.color }} />
                          {agent.name}
                        </span>
                        <div className="flex gap-1">
                          <button
                            onClick={() => { onSendCommand('mute', { agent: agent.name }); setShowAgentMenu(null) }}
                            className="text-xs text-yellow-400 hover:text-yellow-300 px-2 py-1"
                          >
                            Sustur
                          </button>
                          <button
                            onClick={() => { onSendCommand('kick', { agent: agent.name }); setShowAgentMenu(null) }}
                            className="text-xs text-red-400 hover:text-red-300 px-2 py-1"
                          >
                            Çıkar
                          </button>
                        </div>
                      </div>
                    ))}
                    {mutedAgents.length > 0 && (
                      <>
                        <div className="border-t border-gold/10 my-1" />
                        <div className="px-2 py-1 text-xs text-parchment/40">Susturulmuş</div>
                        {mutedAgents.map(agent => (
                          <div key={agent.name} className="flex items-center justify-between p-2 hover:bg-navy-700/50 rounded opacity-60">
                            <span className="text-parchment text-sm flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-gray-500" />
                              {agent.name}
                            </span>
                            <button
                              onClick={() => { onSendCommand('unmute', { agent: agent.name }); setShowAgentMenu(null) }}
                              className="text-xs text-green-400 hover:text-green-300 px-2 py-1"
                            >
                              Aç
                            </button>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <div className="flex gap-4 text-xs text-parchment/30">
        <span>Ctrl+P: Duraklat/Devam</span>
        <span>Ctrl+S: Özet</span>
        <span>Ctrl+K: Konu Değiştir</span>
      </div>

      {analysisResult && (
        <div className="bg-navy-800/80 border border-gold/20 rounded-lg p-4 animate-in fade-in slide-in-from-bottom-2">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gold font-serif text-sm uppercase tracking-wide">
              {analysisResult.kind === 'summary' && '📋 Özet'}
              {analysisResult.kind === 'decisions' && '✓ Kararlar'}
              {analysisResult.kind === 'actions' && '→ Eylemler'}
              {analysisResult.kind === 'map' && '⊞ Karşıt Görüş Haritası'}
            </span>
            <button
              onClick={() => setAnalysisResult(null)}
              className="text-parchment/40 hover:text-parchment text-sm transition-colors"
            >
              ✕
            </button>
          </div>
          <p className="text-parchment/80 text-sm font-serif whitespace-pre-wrap leading-relaxed">
            {analysisResult.content}
          </p>
        </div>
      )}

      {showTopicDialog && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowTopicDialog(false)}>
          <div className="bg-navy-800 border border-gold/30 rounded-lg p-6 w-96 shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="font-serif text-gold mb-4">📌 Konu Değiştir</h3>
            <input
              type="text"
              value={topicValue}
              onChange={(e) => setTopicValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && topicValue.trim()) {
                  onSendCommand('topic', { topic: topicValue })
                  setShowTopicDialog(false)
                  setTopicValue('')
                }
              }}
              placeholder="Yeni konu..."
              className="input-classic w-full mb-4"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setShowTopicDialog(false); setTopicValue('') }} className="text-parchment/50 hover:text-parchment text-sm">
                İptal
              </button>
              <button
                onClick={() => {
                  onSendCommand('topic', { topic: topicValue })
                  setShowTopicDialog(false)
                  setTopicValue('')
                }}
                className="btn-gold"
              >
                Değiştir
              </button>
            </div>
          </div>
        </div>
      )}

      {showAskDialog && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowAskDialog(false)}>
          <div className="bg-navy-800 border border-gold/30 rounded-lg p-6 w-96 shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="font-serif text-gold mb-4">💬 Ajana Soru Sor</h3>
            <div className="flex gap-2 mb-3 flex-wrap">
              {activeAgents.map(agent => (
                <button
                  key={agent.name}
                  onClick={() => setAskAgent(agent.name)}
                  className={`px-3 py-1 rounded-full text-xs transition-all ${
                    askAgent === agent.name
                      ? 'text-white border'
                      : 'text-parchment/60 border border-parchment/20 hover:border-parchment/40'
                  }`}
                  style={askAgent === agent.name ? { backgroundColor: agent.color + '33', borderColor: agent.color } : {}}
                >
                  {agent.name}
                </button>
              ))}
            </div>
            <input
              type="text"
              value={askMessage}
              onChange={(e) => setAskMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && askAgent && askMessage.trim()) {
                  onSendCommand('ask', { agent: askAgent, message: askMessage })
                  setShowAskDialog(false)
                  setAskAgent('')
                  setAskMessage('')
                }
              }}
              placeholder="Sorunuzu yazın..."
              className="input-classic w-full mb-4"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setShowAskDialog(false); setAskAgent(''); setAskMessage('') }} className="text-parchment/50 hover:text-parchment text-sm">
                İptal
              </button>
              <button
                onClick={() => {
                  onSendCommand('ask', { agent: askAgent, message: askMessage })
                  setShowAskDialog(false)
                  setAskAgent('')
                  setAskMessage('')
                }}
                disabled={!askAgent || !askMessage.trim()}
                className="btn-gold disabled:opacity-30"
              >
                Sor
              </button>
            </div>
          </div>
        </div>
      )}

      {showSpawnDialog && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowSpawnDialog(false)}>
          <div className="bg-navy-800 border border-gold/30 rounded-lg p-6 w-[480px] shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="font-serif text-gold mb-2">+ Yeni Ajan Ekle</h3>
            <p className="text-parchment/40 text-xs mb-4">
              Boşluklarla ayırarak yazın: <span className="text-gold/60">isim rol amaç kör_nokta stil tetikleyici</span>
            </p>
            <input
              type="text"
              value={spawnValue}
              onChange={(e) => setSpawnValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && spawnValue.trim()) {
                  onSendCommand('spawn', { definition: spawnValue })
                  setShowSpawnDialog(false)
                  setSpawnValue('')
                }
              }}
              placeholder="Nova Yaratıcı Yeni_fikirler_üretmek Çok_soyut_kalır ..."
              className="input-classic w-full mb-4"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setShowSpawnDialog(false); setSpawnValue('') }} className="text-parchment/50 hover:text-parchment text-sm">
                İptal
              </button>
              <button
                onClick={() => {
                  onSendCommand('spawn', { definition: spawnValue })
                  setShowSpawnDialog(false)
                  setSpawnValue('')
                }}
                className="btn-gold"
              >
                Ekle
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
