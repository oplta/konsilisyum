# Komutlar

Konsilisyum'un 28+ komutu vardır. Bu sayfa tam referans.

## Sözdizimi

```
/<komut> [argümanlar]
```

Komutlar `/` ile başlar. Kısmi eşleşme desteklenir: `/pa` → `/pause`.

## Oturum Yönetimi

### `/new [isim]`

Yeni oturum açar. İsim verilmezse tarih-saat kullanılır.

```
/new Pazarlama stratejisi 2025
```

### `/pause`

Otomatik tur döngüsünü duraklatır. `send` ile hâlâ mesaj yazabilirsin.

### `/resume`

Duraklatılmış oturumu devam ettirir.

### `/list`

Tüm kayıtlı oturumları listeler.

```
ID                          OTURUM                  TURLAR    KONU
2025-01-15T10-30-00         YZ etiği                47        Yapay zeka etiği
2025-01-14T16-00-00         Ürün lansmanı           23        Yeni ürün lansmanı
```

### `/resume-id <id>`

Belirli bir oturumu yükler.

### `/save`

Oturumu diske yazar (normalde otomatik).

### `/q` veya `/quit`

Oturumu kaydeder ve çıkar.

## Konu Yönetimi

### `/topic <metin>`

Yeni konu açar. Önceki konu özetlenip arşivlenir.

```
/topic Veri gizliliği ve GDPR
```

### `/topics`

Tüm konuları listeler (aktif + arşiv).

### `/topic-mode <mod>`

Konu modunu değiştirir.

| Mod       | Açıklama                          |
|-----------|------------------------------------|
| `open`    | Serbest tartışma (varsayılan)     |
| `focused` | Belirli bir soruya odaklanır      |
| `panel`   | Her ajan sırayla görüş bildirir   |

## Ajan Komutları

### `/agents`

Aktif ajanları listeler.

### `/add-agent`

İnteraktif sihirbazla yeni ajan ekler. Detaylar: [Ajanlar](agents.md).

### `/mute <id>`

Ajanı susturur. `/unmute` ile geri al.

### `/unmute <id>`

Susturulmuş ajanı tekrar aktif eder.

### `/remove <id>`

Ajanı tamamen siler. Geri alınamaz.

### `/rename <id> <yeni_ad>`

Ajan adını değiştirir.

## Mesaj Komutları

### `send <mesaj>`

Kullanıcı mesajı olarak kuyruğa alır. Bir sonraki turda orkestratör bu mesajı ilgili ajana yönlendirir.

```
send Hedef kitleyi daraltalım: B2B SaaS
```

### `pass`

Sıradaki ajanın pas geçmesini sağlar.

### `@<ajan> <mesaj>`

Belirli bir ajana direkt mesaj yollar.

```
@mira Bu kararın etik boyutu nedir?
```

## Özet ve Analiz

### `/summary`

Son 20 turun özetini üretir.

### `/summary <N>`

Son N turun özetini üretir.

### `/stats`

Oturum istatistiklerini gösterir:

```
Oturum: YZ etiği
Toplam tur: 47
Aktif ajan: 3
Susturulmuş: 0
Token kullanımı: 12,340
Ortalama tur süresi: 1.8s
En çok konuşan: Atlas (19 tur)
En çok pas geçen: Kaan (8 tur)
```

### `/replay <N>`

Son N turu baştan sona tekrar oynatır.

## Dışa Aktarma

### `/export <format>`

| Format   | Açıklama                              |
|----------|----------------------------------------|
| `md`     | Markdown                               |
| `jsonl`  | Satır başına bir JSON                 |
| `txt`    | Düz metin                              |
| `html`   | HTML rapor                             |

```
/export md
# Konsilisyum Oturum Raporu
...
```

### `/export-to <dosya>`

Belirtilen dosyaya yazar.

```
/export-to rapor.md
```

## Konfigürasyon

### `/config`

Mevcut yapılandırmayı gösterir.

### `/config <anahtar> <değer>`

Çalışma zamanında ayar değiştirir.

```
/config turn_delay 3.0
/config max_auto_turns 100
```

### `/reload-agents`

Ajantar dosyasını (`agents.yaml` veya benzeri) yeniden yükler.

## Anahtar Yönetimi

### `/keys`

Mevcut API anahtarlarını listeler:

```
ID    STATUS     LAST USED       USAGE
k1    active     2 dakika önce   1245 istek
k2    active     5 dakika önce   892 istek
k3    rate-limit 1 dakika önce   1500 istek
```

### `/keys-add <anahtar>`

Yeni anahtar ekler.

### `/keys-remove <id>`

Anahtarı kaldırır.

## Meta

### `/help` veya `/h`

Tüm komutların listesini gösterir.

### `/version`

Konsilisyum sürümünü gösterir.

### `/debug`

Hata ayıklama modunu açar (geliştiriciler için).

## Klavye Kısayolları

TUI'da ek kısayollar:

| Tuş          | İşlev                       |
|--------------|------------------------------|
| `Tab`        | Odak değiştir                |
| `↑/↓`        | Mesaj geçmişi               |
| `Ctrl+L`     | Ekranı temizle               |
| `Ctrl+C`     | Mevcut turu iptal et          |
| `Ctrl+D`     | Çıkış (onay sorar)           |
| `F1`         | Yardım                       |
| `F2`         | Ajan listesi                 |

## Komut Yazma (Geliştirici)

Kendi komutunu eklemek için `konsilisyum/commands/` altına yeni bir modül:

```python
# konsilisyum/commands/my_command.py
from konsilisyum.commands.handler import CommandHandler

@CommandHandler.register("/mycommand")
def my_command(args: list[str], context) -> str:
    return "Çıktı"
```

Detaylar: [Komut Sistemi Mimarisi](../architecture/commands.md).
