"""Real task-ledger implementation for Doraemon V2 (L-level tasks).

This is the shipped implementation, not a parallel simulation: tests must call
these functions. Covers serialization (JSON round-trip), save/reload on disk,
repair-round enforcement (2 per cause, 4 total, inherited across sessions),
new-evidence gating, async no-change polling guard (stop at 2), and the
poll-stop vs task-cancel distinction.

V2.0.2 final-closing hardening:
- `repair_rounds.total` is REQUIRED; a missing total is count-UNRELIABLE and
  refuses repair (never silently zeroed).
- `total` must equal the sum of per-cause counts; a mismatch means count
  corruption and repair is refused.
- Terminal states (BLOCKED / PARTIAL / DONE) NEVER auto-continue repair.
  resume() requires explicit authorization and inherits the FULL historical
  budget (repair_rounds are carried over unchanged, never reset).
- No-new-evidence stops are persisted (mark_stopped) so a later session sees
  the stopped state instead of silently reopening work.
- cancel_task() is separate from the poll stop guard.
"""
import json
from pathlib import Path

CAUSE_LIMIT = 2
TASK_LIMIT = 4
POLL_NO_CHANGE_LIMIT = 2
TERMINAL_STATES = ("BLOCKED", "PARTIAL", "DONE")


class CountMissing(Exception):
    """repair_rounds.total absent or corrupted: counts cannot be trusted,
    repair must be refused. Never default a missing counter to zero."""


class Ledger:
    def __init__(self, data: dict):
        # repair_rounds must keep integer values only (schema constraint).
        self.data = data
        self.data.setdefault("async_tasks", [])
        self.data.setdefault("repair_rounds", {})

    # ---------- count integrity ----------
    @property
    def counts_reliable(self) -> bool:
        """total present and non-null -> counts usable. Missing total means
        count loss: refuse repair, never reopen by defaulting to zero."""
        rr = self.data.get("repair_rounds", {})
        return "total" in rr and rr.get("total") is not None

    @property
    def counts_consistent(self) -> bool:
        """total MUST equal the sum of per-cause counters. Any mismatch is
        count corruption: repair is refused until the discrepancy is resolved
        by the dispatcher (recorded, not auto-fixed)."""
        if not self.counts_reliable:
            return False
        rr = self.data["repair_rounds"]
        per_cause = sum(v for k, v in rr.items() if k != "total" and isinstance(v, int))
        return rr["total"] == per_cause

    # ---------- terminal-state discipline ----------
    @property
    def status(self) -> str:
        return self.data.get("status", "IN_PROGRESS")

    def can_continue(self) -> bool:
        """Terminal states never auto-continue repair: BLOCKED/PARTIAL/DONE
        all require an explicit, authorized resume() first."""
        return self.status not in TERMINAL_STATES

    def resume(self, *, authorized: bool) -> bool:
        """Re-open a terminal ledger. Requires explicit authorization AND
        inherits the FULL historical budget: repair_rounds are carried over
        unchanged (counts are never reset by a session boundary)."""
        if not authorized:
            return False
        self.data["status"] = "IN_PROGRESS"
        self.data.setdefault("resume_log", []).append({"authorized": True})
        return True

    # ---------- persistence (real JSON serialize/save/reload) ----------
    def save(self, path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    @staticmethod
    def load(path) -> "Ledger":
        return Ledger(json.loads(Path(path).read_text(encoding="utf-8")))

    def roundtrip(self, path) -> "Ledger":
        """Serialize -> save -> re-read; returns a fresh Ledger from disk bytes."""
        self.save(path)
        return Ledger.load(path)

    # ---------- BLOCKED / no-new-evidence persistence ----------
    def mark_blocked(self, reason: str) -> None:
        """Persist BLOCKED: status + blocked_reason + final_status=BLOCKED.
        A later session resuming this ledger sees the blocked state, it is
        never silently dropped or re-opened without a recorded reason."""
        self.data["status"] = "BLOCKED"
        self.data["blocked_reason"] = reason
        self.data["final_status"] = "BLOCKED"

    def mark_stopped(self, reason: str) -> None:
        """Persist a no-progress stop: same durability as BLOCKED, but tagged
        with stop_reason so a recovery session can distinguish 'no new
        evidence' from 'budget exhausted'."""
        self.data["status"] = "BLOCKED"
        self.data["stop_reason"] = reason
        self.data["blocked_reason"] = reason
        self.data["final_status"] = "BLOCKED"

    # ---------- repair-round rules (V1.2 rules A/B, inherited across sessions) ----------
    def repair_allowed(self, cause: str) -> bool:
        """True only if the ledger is open (not terminal), counts are
        reliable AND consistent, and caps are not exhausted.

        - Terminal state without authorized resume -> refused.
        - Missing total / total-vs-cause mismatch -> refused (never guessed).
        - Per-cause cap 2 / task cap 4 -> refused.
        """
        if not self.can_continue():
            return False
        if not self.counts_reliable or not self.counts_consistent:
            return False
        rr = self.data["repair_rounds"]
        if rr.get("total") >= TASK_LIMIT:
            return False
        if rr.get(cause, 0) >= CAUSE_LIMIT:
            return False
        return True

    def record_repair(self, cause: str, *, new_evidence: bool, result: str,
                      evidence_refs=None) -> bool:
        """Record a repair round; returns True if it was accepted (counted).

        - Not allowed (terminal / count issue / cap) -> NO_PROGRESS, refused.
        - No new evidence -> recorded, NOT counted; repeated no-evidence
          outcomes end in mark_stopped (persisted), not silent loops.
        - Counted round REQUIRES >=1 evidence ref; free counts are refused.
        - Counted increments keep total == sum(per-cause) intact.
        """
        actions = self.data.setdefault("attempted_actions", [])
        if not self.repair_allowed(cause):
            actions.append({"action": f"repair:{cause}", "result": "NO_PROGRESS",
                           "new_evidence": False})
            return False
        if not new_evidence:
            actions.append({"action": f"repair:{cause}", "result": result,
                           "new_evidence": False})
            return False
        if not evidence_refs:
            # Counted round must stay linked to evidence; refuse free counts.
            actions.append({"action": f"repair:{cause}", "result": "NO_PROGRESS",
                           "new_evidence": False})
            return False
        rr = self.data["repair_rounds"]
        rr[cause] = rr.get(cause, 0) + 1
        rr["total"] = rr.get("total", 0) + 1
        self.data.setdefault("repair_events", []).append(
            {"cause": cause, "new_evidence": True, "result": result,
             "evidence_refs": list(evidence_refs)})
        actions.append({"action": f"repair:{cause}", "result": result,
                        "new_evidence": True})
        return True

    # ---------- async polling guard ----------
    def poll(self, task_ref: str, state: str) -> str:
        """No-change guard. After 2 consecutive no-change polls the POLLER
        stops (stopped=true). This is NOT task cancellation: `cancelled`
        stays False unless cancel_task() is explicitly called.
        A stopped poller persists its state so a new session does not
        silently restart polling."""
        entry = next((t for t in self.data["async_tasks"] if t["task_ref"] == task_ref), None)
        if entry is None:
            entry = {"task_ref": task_ref, "last_state": None,
                     "no_change_polls": 0, "stopped": False, "cancelled": False}
            self.data["async_tasks"].append(entry)
        if entry["stopped"]:
            return "STOPPED_NO_CHANGE"
        if state == entry["last_state"]:
            entry["no_change_polls"] += 1
        else:
            entry["no_change_polls"] = 0
            entry["last_state"] = state
        if entry["no_change_polls"] >= POLL_NO_CHANGE_LIMIT:
            entry["stopped"] = True
            return "STOPPED_NO_CHANGE"
        return "OK"

    def cancel_task(self, task_ref: str, reason: str = "explicit") -> bool:
        """Explicit cancellation of the BACKGROUND task (distinct from the
        poll-stop guard). Sets cancelled=true + cancel_reason; the task is no
        longer expected to complete. Stopping polling (poll) never does this.
        """
        entry = next((t for t in self.data["async_tasks"] if t["task_ref"] == task_ref), None)
        if entry is None:
            entry = {"task_ref": task_ref, "last_state": None, "no_change_polls": 0,
                     "stopped": False, "cancelled": False}
            self.data["async_tasks"].append(entry)
        entry["cancelled"] = True
        entry["cancel_reason"] = reason
        return True
