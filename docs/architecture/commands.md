# Komut Sistemi

Konsilisyum'un 28+ komutu vardır ve hepsi tek bir mekanizmayla çalışır. Bu sayfa o mekanizmayı anlatır.

## Mimarisi

```
Kullanıcı girdisi: "/topic YZ etiği"
        ↓
CommandHandler.parse()  →  ("/topic", ["YZ", "etiği"])
        ↓
Registry.resolve()  →  topic_command function
        ↓
topic_command(args, context)  →  yanıt stringi veya eylem
        ↓
TUI.render(yanıt)
```

## Kayıt Mekanizması

`CommandHandler` dekoratör tabanlı basit bir registry:

```python
# konsilisyum/commands/handler.py
class CommandHandler:
    _registry: dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(fn):
            cls._registry[name] = fn
            return fn
        return decorator

    @classmethod
    def resolve(cls, name: str) -> Callable | None:
        return cls._registry.get(name)

    @classmethod
    def dispatch(cls, name: str, args: list[str], context) -> str:
        fn = cls.resolve(name)
        if not fn:
            return f"Bilinmeyen komut: {name}. /help deneyin."
        return fn(args, context)
```

## Komut Tanımlama

Bir komut dosyası (`konsilisyum/commands/topic.py`):

```python
from konsilisyum.commands.handler import CommandHandler

@CommandHandler.register("/topic")
def topic_command(args: list[str], context) -> str:
    """Yeni konu açar."""
    if not args:
        return "Kullanım: /topic <metin>"

    new_topic = args[0] if len(args) == 1 else " ".join(args)
    session = context.session
    session.archive_current_topic()
    session.current_topic = Topic(content=new_topic)
    return f"Konu değiştirildi: {new_topic}"
```

Otomatik kayıt için dosyanın `konsilisyum/commands/__init__.py` içinde import edilmesi yeterli:

```python
# konsilisyum/commands/__init__.py
from . import (
    pause,
    resume,
    topic,
    add_agent,
    export,
    ...
)
```

## Komut Bağlamı

Her komut bir `context` nesnesi alır:

```python
@dataclass
class CommandContext:
    session: Session
    orchestrator: Orchestrator
    memory: MemoryManager
    session_manager: SessionManager
    tui: TUI  # çıktı için
    config: Config
```

Bu sayede komutlar:

- Oturum verisine erişir
- Orkestratörü kontrol eder (duraklat/devam)
- TUI'a çıktı verir
- Ayar değiştirir

## Örnek: `/add-agent`

İnteraktif komutlar da aynı mekanizmayla çalışır:

```python
@CommandHandler.register("/add-agent")
def add_agent_command(args: list[str], context) -> str:
    tui = context.tui
    name = tui.prompt("Ajan adı:")
    role = tui.prompt("Rolü:")
    goal = tui.prompt("Amacı:")
    blind_spot = tui.prompt("Kör noktası:")
    style = tui.prompt("Üslubu:")
    trigger = tui.prompt("Tetikleyici:")
    color = tui.prompt("Renk (#ff6b6b):", default="#ff6b6b")

    agent = Agent(
        name=name, role=role, goal=goal,
        blind_spot=blind_spot, style=style,
        trigger=trigger, color=color,
    )
    context.session.agents.append(agent)
    return f"✓ Ajan eklendi: {name} (id: {agent.id})"
```

## Aliaslar

Bir komutun birden fazla adı olabilir:

```python
@CommandHandler.register("/h")
@CommandHandler.register("/help")
def help_command(args, context):
    return format_help()
```

Dekoratörler alt alta yazılır. Sıra önemli değil; hangisi önce yazılırsa o "kısayol" sayılır.

## Kısmi Eşleşme

`/pa` → `/pause` olarak çözülür. Bu, `dispatch()` içinde:

```python
@classmethod
def dispatch(cls, name: str, args, context):
    if name in cls._registry:
        return cls._registry[name](args, context)

    # Kısmi eşleşme
    matches = [k for k in cls._registry if k.startswith(name)]
    if len(matches) == 1:
        return cls._registry[matches[0]](args, context)

    if len(matches) > 1:
        return f"Birden fazla eşleşme: {', '.join(matches)}"

    return f"Bilinmeyen komut: {name}"
```

## Async Komutlar

Çoğu komut senkron çünkü orchestration'ı beklemiyor. Ama API çağrısı yapanlar `async` olabilir:

```python
@CommandHandler.register("/summary")
async def summary_command(args, context):
    n = int(args[0]) if args else 20
    summary = await context.orchestrator.generate_summary(n)
    return summary
```

`dispatch()` her iki türü de destekler:

```python
import asyncio

@classmethod
def dispatch(cls, name, args, context):
    fn = cls.resolve(name)
    result = fn(args, context)
    if asyncio.iscoroutine(result):
        return asyncio.run(result)  # veya mevcut loop'ta
    return result
```

## Komut Listeleme

`/help` çıktısı otomatik üretilir:

```python
@CommandHandler.register("/help")
def help_command(args, context):
    lines = ["Mevcut komutlar:", ""]
    for name, fn in sorted(CommandHandler._registry.items()):
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        lines.append(f"  {name:20s}  {doc}")
    return "\n".join(lines)
```

## Tüm Komutlar

Kaynak kod: `konsilisyum/commands/`. Her dosya bir komut. Tam liste için [Komutlar](../usage/commands.md) sayfasına bak.

## Test

```python
def test_topic_command():
    ctx = make_test_context()
    result = CommandHandler.dispatch("/topic", ["YZ", "etiği"], ctx)
    assert "Konu değiştirildi" in result
    assert ctx.session.current_topic.content == "YZ etiği"
```

## Yeni Komut Ekleme

1. `konsilisyum/commands/mycommand.py` oluştur
2. `CommandHandler.register("/mycommand")` ile dekor et
3. `konsilisyum/commands/__init__.py` içine import et
4. Test ekle: `tests/commands/test_mycommand.py`

Detaylar: [Geliştirme: Katkıda Bulunma](../development/contributing.md).
