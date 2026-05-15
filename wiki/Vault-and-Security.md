# Vault and Security

The **vault** is the heart of Carnaval's reversibility. It stores the mapping
between each placeholder and its real value, encrypted at rest. Without the
vault password, a masked document cannot be reversed.

## What the vault holds

For every masked entity the vault keeps a bidirectional mapping:

- `forward`: original value → placeholder
- `backward`: placeholder → original value

Stage S5 fills the vault during masking; stage S7 reads it during re-injection.
The vault is implemented in `src/carnaval/core/vault.py` as the `Vault` class.

## Encryption

| Property | Value |
|---|---|
| Symmetric cipher | AES-256-GCM (authenticated encryption) |
| Key length | 256 bits |
| Key derivation | PBKDF2-HMAC-SHA256 |
| PBKDF2 iterations | 600,000 |
| Salt | 16 random bytes, generated per file |
| GCM nonce | 16 random bytes, generated per file |
| Authentication tag | 16 bytes |

The on-disk file layout is:

```
[ 16-byte salt ][ 16-byte nonce ][ 16-byte tag ][ N-byte ciphertext ]
```

### Why these choices matter

- **AES-256-GCM** is *authenticated* encryption: any tampering with the file is
  detected when it is read — decryption raises a `VaultError` instead of
  returning corrupt data.
- **600,000 PBKDF2 iterations** make brute-force and dictionary attacks
  expensive even with GPUs.
- **A fresh random salt and nonce per file** mean two vaults encrypted with the
  same password never produce comparable ciphertext.

## The password

The password is read from the `CARNAVAL_VAULT_PASSWORD` environment variable
(loaded from `.env` by the CLI). It must be **at least 16 characters**; 32+ is
strongly recommended. A password shorter than 16 characters raises a
`VaultError`.

### Generating a strong password

Linux / macOS:

```bash
openssl rand -base64 48
```

Windows PowerShell:

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
```

### Do and don't

**Do not:**

- commit the password (`.env` is git-ignored — keep it that way),
- log it, even partially,
- pass it as a command-line argument (it would be visible in `ps` and shell
  history),
- hard-code it in source.

**Do:**

- inject it via the `CARNAVAL_VAULT_PASSWORD` environment variable,
- in production, load it from an enterprise secret manager (HashiCorp Vault,
  AWS Secrets Manager, Azure Key Vault) or a mode-600 environment file.

> If you run a command without setting `CARNAVAL_VAULT_PASSWORD`, the CLI falls
> back to a built-in **demo password** and prints a warning. Never use the demo
> password for real data.

## No data leakage in logs

Carnaval's structured logger (`src/carnaval/core/logger.py`) includes a
`_redact_sensitive` processor. Any value logged under a sensitive key is
replaced with `<REDACTED>`. The protected keys include:

```
original, raw_text, raw, text, mapping, vault, vault_contents,
password, secret, forward, backward
```

So even a careless `log.info("event", original="Jane Doe")` produces
`{"event": "event", "original": "<REDACTED>"}`. If you add new keys that may
carry sensitive data, extend this set.

## No network exposure

After the one-time GLiNER model download, Carnaval makes **no outbound network
calls** and opens **no listening port**. You can:

- verify with `tcpdump` / Wireshark,
- run it in a container with no network interface,
- block all outbound traffic for the user running Carnaval.

## Attack surface

### A leaked `vault.enc`

Without the password the file is unreadable. With the password, every original
value is recoverable.

Mitigations: store `outbox/vault/` on an encrypted partition; purge old vaults
after processing; rotate the password periodically.

### The input file in `inbox/`

The input file holds sensitive data **in clear text**. Restrict its
permissions, delete it after anonymization, and keep it on an encrypted
partition.

### The `meta.json` file

`outbox/meta/<stem>_meta.json` contains entity counts per category (statistics,
not sensitive) and the source path. **No original value** is ever written to
the metadata file.

## Audit trail

For SOC-style traceability, capture the structured logs:

```bash
python anonymize.py inbox/doc.txt --profile acknowledge \
    --log-level INFO 2>> /var/log/carnaval/audit.jsonl
```

Each line records *how many* entities of each type were masked — never *which*
ones:

```json
{"event": "s5_mask_done", "by_category": {"PERSON": 2, "EMAIL": 1}, "timestamp": "..."}
```

## GDPR notes

Carnaval implements **pseudonymization** in the sense of GDPR Article 4.5:
personal data is replaced by identifiers that no longer permit identification
without additional information, and that additional information (the vault) is
kept separately and is technically protected.

> Carnaval is a technical tool that *helps* with compliance — it is not a GDPR
> certification. Overall compliance depends on your usage context, retention
> periods, and the data-processing agreements you have with any external LLM
> provider.

## See also

- [Architecture](Architecture.md) — stages S5 (mask) and S7 (re-inject)
- [Reinjection](Reinjection.md) — using the vault to restore values
- [Troubleshooting](Troubleshooting.md) — `VaultError` diagnostics
