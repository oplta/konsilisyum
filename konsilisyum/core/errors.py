from __future__ import annotations


class KonsilisyumError(Exception):
    pass


class NoActiveAgentError(KonsilisyumError):
    pass


class AllKeysExhaustedError(KonsilisyumError):
    pass


class SessionNotFoundError(KonsilisyumError):
    pass


class InvalidCommandError(KonsilisyumError):
    pass


class AgentNotFoundError(KonsilisyumError):
    pass


class QuotaExceededError(KonsilisyumError):
    pass


class RateLimitError(KonsilisyumError):
    def __init__(self, message: str = "Rate limit", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthError(KonsilisyumError):
    pass


class ServerError(KonsilisyumError):
    pass
