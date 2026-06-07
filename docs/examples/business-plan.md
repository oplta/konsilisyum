# Örnek: İş Planı Tartışması

Yeni bir SaaS ürününün go/no-go kararını Konsilisyum ile tartış.

## Senaryo

Bir B2B SaaS fikrin var: **"Küçük ekipler için AI destekli backlog yönetimi"**.

Tek başına karar vermek zor. Konsilisyum'a üç açıdan baktır:

- **Atlas (Stratejist)** — pazar, rakip, finansal fizibilite
- **Mira (Etikçi)** — insan etkisi, veri gizliliği, yanlılık riski
- **Kaan (Şüpheci)** — varsayımları test et, kanıt iste

## Örnek Oturum

### Kurulum

```bash
konsilisyum --new "BacklogAI go/no-go"
```

### Konu

```
> Küçük ekipler (5-15 kişi) için AI destekli backlog yönetimi SaaS ürünü.
> Go/no-go kararı arıyorum. 6 ay içinde MVP, 12 ay içinde 100 müşteri.
```

### Tur 1-3: Atlas ve Mira'nın açılışı

```
[Atlas] Net birim ekonomisi lazım. ARPU hedefi ne? 50$/ay mı 200$/ay mı?
        Bu, kanal stratejisini ve churn toleransını tamamen değiştirir.
        Ayrıca rakipler — Jira, Linear, Notion — zaten güçlü. Diferansiyel?

[Mira]  "AI destekli" dediğinde hangi kararları veriyor? Otomatik
        önceliklendirme mi, scope kesme mi, sprint atama mı? Her biri
        farklı insan etkisi taşır. Biri iş güvencesini tehdit edebilir.

[Kaan]  "Küçük ekipler" heterojen. Solo geliştirici mi, 15 kişilik
        tasarım stüdyosu mu? Her ikisinin ihtiyacı farklı. Somut
        persona verin.
```

### Müdahale 1: Netleştir

```
> send Hedef: 10-50 çalışanlı teknoloji şirketleri, ayda 100$ ARPU,
>          Jira'ya rakip değil eklenti olarak konumlanma
```

### Tur 4-7: Netleşen Tartışma

```
[Atlas] 100$ ARPU ile 100 müşteri = 120K$/yıl ARR. Makul ama düşük.
        LTV/CAC oranı için churn %5'in altında olmalı. Pazarlama kanalı
        — content marketing, ürün liderliği (PLG)?

[Mira]  "AI önceliklendirme" hangi veriyle? Geçmiş sprint verileri
        kişisel performans değerlendirmesine dönebilir. GDPR uyumu?

[Kaan]  "Müşteri 100'e ulaşır" — hangi kanıt? Pilot yapıldı mı?
        Waitlist var mı? Yoksa 12 aylık plan, 100 müşteri değil
        0 müşteriyle sonuçlanabilir.
```

### Müdahale 2: Pilot Bilgisi

```
> send 3 şirketle pilot konuşması yaptım, 2'si "Jira'ya eklenirse
>          ilginç" dedi, 1'i "kendi çözdük" dedi. Henüz waitlist yok.
```

### Tur 8-12: Kanıt Tartışması

```
[Atlas] 2/3 pozitif konuşma = %67 ilgi sinyali. 50 şirkete
        genişlet, %30 dönüşüm hedefle. Bu MVP doğrulaması için yeterli.

[Mira]  Pilot konuşmaları vaat göstergesi mi? Erken aşama "ilginç"
        demek ucuz. Gerçek test: 5 şirketten 3 aylık gerçek kullanım
        verisi iste. Bu etik sorumluluk.

[Kaan]  "Jira'ya eklenti" — Jira API'si var ama üçüncü parti
        uygulama onay süreci uzun. Marketplace'e girmek 6 ay+.
        Zaman çizelgesi gerçekçi mi?
```

### Özet ve Karar

```
/summary 12
```

Çıktı:

```
Konu: BacklogAI go/no-go

Önemli noktalar:
- ARPU 100$ ile 100 müşteri hedefi fizibilite sınırında
- "Jira eklentisi" konumlanması pazarı küçültüyor, bağımsız ürün
  olmalı mı tartışıldı
- 3 pilot konuşması yeterli kanıt değil, 5+ şirket pilot gerekli
- GDPR ve AI karar şeffaflığı etik açıdan açık soru
- Jira marketplace zaman çizelgesi gerçekçi değil

Karar: GO ama koşullu
  - Önce bağımsız MVP (Jira eklentisi değil)
  - 5 şirketle 3 aylık pilot
  - Veri kullanım şeffaflığı politikası
  - Churn < %5 kanıtı olmadan ölçeklendirme yok
```

### Dışa Aktar

```
/export-to backlogai-karar.md
```

## Alınan Dersler

1. **Çoklu perspektif değerli:** tek başına "harika fikir" diye düşüneceğin şey, Kaan'ın şüpheciliğiyle delik deşik edildi.
2. **Pilot veri azdı:** 3 konuşma değil, gerçek kullanım verisi lazım.
3. **Etik boyut geç:** "AI karar veriyor" demek yetmez, şeffaflık gerek.
4. **Zaman çizelgesi gerçekçi değildi:** 6 ayda MVP, sonra marketplace 6 ay daha = 12 ay pazara çıkmadan.

## Komut Dosyası

Tekrar üretmek için:

```bash
konsilisyum --new "BacklogAI go/no-go"
```

```
> [konu metni]
> send [müdahale 1]
> send [müdahale 2]
/summary 12
/export-to karar.md
/q
```

## Sonraki Örnek

- [Etik Senaryo](ethics.md) — otonom karar tartışması
- [Teknik Mimari](tech-design.md) — yazılım kararları
