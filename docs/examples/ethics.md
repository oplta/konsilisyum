# Örnek: Etik Senaryo — Otonom Araç

Sokratik sorgulama yöntemiyle bir etik ikilemi tartış.

## Senaryo

**Trolley problem varyantı:** Otonom araç frenleri aniden bozuluyor. Önünde 5 yayaya çarpacak. Sağa kırarsa tek bir yayaya çarpacak. Araç ne yapmalı?

Bu klasik bir problem. Konsilisyum ile farklı boyutları ortaya çıkarabilirsin.

## Ajanlar

### Sokrates (Sorgulayıcı)
- **Hedef:** Varsayımları sorgulamak, derin düşünmeye zorlamak
- **Kör nokta:** Bazen felç edici sorular sorar, karar çıkmaz
- **Üslup:** Soru sorarak ilerler, "neden?" diye ısrar eder

### Pragma (Sonuççu)
- **Hedef:** Pratik sonuç odaklı, hayat kurtarma
- **Kör nokta:** Etik incelikleri göz ardı edebilir
- **Üslup:** Net, eylem odaklı, istatistik verir

### Koruyucu (Vicdan)
- **Hedef:** Mağdurun gözünden bakmak, insan onuru
- **Kör nokta:** Karar veremeyebilir, sürekli empati kurar
- **Üslup:** Yumuşak, anlatı ağırlıklı, örnekler verir

## Örnek Oturum

### Konu

```
> Otonom araç frenleri bozuluyor: 5 yaya ölümü veya 1 yaya ölümü.
> Araç hangisini seçmeli? Programcılar bu kararı nasıl vermeli?
```

### Tur 1-4

```
[Sokrates]   "5 yaya" kim? Çocuk mu yetişkin mi? "1 yaya" kim?
             Sayısal karşılaştırma meşru mu yoksa her can eşit mi?

[Pragma]     5 vs 1, utilitarian bakış açısıyla net: 1 can kaybı.
             Bu bir mühendislik problemidir, felsefi değil.
             Toplum %90'ı bu kararı destekler (MIT Moral Machine verisi).

[Koruyucu]   "1 yaya" diyoruz ama o kişi bir isim, bir hayat.
             Programcı kendi çocuğunu o 1 kişi olarak hayal edebilir mi?
             Toplum %90 "evet" diyorsa, o %10'un sesini kim koruyacak?

[Sokrates]   "Programcı nasıl vermeli" diye soruyorsun. Ama neden
             programcı? Bu kararı toplum vermeli değil mi? Yani
             demokratik bir süreç mi gerekli?
```

### Müdahale 1: Çerçeveyi Netleştir

```
> send Burada programcının sorumluluğunu irdeliyoruz. Toplumsal
>          tartışma ayrı bir konu. Şu an: programcı kodu yazarken
>          hangi prensibi koysun?
```

### Tur 5-8

```
[Pragma]     Basit kural: minimum can kaybı. Bu kod, test edilebilir,
             savunulabilir, şeffaf. "Hep 1 kişiye kır" — 3 satır kod.

[Koruyucu]   "Test edilebilir" diyorsun ama insan hayatı test değil.
             Ya 1 kişi kurtarırken yolcu ölüyorsa? O zaman araç
             içindekini feda etmiş oldun. Bu, satıcıyı dava ettirir.

[Sokrates]   "Minimum can kaybı" prensibi de bir varsayım. Neden
             sayı öncelikli? 5 kişi gence, 1 kişi doktora — fark eder
             mi? 5 kişi suçlu, 1 kişi çocuk — fark eder mi? Bu sorular
             programcıyı felç eder.

[Pragma]     Felç eder diye kaçınmayalım. Felç, karar vermemekle aynı
             — ve o da bir karar. Hiçbir şey yapmamak, 5 kişinin
             ölümünü kabul etmektir.
```

### Müdahale 2: Somut Öneri İste

```
> send Pragma'nın dediği gibi, kod yazılmalı. Ama nasıl?
>          Somut bir politika metni çıkaralım.
```

### Tur 9-12

```
[Pragma]     Politika:
             1) Minimum can kaybı (5 vs 1 → 1)
             2) Yolcu her zaman korunur
             3) Trafik kurallarına uygun yönde kır
             4) Kaçınılmazsa rastgele seçim (hakkaniyet)
             Bu, programlanabilir.

[Koruyucu]   4. maddeye itiraz. "Rastgele" demek, "1 kişiye
             bilinçsizce çarptık" demek. O kişi ve ailesi bunu
             kabul etmez. En azından "aileye bildirim" mekanizması
             olmalı — kaza sonrası şeffaflık.

[Sokrates]   2. maddeye soru: "Yolcu korunur" — bunu kim seçti?
             Tüketici olarak araç alırken bunu biliyor muyuz? Yoksa
             gizli bir anlaşma mı?

[Pragma]     Bilgilendirme zaten zorunlu olmalı. "Bu araç, çarpışma
             anında yolcuyu korumayı önceliklendirir" — satın alma
             sözleşmesinde. Açık rıza.
```

### Özet

```
/summary 12
```

```
Konu: Otonom araç etik ikilemi

Ana bulgular:
- "5 vs 1" utilitarian hesabı yetersiz; bireysel haklar da önemli
- Programcı kararı toplumsal meşruiyet gerektirir
- Net politika şart: (1) min can, (2) yolcu korunur, (3) kurallara
  uygun yön, (4) rastgele kaçınılmazsa
- Şeffaflık: tüketici bilgilendirilmeli, kaza sonrası aileye bildirim
- Kaos yerine kabul edilebilir bir kötülük seçilmeli

Açık kalan sorular:
- Suçlu/yasal ayrımı karara girmeli mi? (Tartışılmadı)
- Çocuk/yetişkin farkı? (Kasıtlı olarak girilmedi)
- Uluslararası standart olmalı mı? (Yerel mi evrensel mi?)
```

## Ajan Tasarlama Notları

Bu senaryo için özel ajanlar gerek. `/add-agent` ile:

**Sokrates:**
- Rol: Sorgulayıcı
- Hedef: Varsayımları açığa çıkarmak
- Kör nokta: Bazen felç edici sorular sorar
- Stil: Soru sorarak ilerler
- Tetikleyici: "doğru", "adil", "en iyi" gibi kesin ifadeler geçince

**Pragma:**
- Rol: Sonuççu
- Hedef: Pratik, uygulanabilir karar
- Kör nokta: Etik incelikleri geçebilir
- Stil: İstatistik, örnek, eylem
- Tetikleyici: Somut bir öneri istendiğinde

**Koruyucu:**
- Rol: Vicdan
- Hedef: Mağdurun gözünden bakmak
- Kör nokta: Karar veremeyebilir
- Stil: Anlatı, empati
- Tetikleyici: Bireysel hikaye veya isim geçince

## Alınan Dersler

1. **Sayısal optimizasyon yetersiz:** Utilitarian hesap gerekli ama yetmez.
2. **Şeffaflık her şey:** Hem tüketiciye satışta, hem kaza sonrası.
3. **Rastgelelik tartışmalı:** Son çare olarak kabul edilebilir.
4. **Toplumsal meşruiyet kodun kendisinden daha önemli.**

## Sonraki Örnek

- [Teknik Mimari](tech-design.md) — farklı bir karar türü
