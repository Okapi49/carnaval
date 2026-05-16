# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-05-16

### Changed

- README updated for PyPI installation: `pip install carnaval` is now the
  primary install method, the `carnaval-anonymize` / `carnaval-reinject`
  commands replace the old script invocations, and all internal links use
  absolute GitHub URLs so they render correctly on the PyPI project page.

## [0.1.1] - 2026-05-16

### Fixed

- Package data (configuration, business profiles, dictionaries) is now
  bundled inside the `carnaval` package and resolved relative to it.
  A `pip install` of Carnaval is now fully functional; previously the
  configuration and profile loaders assumed a cloned-repository layout
  and failed when the package was installed as a wheel.

### Changed

- Data files moved under `src/carnaval/data/` (config, profiles,
  dictionaries).
- `load_config()` resolves bundled data from the package; the
  `repo_root` parameter is replaced by explicit `profiles_dir` /
  `private_dir` overrides.
- CLI tools resolve `.env` and the default `outbox/` from the current
  working directory instead of the repository root.

## [0.1.0] - 2026-05-15

### Added

- Reversible PII anonymization pipeline (stages S1 to S7): intake,
  preprocess, detect, resolve, mask, output, reinject.
- Encrypted vault (AES-256-GCM) mapping placeholders to original values,
  enabling lossless reinjection of LLM responses.
- Multi-source recognizers:
  - Regex recognizers for emails, phones, IBAN/BIC, URLs, fiscal IDs
    (SIREN/SIRET/VAT), names and addresses, across several languages
    (FR, EN, DE, ES, IT, PT).
  - Deny-list recognizers for organizations, people, places, and a
    singleton "parent organization" placeholder `[ORG]`.
  - Dictionary recognizers for first names and cities.
  - Optional GLiNER zero-shot NER recognizer (extra `ai`).
- Automatic language detection (lingua) with manual override.
- Business profiles (`acknowledge`, `invoice`, `email`) bundling deny
  lists, allow lists, patterns and policies, plus fictional test fixtures.
- Private-profile support (`profiles_private/`) with a fictional
  `example_acknowledge` template for user-specific deny lists.
- Multi-format output: TXT, JSON, JSONL, XML, CoNLL and HTML.
- Command-line tools `carnaval-anonymize` and `carnaval-reinject`.
- Structured logging via structlog.
- Packaging with hatchling, src layout, Apache-2.0 license.

[Unreleased]: https://github.com/carnaval-ai/carnaval/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/carnaval-ai/carnaval/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/carnaval-ai/carnaval/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/carnaval-ai/carnaval/releases/tag/v0.1.0
