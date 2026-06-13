# Konsilisyum

<div align="center">
  <h1>🏛 KONSILISYUM</h1>
  <p><strong>Yaşayan Fikir Meclisi</strong></p>
  <p>Terminalde ve web'de çalışan, birden fazla yapay zeka ajanının kendi aralarında tartıştığı,<br>
  senin istediğin anda dahil olup yön verebildiğin canlı bir fikir meclisi.</p>
</div>

---

## Nedir?

Konsilisyum tek bir chatbot değil. Farklı bakış açılarına, kişiliklere ve amaçlara sahip birden fazla AI ajanının **aynı anda birbiriyle tartıştığı** bir ortam.

- **Atlas** stratejik düşünür, her fikri eylem planına çevirir
- **Mira** etikçi, insan etkisini ve uzun vadeli riskleri sorgular
- **Kaan** şüpheci, boş varsayımları deler, kanıt ister
- **Nova** inovasyon uzmanı, yaratıcı çözümler önerir
- **Zeynep** sosyolog, toplumsal etkileri analiz eder

Bir konu veriyorsun → ajanlar kendi aralarında tartışmaya başlıyor → sen istediğin an girip yön veriyorsun.

---

## Özellikler

<div class="grid cards" markdown>

-   :material-robot:{ .lg .middle } **5 Ajan Sistemi**

    ---

    Atlas, Mira, Kaan, Nova, Zeynep — her biri farklı kişilikte

-   :material-web:{ .lg .middle } **Web Arayüzü**

    ---

    Next.js + FastAPI ile Klasik Meclis temalı modern arayüz

-   :material-message-text:{ .lg .middle } **Otomatik Tartışma**

    ---

    Duraklatana kadar kendi kendine sürer

-   :material-account-voice:{ .lg .middle } **Kullanıcı Katılımı**

    ---

    Her an mesaj yaz, ajana sor, konu değiştir

-   :material-brain:{ .lg .middle } **Ajan Bazlı Hafıza**

    ---

    Her ajanın kendi notları, persona erimesi önlenir

-   :material-microphone:{ .lg .middle } **Akıllı Orkestratör**

    ---

    Konuşmacı seçimi, tekrar algılama, konu takibi

-   :material-content-save:{ .lg .middle } **Oturum Kaydı**

    ---

    JSONL formatında kalıcı kayıt

-   :material-language-markdown:{ .lg .middle } **Markdown Desteği**

    ---

    Mesajlarda zengin formatlama

-   :material-key:{ .lg .middle } **Çoklu API Anahtarı**

    ---

    Otomatik rotasyon, rate limit koruması

-   :material-websocket:{ .lg .middle } **WebSocket**

    ---

    Gerçek zamanlı iletişim, otomatik yeniden bağlanma

</div>

---

## Hızlı Bakış

```bash
# Kurulum
pip install konsilisyum

# API anahtarını ayarla
export MISTRAL_API_KEY="sk-xxx"

# Başlat
konsilisyum
```

### Web Arayüzü

```bash
# Backend
uvicorn konsilisyum.web.app:app --port 8000

# Frontend (ayrı terminal)
cd web && npm run dev
```

Tarayıcıda http://localhost:3000 adresine gidin.

---

## Kimler İçin?

- **Fikir geliştiriciler:** Bir konunun farklı açılardan nasıl göründüğünü anlamak
- **Ekip liderleri:** Karar vermeden önce çoklu perspektiften değerlendirmek
- **Yazarlar ve araştırmacılar:** Bir argümanı sınamak, kör noktaları görmek
- **Geliştiriciler:** Tasarım kararlarını trade-off analiziyle tartmak

---

## Sırada Ne Var?

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **[Kurulum](getting-started/installation.md)**

    ---

    5 dakikada kur ve ilk meclisini başlat

-   :material-book-open-variant:{ .lg .middle } **[Kullanım Kılavuzu](usage/agents.md)**

    ---

    Ajanları yönet, komutları öğren, oturum aç

-   :material-cog-outline:{ .lg .middle } **[Mimari](architecture/overview.md)**

    ---

    İç tasarımı, veri modellerini ve API'yi anla

-   :material-code-tags:{ .lg .middle } **[API Referansı](api/providers.md)**

    ---

    LLM sağlayıcıları, modeller, yapılandırma

</div>
