# Repository maintenance rules

This file governs development of this repository. It is not the user-global JEV router.

- Keep runtime dependencies standard-library-only unless a user approves a change.
- Run `python -m unittest discover -s tests -v` and `python -m jev_workflow demo` after changes.
- Never contact a real provider in ordinary tests or CI. Use synthetic fixtures.
- Preserve advisory-only output, project consent, opt-outs, bounded requests and fail-closed validation.
- Never enable Live, authorize a project, search for credentials, or increase budgets without explicit user instruction.
- Never put secrets, raw customer data, source-repository excerpts or session logs in commits.
- Separate offline tests, live API verification, Codex behavior tests, and actual benchmark results.
- Do not claim reduced tokens, quota usage, cost, latency or defects without matched measurements.
- Check current official API documentation before changing transport/schema. Do not invent fields.
- Do not publish, push, release, or change repository visibility without an explicit destination and authorization.
