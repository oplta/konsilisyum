## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Inconsistent Path Sanitization in SessionManager]
**Vulnerability:** `SessionManager.save` was using a safe path helper for metadata (.json) but raw string concatenation for message logs (.jsonl), allowing directory traversal via session IDs for the log file.
**Learning:** Security helpers must be applied consistently to all file operations within a method. Partial protection can create a false sense of security while leaving other vectors open.
**Prevention:** Audit all filesystem operations to ensure they use centralized sanitization helpers (like `_safe_path`).
