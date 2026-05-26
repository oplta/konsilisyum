## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Bypassing Data-Level Redaction via Raw Exceptions]
**Vulnerability:** Even if data objects like `APIKey` have redaction logic in their error reporting methods, raw exceptions from underlying libraries (e.g., `httpx`) can still bubble up to the UI/orchestrator containing secrets in their string representation.
**Learning:** Security fixes at the data level can be bypassed if the application flow exposes raw exception objects. Centralized redaction must be applied at component boundaries.
**Prevention:** Implement a centralized `mask_secrets` method that knows about all sensitive tokens and apply it at the highest possible level (e.g., Orchestrator) before data leaves the system boundary.
