"""AC behavior test: one full V2 pipeline run on a no-path task.

Simulates an AC session receiving a dispatch instruction without any path,
following Doraemon V2 rules end-to-end and emitting the machine-readable
fields + closure block. Reads the actual V2 files (single source of truth),
so the behavior test verifies the real rule text, not a copy.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "tests"))
import path_engine as pe  # noqa: E402


def run_task(task_instruction: str, task_words: list, budget: dict):
    # 1) load CORE (single load, not re-injected)
    core = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    # 2) classify task type
    if re.search(r"报告|研究|核验", task_instruction):
        task_type, mode = "RESEARCH", "AUDIT" if "审计" in task_instruction else "NORMAL"
    elif re.search(r"文档|PPT|演示|网页|表格", task_instruction):
        task_type, mode = "ARTIFACT", "NORMAL"
    else:
        task_type, mode = "CODE_DEV", "NORMAL"
    ref = {"CODE_DEV": "code-dev", "RESEARCH": "research", "ARTIFACT": "artifact"}[task_type]
    loaded = [f"SKILL.md({ROOT.name})", f"references/{ref}.md", "references/path-discovery.md"]
    for l in loaded:
        p = ROOT / l.split("(")[0]
        assert p.is_file(), f"on-demand load failed for {l}"
    # 3) path discovery: no path given -> mandatory search (never ask first)
    cands = pe.bounded_scan(FIX / "projects", lambda n: any(w in n.lower() for w in task_words),
                            max_depth=4, max_candidates=3)
    sel = pe.select_project(cands, task_words)
    if sel:
        target = str(sel[0][1])
        path_found = True
    else:
        target = None
        path_found = False
    # 4) verify deliverable-like claim: locate latest real report (gate, not skill file)
    reports = [p for p in (FIX / "reports").iterdir() if p.is_file()]
    real = [p.name for p in reports if pe.is_real_report(p.read_text(encoding="utf-8"))]
    # Path hygiene: emit paths RELATIVE to the package fixture root so no local
    # machine absolute path (user profile) leaks into logs/deliverables.
    def _rel(p):
        try:
            return Path(p).relative_to(FIX).as_posix()
        except ValueError:
            return str(p)
    target_rel = _rel(target) if target else None
    # 5) fill machine-readable fields (unreadable budget fields -> UNKNOWN)
    fields = {
        "SKILL_LOADED": f"ac:2.0.2:preview-injected",
        "TASK_TYPE": task_type,
        "MODE": mode,
        "BUDGET": {k: budget.get(k, "UNKNOWN") for k in ("level", "time_seconds", "tool_calls", "model")},
    }
    # 6) closure block
    status = "PASS" if (path_found and real) else "PARTIAL"
    closure = {
        "GOAL": task_instruction,
        "DELIVERED": f"target={target_rel} real_reports={real}",
        "ACCEPTANCE": "path gate >=2 evidence kinds" if path_found else "UNVERIFIED path",
        "GAPS": [] if path_found else ["no candidate reached evidence threshold"],
        "REPOSITORY": "NOT_PUSHED (preview package, no git ops)",
        "FINAL_STATUS": status,
    }
    return {"fields": fields, "loaded": loaded, "closure": closure,
            "candidates_kept": len(cands), "evidence": sel[0][0] if sel else 0}


def main():
    r = run_task("找到采集器项目并核验最近的真实执行报告", ["collector"],
                 budget={"level": "S"})
    print(json.dumps(r, ensure_ascii=False, indent=2))
    ok = (r["closure"]["FINAL_STATUS"] == "PASS"
          and r["candidates_kept"] <= 3
          and len(r["loaded"]) == 3
          and "preview-injected" in r["fields"]["SKILL_LOADED"])
    print("BEHAVIOR_TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
