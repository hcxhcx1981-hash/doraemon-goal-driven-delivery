"""Real JSON Schema Draft 2020-12 validation for the task ledger (dev-only).

DEVELOPMENT dependency: this file uses the `jsonschema` library (see
requirements-dev.txt). The shipped skill has ZERO runtime dependencies; this
checker is a release/CI gate, not part of the host execution path.

Positive cases must validate; negative cases MUST be rejected with an
explanation. Exit 0 = all expectations met; 1 = a positive failed or a
negative unexpectedly passed.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "task-ledger.schema.json").read_text(encoding="utf-8"))

# ---------- positive: minimal L-level ledger ----------
POSITIVE = [
    {
        "task_id": "T-1", "goal": "ship demo", "task_type": "CODE_DEV",
        "status": "IN_PROGRESS", "repair_rounds": {"total": 0},
        "updated_at": "2026-11-09T12:00:00+08:00",
    },
    {
        "task_id": "T-2", "goal": "audit", "task_type": "RESEARCH",
        "mode": "AUDIT", "status": "IN_PROGRESS",
        "budget": {"level": "L", "time_seconds": 3600, "tool_calls": 80,
                   "model": "gpt", "quota": "UNKNOWN"},
        "repair_rounds": {"total": 3, "a": 2, "b": 1},
        "completed": ["collect"], "remaining": ["verify"],
        "next_action": "verify", "updated_at": "2026-11-09T12:00:00+08:00",
    },
    {
        "task_id": "T-3", "goal": "block", "task_type": "CODE_DEV",
        "status": "BLOCKED", "blocked_reason": "quota exhausted",
        "final_status": "BLOCKED", "repair_rounds": {"total": 4},
        "updated_at": "2026-11-09T12:00:00+08:00",
    },
    {
        "task_id": "T-4", "goal": "async", "task_type": "CODE_DEV",
        "status": "IN_PROGRESS", "repair_rounds": {"total": 1},
        "async_tasks": [
            {"task_ref": "j1", "last_state": "running", "no_change_polls": 2,
             "stopped": True, "cancelled": False},
        ],
        "repair_events": [
            {"cause": "a", "new_evidence": True, "result": "FAIL",
             "evidence_refs": ["log-1"]},
        ],
        "updated_at": "2026-11-09T12:00:00+08:00",
    },
]

# ---------- negative: each MUST be rejected ----------
NEGATIVE = [
    ("missing required task_id",
     {"goal": "g", "task_type": "CODE_DEV", "status": "IN_PROGRESS",
      "repair_rounds": {"total": 0}, "updated_at": "2026-11-09"}),
    ("repair_rounds.total missing (count loss must reject)",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
      "status": "IN_PROGRESS", "repair_rounds": {"a": 1}, "updated_at": "2026-11-09"}),
    ("repair_rounds.total over cap 4",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV", "status": "IN_PROGRESS",
      "repair_rounds": {"total": 5}, "updated_at": "2026-11-09"}),
    ("single cause over cap 2",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV", "status": "IN_PROGRESS",
      "repair_rounds": {"total": 2, "a": 3}, "updated_at": "2026-11-09"}),
    ("L-level missing next_action",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV", "status": "IN_PROGRESS",
      "budget": {"level": "L"}, "repair_rounds": {"total": 0},
      "completed": [], "remaining": [], "updated_at": "2026-11-09"}),
    ("BLOCKED without blocked_reason",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV", "status": "BLOCKED",
      "repair_rounds": {"total": 2}, "updated_at": "2026-11-09"}),
    ("async poll: 2 no-change but not stopped",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV", "status": "IN_PROGRESS",
      "repair_rounds": {"total": 0}, "updated_at": "2026-11-09",
      "async_tasks": [{"task_ref": "j", "no_change_polls": 2, "stopped": False}]}),
    ("counted repair round without evidence ref",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV", "status": "IN_PROGRESS",
      "repair_rounds": {"total": 1}, "updated_at": "2026-11-09",
      "repair_events": [{"cause": "a", "new_evidence": True, "result": "FAIL"}]}),
    ("bad task_type enum",
     {"task_id": "T", "goal": "g", "task_type": "BUILD", "status": "IN_PROGRESS",
      "repair_rounds": {"total": 0}, "updated_at": "2026-11-09"}),
    ("unknown top-level property",
     {"task_id": "T", "goal": "g", "task_type": "CODE_DEV", "status": "IN_PROGRESS",
      "repair_rounds": {"total": 0}, "updated_at": "2026-11-09", "rogue": 1}),
]


def main():
    try:
        import jsonschema
        from jsonschema import Draft202012Validator
    except ModuleNotFoundError:
        print("SKIP: jsonschema dev dependency not installed (runtime has no deps).")
        print("Install requirements-dev.txt to run this gate.")
        return 2

    Draft202012Validator.check_schema(SCHEMA)  # schema itself is valid Draft 2020-12
    validator = Draft202012Validator(SCHEMA)
    ok = True
    for i, case in enumerate(POSITIVE):
        errs = list(validator.iter_errors(case))
        if errs:
            ok = False
            print(f"POSITIVE[{i}] UNEXPECTED FAIL: {sorted(e.message for e in errs)}")
        else:
            print(f"POSITIVE[{i}] OK")
    for name, case in NEGATIVE:
        errs = list(validator.iter_errors(case))
        if errs:
            print(f"NEGATIVE OK  : {name}")
        else:
            ok = False
            print(f"NEGATIVE FAIL: {name} (was unexpectedly accepted)")
    print("SCHEMA_CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
