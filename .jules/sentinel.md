## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-14 - [Selective Path Sanitization Gap]
**Vulnerability:** `SessionManager.save` implemented path traversal protection for metadata files but bypassed it for log files (.jsonl) by directly interpolating the session ID.
**Learning:** Security helpers like `_safe_path` create a false sense of security if they aren't used for *all* derived paths in a routine. Developers might assume the ID is "safe" once it passes the first check, forgetting that successive interpolations still create raw paths.
**Prevention:** Ensure all file paths derived from user input pass through the sanitization helper at the point of use, rather than relying on prior checks.
