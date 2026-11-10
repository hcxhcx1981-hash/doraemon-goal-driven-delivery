"""Path discovery reference engine for Doraemon V2 tests (hermetic, host-agnostic).

V1.2 A-H capability, reorganized per V2:
- search stages (A-E), accelerator G bounded defaults (depth 4 / 90s / <=3 candidates)
- verification gate H (>=2 independent evidence kinds; real git state check)
- same-name guard ranked by task-word match score, then evidence count

V2.0.2 RC hardening:
- STRICT candidate cap: bounded_scan_enf never returns more than max_candidates
- task words are RANKING input only, NEVER an identity evidence source:
  a directory whose only signal is a task-word name is a fake project and
  cannot pass the >=2-source gate on its own
- git: work-tree check PLUS resolvable HEAD; branch/remote identity is
  SUB-evidence of the single .git source and never double-counted as a second
  independent source
- same-file dedup: one file yielding structure AND content counts once
- report gate: standard markdown headings recognized; placeholder Run IDs
  (TEMPLATE/PLACEHOLDER/TODO/xxx) rejected; text features only narrow
  candidates -- when base_dir is given, at least one listed deliverable must
  exist on disk (report_candidates vs verify_report split)
"""
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

ACC = {"max_depth": 4, "per_disk_seconds": 90, "max_candidates": 3}

STATUS_RE = re.compile(r"FINAL_STATUS\s*[:=]\s*(PASS|PARTIAL|BLOCKED)")
DELIV_MARKERS = ("交付物索引", "deliverables")
TEMPLATE_MARKERS = ("<placeholder>", "示例模板", "非真实运行证据", "placeholder",
                    "template")
# Placeholder run-id tokens that must NOT count as positive run data
PLACEHOLDER_RUN_IDS = {"template", "placeholder", "todo", "fixme", "xxx", "id"}


def bounded_scan_enf(root, name_pred,
                     max_depth=ACC["max_depth"],
                     max_candidates=ACC["max_candidates"],
                     timeout_seconds=ACC["per_disk_seconds"]):
    """Accelerator G fallback: bounded recursive scan with a REAL deadline.

    STRICT CAP: the returned 'found' list never exceeds max_candidates, even
    when a single directory contains many matches. Deadline is enforced on
    every directory visit via time.monotonic; on timeout the partial list is
    preserved (V2: keep candidates found, never recurse unboundedly).
    """
    base = Path(root)
    base_parts = len(base.parts)
    deadline = time.monotonic() + timeout_seconds
    found, timed_out = [], False
    for dirpath, dirnames, filenames in os.walk(base):
        if time.monotonic() > deadline:
            timed_out = True
            break
        depth = len(Path(dirpath).parts) - base_parts
        # depth boundary: entries (dirs/files) at relative depth <= max_depth
        for dn in dirnames:
            if depth + 1 <= max_depth and len(found) < max_candidates and name_pred(dn):
                found.append(Path(dirpath) / dn)
        for fn in filenames:
            if depth <= max_depth and len(found) < max_candidates and name_pred(fn):
                found.append(Path(dirpath) / fn)
        if len(found) >= max_candidates or depth + 1 > max_depth:
            dirnames[:] = []
        if len(found) >= max_candidates:
            break
    assert len(found) <= max_candidates, "strict candidate cap violated"
    return {"found": found, "timed_out": timed_out, "limit": max_candidates}


def bounded_scan(root, name_pred, max_depth=ACC["max_depth"], max_candidates=ACC["max_candidates"]):
    """Legacy list API (compat with round-1 tests)."""
    return bounded_scan_enf(root, name_pred, max_depth, max_candidates)["found"]


def git_state(dir_path):
    """Real git work-tree verification: rev-parse reports true AND HEAD
    resolves to a real commit (unborn-HEAD repos and empty .git dirs fail).

    Returns 'work-tree' | None (None: not a real repo or git unavailable).
    """
    if not shutil.which("git"):
        return None
    cmd = lambda *args: subprocess.run(
        ["git", "-C", str(dir_path)] + list(args),
        capture_output=True, text=True, timeout=10)
    try:
        r = cmd("rev-parse", "--is-inside-work-tree")
    except Exception:
        return None
    if r.returncode != 0 or r.stdout.strip() != "true":
        return None
    try:
        h = cmd("rev-parse", "--verify", "--quiet", "HEAD")
    except Exception:
        return None
    return "work-tree" if h.returncode == 0 else None


def git_identity(dir_path):
    """Actual repository identity evidence: branch + remote url.

    Independent of directory naming. Returns {"branch", "remote"} (keys may be
    absent when unreadable) or None when not a real repo."""
    if git_state(dir_path) is None:
        return None
    out = {}
    if shutil.which("git"):
        try:
            b = subprocess.run(["git", "-C", str(dir_path), "rev-parse", "--abbrev-ref", "HEAD"],
                               capture_output=True, text=True, timeout=10)
            if b.returncode == 0 and b.stdout.strip():
                out["branch"] = b.stdout.strip()
        except Exception:
            pass
        try:
            r = subprocess.run(["git", "-C", str(dir_path), "remote", "get-url", "origin"],
                               capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out["remote"] = r.stdout.strip()
        except Exception:
            pass
    return out or None


STRUCTURAL_MARKERS = ["src", "app", "lib", "main.py", "index.js", "package.json",
                      "pyproject.toml", "go.mod", "pom.xml", "data"]
CONFIG_MARKERS = ("Makefile", ".env.example", "ci.yml", "setup.py", "pom.xml")
CONTENT_SCAN_FILES = ("README.md", "main.py", "publish.bat", "Makefile")


def match_score(name, task_words):
    """Ranking signal ONLY. Task words never count as identity evidence."""
    n = name.lower()
    return sum(1 for w in task_words if w and w.lower() in n)


def project_identity(dir_path, task_words):
    """Verification gate H: INDEPENDENT evidence SOURCES only.

    A source is counted ONCE no matter how many evidence kinds it yields:
    - a real .git (work-tree + resolvable HEAD) is one source labeled "git";
      branch/remote identity read from that same .git is SUB-evidence, never
      a second source (git and git-identity must not double count).
    - structure / config_ref / content are attributed to the concrete file or
      directory that produced them; the SAME file yielding structure AND
      content evidence counts once (deduplicated by file name).
    - a task-word hit in the directory NAME is a RANKING signal
      (match_score), not a source: a bare directory named after the task
      (fake project) has 0 sources and cannot pass the >=2-source gate.

    Returns a frozenset of source labels; len(set) is the evidence count.
    """
    p = Path(dir_path)
    sources = {}  # file-or-'.git' key -> first kind label
    if git_state(str(p)) == "work-tree":
        sources[".git"] = "git"  # identity is sub-evidence of this single source
    for m in STRUCTURAL_MARKERS:
        if (p / m).is_dir() or (p / m).is_file():
            sources.setdefault(m, "structure")
    for cfg in CONFIG_MARKERS:
        if (p / cfg).is_file():
            sources.setdefault(cfg, "config_ref")
    for f in CONTENT_SCAN_FILES:
        fp = p / f
        if fp.is_file() and any(w.lower() in fp.read_text(encoding="utf-8", errors="ignore").lower()
                                for w in task_words):
            sources.setdefault(f, "content")
    return frozenset(sources.values())


def select_project(candidates, task_words, min_evidence=2,
                   max_candidates=ACC["max_candidates"]):
    """Same-name guard: keep only candidates with >= min_evidence independent
    evidence SOURCES (deduplicated per file; git identity sub-counts the
    single .git source; task words are ranking only). Ranking: task-word
    match score desc, then source count desc, then stable path order.

    The result list itself is capped at max_candidates (strict cap,
    V2.0.2 审计项 6): even when many candidates pass the gate, at most
    max_candidates are returned.

    Returns [(source_count, path)] capped at max_candidates.
    """
    scored = []
    for c in candidates:
        sources = project_identity(str(c), task_words)
        if len(sources) >= min_evidence:
            scored.append((match_score(Path(c).name, task_words), len(sources), Path(c)))
    scored.sort(key=lambda t: (-t[0], -t[1], str(t[2])))
    picked = [(k, p) for _, k, p in scored]
    return picked[:max_candidates]


def _section_marker(line):
    """Recognize a deliverable-index section heading, standard Markdown
    headings ('## 交付物索引') and plain lines alike."""
    s = re.sub(r"^[#>*\-\s]+", "", line.strip())
    return bool(re.match(r"^(交付物索引|deliverables)\s*[:：]?\s*$", s, re.I))


def list_deliverables(text):
    """Refs listed under a 交付物索引 / deliverables section (section-scoped,
    so a negated sentence like '无交付物索引' does NOT count as an index).
    Standard Markdown headings ('## 交付物索引') are recognized."""
    refs = []
    in_section = False
    for line in text.splitlines():
        if _section_marker(line):
            in_section = True
            continue
        if in_section:
            m = re.match(r"^\s*[-*]\s*([^\s`()]+\.[A-Za-z0-9]{1,8})\s*$", line)
            if m:
                refs.append(m.group(1).lstrip("./"))
    return refs


def _positive_run_data(text):
    """Positive (non-negated, non-placeholder) run-data evidence.

    - a real timestamp, or
    - a 'run id <token>' where the token is NOT a placeholder
      (TEMPLATE/PLACEHOLDER/TODO/XXX...) and not immediately negated.
    """
    if re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", text):
        return True
    for m in re.finditer(r"run\s*id\s*[:=]?\s*([A-Za-z0-9_-]{2,})", text, re.I):
        token = m.group(1).lower()
        if token in PLACEHOLDER_RUN_IDS:
            continue
        prefix = text[max(0, m.start() - 3):m.start()]
        if "无" not in prefix:
            return True
    return False


def report_candidates(text, template_markers=TEMPLATE_MARKERS):
    """TEXT-ONLY gate: narrows candidate reports. A real execution report
    needs (1) a closure status marker, (2) positive non-placeholder run data,
    (3) a deliverable index listing >=1 item, (4) not a template.

    IMPORTANT: passing this gate makes the text a CANDIDATE only; it does not
    prove the report is real. Use verify_report(base_dir=...) for the
    existence check on listed deliverables."""
    has_status = bool(STATUS_RE.search(text))
    has_run = _positive_run_data(text)
    has_deliv = len(list_deliverables(text)) > 0
    is_template = any(m.lower() in text.lower() for m in template_markers)
    return has_status and has_run and has_deliv and not is_template


def is_real_report(text, base_dir=None, template_markers=TEMPLATE_MARKERS):
    """Backward-compat wrapper.

    base_dir=None: text-only candidate gate (legacy behavior).
    base_dir given: candidate gate PLUS at least one listed deliverable must
    exist on disk under base_dir (existence check -- text features alone do
    not prove the report is real).
    """
    if not report_candidates(text, template_markers):
        return False
    if base_dir is None:
        return True
    missing, found = report_deliverables(text, base_dir)
    return len(found) > 0


def verify_report(text, base_dir):
    """Two-stage gate: candidate (text) then verification (disk existence).
    Returns (is_candidate, missing, found)."""
    cand = report_candidates(text)
    missing, found = report_deliverables(text, base_dir)
    return cand, missing, found


def report_deliverables(text, base_dir):
    """Existence check: deliverable refs listed in the report vs disk.

    Returns (missing, found) lists of refs as written (relative to base_dir).
    """
    base = Path(base_dir)
    missing, found = [], []
    for ref in list_deliverables(text):
        p = base / ref
        (found if p.exists() else missing).append(ref)
    return missing, found


def find_skill(skills_root, skill_name):
    """Frontmatter-verified skill discovery (V1.2 scenario-2 behavior)."""
    root = Path(skills_root)
    if not root.is_dir():
        return None
    for cand in sorted(root.iterdir()):
        fm = cand / "SKILL.md"
        if cand.is_dir() and fm.is_file():
            head = fm.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^name:\s*(\S+)", head, re.M)
            if m and m.group(1) == skill_name:
                return cand
    return None


def make_git_fixture(base_dir, name, remote=None, commit_msg="init"):
    """Self-built git fixture (V2.0.2): tests create their own git repos via
    `git init` + commit; they never depend on a hidden .git shipped inside a
    ZIP. Returns the repo path (None if git unavailable)."""
    if not shutil.which("git"):
        return None
    d = Path(base_dir) / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "main.py").write_text("run", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(d)], check=True, capture_output=True)
    if remote:
        subprocess.run(["git", "-C", str(d), "remote", "add", "origin", remote],
                       check=True, capture_output=True)
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    subprocess.run(["git", "-C", str(d), "commit", "--allow-empty", "-qm", commit_msg],
                   check=True, capture_output=True, env=env)
    return d


class NeedsAsk:
    """Raised by a task runner when the V1.2 4-condition user-ask gate is reached."""
    def __init__(self, reasons, searched):
        self.reasons = reasons
        self.searched = searched
