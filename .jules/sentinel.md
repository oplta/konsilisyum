## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2026-05-10 - [Centralized Secret Masking in Orchestrator]
**Vulnerability:** Orchestrator leaked managed API keys in its `execute_turn` error responses because it returned the raw string representation of caught exceptions which often contain the key used for the request.
**Learning:** Security fixes must be applied at both the storage layer (KeyPool) and the presentation layer (Orchestrator) to ensure defense in depth. Relying on a single point of sanitization is fragile.
**Prevention:** Implement a centralized `mask_secrets` utility and apply it to all user-facing error messages and internal state logs that might contain sensitive context.
