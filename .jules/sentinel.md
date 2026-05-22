## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Defense-in-Depth Redaction for Exception Messages]
**Vulnerability:** Exceptions caught in the `Orchestrator` turn loop could contain raw API keys if the underlying client or library (like `httpx`) included them in the error string. These raw keys were then returned to the UI.
**Learning:** Redaction must be applied at component boundaries, especially where internal errors are converted to external responses. Storing secrets in `repr=False` fields only protects against accidental logging via `repr()`, not against intentional `str(e)` conversions in exception handlers.
**Prevention:** Use a centralized redaction utility (like `KeyPool.mask_secrets`) to sanitize all caught exceptions before they propagate to user-visible layers.
