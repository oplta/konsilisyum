# Örnek: Teknik Mimari Kararı

Bir yazılım projesinin teknik mimarisini Konsilisyum ile tartış.

## Senaryo

Yeni bir mikroservis tabanlı uygulama için mimari karar vermen gerekiyor. Temel soru: **Monolitik mi, mikroservis mi, modular monolit mi?**

## Ajanlar

### Mimar (Sistemci)
- **Hedef:** Tutarlı, sürdürülebilir mimari
- **Kör nokta:** Aşırı mühendislik, basit çözümleri karmaşıklaştırabilir
- **Üslup:** Şema, diyagram referanslı, pattern odaklı

### Operatör (Pratikçi)
- **Hedef:** Çalışan, gözlemlenebilir, debug edilebilir
- **Kör nokta:** "Çalışıyor" u yeterli görebilir, mimari borç biriktirir
- **Üslup:** Metrik, log, incident anekdotu

### Kaan (Şüpheci) — varsayılan
- **Hedef:** Varsayımları test et, kanıt iste
- **Kör nokta:** Çıkmaza sokabilir
- **Üslup:** Soru, "neden?"

## Konu

```
> 50K kullanıcı bekleyen, e-ticaret + iç operasyon paneli. 5 geliştirici.
> Mimari karar: monolit, modular monolit, mikroservis. 12 ay içinde MVP.
```

## Tur 1-4

```
[Mimar]  Modular monolit. Başlangıç için monolit hızı, sonra
         gerektiğinde ayır. Net modül sınırları: orders, inventory,
         payments, users. Her modül kendi veritabanı şemasına sahip
         ama aynı process.

[Operatör] 50K kullanıcı monolit için çocuk oyuncağı. Mikroservis
           ekibin dağılma noktası. 5 kişiyle 2 takım kurar, her
           takım kendi servisini unutur. On-call kabus olur.

[Kaan]    "Gerektiğinde ayır" diyorsun. Pratikte hiç ayrılmıyor. Veri
         tutarlılığı sorunu, dağıtım coupling'i. Somut örnek:
         şimdiye kadar modular monolitten kaç tane başarıyla
         mikroservise geçildi? (LinkedIn, Shopify — evet.
         Başarısız olan kaç tane var?)

[Mimar]   Kaan haklı. Modular monolit "ideal" çözüm ama ekibin
          disiplini gerekir. Alternatif: monolitik + dikkatli
          modülerleştirme. Veya: baştan monolitik, büyüyünce
          sadece hot path'leri ayıkla.
```

## Müdahale 1: Sınır Netleştir

```
> send Veri: 50K MAU, 5K eşzamanlı, %30 mobil, %70 web.
>          Operasyon paneli: 200 iç kullanıcı, günde 1K işlem.
>          Ekip: 2 backend, 1 frontend, 1 mobile, 1 fullstack.
>          Bütçe: 12 ay, cloud maliyeti maks 2K$/ay.
```

## Tur 5-8

```
[Operatör] Veriler net: monolit yeterli. 2K$ bütçeyle managed
           Kubernetes bile pahalı. EC2 veya App Engine tek
           container. Monitoring: Datadog veya basit Sentry.

[Mimar]    Kabul. Ama "sonra ayır" konusunda Kaan'a katılıyorum.
           Daha iyi alternatif: monolit ama **bounded context**
           kurallarıyla. Modüller arası çağrı sadece açık API'den.
           Bu, ileride ayrışmayı kolaylaştırır — zorlaştırmaz.

[Kaan]     Bounded context kuralını kim uygulayacak? 5 kişilik
          ekipte review süreci mi? Linting? Veya sadece
          güvenirlik? Pratikte bu tür kurallar 6 ayda erir.

[Operatör] Kaan'ın bu yorumu çok gerçekçi. O zaman en dürüst
           cevap: monolit, ama modül yapısı korunur. İleride
           gerekirse **tüm modülü birden** ayır, parça parça değil.
```

## Müdahale 2: Karar

```
> send Tamam, monolit + modüler yapı. Ama "ileride" için hangi
>          tetikleyici? Yani hangi metrik "şimdi ayırma vakti" der?
```

## Tur 9-12

```
[Mimar]    Tetikleyiciler:
           1) Build süresi > 5 dakika
           2) Deploy coupling — bir modül hatası tüm sistemi düşürüyor
           3) Ekip büyümesi — 10+ backend, paralel takım ihtiyacı
           4) Domain net ayrışıyor (e-ticaret ↔ operasyon farklı takımlar)

[Operatör]  Bence en gerçekçi tetikleyici: **sistem çöktüğünde
           geri dönme süresi**. Şu an 30 dakikadan uzunsa, mimari
           artık büyümeyi karşılamıyor demektir.

[Kaan]     Kabul edilebilir. Ama tetikleyici tanımını koda
           dökün: bir metrik alarm olarak ayarlansın. Yoksa
           "ileride bakarız" olur.

[Mimar]    PR'lara mimari checklist ekleyelim:
           - Modül sınırı ihlali var mı?
           - Doğrudan DB erişimi başka modüle var mı?
           - Cross-cutting concern'ler nerede?
           Code review'da bu sorulur. Disiplin burada.
```

## Özet

```
/summary 12
```

```
Karar: Monolit + modüler yapı

Teknik:
- Python FastAPI veya Node.js NestJS
- PostgreSQL (tek veritabanı, modüler şemalar)
- Redis (cache, queue)
- Tek container, cloud Run veya App Engine

Modül sınırları:
- users, auth
- catalog (ürünler, kategoriler)
- cart, checkout
- orders, payments
- inventory
- admin (iç operasyon paneli)

İletişim: modüller arası sadece servis katmanı (servis-servis değil, modül-service)

Bounded context kuralları:
- Modüller arası import sadece public API'den
- DB erişimi kendi modülüne
- Cross-cutting: events/ klasöründe

Tetikleyiciler (ileride mikroservis):
1) Build > 5 dakika
2) MTTR > 30 dakika
3) Ekip > 10 backend
4) Domain net ayrışıyor

Açık sorular:
- Mobile app aynı repo'da mı? (Tartışılmadı)
- Microservice ayrışması için hangi modülden başlanmalı? (Tartışılmadı)
```

## Alınan Dersler

1. **Veri olmadan tartışma soyut kalıyor.** 50K kullanıcı + 2K$ bütçe bilgisi kararı netleştirdi.
2. **Kaan'ın şüpheciliği gerçekçiydi:** "Gerektiğinde ayır" pratikte gerçekleşmiyor.
3. **Tetikleyici tanımı kritik:** Soyut "ileride" yerine metrik.
4. **Disiplin mimarinin parçası:** checklist code review'da uygulanmalı.

## Ajanlar Hakkında

Bu senaryo için **Mimar** ve **Operatör** özel ajanlar olarak eklenebilir. Detaylar: [Ajanlar: Tasarım](../usage/agents.md).

## Sonraki Adım

- [Ajanlar](../usage/agents.md) — kendi ajanını tasarla
- [Mimari: Genel Bakış](../architecture/overview.md) — Konsilisyum'un kendi mimarisi
