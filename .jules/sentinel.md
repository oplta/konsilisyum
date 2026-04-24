## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Centralized Secret Masking in Orchestration]
**Vulnerability:** API keys could still leak through `Orchestrator.execute_turn` when external API calls failed with exceptions containing the key. Redaction was previously ad-hoc and only applied in `KeyPool.report_error`.
**Learning:** Security controls like secret masking should be centralized and applied at the boundaries where internal state (like exceptions) is converted to user-facing or loggable output.
**Prevention:** Use a centralized `mask_secrets` utility that iterates over all known secrets to sanitize any string before it leaves the core execution context.
