"""Distribution packager (V2.0.2 Agent Skills standard).

Guarantees the ZIP the release ships:
- top-level folder name == the `name` field in SKILL.md frontmatter
  (Agent Skills spec: the directory name must equal the skill name)
- all archive paths use standard forward-slash '/' separators
- no hidden .git is shipped (git fixtures are self-built by tests)

Used by tests/package verification AND by the release build step so the
distribution layout and the test that checks it share one source of truth.
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_EXCLUDED_DIRS = {".git", "__pycache__"}
_EXCLUDED_SUFFIXES = {".out"}  # regenerable intermediates; keep *.log as evidence


def skill_name() -> str:
    head = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^name:\s*(\S+)", head, re.M)
    if not m:
        raise ValueError("SKILL.md frontmatter has no `name`")
    return m.group(1)


def _iter_files():
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in _EXCLUDED_DIRS for part in rel.parts):
            continue
        if p.suffix in _EXCLUDED_SUFFIXES:
            continue
        yield p, rel


def build_zip(out_path) -> str:
    """Write the distribution ZIP; returns the top-level folder name used."""
    top = skill_name()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in _iter_files():
            arcname = f"{top}/{rel.as_posix()}"  # standard '/' paths
            z.write(p, arcname)
    return top


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else str(ROOT.parent / "doraemon-goal-driven-delivery-v2.zip")
    name = build_zip(target)
    print(f"PACKAGED top-dir={name} -> {target}")
