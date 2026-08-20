# Provenance and publication boundary

Hermes Prompt Controls is an original community plugin implemented against public Hermes Agent APIs.
No source file is copied from an operational Hermes installation.

## Public sources

| Source | Version | Use | Transformation | License treatment |
|-|-|-|-|-|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | `v2026.8.13`, commit `f80f453ae0679347e38abc917c7f94f717bf96c5` | Plugin discovery, `register(ctx)`, `llm_request`, command registration and public request shapes | Referenced through public APIs; no Hermes source is redistributed | Hermes remains a separately installed host under its own terms |
| Python standard library | Python 3.11–3.13 | JSON, paths, copying, locking primitives and diagnostics | Used through public APIs | Distributed with Python, not vendored |
| Project contract and tests | Current repository | Exact mappings, ordering, idempotence, no-op rules and fictional fixtures | Written for this project from approved public behavior requirements | MIT, copyright Yivas |

The compatibility document links the exact public Hermes symbols used by the proof. A future host
update must revise those links and rerun the clean compatibility test.

## Explicit exclusions

The repository and its distributions exclude:

- `config.json`, `session-state.json` and real `directives/` trees;
- model mappings, prompt profiles, prefills and private system prompts;
- credentials, active endpoints, account or conversation identifiers;
- logs, caches, locks, backups and operational runtime state;
- gateway UI code, adapter monkeypatches and private imports;
- prompts, conversations, profiles or files from an operational Hermes home.

Tests create temporary fictional directives and identifiers. They do not read a user's
`HERMES_HOME`, require credentials or contact a provider.

## Publication process

The first public repository history is created from an explicit, reviewed file list. Earlier local
planning and agent-rule commits are retained only in a private ignored bundle and are not pushed.
Builds must list wheel and sdist contents before any package release is approved.
