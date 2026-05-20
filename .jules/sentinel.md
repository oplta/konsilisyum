## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-22 - [Centralized Secret Masking & Path Validation]
**Vulnerability:** API keys could leak through various error paths (API errors, network timeouts) and session IDs could be used for directory traversal.
**Learning:** Masking secrets only in certain objects (like KeyPool) is insufficient if they are echoed in exceptions from underlying libraries. A centralized masking utility in the KeyPool allows for consistent redaction across the application (e.g., in Orchestrator's turn execution). For path safety, all file operations involving user-provided IDs must use a common sanitization helper.
**Prevention:** Implement a `mask_secrets` method that knows about all managed credentials and apply it at the boundaries where internal errors are converted to user-visible messages. Use a `_safe_path` utility for all session-related file access.
