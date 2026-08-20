---
title: Compatibility evidence
description: Review the pinned Hermes Agent baseline and the public APIs exercised by H1.
---

| Component | Baseline |
|-|-|
| Hermes Agent tag | `v2026.8.13` |
| Package version | `0.20.1` |
| Commit | `f80f453ae0679347e38abc917c7f94f717bf96c5` |
| Request mode | `chat_completions` |
| Plugin entry point | `prompt-controls = hermes_prompt_controls` |

H1 verifies public plugin discovery, `register(ctx)`, `llm_request`, slash-command registration,
request shapes and the host's fail-open middleware behavior. The test loads the plugin through the
same entry-point mechanism intended for a future package.

The source-linked evidence lives in
[`docs/compatibility.md`](https://github.com/Yivas/hermes-prompt-controls/blob/main/docs/compatibility.md).
A host update must pin a new revision, update those links and rerun the clean test before the support
statement changes.
