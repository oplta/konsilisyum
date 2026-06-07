# Kurulum

## Gereksinimler

- **Python 3.11** veya üstü
- **İşletim sistemi:** Linux, macOS, Windows (WSL önerilir)
- **Terminal:** 256 renk destekleyen herhangi bir terminal (ör. iTerm2, Alacritty, Windows Terminal)
- **API anahtarı:** En az bir LLM sağlayıcısı için

## Adım 1 — Python Kurulumu

Python 3.11+ kurulu olduğundan emin ol:

```bash
python --version
# Python 3.11.x veya üstü olmalı
```

Eğer Python kurulu değilse:

=== "macOS"
    ```bash
    brew install python@3.12
    ```

=== "Ubuntu/Debian"
    ```bash
    sudo apt update
    sudo apt install python3.12 python3.12-venv python3-pip
    ```

=== "Windows"
    [python.org](https://www.python.org/downloads/) adresinden indir.
    Kurulum sırasında **"Add Python to PATH"** kutucuğunu işaretle.

## Adım 2 — Sanal Ortam (Önerilir)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

## Adım 3 — Kurulum

=== "pip"
    ```bash
    pip install konsilisyum
    ```

=== "uv (önerilir)"
    ```bash
    # uv yoksa
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Kurulum
    uv pip install konsilisyum
    ```

=== "kaynak koddan"
    ```bash
    git clone https://github.com/oplta/konsilisyum.git
    cd konsilisyum
    pip install -e .
    ```

## Adım 4 — API Anahtarı

En az bir LLM sağlayıcısının API anahtarına ihtiyacın var. Desteklenen sağlayıcılar:

| Sağlayıcı      | Ortam Değişkeni      | Nereden             |
|----------------|----------------------|---------------------|
| Mistral AI     | `MISTRAL_API_KEY`    | [console.mistral.ai](https://console.mistral.ai/) |
| OpenAI         | `OPENAI_API_KEY`     | [platform.openai.com](https://platform.openai.com/) |
| Anthropic      | `ANTHROPIC_API_KEY`  | [console.anthropic.com](https://console.anthropic.com/) |
| Ollama (yerel) | gerek yok            | [ollama.com](https://ollama.com/) |

Birini dışa aktar:

```bash
export MISTRAL_API_KEY="sk-xxx"
```

Kalıcı olması için `~/.bashrc` veya `~/.zshrc`'ye ekleyebilirsin.

!!! tip "Birden fazla anahtar"
    Konsilisyum birden fazla anahtarı destekler. `.env` dosyasına her satıra bir tane yaz:
    ```
    MISTRAL_API_KEY=sk-xxx
    MISTRAL_API_KEY_2=sk-yyy
    ```

## Adım 5 — Çalıştır

```bash
konsilisyum
```

İlk turda varsayılan üç ajanla (Atlas, Mira, Kaan) boş bir meclis açılır. Artık hazırsın!

## Sorun Giderme

### "konsilisyum: command not found"

Sanal ortamın aktif olduğundan emin ol veya PATH'ine `~/.local/bin` ekle.

```bash
# pip --user ile kurduysan
export PATH="$HOME/.local/bin:$PATH"
```

### "ModuleNotFoundError: rich"

Bağımlılıklar kurulmamış:

```bash
pip install -e .
# veya
uv sync
```

### Rate limit hataları

Birden fazla API anahtarı ekle. KeyPool otomatik olarak sıradakini dener.
