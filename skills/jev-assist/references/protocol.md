# CLI contract v0.1.0

`<launcher>` means `python "<installed-skill>/scripts/jev.py"`.
The Python executable may be `python3` or a full interpreter path in your environment.
`doctor` checks local prerequisites only; it does not validate the key or network.

```text
<launcher> doctor --project "<root>"
<launcher> begin --project "<root>"
<launcher> ask --project "<root>" --task "<returned-task-id>" --request -
<launcher> end --project "<root>" --task "<returned-task-id>"
<launcher> stats
```

Send the following JSON through stdin, using actual reviewed excerpts, not placeholders:

```json
{
  "purpose": "classify_test_failures",
  "risk": "low",
  "deterministic_available": false,
  "evidence_sufficient": true,
  "expected_benefit": "batch_semantic_labels",
  "data_reviewed": true,
  "state": "A small, sanitized excerpt with enough evidence to classify a symptom.",
  "questions": {
    "category": {
      "type": "choice",
      "instructions": "Classify the symptom, not an unproven root cause.",
      "criteria": {
        "CACHE_STATE": "Stale cache state is reported",
        "NETWORK": "Network connection symptoms are reported",
        "NEEDS_REVIEW": "Insufficient evidence or another category"
      }
    }
  }
}
```

Allowed purposes: `classify_test_failures`, `rank_candidates`, `check_diff_scope`, `triage_review_comments`.
Benefit must be `avoid_reading_candidates`, `batch_semantic_labels`, or `independent_scope_check`.
These are labels supplied by the agent; code cannot prove that they are true.
High-risk requests are skipped. Low/medium requests still grant no permission.

`choice`: 2–12 string-label options with string descriptions; include `NEEDS_REVIEW`.
`score`: 2–10 ordered string descriptions in `criteria`; returned value is not a percentage.
`noul`: optional criteria `{"true":"...", "false":"..."}`; no fabricated confidence field.
All instructions and state must be strings in this version. Maximum 8 questions; combined serialized
provider payload including guard instructions defaults to 16,000 UTF-8 bytes, NOT tokens.

## Results

`ADVISORY` = validated live response, not approval or a correctness guarantee.
`MOCK` = synthetic abstention values; no network or inference.
`SKIP` = policy, metadata, duplicate, or budget condition prevents a call.
`FALLBACK` = unavailable service, invalid response, or a local error.
All results carry `advisory_only=true`, `authorization_granted=false`, and `codex_usage=null`.
Successful live results carry the actual provider `jev_usage`, model version, and typed answers.
Tool exit 0 means a workflow outcome was returned, NOT that JEV was called successfully. Inspect `status`.
Exit 2 means malformed CLI input or local operation failure.

## Limits and metadata

Default 3 reserved requests per shared user task; 30 per UTC day across all projects in the same
local state directory. Each retry is another reserved request. Defaults: 10-second subprocess
attempt timeout, zero retries, and 24-hour task expiration. An explicitly configured single retry
is only for HTTP 429/503/529 and honors a short Retry-After; longer waits fall back.
Do not reinterpret these development limits as provider limits, dollar caps, or sandbox enforcement.

Identical live requests in the same task are suppressed using a keyed fingerprint. No persistent
answer cache: reuse the earlier result already in the conversation. Changed content changes the
fingerprint; never change content just to evade suppression. Even a failed request is suppressed
unless its configured retry occurs internally. Original evidence must still be current.

The local database retains keyed fingerprints, task identifiers, counters, outcome codes, elapsed
time, model versions, and provider-reported token counts. It does not store prompts, answers,
API keys, or customer records. Users control cleanup; metadata is not automatically uploaded.
The hosting agent's transcript and the external provider have their own retention policies.
