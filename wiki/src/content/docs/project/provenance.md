---
title: Provenance
description: Trace the public APIs, original implementation and publication exclusions.
sidebar:
  order: 2
---

The plugin is original project code written against public Hermes Agent APIs. No source file is
copied from an operational Hermes installation.

Public compatibility comes from Hermes Agent `v2026.8.13` at commit
`f80f453ae0679347e38abc917c7f94f717bf96c5`. The repository references plugin discovery,
registration, middleware, command and request-shape contracts through exact source links.

The mapping, ordering, idempotence, isolation and no-op rules are project contracts implemented with
the Python standard library and fictional tests. Gateway UI code, private imports, adapter
monkeypatches and operational prompt assets are excluded.

Read the full [provenance matrix](https://github.com/Yivas/hermes-prompt-controls/blob/main/docs/provenance.md)
before incorporating code, behavior or data from another source.
