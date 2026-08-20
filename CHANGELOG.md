# Changelog

This project follows semantic versioning after its first release. Until then, verified work remains
under `Unreleased` and does not imply a published package.

## Unreleased

### Added

- Public Hermes Agent compatibility evidence for plugin discovery, middleware registration,
  `chat_completions` request rewriting and command registration.
- Fictional tests for layered `system` directives, no-op behavior, idempotence, request isolation,
  sanitized diagnostics and concurrent configuration writes.
- Repository documentation, community files, CI and a versioned Starlight documentation site.

### Security

- Explicit exclusion of directives, mappings, profiles, prefills, session state, logs, credentials,
  caches and operational configuration from the public repository and distributions.
