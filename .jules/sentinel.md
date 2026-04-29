## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Defense in Depth: Centralized Secret Masking]
**Vulnerability:** Even if internal error reporting is sanitized, raw exceptions caught at the orchestrator level can still leak API keys to the UI or logs.
**Learning:** Security controls should be centralized when possible. By moving masking logic to the `KeyPool`, we ensure consistent redaction in both `report_error` (internal) and `execute_turn` (external).
**Prevention:** Use a centralized secret manager or key pool to provide redaction services for any string that might contain managed secrets before it leaves a security boundary.
