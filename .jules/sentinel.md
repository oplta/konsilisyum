## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Centralized API Key Redaction]
**Vulnerability:** API keys could be leaked in the Orchestrator's error output when exceptions were raised by the API client (e.g., AuthError or ServerError messages containing the key).
**Learning:** Protecting only one point of entry for errors is insufficient. Centralizing the masking logic in the `KeyPool` allows all components that handle errors (Orchestrator, KeyPool, CommandHandler) to consistently redact secrets.
**Prevention:** Implement a `mask_secrets` method that knows about all active secrets in the environment and use it to scrub any string before it's displayed or stored in logs/metadata.
