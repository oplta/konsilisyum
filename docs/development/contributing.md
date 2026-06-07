# Katkıda Bulunma

Konsilisyum'a katkıda bulunmak için teşekkürler! Bu rehber süreci hızlandırır.

## Hızlı Başlangıç

```bash
# 1. Fork'la (GitHub'da)
# 2. Klonla
git clone https://github.com/<sen>/konsilisyum.git
cd konsilisyum

# 3. Bağımlılıkları kur
uv sync

# 4. Testleri çalıştır
uv run pytest

# 5. Çalışmaya başla
git checkout -b feat/my-feature
```

## Geliştirme Ortamı

### Gereksinimler

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (paket yöneticisi)
- Git

### Kurulum

```bash
# Geliştirme bağımlılıkları ile birlikte
uv sync --extra dev

# Pre-commit hook'ları
uv run pre-commit install
```

## Kod Standartları

### Stil

- **Formatter:** Ruff (black uyumlu)
- **Linter:** Ruff (flake8 + isort kuralları)
- **Type hints:** Zorunlu, mypy ile kontrol
- **Docstring:** Google stili
- **Satır uzunluğu:** 100 karakter
- **Import sırası:** stdlib → third-party → local (Ruff yönetir)

### Öncesi/Sonrası

Kötü:

```python
def process(d):
    if d['type']=='msg':
        return do_msg(d)
    else:
        return None
```

İyi:

```python
def process_message(data: dict) -> TurnResult | None:
    """Bir mesajı işler ve tur sonucunu döndürür."""
    if data.get("type") != "msg":
        return None
    return _do_msg(data)
```

### Yapısal Kurallar

- `core/` modülleri diğer katmanlara bağımlı **olmamalı**
- `api/` sadece HTTP/LLM ile ilgili
- `commands/` çekirdeği sarmalar, doğrudan HTTP çağırmaz
- `tui/` render ve girdi, iş mantığı **yok**

## Branch Stratejisi

```
main              # kararlı sürümler
  ├── feat/*      # yeni özellik
  ├── fix/*       # hata düzeltme
  ├── docs/*      # doküman
  └── refactor/*  # yapısal değişiklik
```

PR'lar `main`'e açılır.

## Commit Mesajları

[Conventional Commits](https://www.conventionalcommits.org/) kullanıyoruz:

```
<tip>(<kapsam>): <kısa açıklama>

<detaylı açıklama (opsiyonel)>

<issue referansı>
```

### Tipler

- `feat` — yeni özellik
- `fix` — hata düzeltme
- `docs` — doküman
- `refactor` — yapısal değişiklik, davranış değişmiyor
- `test` — test ekleme/düzeltme
- `chore` — bakım (CI, build, deps)

### Kapsamlar

- `orchestrator`, `memory`, `session`, `api`, `tui`, `commands`, `docs`, `ci`

### Örnekler

```
feat(orchestrator): ajan öncelik puanına tetikleyici bonusu ekle

`trigger` alanı eşleşen ajan +2 puan alır. Bu, belirli bir konu
geldiğinde doğru ajanın konuşmasını garantiler.

Closes #45
```

```
fix(memory): 500 kelimelik mesajları keserken yanlış bölüyordu

`split()` üç nokta hatalı yere ekleniyordu. Artık `[:500]` sonrası
" [...kesildi]" doğru biçimde ekleniyor.

Fixes #67
```

## Pull Request Süreci

1. **Branch oluştur:** `feat/agent-memory-persistence`
2. **Kod yaz + test ekle** (önce test yazmak daha iyi)
3. **`pytest` ve `ruff` geçsin**
4. **Commit'le** (Conventional Commits)
5. **Push'la ve PR aç** (`main`'e)
6. **CI yeşil olsun**
7. **Review bekle**, gerekli değişiklikleri yap
8. **Merge edilir**

### PR Şablonu

```markdown
## Değişiklik
<ne yaptın, neden>

## Test
<nasıl test ettin>

## Checklist
- [ ] Testler geçiyor
- [ ] Ruff temiz
- [ ] Mypy temiz
- [ ] Yeni test eklendi (davranış değiştiyse)
- [ ] Doküman güncellendi
```

## Issue Açma

### Bug Report

```markdown
**Açıklama**
Ne oldu?

**Beklenen**
Ne olmalıydı?

**Yeniden Üretme**
1. ...
2. ...
3. ...

**Ortam**
- OS: macOS 14.5
- Python: 3.12.3
- Konsilisyum: 0.2.1
- Model: mistral-small

**Loglar**
```
<paste>
```
```

### Feature Request

```markdown
**Sorun**
<Hangi sorunu çözüyor>

**Önerilen Çözüm**
<Nasıl yapılabilir>

**Alternatifler**
<Başka yaklaşımlar>
```

## Yeni Sağlayıcı Ekleme

Detaylar: [API Katmanı: Yeni Sağlayıcı](../architecture/api.md)

Kısa:

1. `konsilisyum/api/providers.py` içinde sınıf
2. `BaseLLMClient`'dan miras
3. `complete()` metodunu implement et
4. `PROVIDERS` registry'sine ekle
5. Entegrasyon testi ekle
6. Dokümanı güncelle

## Yeni Komut Ekleme

Detaylar: [Komut Sistemi: Yeni Komut](../architecture/commands.md#yeni-komut-ekleme)

Kısa:

Kısa:

1. `konsilisyum/commands/mycommand.py`
2. `@CommandHandler.register("/mycommand")` ile dekor et
3. `konsilisyum/commands/__init__.py` içine import et
4. Test ekle

## Mimari Kararlar

Büyük değişiklikler için önce **issue** aç ve tartış. Mimari karar kaydı (ADR) gerekebilir.

```markdown
# ADR-001: Orkestratör puan sistemi

## Durum
Kabul edildi (2025-01-15)

## Bağlam
Konuşmacı seçimi nasıl yapılmalı?

## Karar
Puan tabanlı, son konuşana -3.0 ceza, kullanıcı mesajı varsa herkese +1.0.

## Sonuçlar
- Sıra deterministik değil ama öngörülebilir
- Direkt sorular öncelik kazanır
- Susturulmamış tüm ajanlar sıra alır
```

## CI/CD {#ci-cd}

Her push'ta:

```yaml
# .github/workflows/ci.yml
- Lint (ruff)
- Type check (mypy)
- Test (pytest + coverage)
```

Coverage %70 altına düşerse PR reddedilir.

## Davranış Kuralları

[Contributor Covenant](https://www.contributor-covenant.org/) uygulanır. Saygılı, yapıcı, kapsayıcı ol.

## Lisans

Katkıda bulunarak katkınızın MIT lisansı altında yayınlanmasını kabul edersiniz.

## İletişim

- **GitHub Issues** — bug, özellik
- **GitHub Discussions** — soru, fikir
- **Email** — info@oplta.dev (güvenlik için)

Teşekkürler! 🎉
