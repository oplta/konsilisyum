## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Bypassing Localized Redaction via Raw Exceptions]
**Vulnerability:** Even though `KeyPool.report_error` was masking keys, raw exceptions caught in the `Orchestrator` were still exposing the full API keys in the UI because they were converted to strings and returned without redaction.
**Learning:** Security fixes at the data layer (like `KeyPool`) can be bypassed if the application logic catches and re-exposes raw exception data from underlying libraries (like `httpx`).
**Prevention:** Implement centralized redaction at component boundaries (e.g., in the Orchestrator's turn execution) in addition to sanitizing stored error states.
