'use client'

import { useState, useCallback, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useSessionStore } from '@/hooks/useWebSocket'

interface QuickCommandsProps {
  onSendCommand: (cmd: string, args?: Record<string, string>) => void
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  if (typeof window === 'undefined') return null
  return createPortal(
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-[9999] scale-in" onClick={onClose}>
      <div className="bg-navy-800 border border-gold/30 rounded-xl shadow-2xl relative z-[10000]" onClick={e => e.stopPropagation()}>
        {children}
      </div>
    </div>,
    document.body
  )
}

export default function QuickCommands({ onSendCommand }: QuickCommandsProps) {
  const { status, agents, analysisResult, setAnalysisResult } = useSessionStore()
  const [showTopicDialog, setShowTopicDialog] = useState(false)
  const [showSpawnDialog, setShowSpawnDialog] = useState(false)
  const [showAskDialog, setShowAskDialog] = useState(false)
  const [showAgentMenu, setShowAgentMenu] = useState<string | null>(null)
  const [topicValue, setTopicValue] = useState('')
  const [askAgent, setAskAgent] = useState('')
  const [askMessage, setAskMessage] = useState('')

  const [spawnName, setSpawnName] = useState('')
  const [spawnRole, setSpawnRole] = useState('')
  const [spawnGoal, setSpawnGoal] = useState('')
  const [spawnBlindSpot, setSpawnBlindSpot] = useState('')
  const [spawnStyle, setSpawnStyle] = useState('')
  const [spawnTrigger, setSpawnTrigger] = useState('')

  const isPaused = status === 'paused'

  const handleTogglePause = useCallback(() => {
    onSendCommand(isPaused ? 'resume' : 'pause')
  }, [isPaused, onSendCommand])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'p': e.preventDefault(); handleTogglePause(); break
          case 's': e.preventDefault(); onSendCommand('summary'); break
          case 'k': e.preventDefault(); setShowTopicDialog(true); break
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleTogglePause, onSendCommand])

  const activeAgents = agents.filter(a => a.status === 'active')
  const mutedAgents = agents.filter(a => a.status === 'muted')

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5 items-center">
        <div className="flex gap-0.5 bg-navy-800/50 rounded-lg p-0.5">
          <button
            onClick={handleTogglePause}
            className={`px-3 py-1.5 rounded-md text-xs font-display tracking-wide transition-all ${
              isPaused
                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
            }`}
          >
            {isPaused ? '▶ Devam' : '⏸ Duraklat'}
          </button>
        </div>

        <div className="w-px h-5 bg-gold/20" />

        <div className="flex gap-0.5 bg-navy-800/50 rounded-lg p-0.5">
          <button onClick={() => onSendCommand('summary')} className="btn-gold text-xs">📋 Özet</button>
          <button onClick={() => onSendCommand('decisions')} className="btn-gold text-xs">✓ Kararlar</button>
          <button onClick={() => onSendCommand('actions')} className="btn-gold text-xs">→ Eylemler</button>
          <button onClick={() => onSendCommand('map')} className="btn-gold text-xs">⊞ Harita</button>
        </div>

        <div className="w-px h-5 bg-gold/20" />

        <button onClick={() => setShowTopicDialog(true)} className="btn-gold text-xs">📌 Konu</button>
        <button onClick={() => setShowAskDialog(true)} className="btn-gold text-xs">💬 Sor</button>
        <button onClick={() => setShowSpawnDialog(true)} className="btn-gold text-xs">+ Ajan</button>

        {agents.length > 0 && (
          <>
            <div className="w-px h-5 bg-gold/20" />
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
                          <button onClick={() => { onSendCommand('mute', { agent: agent.name }); setShowAgentMenu(null) }} className="text-xs text-yellow-400 hover:text-yellow-300 px-2 py-1">Sustur</button>
                          <button onClick={() => { onSendCommand('kick', { agent: agent.name }); setShowAgentMenu(null) }} className="text-xs text-red-400 hover:text-red-300 px-2 py-1">Çıkar</button>
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
                            <button onClick={() => { onSendCommand('unmute', { agent: agent.name }); setShowAgentMenu(null) }} className="text-xs text-green-400 hover:text-green-300 px-2 py-1">Aç</button>
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

      <div className="flex gap-5 text-xs text-parchment/30 font-body">
        <span className="flex items-center gap-1.5">
          <kbd className="px-1.5 py-0.5 bg-navy-800/50 rounded text-parchment/40 text-[10px]">Ctrl</kbd>
          <span>+</span>
          <kbd className="px-1.5 py-0.5 bg-navy-800/50 rounded text-parchment/40 text-[10px]">P</kbd>
          <span className="ml-1">Duraklat</span>
        </span>
        <span className="flex items-center gap-1.5">
          <kbd className="px-1.5 py-0.5 bg-navy-800/50 rounded text-parchment/40 text-[10px]">S</kbd>
          <span>+</span>
          <kbd className="px-1.5 py-0.5 bg-navy-800/50 rounded text-parchment/40 text-[10px]">S</kbd>
          <span className="ml-1">Özet</span>
        </span>
        <span className="flex items-center gap-1.5">
          <kbd className="px-1.5 py-0.5 bg-navy-800/50 rounded text-parchment/40 text-[10px]">Ctrl</kbd>
          <span>+</span>
          <kbd className="px-1.5 py-0.5 bg-navy-800/50 rounded text-parchment/40 text-[10px]">K</kbd>
          <span className="ml-1">Konu</span>
        </span>
      </div>

      {analysisResult && (
        <div className="glass-panel rounded-xl p-5 slide-up">
          <div className="flex items-center justify-between mb-3">
            <span className="text-gold font-display text-sm uppercase tracking-wider">
              {analysisResult.kind === 'summary' && '📋 Özet'}
              {analysisResult.kind === 'decisions' && '✓ Kararlar'}
              {analysisResult.kind === 'actions' && '→ Eylemler'}
              {analysisResult.kind === 'map' && '⊞ Karşıt Görüş Haritası'}
            </span>
            <button onClick={() => setAnalysisResult(null)} className="text-parchment/40 hover:text-parchment text-sm transition-colors">✕</button>
          </div>
          <p className="text-parchment/80 text-sm font-body whitespace-pre-wrap leading-relaxed">
            {analysisResult.content}
          </p>
        </div>
      )}

      {showTopicDialog && (
        <Modal onClose={() => setShowTopicDialog(false)}>
          <div className="p-8 w-[500px]">
            <div className="flex items-center gap-3 mb-6">
              <span className="text-2xl">📌</span>
              <h3 className="font-display text-xl text-gold tracking-wide">Konu Değiştir</h3>
            </div>
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
              placeholder="Yeni tartışma konusu..."
              className="input-classic w-full mb-6 text-lg"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setShowTopicDialog(false); setTopicValue('') }} className="text-parchment/50 hover:text-parchment text-sm font-body px-4 py-2">İptal</button>
              <button onClick={() => { onSendCommand('topic', { topic: topicValue }); setShowTopicDialog(false); setTopicValue('') }} className="btn-gold">Değiştir</button>
            </div>
          </div>
        </Modal>
      )}

      {showAskDialog && (
        <Modal onClose={() => setShowAskDialog(false)}>
          <div className="p-8 w-[500px]">
            <div className="flex items-center gap-3 mb-6">
              <span className="text-2xl">💬</span>
              <h3 className="font-display text-xl text-gold tracking-wide">Ajana Soru Sor</h3>
            </div>
            <div className="flex gap-2 mb-4 flex-wrap">
              {activeAgents.map(agent => (
                <button
                  key={agent.name}
                  onClick={() => setAskAgent(agent.name)}
                  className={`px-4 py-2 rounded-full text-sm transition-all font-display tracking-wide ${
                    askAgent === agent.name
                      ? 'text-white border-2'
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
              className="input-classic w-full mb-6 text-lg"
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setShowAskDialog(false); setAskAgent(''); setAskMessage('') }} className="text-parchment/50 hover:text-parchment text-sm font-body px-4 py-2">İptal</button>
              <button
                onClick={() => { onSendCommand('ask', { agent: askAgent, message: askMessage }); setShowAskDialog(false); setAskAgent(''); setAskMessage('') }}
                disabled={!askAgent || !askMessage.trim()}
                className="btn-gold disabled:opacity-30"
              >Sor</button>
            </div>
          </div>
        </Modal>
      )}

      {showSpawnDialog && (
        <Modal onClose={() => setShowSpawnDialog(false)}>
          <div className="p-8 w-[600px] max-h-[90vh] overflow-y-auto">
            <div className="flex items-center gap-3 mb-6">
              <span className="text-2xl">✨</span>
              <h3 className="font-display text-xl text-gold tracking-wide">Yeni Ajan Ekle</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-body text-parchment/70 mb-2">İsim *</label>
                <input type="text" value={spawnName} onChange={(e) => setSpawnName(e.target.value)} placeholder="Örn: Nova, Zeynep, Felix" className="input-classic w-full" autoFocus />
              </div>
              <div>
                <label className="block text-sm font-body text-parchment/70 mb-2">Rol *</label>
                <input type="text" value={spawnRole} onChange={(e) => setSpawnRole(e.target.value)} placeholder="Örn: İnovasyon Uzmanı, Etik Danışmanı" className="input-classic w-full" />
              </div>
              <div>
                <label className="block text-sm font-body text-parchment/70 mb-2">Amaç *</label>
                <textarea value={spawnGoal} onChange={(e) => setSpawnGoal(e.target.value)} placeholder="Bu ajan tartışmaya ne katmak istiyor?" className="input-classic w-full h-20 resize-none" />
              </div>
              <div>
                <label className="block text-sm font-body text-parchment/70 mb-2">Kör Nokta</label>
                <input type="text" value={spawnBlindSpot} onChange={(e) => setSpawnBlindSpot(e.target.value)} placeholder="Örn: Pratik zorlukları göz ardı etme" className="input-classic w-full" />
              </div>
              <div>
                <label className="block text-sm font-body text-parchment/70 mb-2">Konuşma Stili</label>
                <input type="text" value={spawnStyle} onChange={(e) => setSpawnStyle(e.target.value)} placeholder="Örn: Heyecanlı, metaforlarla dolu" className="input-classic w-full" />
              </div>
              <div>
                <label className="block text-sm font-body text-parchment/70 mb-2">Tetikleyici</label>
                <input type="text" value={spawnTrigger} onChange={(e) => setSpawnTrigger(e.target.value)} placeholder="Örn: Geleneksel yaklaşımlar görünce devreye girer" className="input-classic w-full" />
              </div>
            </div>
            <div className="flex gap-3 justify-end mt-6">
              <button onClick={() => { setShowSpawnDialog(false); setSpawnName(''); setSpawnRole(''); setSpawnGoal(''); setSpawnBlindSpot(''); setSpawnStyle(''); setSpawnTrigger('') }} className="text-parchment/50 hover:text-parchment text-sm font-body px-4 py-2">İptal</button>
              <button
                onClick={() => {
                  if (!spawnName || !spawnRole || !spawnGoal) return
                  const definition = `${spawnName} ${spawnRole} ${spawnGoal} ${spawnBlindSpot || 'Belirtilmedi'} ${spawnStyle || 'Normal'} ${spawnTrigger || 'Belirtilmedi'}`
                  onSendCommand('spawn', { definition })
                  setShowSpawnDialog(false)
                  setSpawnName(''); setSpawnRole(''); setSpawnGoal(''); setSpawnBlindSpot(''); setSpawnStyle(''); setSpawnTrigger('')
                }}
                disabled={!spawnName || !spawnRole || !spawnGoal}
                className="btn-gold disabled:opacity-30 disabled:cursor-not-allowed"
              >Ekle</button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
