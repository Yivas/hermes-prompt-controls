# Hermes Prompt Controls

Hermes Prompt Controls is an unofficial, community-maintained Hermes Agent plugin for explicit
per-model `system` prompt controls. It uses the public plugin entry point and request middleware; it
does not modify Hermes Agent core.

[Documentation](https://yivas.github.io/hermes-prompt-controls/) ·
[Compatibility](docs/compatibility.md) · [Contributing](CONTRIBUTING.md) ·
[Security](SECURITY.md)

## Status

- **Stage:** pre-release. No package version, tag or PyPI release has been published.
- **Project mode:** open source collaborative. In-scope issues and pull requests are welcome.
- **Hermes baseline:** `v2026.8.13`, package `0.20.1`, commit
  `f80f453ae0679347e38abc917c7f94f717bf96c5`.
- **Supported request mode:** `chat_completions`.
- **Python evidence:** 3.11, 3.12 and 3.13 are covered by the declared development matrix.

The current code is an H1 compatibility proof. It demonstrates installation, plugin discovery,
registration, a slash command and fictional layered `system` rewriting. It is not a stable public
API and must not be installed as though it were a released package.

## Scope

The repository may contain plugin code, tests, packaging metadata, documentation and fictional
fixtures. It does not contain or distribute:

- operational directives or model mappings;
- prompt profiles, prefills or private system prompts;
- session state, conversation data, logs or caches;
- credentials, active endpoints or operator configuration;
- telemetry, analytics or phone-home behavior.

Gateway UI, adapter monkeypatches, automatic profile selection and changes to Hermes Agent core are
out of scope.

## Development installation

The compatibility test uses a clean checkout of the pinned Hermes Agent commit. Hermes is the host,
not a runtime dependency of this package.

```bash
git clone https://github.com/Yivas/hermes-prompt-controls.git
cd hermes-prompt-controls
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Clone and install the pinned host separately:

```bash
git clone https://github.com/NousResearch/hermes-agent.git ../hermes-agent
git -C ../hermes-agent checkout f80f453ae0679347e38abc917c7f94f717bf96c5
python -m pip install -e ../hermes-agent
cd ../hermes-agent
python -m unittest discover -s ../hermes-prompt-controls/tests -v
```

The behavioral test uses a temporary `HERMES_HOME`, fictional directives, no credentials and
blocked socket and subprocess calls during plugin discovery and execution.

## Proven contract

The package exposes the entry point:

```toml
[project.entry-points."hermes_agent.plugins"]
prompt-controls = "hermes_prompt_controls"
```

The plugin registers `llm_request` middleware and `/prompt-controls`. H1 proves:

- ordered global, platform, model and session selections;
- exact matching without wildcards or normalization;
- insertion or prepending of text to the first textual `system` message;
- request copying, metadata preservation and idempotence;
- sanitized no-op behavior for missing, invalid, unsafe or unsupported input;
- fail-open host behavior without leaking prompt content, mappings, IDs or paths.

See [Compatibility evidence](docs/compatibility.md) and
[Provenance](docs/provenance.md) for the pinned public symbols, transformations and exclusions.

## Local configuration proof

The H1 proof reads operator-owned files under:

```text
HERMES_HOME/prompt-controls/
├── config.json
├── session-state.json
└── directives/
```

These files are local state and are ignored by Git. The repository does not provide real
directives, mappings or session identifiers. Examples in tests and documentation are fictional.

`HERMES_HOME` is a trust boundary, not a sandbox. The plugin rejects traversal and static symlinks,
but it does not protect against another process that can already replace files inside that home.

## Security and privacy

The pinned Hermes host is fail-open. Invalid plugin input leaves the outbound request unchanged and
emits at most one constant diagnostic. The plugin cannot promise to block an LLM call when the host
middleware fails.

Changing `system` content can change provider-derived cache identity. The plugin preserves existing
cache fields but does not create, reinterpret or rewrite cache keys.

Report vulnerabilities through GitHub Private Vulnerability Reporting. Do not include directives,
prompts, session IDs, active configuration or logs in public issues. Read [SECURITY.md](SECURITY.md)
for the reporting and redaction requirements.

## Documentation and participation

The maintained documentation is published at
<https://yivas.github.io/hermes-prompt-controls/>. Its source lives under `wiki/`.

Use [GitHub Issues](https://github.com/Yivas/hermes-prompt-controls/issues) for reproducible bugs
and scoped proposals after searching existing reports. Pull requests must follow
[CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License and affiliation

Hermes Prompt Controls is licensed under the [MIT License](LICENSE). It is an unofficial community
project and is not part of, sponsored by or endorsed by Hermes Agent or Nous Research.
