# Hermes compatibility

## Validated baseline

| Component | Validated value |
|-|-|
| Hermes Agent release | `v2026.8.13` |
| Hermes Agent commit | `f80f453ae0679347e38abc917c7f94f717bf96c5` |
| First approved API mode | `chat_completions` |
| Installation topology | pip entry point `hermes_agent.plugins` |
| Plugin entry point | `prompt-controls = hermes_prompt_controls` |

The baseline is the public commit behind the `v2026.8.13` tag. Compatibility evidence is pinned to that commit so later changes on `main` cannot alter the cited contract.

## Observed contract

- Hermes discovers pip packages through the `hermes_agent.plugins` entry-point group, records each entry-point name as the plugin key, and loads the referenced module: [`hermes_cli/plugins.py` lines 4292-4317](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/plugins.py#L4292-L4317) and [lines 4776-4791](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/plugins.py#L4776-L4791).
- The loader reads the module-level `register` function, creates `PluginContext`, calls `register(ctx)`, and records active middleware registrations: [`hermes_cli/plugins.py` lines 4553-4593](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/plugins.py#L4553-L4593).
- `ctx.register_middleware("llm_request", callback)` adds the callback to the middleware registry: [`hermes_cli/plugins.py` lines 3189-3215](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/plugins.py#L3189-L3215).
- `ctx.register_command(name, handler, description, args_hint)` registers an in-session slash command whose handler receives only the raw argument string: [`hermes_cli/plugins.py` lines 2000-2056](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/plugins.py#L2000-L2056). The public contract does not provide the active platform, model, or session to that handler.
- Before a provider call, Hermes passes the effective provider kwargs as `request`, plus `task_id`, `turn_id`, `api_request_id`, `session_id`, `platform`, `model`, `provider`, `base_url`, `api_mode`, and `api_call_count`: [`agent/conversation_loop.py` lines 2592-2607](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/agent/conversation_loop.py#L2592-L2607).
- Request middleware receives `request` and `original_request`. A callback may return `{"request": {...}}`; Hermes ignores other return shapes and returns `RequestMiddlewareResult(payload, original_payload, changed, trace)`: [`hermes_cli/middleware.py` lines 38-44](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/middleware.py#L38-L44) and [lines 77-119](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/middleware.py#L77-L119).
- In `chat_completions`, provider kwargs contain `model` and a `messages` list in OpenAI chat format. A leading `system` message remains in that list except for model-specific role conversion handled by Hermes: [`agent/transports/chat_completions.py` lines 356-419](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/agent/transports/chat_completions.py#L356-L419).

## Failure behavior observed

Hermes isolates each request-middleware callback. It logs an exception, discards that callback result, and continues with the remaining results: [`hermes_cli/plugins.py` lines 5170-5191](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/hermes_cli/plugins.py#L5170-L5191). The conversation loop also catches a failure around the complete request-middleware pass and keeps the current request: [`agent/conversation_loop.py` lines 2592-2612](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/agent/conversation_loop.py#L2592-L2612).

This is fail-open host behavior. The plugin does not claim that middleware can block an LLM call.

## Prompt-controls contract proven in H1

The proof reads only from `HERMES_HOME/prompt-controls/`:

- `directives/*.md` is the local directive library.
- `config.json` contains ordered `global`, `platforms`, and `models` selections.
- `session-state.json` contains exact `sessions` selections and stays separate from stable configuration because session identifiers are local state.
- Layers compose in global, platform, model, then session order. Duplicate filenames are applied once.
- The composed block is prepended when the first `system` message contains text. If no `system` message exists, a new one is inserted first; other `system` content shapes are unsupported no-ops.
- Reapplying the same selection is a no-op. Caller-owned request data and `original_request` remain unchanged.
- Missing `config.json`, `session-state.json`, or selections are silent no-ops. Invalid JSON or schema, unsafe references, missing selected directives, unsupported API modes, and unsupported message shapes produce one constant warning and preserve the request.
- Cache-related request fields and message metadata are copied unchanged. The plugin modifies only textual `system` content and does not create or rewrite cache keys; providers may derive a different cache identity from the changed prompt.

The `/prompt-controls` command lists library files and changes global, platform, or model selections under an interprocess lock with atomic replacement of `config.json`. Session selection remains a manual edit in H1: the pinned public slash-command handler receives raw arguments but no active session context. The plugin does not infer session identity from process-global state.

`HERMES_HOME` is operator-owned. Static symlinks and traversal are rejected so ordinary configuration cannot escape `directives/`; the plugin does not claim to resist a same-user process that can replace files inside that home during a request.

## Decisions

`chat_completions` is the first supported API mode because it is Hermes's default OpenAI-compatible path and keeps `system` content in the `messages` role sequence. Native Anthropic, Responses, Bedrock, and Codex app-server shapes remain unsupported until each receives its own behavioral test.

The pip entry point is the minimum installation topology for this repository. It uses the existing `src/hermes_prompt_controls` package, needs no copied directory under `HERMES_HOME`, and is the documented public-distribution path in Hermes: [`website/docs/developer-guide/plugins/index.md` lines 1533-1545](https://github.com/NousResearch/hermes-agent/blob/f80f453ae0679347e38abc917c7f94f717bf96c5/website/docs/developer-guide/plugins/index.md#L1533-L1545).

## Validation evidence

The original clean-room check used Python 3.12.9 in a new virtual environment. The same two tests were later repeated successfully on Python 3.11, 3.12, and 3.13. Hermes was installed editable from the clean pinned checkout because its build explicitly rejects wheels; this package was installed as a wheel from its checkout. The test then ran from the Hermes checkout, matching its supported development launch layout:

```text
Hermes checkout: v2026.8.13 / f80f453ae0679347e38abc917c7f94f717bf96c5
Hermes package:   hermes-agent 0.20.1
Plugin package:   hermes-prompt-controls 0.0.0
Entry point:      prompt-controls = hermes_prompt_controls
Baseline check:   Git commit and hermes-agent package version matched
Tests:            2 passed
Behavior:         layered rewrite, insertion, cache-field preservation, idempotence, no-op,
                  diagnostics, symlink rejection, command handler, concurrent config writes,
                  host failure
Network/process:  connect, connect_ex, sendto, create_connection, and Popen blocked
Credentials:      environment cleared before Hermes import and plugin execution
HERMES_HOME:      temporary directory with fictional files and identifiers
```

## Proven scope

The current module registers `llm_request` and `/prompt-controls`. `tests/test_registration.py` verifies through Hermes `PluginManager`, with sockets and subprocesses blocked, that a clean pip installation is discovered and enabled. The host exposes no public inspection API for registrations, so the test reads the manager's private registration collections and temporarily replaces the manager accessor as test instrumentation. Product code does not import, patch, or depend on those private members. Fictional fixtures cover layered composition, insertion without an existing `system` message, idempotence, request ownership, command updates, absent mappings, invalid configuration, unsupported shapes, sanitized diagnostics, and fail-open callback failure.

Only `chat_completions` and fictional Markdown directives are proven. Native Anthropic, Responses, Bedrock, Codex app-server, session-aware command mutation, release packaging, provenance review, and the full H1 gate remain open.
