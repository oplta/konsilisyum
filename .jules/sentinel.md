## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [API Key Leakage in Orchestrator Exceptions]
**Vulnerability:** Raw API keys were leaked in the `TurnResult.error` field when `MistralClient` raised exceptions (like AuthError) containing the key, bypassing the `KeyPool`'s internal sanitization.
**Learning:** Redaction must be applied at component boundaries. Security fixes at the data layer (`KeyPool`) can be bypassed if the execution layer (`Orchestrator`) captures and returns raw exception strings.
**Prevention:** Use a centralized masking utility (e.g., `KeyPool.mask_secrets`) in the orchestrator's exception handlers before exposing error messages to the UI.
