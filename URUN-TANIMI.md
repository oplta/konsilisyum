# Konsilisyum — Ürün Tanımı

## Vizyon

Konsilisyum, terminalde çalışan canlı bir fikir meclisidir. Birden fazla yapay zeka ajanı, birbirinden farklı bakış açılarıyla kendi aralarında sürekli konuşur. Kullanıcı ister sadece izler, ister konuşmaya dahil olur, ister sistemi yapısal olarak yönlendirir.

Tek bir amaçla sınırlandırılmamıştır: karar almak, fikir üretmek, senaryo tartışmak, felsefi sohbet etmek veya rol oyunu deneyimi yaşamak — hepsi mümkündür. Akış, karakterlerin doğası nereye götürürse oraya gider.

Sistem, kullanıcı durdurana kadar kendi kendine devam eder. Konular kendi kendine evrilir. Tartışma canlı, derin ve gerçekçidir.

---

## MVP Kapsamı

### Dahil olanlar

| Bileşen | Detay |
|---------|-------|
| **TUI Arayüzü** | Paneller, durum satırı, ajan listesi, mesaj akışı, renkli çıktı |
| **Ajan Sistemi** | Sabit başlangıç ajanları + kullanıcı tarafından ekleme/çıkarma/değiştirme |
| **Orkestratör** | Tur yönetimi, konuşmacı seçimi, tekrar kontrolü, konu takibi |
| **Hafıza** | Ajan başına kapsamlı hafıza + ortak konuşma geçmişi |
| **Kullanıcı Katılımı** | Geniş müdahale: mesaj, yapısal komutlar, ajan yönetimi, rol atama |
| **Konu Yönetimi** | Başlangıç konusu + kendi kendine evrilme |
| **Çıktı Tipleri** | Canlı tartışma (birincil), özet, karar taslağı, yapılacaklar listesi, karşıt görüş haritası |
| **Oturum Kaydı** | JSONL tabanlı kalıcı kayıt |
| **API Yönetimi** | Çoklu API anahtarı desteği, ajan başına anahtar atama, rotasyon |

### Dahil olmayanlar (Faz 2+)

- Uzun dönem vektör veritabanı
- Web tarama / dış araç kullanımı
- Ajanların kendi kendine yeni hedef üretmesi
- Sesli veya grafik arayüz
- Ajanlar arası gizli mesajlaşma
- Gelişmiş oylama / anayasa sistemi

---

## Ajan Modeli

Her ajan şu özelliklerden oluşur:

```
isim:          Atlantis
rol:           Stratejist
amaç:          Fikirleri uygulanabilir eylem planına çevirmek
kör nokta:     İnsan maliyetini küçümseme eğilimi
stil:          Kısa, net, karar odaklı
tetikleyici:   Belirsizlik görünce çerçeve kurar
api_key:       mistral-key-xxx   # Ajan bazlı API anahtarı
hafıza:        []                 # Ajan özel hafıza (anahtar anlar, kararlar, izlenimler)
```

### Varsayılan Başlangıç Ajanları

| Ajan | Rol | Amaç | Kör Nokta | Stil |
|------|-----|------|-----------|------|
| **Atlas** | Stratejist | Fikirleri uygulanabilir plana çevirmek | İnsan maliyetini küçümseme | Kısa, net, karar odaklı |
| **Mira** | Etikçi | İnsan etkisini ve uzun vadeli riskleri sorgulamak | Aşırı temkinlilik | Sakin, analitik, uyarıcı |
| **Kaan** | Şüpheci | Boş varsayımları ve romantik fikirleri delmek | Yapıcı olmadan eleştirmek | Sert, kısa, meydan okuyan |

Kullanıcı bunları değiştirebilir, yenisini ekleyebilir, çıkarabilir.

---

## Hafıza Mimarisi

İki katmanlı hafıza:

### 1. Ortak Konuşma Geçmişi
- Tüm mesajlar kronolojik sırayla
- Son N mesaj her turda bağlama dahil
- JSONL dosyasına kalıcı yazım

### 2. Ajan Bazlı Hafıza
- Her ajanın kendi "anahtar anlar" listesi
- Önemli bulduğu argümanları, katkıları, itirazları kaydeder
- Tartışmanın gidişatına dair kişisel izlenimler
- Bu hafıza ajanın prompt'una eklenir → persona erimesini önler

### 3. Periyodik Özet
- Her X turda bir, konuşma özetlenir
- Özet ortak hafızada saklanır
- Bağlam penceresi taşmasını önler

---

## API Anahtarı Yönetimi

```
api_keys:
  - key: "mistral-xxx1"
    assigned: "Atlas"
  - key: "mistral-xxx2"
    assigned: "Mira"
  - key: "mistral-xxx3"
    assigned: "Kaan"
  - key: "mistral-xxx4"
    pool: true          # Havuz anahtarı, yeni ajanlara atanır
```

Strateji:
- Her ajan mümkünse kendi anahtarını kullanır
- Anahtar biterse veya rate limit'e düşerse havuzdan çekilir
- Rotasyon: sıralı veya rastgele
- 50+ anahtar olduğu için maliyet ve rate limit pratikte sorun değil

---

## TUI Tasarımı

```
┌─────────────────────────────────────────────────────────────────┐
│  🏛 KONSILISYUM   Konu: "Şehirlerde yapay zekâ ile yönetişim"  │
│  Durum: ● ÇALIŞIYOR   Tur: 24   Ajanlar: Atlas, Mira, Kaan    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Tur 22] Mira (Etikçi):                                       │
│    Bu yaklaşımın temel sorunu, karar şeffaflığını               │
│    tamamen algoritmaya devretmesi. Vatandaşın itiraz             │
│    mekanizması kalmaz mı?                                       │
│                                                                 │
│  [Tur 23] Kaan (Şüpheci):                                      │
│    Mira haklı ama aşırı temkinli. "Tamamen" kelimesini          │
│    kullanmak manipülatif. Hiçbir sistem yüzde yüz               │
│    şeffaf değildi zaten. Sorun değil bu.                        │
│                                                                 │
│  [Tur 24] Atlas (Stratejist):                                   │
│    İkinizin de noktasını alırsam: hibrit bir model              │
│    gerekiyor. Algoritmik öneri + insan onay katmanı.            │
│    Bunun için üç aşamalı bir çerçeve kurabilirim.               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Ajanlar:  ■ Atlas  ■ Mira  ■ Kaan     │  Sıradaki: Mira      │
├─────────────────────────────────────────────────────────────────┤
│  > _                                                            │
└─────────────────────────────────────────────────────────────────┘
```

### TUI Bileşenleri

| Bileşen | Açıklama |
|---------|----------|
| **Başlık çubuğu** | Konsil adı, aktif konu, durum (çalışıyor/duraklatıldı), tur sayısı, ajan listesi |
| **Mesaj alanı** | Kaydırılabilir tartışma akışı, her mesaj ajan rengiyle |
| **Durum çubuğu** | Ajan renk göstergeleri, sıradaki konuşmacı |
| **Girdi satırı** | Kullanıcı komutları ve mesajlar |

---

## Komut Seti

### Temel Komutlar

| Komut | Açıklama |
|-------|----------|
| `/help` | Tüm komutları göster |
| `/pause` | Otomatik akışı duraklat |
| `/resume` | Akışı devam ettir |
| `/quit` | Konsilden çık |
| `/status` | Oturum durumunu göster |

### Katılım Komutları

| Komut | Açıklama |
|-------|----------|
| `/say mesaj` | Tartışmaya mesaj bırak (tüm ajanlar görür) |
| `/ask AjanAdı mesaj` | Belirli bir ajana soru sor |
| `/think mesaj` | Mesajı sisteme enjekte et, sanki bir ajan söylemiş gibi |

### Konu Komutları

| Komut | Açıklama |
|-------|----------|
| `/topic yeni konu` | Konuyu değiştir |
| `/evolve` | Ajanların konuyu kendi yönüne evirmesine izin ver |
| `/focus` | Konuyu merkeze geri çek |

### Ajan Yönetimi

| Komut | Açıklama |
|-------|----------|
| `/agents` | Ajan listesini ve durumlarını göster |
| `/spawn isim rol amaç...` | Yeni ajan ekle |
| `/kick AjanAdı` | Ajanı çıkar |
| `/mute AjanAdı` | Ajanı sustur (dinler ama konuşmaz) |
| `/unmute AjanAdı` | Ajanı geri aç |
| `/profile AjanAdı` | Ajan profilini göster |
| `/edit AjanAdı alan değer` | Ajan özelliğini değiştir |

### Rol Atama

| Komut | Açıklama |
|-------|----------|
| `/role hakem` | Kullanıcıya hakem rolü ver (söz hakkı dağıtımı) |
| `/role moderatör` | Kullanıcıya moderatör rolü ver |
| `/role gözlemci` | Kullanıcı sadece izler |
| `/role katılımcı` | Kullanıcı aktif katılımcı |

### Çıktı Komutları

| Komut | Açıklama |
|-------|----------|
| `/summary` | Tartışma özeti |
| `/decisions` | Karar taslakları |
| `/actions` | Yapılacaklar listesi |
| `/map` | Karşıt görüş haritası |
| `/export format` | Oturumu dışa aktar (jsonl, md, txt) |

### Sistem Komutları

| Komut | Açıklama |
|-------|----------|
| `/save` | Oturumu kaydet |
| `/load dosya` | Oturum yükle |
| `/keys` | API anahtarı durumunu göster |
| `/config` | Yapılandırma |

---

## Orkestratör Mantığı

Orkestratör her turda şu kararları alır:

```
1. Kullanıcı mesajı var mı?
   → EVET: Kullanıcı mesajı öncelikli, ajanlar buna tepki verir
   → HAYIR: Devam

2. Konu hâlâ geçerli mi?
   → Evolve modundaysa: ajanların doğal yönelimine izin ver
   → Focus modundaysa: konu dışına çıkmayı engelle

3. Sonraki konuşmacı kim?
   → Son konuşmacıya cevap verilmesi gereken biri var mı?
   → Uzun süredir susan bir ajan var mı?
   → Konuya en ilgili ajan kim?
   → Rastgeleliğe azıcık yer ver (tahmin edilebilirliği kır)

4. Mesaj üretmeli mi yoksa pas mı?
   → Son 3 mesajda söyleyecek yeni bir şey var mı?
   → Tekrar algılandıysa pas geç
   → Ajan susturulmuşsa atla

5. Özet zamanı mı?
   → Her 15-20 turda bir otomatik özet tetikle
   → Bağlam penceresi dolmak üzereyse özetle sıkıştır

6. Duraklatılmış mı?
   → EVET: Bekle, kullanıcı komutunu bekle
   → HAYIR: Sonraki tur
```

### Tekrar Önleme

- Son 5 mesajın embedding benzerliğini kontrol et (basit: anahtar kelime örtüşmesi)
- %70+ benzerlik → pas geç veya farklı açı iste
- Ajan bazlı "zaten söylediklerim" takibi

### Persona Erimesi Önleme

- Her turda ajan profili prompt'a tam olarak eklenir
- Ajan bazlı hafıza, kişisel perspektifi korur
- Stil talimatları her prompt'ta tekrar edilir

---

## Kullanıcı Akışı

```
1. Kullanıcı terminali açar: python konsilisyum.py

2. Karşılama ekranı:
   ┌──────────────────────────────┐
   │  🏛 KONSILISYUM              │
   │  Yaşayan Fikir Meclisi       │
   │                              │
   │  Konsil üyeleri yüklendi:    │
   │  ■ Atlas (Stratejist)        │
   │  ■ Mira (Etikçi)            │
   │  ■ Kaan (Şüpheci)           │
   │                              │
   │  Konu girin veya /load ile  │
   │  önceki oturumu yükleyin:    │
   │  > _                        │
   └──────────────────────────────┘

3. Konu girilir: "Yapay zekâ eğitimi geleceği nasıl şekillendirir?"

4. TUI açılır, akış başlar.

5. Kullanıcı izler, müdahale eder, veya yönetir.

6. /summary, /decisions, /actions ile çıktı alınır.

7. /quit ile çıkılır, oturum otomatik kaydedilir.
```

---

## Teknik Yığın

| Katman | Teknoloji |
|--------|-----------|
| Dil | Python 3.11+ |
| TUI | Textual (rich terminal UI framework) |
| LLM API | Mistral AI (mistral-small / mistral-medium) |
| Depolama | JSONL (konuşma kaydı) + JSON (yapılandırma) |
| Yapılandırma | YAML veya TOML |
| Paketleme | pip installable, tek girdi noktası |

### Proje Yapısı

```
konsilisyum/
├── konsilisyum/
│   ├── __init__.py
│   ├── main.py              # Girdi noktası
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py           # Textual TUI uygulaması
│   │   ├── widgets.py       # Özel widget'lar
│   │   └── theme.py         # Renk ve stil
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py         # Ajan modeli ve yönetimi
│   │   ├── orchestrator.py  # Tur mantığı ve karar verme
│   │   ├── memory.py        # Hafıza katmanı
│   │   ├── session.py       # Oturum yönetimi
│   │   └── topic.py         # Konu yönetimi
│   ├── api/
│   │   ├── __init__.py
│   │   ├── mistral.py       # Mistral API istemcisi
│   │   └── keypool.py       # API anahtarı havuzu ve rotasyon
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── parser.py        # Komut ayrıştırıcı
│   │   └── handler.py       # Komut işleyici
│   ├── output/
│   │   ├── __init__.py
│   │   ├── summary.py       # Özet üretici
│   │   ├── decisions.py     # Karar taslakları
│   │   ├── actions.py       # Yapılacaklar listesi
│   │   └── exporter.py      # Dışa aktarma
│   └── config/
│       ├── __init__.py
│       ├── settings.py      # Yapılandırma yönetimi
│       └── defaults.py      # Varsayılan ajanlar ve ayarlar
├── data/
│   ├── sessions/            # Oturum kayıtları (JSONL)
│   └── config.yaml          # Yapılandırma dosyası
├── tests/
│   ├── test_agent.py
│   ├── test_orchestrator.py
│   ├── test_memory.py
│   └── test_commands.py
├── pyproject.toml
├── README.md
└── URUN-TANIMI.md           # Bu dosya
```

---

## İlk 3 İterasyon Planı

### İterasyon 1: Çekirdek Prototip

**Hedef:** Ajanlar birbirinden farklı konuşuyor ve dönüşümlü tartışma akıyor.

- Python projesi iskeleti
- Mistral API istemcisi (tek anahtar ile)
- 3 sabit ajan tanımı
- Basit tur döngüsü: sırayla konuşma
- Basit terminal çıktısı (print bazlı, TUI yok henüz)
- Temel komutlar: `/pause`, `/resume`, `/say`, `/quit`
- JSONL oturum kaydı

**Doğrulama:** 3 ajan sırayla konuşuyor, birbirinden ayırt edilebiliyor, `/pause` ve `/say` çalışıyor.

### İterasyon 2: Orkestratör + Hafıza + TUI

**Hedef:** Akış akıllı, hafıza var, arayüz güzel.

- Orkestratör: akıllı konuşmacı seçimi, tekrar algılama, konu takibi
- İki katmanlı hafıza: ortak geçmiş + ajan bazlı
- Textual TUI: başlık, mesaj alanı, durum çubuğu, girdi satırı
- Geniş komut seti: `/ask`, `/topic`, `/summary`, `/agents`, `/spawn`, `/kick`, `/mute`
- API anahtarı havuzu: ajan bazlı atama, rotasyon
- Periyodik özet mekanizması

**Doğrulama:** 10 dakika sadece izlenebiliyor, tekrar olmuyor, kullanıcı müdahalesi akışı değiştiriyor, TUI okunabilir.

### İterasyon 3: Kalite + Çıktı + Ürünleşme

**Hedef:** Ürün kalitesinde deneyim, zengin çıktı, oturum yönetimi.

- Persona erimesi önleme iyileştirmesi
- `/decisions`, `/actions`, `/map` çıktı komutları
- `/role` sistemi: hakem, moderatör, gözlemci, katılımcı
- Oturum kaydetme/yükleme
- `/export` ile dışa aktarma
- Yapılandırma dosyası ile özelleştirme
- Hata yönetimi ve edge case'ler
- README ve belgelendirme

**Doğrulama:** Yeni bir kullanıcı belgeyi okuyup çalıştırabiliyor, tüm komutlar kararlı, oturum kaydı güvenilir, çıktılar anlamlı.

---

## Güvenlik Frenleri

| Fren | Değer |
|------|-------|
| Maksimum mesaj uzunluğu | 500 kelime |
| Bağlam penceresi | Son 30 mesaj + özet |
| Otomatik özet aralığı | Her 20 tur |
| Maksimum otomatik tur (kullanıcı müdahalesiz) | 50 tur |
| Tekrar eşiği | %70 benzerlik → pas |
| Rate limit | Ajan başına saniyede max 1 istek |
| Token limiti | İstem başına max 2000 token |

---

## Başarı Kriterleri

- [ ] Kullanıcı 10 dakika sadece izleyip sıkılmadan akışı takip edebiliyor
- [ ] Ajanlar birbirinden ayırt edilebiliyor (farklı ses tonu, farklı bakış açısı)
- [ ] Sistem sürekli kendini tekrar etmiyor
- [ ] Kullanıcı müdahalesi konuşmanın yönünü gerçekten değiştiriyor
- [ ] Bir tur sonra kullanıcı etkisi kaybolmuyor
- [ ] Oturum sonunda işe yarar bir özet çıkıyor
- [ ] TUI okunabilir ve düşük sürtünmeli
- [ ] 50+ API anahtarı sorunsuz rotasyon yapıyor
- [ ] Ajan ekleme/çıkarma anında çalışıyor
