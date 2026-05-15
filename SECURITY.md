# Security Policy

Carnaval handles sensitive data (PII detection, an encrypted vault). Security
reports are taken seriously.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, email **carnaval.oss@gmail.com** with:

- a description of the vulnerability and its potential impact;
- steps to reproduce (proof of concept if possible);
- the affected version and environment;
- any suggested mitigation.

You can expect an acknowledgement within a few business days. Once the issue is
confirmed, a fix will be prepared and a coordinated disclosure agreed with the
reporter.

## Scope — areas of particular attention

- **Vault encryption** — AES-256-GCM, key derivation via PBKDF2. Any weakness in
  key handling, IV/nonce reuse, or authentication tag verification.
- **Reversibility leakage** — a placeholder that could be reversed without the
  vault password.
- **Detection gaps** — sensitive data that escapes anonymization and could be
  forwarded to an external service.

## Good Practice for Users

- Never commit a real `profiles_private/` profile or a populated `*.vault.enc`.
- Keep the vault password out of source control (use environment variables).
- Review the anonymized output before sending it to any third-party service.
