# Doraemon Goal-Driven Delivery (V2.0.2 Release Candidate)

**Version 2.0.2 · Baseline V1.2 (SHA256 `D0DB9299…`) · One authorization, continuous delivery, evidence-based acceptance, bounded circuit breaker.**

[中文](README.md) · [Full rules CORE](SKILL.md) · [Installation](docs/INSTALLATION.md) · [Architecture](docs/ARCHITECTURE.md) · [Workflow](docs/WORKFLOW.md) · [Safety](docs/SAFETY.md) · [Dispatch example](examples/task-dispatch.md) · [Acceptance report template](examples/acceptance-report.md)

## Project positioning

This project is an execution-governance Skill (a prompt-layer execution protocol) — it is not an auto-scheduler, not a runtime sandbox, and it has no unverified host-level programmatic enforcement:

- It changes the Agent's unit of work from "step-by-step Q&A" to "fully acceptable outcomes": within one explicit authorization it completes implement → test → fix → re-test continuously; ordinary technical problems are handled autonomously; only material risk / irreversible / out-of-scope events are escalated to the user.
- It provides a failure circuit breaker (≤2 rounds per root cause, ≤4 rounds per task, stop without new evidence) and cross-session ledger recovery (`task-ledger.json` for L-level tasks only).
- It does **not** auto-install the Skill, does **not** provide host-level programmatic enforcement, and does **not** auto-purchase quota. Whether a host can enforce any rule is determined by real host testing; unverified capabilities are marked UNVERIFIED, never "supported".
- Platform safety rules, user authorization, project `AGENTS.md` and dev guards **take precedence over this Skill**; it grants no extra permissions.

## Architecture: CORE + one-level references + adapters

```
doraemon-goal-driven-delivery/
├── SKILL.md               # V2 CORE entry (compactness is a goal; high-risk must-stop always visible; 12 hard-rule pointers + machine fields)
├── references/            # One-level on-demand loading, no second-level nesting
│   ├── code-dev.md        #   CODE_DEV task rules
│   ├── research.md        #   RESEARCH task rules (AUDIT is its MODE)
│   ├── artifact.md        #   ARTIFACT task rules (incl. PPT sub-workflow)
│   ├── path-discovery.md  #   Path autonomous discovery (V1.2 A–H: stage/accelerator/gate)
│   ├── recovery.md        #   Circuit breaker/async/budget/cross-session/V1.2 governance §7/session reuse §8
│   └── machine-fields.md #   Machine fields + task classification spec (single source, no drift)
├── schemas/               # task-ledger.schema.json (JSON Schema Draft 2020-12)
├── adapters/              # Five host adapters: agnes / codex / hermes / workbuddy / codebuddy
├── tests/                 # Layered tests + reference impls (path_engine.py / ledger.py / schema_check.py)
├── docs/ examples/ LICENSE CHANGELOG.md
```

**Agent Skills standard compatibility**: `SKILL.md` frontmatter follows the agentskills.io standard — required `name` (must equal the directory name) + `description`; non-standard fields (version/base/tasks) moved into the `metadata` map; `license` uses the standard optional field.

## Task classification (three top-level types only, no new top-level types)

| TASK_TYPE | Classification (by primary deliverable) | Loads | Note |
|---|---|---|---|
| CODE_DEV | deliverable = code/feature/fix/config | code-dev.md | V1.2 BUILD mapped here |
| RESEARCH | deliverable = research/verification/conclusion/evidence | research.md | **AUDIT is MODE=AUDIT, not a top-level type** |
| ARTIFACT | deliverable = doc/PPT/spreadsheet/web | artifact.md | **PPT is a subtype**, using the artifact.md "PPT dedicated workflow" |

Mixed deliverables classify by the primary one; secondary requirements go to GAPS and load only the primary reference. Single source for classification & fields: [machine-fields.md](references/machine-fields.md).

### Three task-type usage examples (dispatch body fragments)

| Task | Dispatch fields | Classification | Loads |
|---|---|---|---|
| Add incremental pull to the auction collector | `TASK_TYPE=CODE_DEV` `GOAL=…` `BUDGET={level:M,time_seconds:1800,tool_calls:25}` | CODE_DEV | code-dev.md |
| Re-verify whether a previous audit conclusion still holds | `TASK_TYPE=RESEARCH` `MODE=AUDIT` | RESEARCH (AUDIT = its MODE) | research.md |
| Produce a V2-architecture PPT for review | `TASK_TYPE=ARTIFACT` (PPT subtype) | ARTIFACT | artifact.md "PPT dedicated workflow" |

Each example spells out GOAL / scope / acceptance / authorization / BUDGET in the dispatch; the Agent executes continuously in one pass and handles ordinary technical choices autonomously — only material risk is escalated.

## Soft rules vs runtime hard limits (must be distinguished)

- **Soft rules (this Skill)**: all 12 hard rules, the 2/4-round circuit breaker, the poll stop, and ledger inheritance are **prompt-layer conventions** the model is asked to follow. Where a host has no programmatic enforcement, "circuit breaking" shows up as the Agent stopping and recording, not as a runtime block.
- **Runtime hard limits (host/platform, not this Skill)**: tool permissions, production gates, authorization boundaries, and quota are controlled by the platform / user authorization; this Skill **grants none of them and does not bypass them**.
- Host capability is therefore labeled by real testing (table below); unverified items stay UNVERIFIED. Never treat "the host supports this / it is verified" as a default fact.

## Progressive loading & session reuse

- **One-level references**: CORE holds pointers only; references never nest-reference other references (code-dev.md inlines circuit-breaker points instead of a second-level link to recovery.md).
- **On-demand triggers**: ordinary tasks load no reference; path-discovery.md loads only when a local file/project/config/Skill/report is referenced without a precise path; recovery.md loads on circuit breaker/async/budget/recovery/governance boundary.
- **Session reuse (recovery.md §8)**: within one session CORE loads once; the same task does not re-read already-read references; a new task loads only newly needed references; a new session recovering an L-level task reads the **ledger recovery point (next_action / counts / budget) first, never replays the full history**.

## Budget & circuit breaker

- Task size S/M/L set by the dispatcher; unreadable budget keys write `UNKNOWN` (never a shortened form), unreadable quota writes `QUOTA=UNKNOWN`.
- Circuit breaker inherits V1.2 rules A–E: ≤2 evidenced rounds per cause; ≤4 valid rounds per task; stop without new evidence; no rename/split/restart to evade counts.
- Each repair round records: root-cause hypothesis / supporting evidence / minimal change / acceptance method; counted rounds must link ≥1 evidence ref in `repair_events` (a `new_evidence=true` round without refs is rejected).
- **Async guard**: wait for completion notifications; after 2 consecutive no-change polls the **poller stops** — stopping the poll is **not** cancelling the background task; cancellation is a separate `cancelled` flag in the ledger.
- **Counts are not lost**: the L-level ledger's `repair_rounds.total` is mandatory; when the counter is missing, continued repair is **refused — never defaulted to zero**; when there is no new evidence the `BLOCKED` state is persisted (status + blocked_reason + final_status written together).

## Cross-session recovery (L-level only)

See [schemas/task-ledger.schema.json](schemas/task-ledger.schema.json) (Draft 2020-12). Recovery: read ledger → verify deliverables still exist → inherit repair counts & budget → resume from `next_action` → do not redo verified work. The ledger is never committed to a public repo and never records keys/privacy.

## Host adapters (four-state, honest labeling)

| Host | DISCOVERED | INSTALLED | LOADED | BEHAVIOR_VERIFIED |
|---|---|---|---|---|
| Agnes Code | skills dir writable | pending install round (this package does not install) | UNVERIFIED | UNVERIFIED |
| Codex | skills dir writable | pending install round | UNVERIFIED | UNVERIFIED |
| Hermes | existing copy is V1.1; sync required before V2 | no (currently V1.1) | UNVERIFIED | UNVERIFIED |
| WorkBuddy | dir exists | no (dispatch-injected) | UNVERIFIED | UNVERIFIED |
| CodeBuddy | no install dir dependency | no (dispatch-injected) | UNVERIFIED | UNVERIFIED |

See [adapters/](adapters/). The CodeBuddy inline rules are **consistency-checked against the CORE** (reproducible static check via `tests/consistency_check.py`; there is no generator, so auto-generation is never claimed); unverified capabilities are never written as "auto-supported".

## Installation & testing

```powershell
# Installation (install round; this preview/RC package does not install or modify host config): docs/INSTALLATION.md
python -X utf8 -m unittest discover -s tests -v      # full layered test suite (shipped reference impls + self-built git fixtures)
python -X utf8 tests\schema_check.py                  # JSON Schema Draft 2020-12 real positive/negative validation (needs jsonschema, a dev dependency)
python -X utf8 tests\behavior_ac.py                   # host-simulated behavior test (simulation ≠ real host behavior verification)
python -X utf8 tests\consistency_check.py             # CodeBuddy inline-rules vs CORE consistency check (reproducible, exit 0 = aligned)
```

**Dependency separation**: runtime has zero dependencies (Python stdlib); dev dependency in `requirements-dev.txt` (jsonschema, used only by schema_check and full validation). The ZIP runs all tests after extraction; git fixtures are self-built by tests (`make_git_fixture`), not dependent on a hidden `.git` shipped in the ZIP.

**Test layers** (quality over count):
1. Static rule tests: document contracts / frontmatter / links / secret patterns / CORE budget;
2. Real code tests: shipped `path_engine.py` + `ledger.py` with real git repo fixtures;
3. Simulation tests: behavior pipeline simulated in a temp tree (explicitly labeled "simulation", not real host behavior verification);
4. Host behavior tests: must run an isolated E2E in the real host (CX/AC runtime LOADED/BEHAVIOR_VERIFIED cannot be verified by this package; all UNVERIFIED).

## Verification status (as of 2026-11-09)

| Item | Status |
|---|---|
| V1.2 authoritative source / backup / AC & Codex installed copies | zero-change hashes verified (D0DB9299 / 4BA20606) |
| Full test suite (static + real code + simulation) | see tests/*.log |
| schema Draft 2020-12 positive/negative | schema_check.py (jsonschema 4.26.0) |
| Host LOADED / BEHAVIOR_VERIFIED | all UNVERIFIED (needs real-host E2E) |
| Hermes sync | still V1.1; must upgrade before V2 deployment |

## Safety limits

- No leaking/uploading keys, tokens, cookies, passwords, private data or `.env`; no auto-purchasing quota; unreadable quota = `QUOTA=UNKNOWN`.
- No modifying/bypassing project safety gates; irreversible operations, privilege escalation, privacy exfiltration, and new costs must stop and escalate.
- Release scan: secret patterns, real privacy, user local absolute paths, log leakage; all files UTF-8.
- The MIT license covers only this repository's content (see [LICENSE](LICENSE)); it does not cover third-party Agent implementations or trademarks.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) (2.0.2 RC: 9 structural fixes + professional README; 2.0.1: audit-defect round 2; 2.0.0-draft: initial build).
