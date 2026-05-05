## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Defense in Depth: Centralized Secret Masking & Path Sanitization]
**Vulnerability:** API keys could still leak through `Orchestrator` exception handling when an LLM provider returns an error containing the key. Additionally, session message files (`.jsonl`) were saved without path sanitization, potentially allowing directory traversal if a session ID contained `..`.
**Learning:** Security measures must be applied consistently across all layers. Partial sanitization (e.g., sanitizing metadata files but not message files) creates gaps. Centralizing masking logic in a single point (like `KeyPool.mask_secrets`) makes it easier to apply consistently across the application.
**Prevention:** Use a centralized utility for redacting sensitive data. Ensure all file operations derived from user input (like session IDs) pass through a strict sanitization function like `_safe_path`.
