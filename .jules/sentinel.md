## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Centralized Masking for Defense-in-Depth]
**Vulnerability:** Orchestrator was leaking API keys when LLM client exceptions (e.g. from `httpx`) were caught and returned as `TurnResult.error`.
**Learning:** Individual sanitization in `report_error` is fragile. A centralized `mask_secrets` method in the `KeyPool` that knows about all managed keys allows for consistent redaction across different layers (API and Orchestrator).
**Prevention:** Implement a central registry or pool for secrets that provides a masking utility to be used at all exit points (logs, UI responses, error fields).
