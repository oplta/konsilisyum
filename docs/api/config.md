# Yapılandırma

Konsilisyum üç düzeyde yapılandırılır:

1. **Ortam değişkenleri** (en yüksek öncelik)
2. **Proje config** (`./konsilisyum.yaml`)
3. **Kullanıcı config** (`~/.konsilisyum/config.yaml`)

Öncelik sırası: ortam değişkeni > proje > kullanıcı > varsayılan.

## Konumlar

```bash
# Kullanıcı (kişisel tercihler)
~/.konsilisyum/config.yaml

# Proje (repo-seviyesi, takım paylaşımı)
./konsilisyum.yaml

# API anahtarları (asla commit'leme!)
~/.konsilisyum/.env
```

## Tam Şema

```yaml
# konsilisyum.yaml
provider: mistral          # hangi sağlayıcı
model: mistral-small-latest

# LLM parametreleri
llm:
  max_tokens: 300
  temperature: 0.7
  timeout: 30

# Orkestratör ayarları
orchestrator:
  turn_delay: 2.0          # turlar arası bekleme (saniye)
  max_auto_turns: 50       # kullanıcı müdahalesi olmadan maks tur

# Hafıza ayarları
memory:
  context_window_size: 8
  summary_interval: 20
  memory_update_interval: 5
  max_agent_memory_items: 20

# Tekrar algılama
repetition:
  enabled: true
  threshold: 0.7           # Jaccard benzerliği

# API anahtarları
api_keys:
  - env: MISTRAL_API_KEY
    is_pool: true          # havuzda, herkes kullanabilir
  - env: MISTRAL_API_KEY_2
    is_pool: true
  - env: ATLAS_KEY
    is_pool: false         # özel, sadece Atlas için
    agent: Atlas

# TUI ayarları
tui:
  theme: auto              # auto | light | dark
  animations: true
  show_timestamps: true

# Oturum kayıt
session:
  save_interval: 5         # her 5 turda bir snapshot
  auto_export_on_quit: false

# Logging
logging:
  level: INFO              # DEBUG | INFO | WARNING | ERROR
  file: data/logs/konsilisyum.log
  format: json             # json | text
```

## Sağlayıcı Seçenekleri

### `provider`

- `mistral` (varsayılan)
- `openai`
- `anthropic`
- `ollama`

### `model`

Sağlayıcıya göre değişir. Tam liste: [LLM Sağlayıcıları](providers.md).

## Ortam Değişkenleri

| Değişken              | Açıklama                       |
|-----------------------|---------------------------------|
| `MISTRAL_API_KEY`     | Mistral ana anahtarı            |
| `MISTRAL_API_KEY_2`   | İkinci anahtar (havuz)          |
| `OPENAI_API_KEY`      | OpenAI anahtarı                 |
| `ANTHROPIC_API_KEY`   | Anthropic anahtarı              |
| `KONSILISYUM_CONFIG`  | Özel config dosya yolu          |
| `KONSILISYUM_LOG`     | Özel log dosya yolu             |
| `KONSILISYUM_DEBUG`   | `1` ise debug modu              |

## `.env` Dosyası

API anahtarları için `.env` kullanılması önerilir (git'e ekleme!):

```bash
# ~/.konsilisyum/.env
MISTRAL_API_KEY=sk-xxx
MISTRAL_API_KEY_2=sk-yyy
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

`.gitignore`'a ekle:

```
.env
*.env
data/sessions/
data/logs/
```

## Çalışma Zamanı Ayarı

Bazı ayarlar TUI içinden değiştirilebilir:

```
/config turn_delay 3.0
/config max_auto_turns 100
/config theme dark
```

Bu değişiklikler sadece RAM'de kalır, kalıcı olması için `config save`:

```
/config save
```

## Doğrulama

Yapılandırmanı doğrulamak için:

```bash
konsilisyum --check-config
```

Çıktı:

```
✓ Provider: mistral
✓ Model: mistral-small-latest
✓ API key: sk-xxx... (MISTRAL_API_KEY)
✓ Pool keys: 2
✓ Config dosyası: ~/.konsilisyum/config.yaml
✓ Tüm ayarlar geçerli
```

## Hata Durumları

### "API anahtarı bulunamadı"

```bash
export MISTRAL_API_KEY="sk-xxx"
# veya
echo 'MISTRAL_API_KEY=sk-xxx' > ~/.konsilisyum/.env
```

### "Geçersiz yapılandırma: turn_delay"

Geçerli aralık dışı bir değer:

```yaml
turn_delay: -1   # ✗ negatif olamaz
turn_delay: 2.0  # ✓
```

### "Sağlayıcı desteklenmiyor"

`provider: gpt5` gibi geçersiz bir değer:

```bash
konsilisyum --check-config
# Hata: Desteklenmeyen sağlayıcı: gpt5
# Geçerli: mistral, openai, anthropic, ollama
```

## Profiller

Birden fazla ortam için farklı config'ler:

```bash
# Geliştirme
konsilisyum --config ~/.konsilisyum/dev.yaml

# Üretim
konsilisyum --config ~/.konsilisyum/prod.yaml
```

veya `KONSILISYUM_CONFIG` ile:

```bash
export KONSILISYUM_CONFIG=~/.konsilisyum/prod.yaml
konsilisyum
```

## Sonraki Adım

- [LLM Sağlayıcıları](providers.md) — provider/model kombinasyonları
- [Veri Modelleri](models.md) — config'te başvurulan modeller
