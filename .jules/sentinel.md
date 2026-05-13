## 2025-05-14 - [API Key Leakage in Error Reports]
**Vulnerability:** Mistral API keys were being leaked in the `last_error` field of `APIKey` objects when `KeyPool.report_error` was called with error messages containing the full key.
**Learning:** Error messages from LLM providers or internal logs often contain the very secrets they are reporting issues about. Simply masking the key in `repr` is not enough if the key is then echoed into another field like `last_error`.
**Prevention:** Always sanitize error messages that might contain sensitive inputs before storing or logging them.

## 2025-05-15 - [API Key Exposure in Orchestrator Errors]
**Vulnerability:** raw exceptions from the LLM client were being bubbled up to the Orchestrator and then to the UI, bypassing the redaction logic in `KeyPool.report_error`.
**Learning:** Security fixes at the data/model level can be bypassed by raw exceptions in the control layer. Redaction must be applied at the outer boundaries where data leaves the system or enters the logs.
**Prevention:** Apply centralized redaction (e.g., `KeyPool.mask_secrets`) at component boundaries and in all exception handlers that might touch sensitive data.
