<div align="center">

# 🏛 KONSILISYUM

**Yaşayan Fikir Meclisi**

Terminalde ve web'de çalışan, birden fazla yapay zeka ajanının kendi aralarında tartıştığı,
senin istediğin anda dahil olup yön verebildiğin canlı bir fikir meclisi.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-166%20passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

</div>

---

## 🎯 Nedir?

Konsilisyum tek bir chatbot değil. Farklı bakış açılarına, kişiliklere ve amaçlara sahip birden fazla AI ajanının **aynı anda birbiriyle tartıştığı** bir ortam.

- **Atlas** stratejik düşünür, her fikri eylem planına çevirir
- **Mira** etikçi, insan etkisini ve uzun vadeli riskleri sorgular
- **Kaan** şüpheci, boş varsayımları deler, kanıt ister
- **Nova** inovasyon uzmanı, yaratıcı çözümler ve geleceğe dönük teknolojiler önerir
- **Zeynep** sosyolog, toplumsal etkileri ve kültürel dinamikleri analiz eder

Bir konu veriyorsun → ajanlar kendi aralarında tartışmaya başlıyor → sen istediğin an girip yön veriyorsun.

---

## ✨ Özellikler

- **🤖 5 Ajan Sistemi** — Atlas, Mira, Kaan, Nova, Zeynep — her biri farklı kişilikte
- **🌐 Web Arayüzü** — Next.js + FastAPI ile Klasik Meclis temalı modern arayüz
- **🔄 Otomatik Tartışma Akışı** — Duraklatana kadar kendi kendine sürer
- **🗣 Kullanıcı Katılımı** — Her an mesaj yaz, ajana sor, konu değiştir
- **🧠 Ajan Bazlı Hafıza** — Her ajanın kendi notları, persona erimesi önlenir
- **🎭 Orkestratör** — Akıllı konuşmacı seçimi, tekrar algılama, konu takibi
- **💾 Oturum Kaydı** — JSONL formatında kalıcı kayıt
- **📝 Markdown Desteği** — Mesajlarda zengin formatlama
- **⚡ 28+ Terminal Komutu** — Ajan yönetimi, özet, dışa aktarma ve daha fazlası
- **🔑 Çoklu API Anahtarı** — Otomatik rotasyon, rate limit koruması
- **🔗 WebSocket** — Gerçek zamanlı iletişim, otomatik yeniden bağlanma

---

## 🚀 Kurulum

```bash
git clone https://github.com/oplta/konsilisyum.git
cd konsilisyum
pip install -e .
```

### Frontend Kurulumu

```bash
cd web
npm install
```

### API Anahtarı

`.env` dosyası oluşturun:

```env
MISTRAL_API_KEYS=anahtar1,anahtar2,anahtar3
MISTRAL_MODEL=mistral-large-latest
```

Tek anahtar da yeterli:

```env
MISTRAL_API_KEYS=tek_bir_anahtar
```

---

## 💻 Kullanım

### Web Arayüzü

```bash
# Backend
uvicorn konsilisyum.web.app:app --port 8000

# Frontend (ayrı terminal)
cd web && npm run dev
```

Tarayıcıda http://localhost:3000 adresine gidin.

### Terminal (CLI)

```bash
# Konu ile başlat
konsilisyum "Yapay zeka eğitimi geleceği nasıl şekillendirir?"

# Konu sorarak başlat
konsilisyum

# Textual TUI ile başlat
konsilisyum --tui "Yapay zeka eğitimi geleceği nasıl şekillendirir?"
```

### Tartışma Akışı

```
[Tur 0] Atlas (Stratejist):
  Çerçeve kuralım: erişim, özelleştirme ve etik. Üç eksen...

[Tur 1] Mira (Etikçi):
  Atlas'ın çerçevesinde güç asimetrisi riski örtük kalıyor...

[Tur 2] Kaan (Şüpheci):
  Mira, "güç asimetrisi" lafını havada bırakma. Çözümün ne?

[Tur 3] Nova (İnovasyon Uzmanı):
  Dijital okuryazarlık programları ile toplumsal dönüşüm...

[Tur 4] Zeynep (Sosyolog):
  Teknoloji adoption sürecinde kültürel direnç unsurları...
```

---

## ⌨️ Komutlar

### Temel

| Komut | Açıklama |
|-------|----------|
| `/help` | Tüm komutları göster |
| `/pause` | Akışı duraklat |
| `/resume` | Akışı devam ettir |
| `/quit` | Konsilden çık |
| `/status` | Oturum durumu |

### Katılım

| Komut | Açıklama |
|-------|----------|
| `mesaj` veya `/say mesaj` | Tartışmaya mesaj bırak |
| `/ask Atlas stratejin ne?` | Belirli bir ajana soru sor |
| `/think mesaj` | Sessizce mesaj enjekte et |

### Ajan Yönetimi

| Komut | Açıklama |
|-------|----------|
| `/agents` | Ajan listesini göster |
| `/spawn Kaan Şüpheci Fikir delmek` | Yeni ajan ekle |
| `/kick Kaan` | Ajan çıkar |
| `/mute Kaan` | Ajan sustur |
| `/unmute Kaan` | Ajan geri aç |
| `/profile Atlas` | Ajan profilini göster |
| `/edit Atlas role Vizyoner` | Ajan özelliğini değiştir |

### Konu

| Komut | Açıklama |
|-------|----------|
| `/topic yeni konu` | Konu değiştir |
| `/evolve` | Konunun evrilmesine izin ver |
| `/focus` | Konuyu merkeze kilitle |

### Çıktı

| Komut | Açıklama |
|-------|----------|
| `/summary` | Tartışma özeti |
| `/decisions` | Karar taslakları |
| `/actions` | Yapılacaklar listesi |
| `/map` | Karşıt görüş haritası |

### Sistem

| Komut | Açıklama |
|-------|----------|
| `/save` | Oturumu kaydet |
| `/load` | Oturum yükle veya listele |
| `/export md` | Oturumu dışa aktar (md/jsonl/txt) |
| `/keys` | API anahtarı durumu |
| `/role hakem` | Kullanıcı rolü ata |

---

## 🏗 Mimari

```
konsilisyum/
├── core/
│   ├── models.py          # Veri modelleri (Agent, Message, Topic, Session)
│   ├── orchestrator.py    # Tur döngüsü, konuşmacı seçimi, prompt yönetimi
│   ├── memory.py          # Paylaşımlı geçmiş + ajan bazlı hafıza
│   ├── session.py         # JSONL oturum kaydı ve yükleme
│   └── errors.py          # Hata sınıfları hiyerarşisi
├── api/
│   ├── mistral.py         # Mistral AI API istemcisi + retry
│   ├── llm.py             # Ortak LLM arayüzü + hata sınıfları
│   └── keypool.py         # Çoklu anahtar havuzu + rotasyon
├── commands/
│   ├── parser.py          # Komut ayrıştırıcı
│   └── handler.py         # 28 komut işleyici
├── config/
│   ├── settings.py        # YAML + .env yapılandırma
│   └── defaults.py        # Varsayılan ajan tanımları (5 ajan)
├── web/
│   ├── app.py             # FastAPI uygulaması
│   ├── routes.py          # REST API endpointleri
│   ├── websocket.py       # WebSocket handler
│   └── schemas.py         # Pydantic şemaları
├── tui/
│   ├── app.py             # Textual TUI uygulaması
│   └── theme.tcss         # TUI stil dosyası
├── bootstrap.py           # CLI, TUI ve Web için ortak başlatma
├── main.py                # CLI giriş noktası
└── tests/                 # 166 test

web/                       # Next.js Frontend
├── app/
│   ├── page.tsx           # Ana sayfa (konu seçimi)
│   └── session/[id]/      # Oturum sayfası
├── components/
│   ├── AgentCards.tsx      # Ajan kartları
│   ├── MessageStream.tsx   # Mesaj akışı
│   ├── MessageCard.tsx     # Mesaj kartı (Markdown)
│   ├── BackstagePanel.tsx  # Kontrol paneli
│   ├── QuickCommands.tsx   # Hızlı komutlar
│   └── Header.tsx          # Üst bilgi çubuğu
├── hooks/
│   └── useWebSocket.ts    # WebSocket hook'u
├── stores/
│   └── sessionStore.ts    # Zustand state yönetimi
└── lib/
    └── api.ts             # REST API yardımcıları
```

---

## 🧪 Test

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## 📋 Ajanlar

| Ajan | Rol | Amaç | Kör Nokta |
|------|-----|------|-----------|
| **Atlas** | Stratejist | Fikirleri eylem planına çevirmek | İnsan maliyetini küçümseme |
| **Mira** | Etikçi | İnsan etkisini ve riskleri sorgulamak | Aşırı temkinlilik |
| **Kaan** | Şüpheci | Boş varsayımları delmek | Yapıcı olmadan eleştirmek |
| **Nova** | İnovasyon Uzmanı | Yaratıcı çözümler önermek | Pratik zorlukları göz ardı etme |
| **Zeynep** | Sosyolog | Toplumsal etkileri analiz etmek | Bireysel ajansı hafife alma |

`/spawn` ile yeni ajan ekleyebilir, `/edit` ile değiştirebilirsin.

---

## 🛡 Güvenlik Frenleri

| Fren | Değer |
|------|-------|
| Bağlam penceresi | Son 8 mesaj + özet |
| Otomatik özet aralığı | Her 20 tur |
| Maksimum otomatik tur | 50 (sonra duraklar) |
| Tekrar eşiği | %70 benzerlik → pas |
| Token limiti | İstem başına 4096 token |

---

## 📄 Dokümantasyon

- [Ürün Tanımı](URUN-TANIMI.md) — MVP kapsamı, kullanıcı akışı, yol haritası
- [Teknik Tasarım](TEKNIK-TASARIM.md) — Detaylı mimari, prompt tasarımı, veri yapıları

---

## 🗺 Yol Haritası

- [x] **Faz 1:** Çekirdek prototip — 3 ajan, tur döngüsü, temel komutlar
- [x] **Faz 2:** Orkestratör iyileştirme, Textual TUI, oturum yükleme
- [x] **Faz 3:** Karar taslakları, yapılacaklar listesi, dışa aktarma, rol sistemi
- [x] **Faz 4:** Vektör hafıza (SQLite + numpy), API anahtarı havuzu iyileştirmeleri
- [x] **Faz 5:** Web arayüzü (Next.js + FastAPI), 5 ajan, WebSocket, Markdown
- [ ] **Faz 6:** Web arama (Tavily), gelişmiş TUI, uzun dönem hafıza

---

<div align="center">

**Konsilisyum** — Fikirler çarpışsın, en iyisi sağ kalsın.

</div>
