# Contributing to Hermes Prompt Controls

Hermes Prompt Controls is an open source collaborative, pre-release project. We welcome focused bug
reports, compatibility evidence, documentation corrections and pull requests that preserve its
privacy boundary.

## Choose the right channel

- Use the bug form for reproducible behavior against a declared Hermes Agent baseline.
- Use the feature form for a scoped public contract or compatibility proposal.
- Use GitHub Private Vulnerability Reporting for undisclosed vulnerabilities.
- Use the pull request template for code or documentation changes.

Search open and closed issues first. The project does not promise a response time, acceptance or a
release date.

## Protect private prompt data

Every example must be fictional. Remove or replace directives, mappings, prompt content, profiles,
prefills, session IDs, conversation data, credentials, active endpoints, configuration, filesystem
paths, logs and caches.

Do not attach `config.json`, `session-state.json`, a real `directives/` tree or an operational
`HERMES_HOME`. Start a private vulnerability report when a sanitized reproduction cannot describe a
security issue safely.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

The behavioral test requires a clean, separately installed checkout of Hermes Agent at the baseline
documented in `docs/compatibility.md`. Hermes is a test host, not a runtime dependency.

```bash
python -m build
python -m twine check dist/*
python -m unittest discover -s tests -v
```

Documentation contributors use the frozen wiki lockfile:

```bash
cd wiki
npm ci
npm run build
```

## Change requirements

- Use English for code, comments, tests, fixtures, documentation, commits, issues and pull requests.
- Use only public Hermes Agent APIs pinned in the compatibility document.
- Preserve message roles, order, metadata, request isolation and idempotence.
- Keep unsupported request shapes and invalid input as sanitized no-ops.
- Do not introduce imports from private host modules, monkeypatches or gateway UI coupling.
- Do not add telemetry, analytics, live provider calls or credentials.
- Record the source, license, transformation and exclusions for incorporated behavior or code.
- Update compatibility and documentation when the supported host, request mode or failure contract
  changes.

## Pull requests

Explain the motivation, public behavior, Hermes baseline, request modes, privacy and cache effects,
fixtures, tests and documentation. Keep unrelated refactors out of the change.

A release is a separate decision. Do not bump `0.0.0`, create a tag or publish a package in an
ordinary contribution.

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
