# Oturumlar

Bir Konsilisyum oturumu tüm ajanları, konuları, mesajları ve meta verileri içerir. Oturumlar `data/sessions/` altında JSON dosyaları olarak saklanır.

## Oturum Yapısı

```json
{
  "id": "2025-01-15T10-30-00",
  "name": "YZ etiği",
  "created_at": "2025-01-15T10:30:00",
  "status": "running",
  "current_turn": 47,
  "current_topic": {
    "content": "Yapay zeka etiği",
    "mode": "open",
    "created_at": "2025-01-15T10:30:00"
  },
  "agents": [
    {
      "id": "1",
      "name": "Atlas",
      "role": "Stratejist",
      "goal": "...",
      "blind_spot": "...",
      "style": "...",
      "trigger": "...",
      "status": "active"
    }
  ],
  "messages": [
    {
      "turn": 1,
      "speaker": "Atlas",
      "content": "...",
      "speaker_type": "agent",
      "topic": "Yapay zeka etiği",
      "timestamp": "2025-01-15T10:30:05"
    }
  ],
  "topics": [...],
  "summaries": [...]
}
```

## Oturum Yaşam Döngüsü

```
yok → new (komut) → running → paused → running → ... → saved
                                     ↓
                                  archived
```

| Durum          | Açıklama                                  |
|----------------|--------------------------------------------|
| (yok)          | Henüz oturum açılmadı                      |
| `running`      | Aktif, otomatik turlar devam ediyor        |
| `paused`       | Duraklatıldı, otomatik turlar durmuş       |
| `archived`     | Konuşma tamamlandı, salt okunur            |

## Oturum Açma

### Yeni

```bash
konsilisyum --new "Yeni oturum"
```

### Sıfırdan

```bash
konsilisyum
```

Boş TUI açılır, ilk `>` girdiğiniz konu olur.

### Mevcutu Yükle

```bash
konsilisyum --resume <id>
konsilisyum --list   # ID'leri görmek için
```

## Oturum Kaydetme

Kaydetme **otomatiktir**. Aşağıdaki olaylardan biri gerçekleşince dosya yazılır:

- Her 5 turda bir (snapshot)
- `/save` komutu
- `/q` ile çıkış
- `SIGINT` (Ctrl+C)

Elle kaydetmek için:

```
/save
```

## Oturum Listeleme

```bash
konsilisyum --list
```

veya TUI içinde:

```
/list
```

## Dışa Aktarma

### Markdown

```
/export md
```

veya dosyaya:

```
/export-to rapor.md
```

Üretilen rapor:

```markdown
# YZ etiği

**Konu:** Yapay zeka etiği
**Tarih:** 2025-01-15 10:30
**Tur Sayısı:** 47

---

**[Atlas]** (Tur 1):
Etik, somut kurallar dizisidir...

**[Mira]** (Tur 2):
Peki "zarar" kime göre?...
```

### JSONL

Her satır bir JSON mesaj:

```json
{"turn": 1, "speaker": "Atlas", "content": "...", "timestamp": "..."}
{"turn": 2, "speaker": "Mira", "content": "...", "timestamp": "..."}
```

Akış analizi veya başka araçlara besleme için ideal.

### HTML

```
/export html
```

Bağımsız, stillendirilmiş HTML rapor. E-posta ile gönderilebilir.

## Oturum Paylaşımı

Bir oturum dosyasını (`data/sessions/<id>.json`) başka birine gönderdiğinde o kişi onu yükleyebilir:

```bash
# Alıcı taraf
cp gelen-oturum.json data/sessions/
konsilisyum --list
konsilisyum --resume <id>
```

!!! warning "API Anahtarları Paylaşılmaz"
    Oturum JSON'unda API anahtarları yer almaz. Karşı taraf kendi anahtarını kullanır.

## Oturum Arşivleme

Aktif kullanmadığın ama saklamak istediğin oturumları arşive taşı:

```bash
mv data/sessions/<id>.json data/archive/
```

Arşivdekiler `--list`'te görünmez ama doğrudan `--resume <id>` ile yüklenebilir.

## Oturum Silme

!!! danger "Dikkat"
    Silme geri alınamaz. Emin değilsen arşivle.

```bash
rm data/sessions/<id>.json
```

## Konu Arşivleme

Bir oturumda `/topic` ile konu değiştirdiğinde eski konu otomatik arşivlenir:

```json
{
  "topics": [
    {
      "content": "İlk konu",
      "status": "archived",
      "summary": "..."
    },
    {
      "content": "Şimdiki konu",
      "status": "active"
    }
  ]
}
```

Tüm konuları görmek:

```
/topics
```

## Programatik Erişim

```python
from konsilisyum.core.session import SessionManager

manager = SessionManager("data/sessions")
sessions = manager.list_sessions()
session = manager.load("2025-01-15T10-30-00")
markdown = manager.export(session, "md")
```

Detaylar: [API Referansı](../api/models.md).
