## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Defense-in-Depth for Secret Redaction]
**Vulnerability:** Even with `KeyPool.report_error` sanitizing messages, the `Orchestrator.execute_turn` was catching raw exceptions from the API client and returning `str(e)` directly, which could contain API keys in some error scenarios.
**Learning:** Security fixes should be applied at multiple layers. A centralized redaction utility is more effective than individual sanitization calls scattered throughout the codebase.
**Prevention:** Implement a centralized secret masking utility in the credential manager and apply it to all potential exit points for error messages, including top-level exception handlers.
