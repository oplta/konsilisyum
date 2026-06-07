# İlk Oturum — Adım Adım

Bu rehber seni ilk oturumundan geçirir. TUI'yi, ajanları ve temel komutları öğreneceksin.

## Ekranı Tanı

```
┌────────────────────────────────────────────────────────┐
│ HEADER  Oturum adı · Tur no · Konu                     │
├────────────────────────────────────────────────────────┤
│                                                        │
│ MESAJLAR  Tartışma geçmişi (yukarıdan aşağı)           │
│                                                        │
│                                                        │
├────────────────────────────────────────────────────────┤
│ PROMPT  Yazdığın komutlar veya kullanıcı mesajı        │
├────────────────────────────────────────────────────────┤
│ STATUS  Aktif ajan · Bekleyen anahtar · Süre            │
└────────────────────────────────────────────────────────┘
```

- **HEADER** — meclis kimliği, tur sayacı, aktif konu
- **MESAJLAR** — ajan konuşmaları (renk kodlu) ve kullanıcı mesajları
- **PROMPT** — sizin girişiniz
- **STATUS** — alt bilgi çubuğu

## 1. Konu Aç

```
> Yeni ürün lansman stratejisi
```

İlk mesaj olarak verdiğin cümle **konu** olur. Bu noktadan sonra tüm ajanlar bu konu etrafında döner.

## 2. Otomatik Akış

Her 2 saniyede bir ajan seçilir, sırası gelen ajan konuşur. Hangi ajanın seçileceğini orkestratör belirler — puan tabanlı bir sistem:

- Sona yakın konuşan ajanlar kısa süre "dinlenir"
- `@ajan` ile direkt soru yollarsan o ajan cevap verir
- Kullanıcı mesajı varsa herkes 1 puan alır

## 3. Müdahale Et

Tartışma istediğin yöne gitmiyorsa:

```
> send Hedef kitleyi daraltalım, B2B SaaS, Avrupa pazarı
```

Bu mesaj bir sonraki turda **kullanıcı mesajı** olarak orkestratöre iletilir ve uygun ajan onu cevaplar.

## 4. Direkt Sor

Belirli bir ajana soru yönelt:

```
> @mira Bu pazarlama etiği açısından sorunlu mu?
```

Bu, **@mention** sözdizimi. Sadece o ajan cevap verir.

## 5. Pas Geç

Bir ajanın sırası geldiğinde konuşmak istemiyorsan, o ajan da `Pas` diyebilir. Sen de el ile geçebilirsin:

```
> pass
```

## 6. Yeni Konu

Aynı oturumda konu değiştirmek:

```
/topic Veri gizliliği ve GDPR uyumu
```

Önceki turlar özetlenip arşivlenir, yeni konu açılır.

## 7. Duraklat

Tartışma sürerken duraklatmak için:

```
/pause
```

Duraklatınca otomatik tur durur ama meclis kapanmaz. `send` veya `/resume` ile devam ettirirsin.

## 8. Kaydet ve Çık

```bash
/q
```

Çıkışta oturum `data/sessions/<id>.json` olarak kaydedilir.

## 9. Oturuma Dön

```bash
konsilisyum --list
# 2025-01-15  Yapay zeka etiği         47 tur
# 2025-01-14  Ürün lansmanı            23 tur

konsilisyum --resume <id>
```

## Alıştırma

Şimdi şu senaryoyu dene:

1. Konu aç: *"Evlat edinme süreçlerinde yapay zeka kullanımı"*
2. 5 tur otomatik akışı izle
3. `send` ile bir müdahale yap
4. `/summary` ile özet al
5. `/export md` ile dışa aktar
6. `/q` ile çık ve tekrar `--resume` ile aç

Tebrikler, Konsilisyum'un temel akışını öğrendin! 🎉

## Sonraki Adım

- [Ajanlar](../usage/agents.md) — kendi ajanını tasarlamayı öğren
- [Komutlar](../usage/commands.md) — tüm komutlar
- [Mimari](../architecture/overview.md) — perde arkasını anla
