from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class InputType(Enum):
    COMMAND = "command"
    MESSAGE = "message"
    EMPTY = "empty"


@dataclass
class ParsedInput:
    input_type: InputType
    command: str | None = None
    args: dict | None = None
    raw: str = ""


COMMANDS = {
    "help": {"params": [], "desc": "Komutlari goster"},
    "pause": {"params": [], "desc": "Akisi duraklat"},
    "resume": {"params": [], "desc": "Akisi devam ettir"},
    "quit": {"params": [], "desc": "Konsilden cik"},
    "status": {"params": [], "desc": "Oturum durumu"},
    "say": {"params": ["message"], "desc": "Mesaj birak"},
    "ask": {"params": ["agent", "message"], "desc": "Ajana soru sor"},
    "think": {"params": ["message"], "desc": "Mesaj enjekte et"},
    "topic": {"params": ["topic"], "desc": "Konu degistir"},
    "evolve": {"params": [], "desc": "Konu evrimini serbest birak"},
    "focus": {"params": [], "desc": "Konuyu merkeze cek"},
    "agents": {"params": [], "desc": "Ajan listesi"},
    "spawn": {"params": ["definition"], "desc": "Yeni ajan ekle"},
    "kick": {"params": ["agent"], "desc": "Ajan cikar"},
    "mute": {"params": ["agent"], "desc": "Ajan sustur"},
    "unmute": {"params": ["agent"], "desc": "Ajan ac"},
    "profile": {"params": ["agent"], "desc": "Ajan profili"},
    "edit": {"params": ["agent", "field", "value"], "desc": "Ajan duzenle"},
    "role": {"params": ["role"], "desc": "Kullanici rolu ata"},
    "summary": {"params": [], "desc": "Tartisma ozeti"},
    "decisions": {"params": [], "desc": "Karar taslaklari"},
    "actions": {"params": [], "desc": "Yapilacaklar listesi"},
    "map": {"params": [], "desc": "Karsit gorus haritasi"},
    "export": {"params": ["format"], "desc": "Disa aktar"},
    "save": {"params": [], "desc": "Oturumu kaydet"},
    "load": {"params": ["file"], "desc": "Oturum yukle"},
    "keys": {"params": [], "desc": "API anahtar durumu"},
    "config": {"params": [], "desc": "Yapilandirma"},
}


def parse_input(raw: str) -> ParsedInput:
    raw = raw.strip()
    if not raw:
        return ParsedInput(input_type=InputType.EMPTY)

    if not raw.startswith("/"):
        return ParsedInput(input_type=InputType.MESSAGE, raw=raw)

    parts = raw[1:].split(maxsplit=1)
    if not parts:
        return ParsedInput(input_type=InputType.MESSAGE, raw=raw)

    cmd_name = parts[0].lower()
    cmd_body = parts[1] if len(parts) > 1 else ""

    if cmd_name not in COMMANDS:
        return ParsedInput(
            input_type=InputType.MESSAGE,
            raw=raw,
        )

    cmd_def = COMMANDS[cmd_name]
    args = _parse_args(cmd_name, cmd_def["params"], cmd_body)

    return ParsedInput(
        input_type=InputType.COMMAND,
        command=cmd_name,
        args=args,
        raw=raw,
    )


def _parse_args(cmd: str, params: list[str], body: str) -> dict:
    if not params:
        return {}
    if len(params) == 1:
        return {params[0]: body}
    if params[0] == "agent":
        parts = body.split(maxsplit=1)
        agent_name = parts[0] if parts else ""
        rest = parts[1] if len(parts) > 1 else ""
        if len(params) == 2:
            return {params[0]: agent_name, params[1]: rest}
        if len(params) == 3 and rest:
            field_parts = rest.split(maxsplit=1)
            field = field_parts[0] if field_parts else ""
            value = field_parts[1] if len(field_parts) > 1 else ""
            return {params[0]: agent_name, params[1]: field, params[2]: value}
        return {params[0]: agent_name}
    return {p: body for p in params}


def get_help_text() -> str:
    lines = ["[bold]Konsilisyum Komutlari[/bold]", ""]
    for name, defn in COMMANDS.items():
        params_str = " ".join(f"<{p}>" for p in defn["params"])
        cmd_str = f"/{name} {params_str}".strip()
        lines.append(f"  {cmd_str:30s} {defn['desc']}")
    return "\n".join(lines)
