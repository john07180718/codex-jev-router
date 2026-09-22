# Codex JEV Router

Repository: <https://github.com/john07180718/codex-jev-router>

An optional, advisory-only development workflow: Codex may select a skill for narrow semantic
classification, candidate relevance, review triage, or an explicit diff-scope check. Ordinary coding,
search, arithmetic and tests stay with Codex and deterministic tools.

**Experimental v0.1.0. Independent community project, not an OpenAI or TypeSafe product.**
No guaranteed token reduction, speedup, accuracy improvement or subscription-quota savings.
See the [Chinese README](README.md), [validation record](docs/VALIDATION.md), and [security policy](SECURITY.md).

## Try offline

Python 3.10+, standard library only at runtime. From the repository root:

```bash
python -m jev_workflow demo
python -m unittest discover -s tests -v
python tools/install.py --scope user --global-rule
python tools/install.py --scope user --global-rule --apply
```

Installation copies a self-contained skill/CLI into `$HOME/.agents/skills/jev-assist` and optionally
merges a small managed block into the active global `AGENTS.md`/`AGENTS.override.md` under
`CODEX_HOME`. It backs up existing content and refuses unmanaged or modified skill conflicts.
Restart Codex and verify local discovery. Windows, WSL and remote environments need separate setup.

Default mode is **mock**: no key, no network and no inference. For real work, the skill skips JEV until
live-mode prerequisites are met. An explicit user must authorize each canonical project path, enable
live mode, and safely provide their own `TYPESAFE_API_KEY` to the Codex process. API access and fees
are the user's responsibility. Neither installation nor `doctor` proves real connectivity.

```bash
python -m jev_workflow authorize --project "/path/to/project" --allow-external-data
python -m jev_workflow configure --mode live
python tools/with_key.py codex
```

The last command is for a human interactive terminal only. It asks for the key with hidden input and
passes it through the child process environment, without saving it. It is not secret isolation.

## Guarantees and boundaries

The wrapper enforces its own schema, project consent, payload-size limits, duplicate suppression and
SQLite-backed call reservations. Default: three calls per shared user task, thirty per UTC day in
one local state directory, ten-second worker timeout, no retries. Configurable retries count against
the same budgets. It does not meter or constrain arbitrary calls outside the wrapper.

It supports a restricted string-based subset of TypeSafe Choice, Score and Noul; not a full SDK.
All results are advisory and always carry `authorization_granted=false`. No deployment, trade,
payment, deletion or runtime product integration is authorized. Regex privacy checks are best-effort,
not complete DLP. Do not submit secrets or unauthorized data. A timeout may still be billed.

No raw prompts, keys or responses are persisted by the usage ledger. The host agent's transcript and
the provider have separate retention policies. Metrics never infer Codex tokens; import verified
measurements for paired comparisons using `tools/compare_usage.py`.

CI runs offline tests only and requires no provider credentials. Live API, Codex end-to-end activation,
cross-platform CI and performance results must be verified in their actual environments before claiming
support. Latest checked official references: [sources](docs/SOURCES.md).

MIT licensed. This project has not been published to a package registry or plugin directory by this
source bundle; do not assume similarly named registry packages are this code.
