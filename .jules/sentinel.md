## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Broad Secret Masking in Orchestration]
**Vulnerability:** Exceptions caught during LLM completion in `Orchestrator.execute_turn` were being returned as raw strings in `TurnResult`, which often contained the API key if the failure was auth or rate-limit related.
**Learning:** Security is not localized; even if a component (like `KeyPool`) masks its own data, higher-level consumers (like `Orchestrator`) might bypass this by handling raw exception strings from lower-level libraries (like `httpx` or `MistralClient`).
**Prevention:** Implement a centralized `mask_secrets` method that redacts ALL managed secrets, and apply it at the boundaries where internal state (including exceptions) is converted to external reports or user-visible errors.
