## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [Centralized Secret Redaction in KeyPool]
**Vulnerability:** API keys could still leak in raw exceptions caught by the Orchestrator or in complex error messages in the KeyPool if multiple keys were involved.
**Learning:** Redacting only the specific key being used is insufficient when other managed keys might be present in the same context or error string. Centralized masking in the `KeyPool` ensures all managed secrets are protected regardless of where the error originates.
**Prevention:** Implement a `mask_secrets` method that iterates over all managed keys and use it at all component boundaries where internal data is exposed to the UI or logs.
