---
title: System directive contract
description: Understand selection, ordering, request isolation, idempotence and no-op behavior.
sidebar:
  order: 1
---

The H1 proof reads ordered Markdown filenames from local configuration and resolves them under
`HERMES_HOME/prompt-controls/directives/`.

## Selection order

Selections compose in this order:

1. global;
2. exact platform;
3. exact model;
4. exact session.

A filename selected more than once is applied at its first position only. Platform, model and
session keys use exact matching without wildcard or normalization behavior.

## Request transformation

For `chat_completions`:

- the plugin copies each branch it modifies;
- a composed block is prepended to the first textual `system` message with a blank line;
- if no `system` message exists, one is inserted at the beginning;
- all other messages retain their role, order, content and metadata;
- an already present complete block or exact prefix is not added again.

Applying the same configuration twice produces the same request as applying it once.

## No-op and diagnostics

Missing configuration or selections are silent no-ops. Invalid JSON, invalid schema, unsafe
references, missing selected directives and unsupported content shapes leave the request unchanged
and emit at most one constant warning.

Diagnostics do not include prompt text, mappings, filenames, session identifiers or absolute paths.
The host remains fail-open, so the plugin does not claim to block an LLM call.
