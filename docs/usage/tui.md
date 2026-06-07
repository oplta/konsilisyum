# TUI Kısayolları

Konsilisyum TUI (Terminal User Interface) Rich kütüphanesi üzerine kuruludur. Bu sayfa tüm kısayolları ve görsel ipuçlarını kapsar.

## Ekran Bölgeleri

```
┌────────────────────────────────────────────────────────┐
│ 🏛 KONSİLİSYUM · YZ etiği · Tur 47    ⏸ Duraklatıldı  │  ← Header
├────────────────────────────────────────────────────────┤
│                                                        │
│   [Atlas] Net kararlar almak için kurallar dizisi      │
│            ve sınırlar gerekir.                        │
│                                                        │
│   [Mira]  Peki "zarar" kime göre? Bu kuralları kim     │  ← Mesajlar
│            yazıyor? Mağdurun sesi nerede?              │     (scroll)
│                                                        │
│   [Kaan]  Somut bir örnek verin...                     │
│                                                        │
│                                                        │
├────────────────────────────────────────────────────────┤
│ > send Hedef kitle B2B SaaS_                          │  ← Prompt
├────────────────────────────────────────────────────────┤
│ Atlas · 1.2s · 12,340 tok · 3 ajan · 2 anahtar         │  ← Status
└────────────────────────────────────────────────────────┘
```

## Klavye Kısayolları

### Genel

| Tuş            | İşlev                                  |
|----------------|------------------------------------------|
| `Enter`        | Prompt'u gönder                         |
| `Tab`          | Odak bölgesi değiştir                   |
| `Shift+Tab`    | Önceki odağa dön                        |
| `↑` / `↓`      | Mesaj geçmişinde gez                    |
| `PgUp` / `PgDn`| Sayfa sayfa kaydır                      |
| `Home` / `End` | Başa / sona git                         |
| `Ctrl+L`       | Ekranı temizle (header hariç)           |
| `Ctrl+C`       | Mevcut turu iptal et (çift basış = çık) |
| `Ctrl+D`       | Çıkışı onayla                           |

### Komut Paleti

| Tuş            | İşlev                                  |
|----------------|------------------------------------------|
| `/`            | Slash menüsünü aç                      |
| `?` veya `F1`  | Yardım ekranı                          |
| `F2`           | Ajan listesi                            |
| `F3`           | Konu geçmişi                            |
| `F4`           | İstatistikler                           |
| `F5`           | Özet oluştur                            |
| `Esc`          | Mevcut diyaloğu kapat                   |

### Düzenleme

| Tuş            | İşlev                                  |
|----------------|------------------------------------------|
| `Ctrl+A`       | Satır başına git                        |
| `Ctrl+E`       | Satır sonuna git                        |
| `Ctrl+U`       | Satırı sil                              |
| `Ctrl+K`       | Satır sonuna kadar sil                  |
| `Ctrl+W`       | Son kelimeyi sil                        |
| `Ctrl+←/→`     | Kelime kelime gez                       |

## Renk Kodları

Her ajanın TUI rengi `color` alanıyla belirlenir. Varsayılan palet:

| Ajan   | Renk       | Hex      |
|--------|------------|----------|
| Atlas  | Kırmızı    | `#ff6b6b` |
| Mira   | Mavi       | `#4ecdc4` |
| Kaan   | Sarı       | `#ffe66d` |

Özel ajanlar için hex kodu verebilirsin:

```
/add-agent
...
Renk (#ff6b6b): #a78bfa
```

## Animasyonlar

Ajan konuşurken sağ alttaki **typing indicator** yanıp söner:

```
⠋ Atlas yazıyor...
```

Tur tamamlandığında kısa bir geçiş efekti oynanır (kapatılabilir):

```
/config animations off
```

## Çoklu Pencere

TUI desteklemediği için terminal **panel** araçlarıyla yan yana kullanılabilir:

```bash
# tmux
tmux new-session -s konsilisyum 'konsilisyum'
# Ctrl+B " ile yeni pane, log için

# iTerm2
# Cmd+D ile split, bir tarafta konsilisyum, diğerinde log
```

Log dosyası: `data/logs/konsilisyum.log`.

## Tema

Varsayılan karanlık ve aydınlık uyumludur. Sistem temasını izler.

Manuel:

```
/config theme dark
/config theme light
```

## Erişilebilirlik

- Tüm renkler **sembol + renk** çifti taşır (örn. `[Atlas]` + kırmızı)
- Konuşan ajanın ismi **bold**
- Status çubuğunda **metin** her zaman okunabilir, renk yedek

Ekran okuyucu uyumluluğu için kısmi destek mevcuttur. Geri bildirim için issue açabilirsin.

## Sorun Giderme

### "Emoji görünmüyor"

Terminalin UTF-8 desteklediğinden emin ol:

```bash
echo $LANG
# en_US.UTF-8 veya tr_TR.UTF-8 olmalı
```

### "Renk bozuk"

```bash
export TERM=xterm-256color
```

### "TUI donuyor"

`Ctrl+C` iki kez bas. Kaydedilmemiş turlar kaybolabilir.
