from __future__ import annotations

from datetime import datetime, timedelta

from konsilisyum.core.models import APIKey, Agent, KeyStatus


class KeyPool:
    def __init__(self, keys: list[APIKey]):
        self.keys: dict[str, APIKey] = {k.id: k for k in keys}
        self._rr_index = 0

    def get_key(self, agent: Agent | None = None) -> APIKey:
        if agent and agent.api_key_id:
            key = self.keys.get(agent.api_key_id)
            if key and self._is_available(key):
                return key

        pool_keys = [k for k in self.keys.values() if k.is_pool and self._is_available(k)]
        if pool_keys:
            key = pool_keys[self._rr_index % len(pool_keys)]
            self._rr_index += 1
            return key

        available = [k for k in self.keys.values() if self._is_available(k)]
        if available:
            key = available[self._rr_index % len(available)]
            self._rr_index += 1
            return key

        raise RuntimeError("Kullanilabilir API anahtari yok")

    def mask_secrets(self, text: str) -> str:
        if not text:
            return text
        for key_obj in self.keys.values():
            if not key_obj.key:
                continue
            if key_obj.key in text:
                if len(key_obj.key) > 8:
                    masked = f"{key_obj.key[:4]}...{key_obj.key[-4:]}"
                else:
                    masked = "***"
                text = text.replace(key_obj.key, masked)
        return text

    def _is_available(self, key: APIKey) -> bool:
        if key.status in (KeyStatus.EXHAUSTED, KeyStatus.ERROR):
            return False
        if key.status == KeyStatus.RATE_LIMITED:
            if key.rate_limited_until and datetime.now() < key.rate_limited_until:
                return False
            if key.rate_limited_until and datetime.now() >= key.rate_limited_until:
                key.status = KeyStatus.ACTIVE
                key.rate_limited_until = None
                return True
            return False
        return True

    def report_success(self, key_id: str, tokens: int):
        key = self.keys.get(key_id)
        if key:
            key.usage_count += 1
            key.token_count += tokens
            key.last_used = datetime.now()

    def report_error(self, key_id: str, error: str, retry_after: int | None = None):
        key = self.keys.get(key_id)
        if not key:
            return

        # Sanitize error: mask any managed keys if they appear in the error message
        error = self.mask_secrets(error)

        key.last_error = error
        key.error_count += 1
        if "rate_limited" in error:
            key.status = KeyStatus.RATE_LIMITED
            if retry_after:
                key.rate_limited_until = datetime.now() + timedelta(seconds=retry_after)
        elif "auth" in error:
            key.status = KeyStatus.EXHAUSTED
        if key.error_count > 10:
            key.status = KeyStatus.ERROR

    def health(self) -> dict:
        active = sum(1 for k in self.keys.values() if self._is_available(k))
        return {
            "total": len(self.keys),
            "active": active,
            "error": sum(1 for k in self.keys.values() if k.status == KeyStatus.ERROR),
            "exhausted": sum(1 for k in self.keys.values() if k.status == KeyStatus.EXHAUSTED),
        }

    def get_raw_key(self, agent: Agent | None = None) -> str:
        key = self.get_key(agent)
        return key.key
