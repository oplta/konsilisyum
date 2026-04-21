from __future__ import annotations

import os
import re
import copy
from pathlib import Path

import yaml

from konsilisyum.config.defaults import DEFAULT_AGENTS
from konsilisyum.core.models import Agent, APIKey


DEFAULT_CONFIG = {
    "llm": {
        "model": "mistral-large-latest",
        "max_tokens": 300,
        "temperature": 0.7,
    },
    "memory": {
        "context_window_size": 8,
        "summary_interval": 20,
        "memory_update_interval": 5,
        "max_agent_memory_items": 20,
    },
    "orchestrator": {
        "turn_delay": 2.0,
        "max_auto_turns": 50,
        "repetition_threshold": 0.7,
    },
    "session": {
        "auto_save_interval": 5,
        "sessions_dir": "data/sessions",
    },
}

ENV_FILE = ".env"


def load_env(path: str = ENV_FILE):
    p = Path(path)
    if not p.exists():
        return
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


class Config:
    def __init__(self, data: dict | None = None):
        self._data = data or dict(DEFAULT_CONFIG)
        self.llm = self._data.get("llm", DEFAULT_CONFIG["llm"])
        self.memory = self._data.get("memory", DEFAULT_CONFIG["memory"])
        self.orchestrator = self._data.get("orchestrator", DEFAULT_CONFIG["orchestrator"])
        self.session_config = self._data.get("session", DEFAULT_CONFIG["session"])

    @classmethod
    def load(cls, path: str = "data/config.yaml") -> Config:
        load_env()

        model = os.environ.get("MISTRAL_MODEL", "")
        if model:
            DEFAULT_CONFIG["llm"]["model"] = model

        p = Path(path)
        data = copy.deepcopy(DEFAULT_CONFIG)
        if p.exists():
            with open(p) as f:
                yaml_data = yaml.safe_load(f) or {}
            yaml_data = cls._resolve_env_vars(yaml_data)
            cls._deep_merge(data, yaml_data)

        return cls(data)

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                Config._deep_merge(base[k], v)
            else:
                base[k] = v

    @staticmethod
    def _resolve_env_vars(data):
        if isinstance(data, str):
            pattern = r"\$\{([^}]+)\}"
            matches = re.findall(pattern, data)
            for match in matches:
                data = data.replace(f"${{{match}}}", os.environ.get(match, ""))
            return data
        if isinstance(data, dict):
            return {k: Config._resolve_env_vars(v) for k, v in data.items()}
        if isinstance(data, list):
            return [Config._resolve_env_vars(v) for v in data]
        return data

    def get_agents(self) -> list[Agent]:
        agents_data = self._data.get("agents", DEFAULT_AGENTS)
        return [Agent(**a) for a in agents_data]

    def get_api_keys(self) -> list[APIKey]:
        # Once .env'deki MISTRAL_API_KEYS'ten oku (comma-separated)
        env_keys = os.environ.get("MISTRAL_API_KEYS", "")
        if env_keys:
            keys = [k.strip() for k in env_keys.split(",") if k.strip()]
            result = []
            agents = self.get_agents()
            for i, key in enumerate(keys):
                assigned = agents[i].name if i < len(agents) else None
                is_pool = i >= len(agents)
                result.append(APIKey(
                    id=f"key-{i:03d}",
                    key=key,
                    assigned_agent=assigned,
                    is_pool=is_pool,
                ))
            return result

        # Yoksa config.yaml'daki api_keys'ten oku
        keys_data = self._data.get("api_keys", [])
        result = []
        for i, k in enumerate(keys_data):
            key_val = k.get("key", "")
            if not key_val:
                continue
            result.append(APIKey(
                id=k.get("id", f"key-{i:02d}"),
                key=key_val,
                assigned_agent=k.get("assigned"),
                is_pool=k.get("pool", False),
            ))
        return result

    def get_fallback_key(self) -> str | None:
        env_key = os.environ.get("MISTRAL_API_KEY", "")
        if env_key:
            return env_key
        keys = self.get_api_keys()
        return keys[0].key if keys else None
