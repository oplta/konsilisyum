## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Global Secret Masking in Multi-Key Environments]
**Vulnerability:** Incomplete sanitization of error messages. While `KeyPool.report_error` was masking the specific key it received, other managed keys or keys leaked in higher-level components like `Orchestrator` remained exposed.
**Learning:** In systems managing multiple secrets (like a key pool), any one secret might leak into an error message regardless of which secret triggered the error. Selective masking is insufficient.
**Prevention:** Implement a global `mask_secrets` utility that redacts all managed credentials from any string before it is logged or returned to the user/UI.
