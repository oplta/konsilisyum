## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2026-05-06 - [Holistic Secret Redaction]
**Vulnerability:** Even if API keys are masked in `repr`, they can still leak through exception messages raised by third-party libraries (like httpx or Mistral API) when those exceptions are echoed to the user.
**Learning:** Security hardening must be applied at the boundaries where internal state (including errors) is converted to output. Relying on individual components to "not leak" is insufficient.
**Prevention:** Implement a centralized masking utility that knows about all sensitive tokens in the session and apply it to all error reporting paths.
