## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2026-05-24 - [API Key Leakage in Orchestrator Turn Execution]
**Vulnerability:** API keys were leaked in the `TurnResult.error` message when an LLM call failed with a raw exception that included the secret.
**Learning:** Security fixes at the data level (e.g., `KeyPool.report_error`) can be bypassed if the application logic catches raw exceptions from underlying libraries and returns them directly to the user or logs. Redaction should also be applied at component boundaries.
**Prevention:** Implement a centralized `mask_secrets(text)` method that can redact all managed secrets from any string, and apply it in the top-level error handling logic (e.g., `Orchestrator.execute_turn`).
