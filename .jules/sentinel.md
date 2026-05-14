## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Centralized Secret Masking and Orchestrator Leak Protection]
**Vulnerability:** API keys could still leak through unhandled exceptions in the `Orchestrator` even if `KeyPool.report_error` was protected, as raw exceptions from `httpx` or the API client bypassed the pool's internal sanitization.
**Learning:** Security controls at the data layer (KeyPool) are insufficient if the execution layer (Orchestrator) exposes raw error objects to the user interface. Redaction must happen at the outermost boundary before data leaves the system core.
**Prevention:** Implement a centralized `mask_secrets` method in the credential manager that sorts keys by length (descending) to prevent partial matching (e.g., matching 'key' in 'key123') and apply it at the Orchestrator level before returning errors.
