# Troubleshooting

Common problems and how to fix them. If your issue is not listed, see
[Reporting a bug](#reporting-a-bug) at the bottom.

## VaultError: wrong password or corrupt vault

**Cause** - the `CARNAVAL_VAULT_PASSWORD` used for `reinject.py` does not match
the one used for `anonymize.py`.

**Fix** - check the environment variable. If the password changed between the
two runs, the vault can no longer be decrypted: either recover the old
password, or re-anonymize the source document to regenerate the vault.

## VaultError: password too short

**Cause** - the password is shorter than 16 characters.

**Fix** - use a password of at least 16 characters (32+ recommended):

```bash
openssl rand -base64 48
```

See [Vault and Security](Vault-and-Security.md).

## IntakeError: file not found / empty / too large

- **Not found** - check the path (relative vs absolute).
- **Empty** - Carnaval rejects 0-byte files; check the upstream PDF extraction.
- **Too large** - the default cap is 50 MB. Raise it from the API:

  ```python
  intake(path, max_size_bytes=100 * 1024 * 1024)
  ```

## GLiNER download hangs

**Symptom** - on the first run, the process stalls at "Fetching files...".

**Cause** - a firewall or proxy is blocking `huggingface.co`.

**Fix:**

- allow access to `huggingface.co` and `cdn-lfs.huggingface.co`,
- set an HTTPS proxy: `HTTPS_PROXY=...`,
- or download the model on another machine and copy `~/.cache/huggingface/`
  across (see the offline setup in [Installation](Installation.md)).

**Alternative** - run with `--no-gliner`; the pipeline falls back to regex and
deny lists only.

## Slow performance

| Symptom | Likely cause | Fix |
|---|---|---|
| First run > 60 s | Model download | Normal - wait |
| Every run > 15 s | GLiNER on CPU | Acceptable, or use a GPU |
| Still slow with `--no-gliner` | Very long document | Expected - many spans |

## Too many false positives

**Symptom** - non-sensitive words get masked.

**Causes** - GLiNER threshold too low, or a mis-calibrated custom recognizer.

**Fix:**

- raise the neural threshold: `--gliner-threshold 0.6`,
- inspect the JSON output to see which `recognizer` produced the false
  positive, then adjust that recognizer's regex or score.

## Not enough detection (a leak)

**Symptom** - an obvious name is not masked.

**Causes** - GLiNER disabled, the name is not in any deny list and matches no
regex, or the GLiNER threshold is too high.

**Fix:**

- enable GLiNER and lower the threshold to `0.3`,
- add the name to `deny_lists/people.yaml` (see [Profiles](Profiles.md)).

## Garbled text - stray `|` characters inside words

**Symptom** - faulty PDF extraction produces text like `Chi | mieBERTAUX`.

**Fix** - enable `--cleanup-pipes`:

```bash
python anonymize.py inbox/doc.txt --profile acknowledge --cleanup-pipes
```

This option is off by default because it carries a small risk of altering
genuine business content.

## latin-1 encoding in the output

**Cause** - the source file was latin-1, so the automatic fallback kicked in.

**Fix** - none needed; the content is preserved. To force UTF-8, convert the
file upstream: `iconv -f latin1 -t utf8 in.txt > out.txt`.

## ImportError: No module named 'carnaval'

**Cause** - running outside the virtual environment or outside the project
folder.

**Fix** - activate the venv and run from the project root:

```bash
.\.venv\Scripts\Activate.ps1     # Windows
source .venv/bin/activate        # Linux / macOS
python anonymize.py ...
```

## A valid IBAN is not detected

**Cause** - the IBAN validator requires `mod 97 == 1`. Confirm the IBAN is
formally valid with an external checker.

If it is valid but still missed, open an issue with a **self-anonymized**
example (mask the real value yourself before posting).

## Tests fail after a change

Isolate the failure stage by stage:

```bash
pytest tests/unit/test_s3_detect.py -v               # one file
pytest tests/unit/test_s3_detect.py::TestDetect -v   # one class
pytest --lf                                          # only last-failed tests
```

The assertion message usually shows the expected vs actual value.

## Logs are empty

**Cause** - the log level is too high.

**Fix:**

```bash
python anonymize.py inbox/doc.txt --profile acknowledge \
    --log-level DEBUG --console
```

`--console` renders logs human-readable (JSON is the default, for
machine-readability).

## Reporting a bug

If nothing above matches:

1. Reproduce with a minimal input text.
2. Re-run with `--log-level DEBUG --console`.
3. Open an issue including: Python version, OS, the **anonymized** input text,
   the exact command, the full output and the error trace.

See [Contributing](Contributing.md) for the issue conventions.
