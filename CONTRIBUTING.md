# Contributing to Carnaval

Thank you for taking the time to contribute. Carnaval is an open-source
reversible PII anonymization framework released under the **Apache License
2.0**, and contributions of all kinds are welcome.

By participating in this project you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [The golden rule: no real data](#the-golden-rule-no-real-data)
- [Development setup](#development-setup)
- [Code style](#code-style)
- [Tests](#tests)
- [Commit and pull request workflow](#commit-and-pull-request-workflow)
- [Reporting bugs](#reporting-bugs)
- [Requesting features](#requesting-features)
- [License](#license)

## Ways to contribute

- **Report a bug** or **request a feature** via GitHub issues.
- **Improve the documentation** — the [wiki](wiki/Home.md) and the `docs/`
  folder.
- **Add or improve recognizers, profiles, dictionaries, output formats.**
- **Add tests**, especially for edge cases and regressions.

If you plan a substantial change, please open an issue first so the design can
be discussed before you invest effort.

## The golden rule: no real data

Carnaval is a privacy tool. Its public repository must contain **no personal or
confidential data** — ever.

In every fixture, test, example and documentation snippet, use **fictitious
entities only**:

- Organizations: `Acme Corp`, `Globex Inc.`, `Initech`, `Vandelay Industries`
- People: `Jane Doe`, `John Smith`, `Alice Anderson`, `Bob Brown`
- Places: `Springfield`
- Domains: anything ending in `.example` (`globex.example`)

Real client data belongs exclusively in `profiles_private/`, which is listed in
`.gitignore` and must never be committed. Pull requests containing what looks
like real personal data will be declined until cleaned up.

## Development setup

Requires **Python 3.11+** (tested on 3.13).

```bash
git clone <repository-url>
cd carnaval

python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Set a vault password for local testing:

```bash
cp .env.example .env
# edit .env: CARNAVAL_VAULT_PASSWORD must be at least 16 characters
```

See the [Installation guide](wiki/Installation.md) for more, including the
offline setup.

## Code style

- **Python 3.11+** with modern type hints — `list[str]`, `dict[str, int]`,
  `X | None`.
- **Recognizers are pure functions**: they take `text: str` and return
  `list[Span]`, with no side effects.
- **Compile regex patterns at module level**, not inside functions.
- **One responsibility per module** — one file, one entity type or one stage.
- **Never log sensitive values.** The structured logger redacts a set of
  sensitive keys; if you introduce new keys that may carry secrets, add them to
  that set (`src/carnaval/core/logger.py`).
- Follow **PEP 8**. Keep functions small and document public functions with
  docstrings.
- Prefer clarity over cleverness — Carnaval explicitly avoids "magic".

## Tests

The project uses `pytest`.

```bash
pytest                       # full suite (slow neural tests are skipped)
pytest -m "not slow"         # explicitly skip the slow tests
pytest -m slow               # only the slow GLiNER tests (downloads the model)
pytest --cov=src/carnaval    # with a coverage report
```

Test layout:

| Folder | Scope |
|---|---|
| `tests/unit/` | one file per pipeline stage and core module |
| `tests/recognizers/` | regex, deny-list and AI recognizer tests |
| `tests/integration/` | full-pipeline and per-profile tests |

When you add a recognizer, include **positive and negative** unit tests (at
least 5 of each) and at least one end-to-end integration test. See the
[Recognizers wiki page](wiki/Recognizers.md).

All tests must pass before a pull request is merged.

## Commit and pull request workflow

1. Fork the repository and create a topic branch from the default branch.
2. Make focused commits with clear messages explaining the *why*, not just the
   *what*.
3. Keep the test suite green (`pytest`).
4. Update documentation when behaviour changes.
5. Open a pull request describing the change, the motivation and any trade-offs.

**Pull request checklist:**

- [ ] The full test suite passes.
- [ ] New code is covered by tests.
- [ ] No real or personal data anywhere in the diff.
- [ ] Documentation updated if behaviour changed.
- [ ] Commit history is clean and descriptive.

## Reporting bugs

Open an issue including:

- Python version and operating system.
- The exact command or code that triggers the bug.
- The input text — **anonymized by you** before posting.
- The full output and error trace.
- What you expected to happen.

See the [Troubleshooting wiki page](wiki/Troubleshooting.md) first — your issue
may already have a known fix.

**Security vulnerabilities** must not be reported via public issues. Email
**carnaval.oss@gmail.com** instead — see [SECURITY.md](SECURITY.md).

## Requesting features

Open an issue describing the use case and the problem it solves. Concrete
examples (with fictitious data) help a lot.

## License

By contributing to Carnaval you agree that your contributions will be licensed
under the **Apache License 2.0**, the same license as the project. See
[LICENSE](LICENSE).
