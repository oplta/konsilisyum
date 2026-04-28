## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2026-04-28 - [Centralized Credential Redaction]
**Vulnerability:** API keys could be leaked in error results when an LLM call failed and the exception message or provider error included the raw key.
**Learning:** Redacting a key only when it's "the" key associated with a report is insufficient. Errors can propagate and cross-contaminate (e.g., an error with Key A might contain Key B in its context).
**Prevention:** Implement a centralized `mask_secrets` utility that knows about ALL managed secrets and use it to sanitize all exception messages and error reports before they reach the UI or persistent storage.
