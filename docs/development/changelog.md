# Sürüm Notları

Konsilisyum'un sürüm geçmişi. [Semver](https://semver.org/) uyumlu.

## [Dev] — Geliştirme Aşamasında

### Eklenen
- LLM abstraction layer (Issue #58)
- Yapısal loglama altyapısı (Issue #59)
- GitHub Actions CI/CD (Issue #60)
- 17 entegrasyon testi (Issue #61)
- MkDocs dokümantasyon sitesi (Issue #62)

### Planlanan
- Vektör tabanlı hafıza (cross-session)
- Web UI (Textual → Web export)
- Plugin sistemi (üçüncü parti komutlar)

---

## [0.1.0] — 2025-01-15

İlk genel sürüm. Temel meclis işlevi çalışır durumda.

### Eklenen

#### Çekirdek
- Üç varsayılan ajan (Atlas, Mira, Kaan)
- Orkestratör (puan tabanlı konuşmacı seçimi)
- Hafıza yönetimi (bağlam penceresi + ajan hafızası + özet)
- Oturum kaydet/yükle (JSON)
- Çoklu konu desteği
- Tekrar algılama (Jaccard)
- Otomatik duraklatma (max_auto_turns)

#### API
- Mistral AI entegrasyonu
- OpenAI entegrasyonu
- Anthropic entegrasyonu
- Ollama (yerel) entegrasyonu
- KeyPool — çoklu anahtar rotasyonu
- Otomatik retry + üstel geri çekilme

#### TUI
- Rich tabanlı modern arayüz
- Renk kodlu ajanlar
- Typing indicator
- Klavye kısayolları
- Slash komut paleti

#### Komutlar (28+)
- Oturum: `/new`, `/pause`, `/resume`, `/list`, `/q`
- Konu: `/topic`, `/topics`, `/topic-mode`
- Ajan: `/agents`, `/add-agent`, `/mute`, `/unmute`, `/remove`
- Mesaj: `send`, `pass`, `@ajan`
- Analiz: `/summary`, `/stats`, `/replay`
- Dışa aktar: `/export md|jsonl|txt|html`
- Yapılandırma: `/config`, `/reload-agents`
- Anahtar: `/keys`, `/keys-add`, `/keys-remove`
- Meta: `/help`, `/version`, `/debug`

#### Test
- 38+ birim testi
- Mock'lı HTTP testleri (respx)
- Coverage %70+

### Bilinen Sınırlamalar
- Çapraz oturum hafıza yok
- Çoklu LLM sağlayıcısı aynı anda kullanılamaz
- Web arayüzü yok
- Mobil uyumlu değil (terminal zorunlu)

---

## [0.0.x] — Alpha (2024)

Erken geliştirme aşamaları, kamuya açılmadı.
