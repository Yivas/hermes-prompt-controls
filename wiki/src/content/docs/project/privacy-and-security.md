---
title: Privacy and security
description: Keep operational prompt data outside the repository and understand the fail-open boundary.
sidebar:
  order: 1
---

Local configuration can contain prompt content, model mappings and session identifiers. Treat the
entire `HERMES_HOME/prompt-controls/` directory as sensitive operator state.

The repository and distributions exclude configuration, directives, profiles, prefills, session
state, credentials, endpoints, logs and caches. Tests use fictional files in a temporary home.

`HERMES_HOME` is an operator trust boundary, not a sandbox. Static symlinks and path traversal are
rejected, but another process with write access to that home can still replace files during a
request.

The pinned Hermes Agent host is fail-open. If plugin input is invalid or middleware fails, the
request remains unchanged. Do not use the plugin as a security policy enforcement layer.

Report plugin vulnerabilities through GitHub Private Vulnerability Reporting. Never put real
prompt data or session identifiers in a public issue.
