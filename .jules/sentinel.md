## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Defense in Depth for Secret Masking]
**Vulnerability:** API keys could still leak via raw exception messages caught at the Orchestrator level, even if the data-layer (KeyPool) had some masking in its error reporting.
**Learning:** Masking must be applied at component boundaries where data is prepared for external consumption (like UI or API responses). Relying on internal error sanitization is insufficient if exceptions can bypass those paths and reach the orchestrator.
**Prevention:** Implement a centralized masking utility and ensure it is called in all top-level exception handlers that return error messages to the user.
