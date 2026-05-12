## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Defense in Depth for Secret Redaction]
**Vulnerability:** While `KeyPool.report_error` sanitized its own key, exceptions raised by underlying libraries (like `httpx`) or the `MistralClient` were passed raw to the `Orchestrator`, which then returned them to the UI, potentially leaking any key in the message.
**Learning:** Security fixes at the data level (`KeyPool`) aren't sufficient if the orchestration layer (`Orchestrator`) bypasses those methods when handling raw exceptions. Redaction should happen at the last possible moment before data leaves the core logic.
**Prevention:** Implement a centralized masking method that redacts ALL known secrets from the pool, and apply it to all exception handlers that communicate with the UI or external logs.
