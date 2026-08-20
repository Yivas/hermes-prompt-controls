# Security policy

Hermes Prompt Controls changes outbound LLM request content inside Hermes Agent. This policy covers
vulnerabilities in the plugin and its documented integration boundary.

## Supported versions

| Version | Supported |
|-|-|
| Unreleased `main` | Best effort; pre-release contract only |
| Published versions | None |

No stable package has been released. Reports must identify the commit tested and the Hermes Agent
baseline.

## Report a vulnerability privately

Use GitHub's **Report a vulnerability** form:
<https://github.com/Yivas/hermes-prompt-controls/security/advisories/new>.

Do not disclose an unpatched vulnerability in a public issue or pull request. Include, when
available:

- plugin commit and Hermes Agent version or commit;
- operating system, Python version and installation method;
- affected request mode and plugin operation;
- minimal reproduction using fictional directives and identifiers;
- expected and observed behavior;
- impact, prerequisites and known workaround.

Remove prompt content, real directives, model mappings, profiles, prefills, session identifiers,
conversation data, credentials, active endpoints, operational configuration, absolute paths, logs
and caches.

Maintainers will review the report and coordinate a fix and disclosure when possible. The project
does not promise a response deadline, embargo, bounty, CVE or release date.

## Security boundaries

- Hermes Agent is the host and retains its own middleware failure behavior.
- The pinned host is fail-open. The plugin leaves a request unchanged on invalid input or internal
  failure; it is not a policy enforcement boundary.
- `HERMES_HOME` is controlled by the operator. Traversal and static symlinks are rejected, but the
  plugin cannot defend against another authorized local process replacing files during a request.
- Existing cache metadata is preserved. Providers may derive a different cache identity after
  `system` content changes.
- The plugin contains no telemetry, analytics, provider client or network feature.

Tests use temporary homes, fictional data and blocked socket and subprocess calls during discovery
and request rewriting. Repository workflows must not require credentials or an operational Hermes
installation.
