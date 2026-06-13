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
