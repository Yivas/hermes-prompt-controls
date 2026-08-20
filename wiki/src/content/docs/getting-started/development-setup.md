---
title: Development setup
description: Install the plugin proof beside the exact Hermes Agent host used by H1.
sidebar:
  order: 1
---

Hermes Prompt Controls has no published package. Use a clean development checkout:

```bash
git clone https://github.com/Yivas/hermes-prompt-controls.git
cd hermes-prompt-controls
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Install the pinned host separately:

```bash
git clone https://github.com/NousResearch/hermes-agent.git ../hermes-agent
git -C ../hermes-agent checkout f80f453ae0679347e38abc917c7f94f717bf96c5
python -m pip install -e ../hermes-agent
cd ../hermes-agent
python -m unittest discover -s ../hermes-prompt-controls/tests -v
```

The test creates a temporary `HERMES_HOME`, installs fictional directives and blocks sockets and
subprocesses during discovery and request rewriting. It must not read an operational Hermes home or
require provider credentials.

:::caution
Do not copy the examples into an operational environment without reviewing the pre-release code and
its fail-open boundary. There is no stable package or migration guarantee.
:::
