# Hızlı Başlangıç

İlk 5 dakikanda Konsilisyum'u çalıştır ve ilk tartışmayı başlat.

## 1. Kurulumu Doğrula

```bash
konsilisyum --version
# konsilisyum 0.1.0 gibi bir çıktı beklenir
```

## 2. İlk Oturum

```bash
konsilisyum
```

Karşına şöyle bir ekran gelir:

```
╭─────────────────────────────────────────────────────╮
│ 🏛 KONSİLİSYUM  v0.1.0                              │
│ Aktif oturum yok. Bir konu girerek başla.           │
│                                                     │
│ Ajanlar: Atlas (Stratejist) · Mira (Etikçi) ·       │
│          Kaan (Şüpheci)                             │
╰─────────────────────────────────────────────────────╯

> 
```

## 3. Konu Ver

Prompt'a bir konu yaz ve Enter'a bas:

```
> Yapay zeka ajanlarının karar alma süreçlerinde otonomisi
```

Ardından meclis başlar:

```
╭─────────────────────────────────────────────────────╮
│ 🏛 KONSİLİSYUM  Tur 3                               │
│ Konu: Yapay zeka ajanlarının karar alma süreçleri   │
│ Ajanlar: Atlas · Mira · Kaan                         │
│                                                     │
│ [Atlas] Net kararlar alabilmesi için kurallar dizisi│
│         ve sınırlar gerekir. Ajanın durma noktasını │
│         önceden tanımlamalıyız.                     │
│                                                     │
│ [Mira]  Peki "zarar" kime göre? Bu kuralları kim    │
│         yazıyor? Mağdurun sesi nerede?              │
│                                                     │
│ [Kaan]  Somut bir örnek verin. Hangi karar, hangi   │
│         ajan, hangi koşulda? Aksi halde varsayım.   │
╰─────────────────────────────────────────────────────╯
```

## 4. Dahil Ol

Tartışma devam ederken istediğin an mesaj yazabilirsin:

```
> send Kaan'ın itirazı haklı, bir örnek verelim: otonom araç
```

Konsilisyum senin mesajını bir sonraki turda devreye alır.

## 5. Yönet Komutları

`/` ile başlayan komutlar meclisi yönetir. Birkaç temel:

| Komut               | İşlevi                              |
|---------------------|--------------------------------------|
| `/pause`            | Otomatik tartışmayı duraklatır       |
| `/resume`           | Devam ettirir                        |
| `/topic`            | Yeni konu aç                         |
| `/summary`          | Son 20 turun özetini gösterir        |
| `/add-agent`        | Yeni ajan ekler                      |
| `/agents`           | Mevcut ajanları listeler             |
| `/export md`        | Markdown olarak dışa aktarır         |
| `/help`             | Tüm komutları listeler               |

## 6. Çıkış

```bash
/q
# veya Ctrl+C
```

Oturum otomatik kaydedilir. Sonraki açılışta:

```bash
konsilisyum --resume
```

## Sonraki Adımlar

- [İlk Oturum](first-session.md) — adım adım detaylı yürüyüş
- [Ajanlar](../usage/agents.md) — ajan modelini ve kişiliği anla
- [Komutlar](../usage/commands.md) — tüm komutların referansı
