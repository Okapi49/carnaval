# Contributing

Thank you for your interest in improving Carnaval. This page is the
wiki-friendly summary; the canonical contribution guide is
[`CONTRIBUTING.md`](../CONTRIBUTING.md) at the repository root, and all
participants are expected to follow the
[Code of Conduct](../CODE_OF_CONDUCT.md).

## Ways to contribute

- Report bugs and request features through issues.
- Improve documentation - this wiki and the `docs/` folder.
- Add or improve recognizers, profiles, dictionaries and output formats.
- Add tests, especially for edge cases.

## Setting up

```bash
git clone <repository-url>
cd carnaval
python -m venv .venv
source .venv/bin/activate          # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

See [Installation](Installation.md) for the full setup.

## The golden rule: no real data

Carnaval is a privacy tool - its public repository must contain **no personal
or client data**. In fixtures, tests, examples and documentation, use only
fictitious entities: `Acme Corp`, `Globex Inc.`, `Initech`, `Jane Doe`,
`John Smith`, `Springfield`, and the `example`/`.example` domains.

Real client data belongs in `profiles_private/`, which is git-ignored - see
[Profiles](Profiles.md).

## Code style

- Target **Python 3.11+**; use modern type hints (`list[str]`, `X | None`).
- Recognizers are **pure functions** - `text` in, `list[Span]` out, no side
  effects.
- Compile regex patterns at module level.
- Keep one responsibility per module.
- Never log sensitive values; rely on the logger's redaction and extend the
  protected key set if you add new keys.
- Follow PEP 8; keep functions small and documented with docstrings.

## Running the tests

```bash
pytest                       # full suite, skips the slow neural tests
pytest -m "not slow"         # explicitly skip slow tests
pytest -m slow               # only the slow GLiNER tests (downloads the model)
pytest --cov=src/carnaval    # with coverage
```

Test layout:

- `tests/unit/` - one file per pipeline stage and core module
- `tests/recognizers/` - regex, deny-list and AI recognizer tests
- `tests/integration/` - full-pipeline and per-profile tests

Every new recognizer needs **positive and negative** unit tests (at least 5 of
each) plus one integration test. See [Recognizers](Recognizers.md).

## Pull request checklist

Before opening a PR:

1. The full test suite passes (`pytest`).
2. New code has tests.
3. No real data appears anywhere.
4. Documentation is updated if behaviour changed.
5. The commit history is clean and the description explains the *why*.

## License

By contributing you agree that your contribution is licensed under the
**Apache License 2.0**, like the rest of the project.
