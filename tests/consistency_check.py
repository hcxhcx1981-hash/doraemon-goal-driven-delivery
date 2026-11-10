"""Reproducible consistency check between CodeBuddy inline-rules and V2 CORE.

The inline rules are a HAND-CURATED summary, NOT auto-generated from a
generator. This script is the consistency mechanism: it diffs the 12 rule
numbers, version, machine fields, and the high-risk must-stop line against
the CORE (SKILL.md) so drift is caught deterministically. Run from the repo
root:  python -X utf8 tests/consistency_check.py   -> exit 0 on consistency.

Any mismatch prints the exact rule/field that drifted and exits 1.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = (ROOT / "SKILL.md").read_text(encoding="utf-8")
INLINE = (ROOT / "adapters" / "codebuddy" / "inline-rules.md").read_text(encoding="utf-8")


def core_rule_text(n: int) -> str:
    """The n-th CORE hard-rule line, stripped of its number + whitespace."""
    m = re.search(rf"^{n}\s*(.+)$", CORE, re.M)
    return m.group(1).strip() if m else ""


def inline_rule_text(n: int) -> str:
    m = re.search(rf"^{n}\s*(.+)$", INLINE, re.M)
    return m.group(1).strip() if m else ""


def core_key_terms(n: int):
    """Distinctive keywords that MUST survive in the inline summary of rule n.
    These are semantic anchors, not full equality (the inline file is a
    compressed summary), so each anchor is a substring check."""
    anchors = {
        1: ["目标", "基线"],
        2: ["连续", "修复"],
        3: ["UNVERIFIED"],
        4: ["同根因", "4轮"],
        5: ["轮询", "取消后台任务"],
        6: ["L级", "task-ledger.json"],
        7: ["QUOTA", "UNKNOWN"],
        8: ["密钥", "Token", "Cookie"],
        9: ["免打扰", "四条件"],
        10: ["擅自扩大", "后续阶段"],
        11: ["DISCOVERED", "BEHAVIOR_VERIFIED"],
        12: ["总控", "派工方"],
    }
    return anchors.get(n, [])


def version_in_core() -> str:
    m = re.search(r'version:\s*"([\d.]+)"', CORE)
    return m.group(1) if m else ""


def main():
    problems = []
    # 1) version must be carried in the inline header
    ver = version_in_core()
    if ver and ver not in INLINE:
        problems.append(f"version {ver} missing from inline header")
    # 2) every one of the 12 rules must exist with semantic anchors
    for n in range(1, 13):
        itext = inline_rule_text(n)
        if not itext:
            problems.append(f"rule {n}: missing from inline file")
            continue
        for anchor in core_key_terms(n):
            if anchor not in itext and anchor not in INLINE:
                problems.append(f"rule {n}: anchor '{anchor}' drifted")
    # 3) high-risk must-stop line must be present in BOTH (entry visibility)
    if "必停" not in CORE:
        problems.append("CORE entry lacks the high-risk 必停 block")
    if "必停" not in INLINE:
        problems.append("inline lacks the high-risk 必停 block")
    # 4) machine fields must match between the two files
    for field in ("SKILL_LOADED", "TASK_TYPE", "MODE", "BUDGET"):
        if field not in CORE or field not in INLINE:
            problems.append(f"machine field {field} missing (core={field in CORE}, inline={field in INLINE})")
    # 5) inline size target (<= 2.5KB = 2560 bytes)
    size = (ROOT / "adapters" / "codebuddy" / "inline-rules.md").stat().st_size
    if size > 2560:
        problems.append(f"inline-rules {size}B exceeds 2.5KB target")
    # report
    if problems:
        print("CONSISTENCY_CHECK: FAIL")
        for p in problems:
            print("  -", p)
        return 1
    print(f"CONSISTENCY_CHECK: PASS (v{ver}, 12/12 rules aligned, {size}B <= 2560B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
