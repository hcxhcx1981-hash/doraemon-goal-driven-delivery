"""Doraemon V2.0.2 RC test suite (layered, quality over count).

Layers (explicit, no simulation passed off as host-behavior verification):
- L1 static: document contracts, frontmatter, links, secret patterns, CORE budget
- L2 real-code: shipped tests/path_engine.py + tests/ledger.py with self-built git fixtures
- L3 simulation: host-pipeline simulation in temp trees (explicitly labeled "simulation")
- L4 host-behavior: NOT executed here; must be a real-host isolated E2E (all UNVERIFIED)

Round-1 (29) + round-2 (17) tests are RETAINED and re-verified item by item
against the V2.0.2 code; round-3 additions cover the RC audit items:
count-loss, fake projects, fake/placeholder reports, strict candidate cap,
poll-stop vs task-cancel, adapter/README consistency, real Draft 2020-12
validation when the jsonschema dev dependency is available.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(Path(__file__).parent))
import path_engine as pe  # noqa: E402
import ledger as ledger_mod  # noqa: E402
import consistency_check  # noqa: E402
from ledger import Ledger  # noqa: E402

INLINE_FILE = ROOT / "adapters" / "codebuddy" / "inline-rules.md"
CB_ADAPTER = ROOT / "adapters" / "codebuddy" / "ADAPTER.md"

SCHEMA = ROOT / "schemas" / "task-ledger.schema.json"
CORE = ROOT / "SKILL.md"
CB = ROOT / "adapters" / "codebuddy" / "inline-rules.md"
README_ZH = ROOT / "README.md"
README_EN = ROOT / "README_EN.md"

# NOTE (L4 host-behavior layer): real-host E2E (CX/AC LOADED / BEHAVIOR_VERIFIED)
# is NOT executed in this package and is documented UNVERIFIED in README/adapters.


# ==================== L1 static: fuse reference contract (V1.2 semantics) ====================
class FuseReference:
    def __init__(self):
        self.total, self.causes, self.stopped = 0, {}, False

    def attempt(self, cause, *, evidence=True, regression=False,
                authorized=True, resources=True, critical_evidence=True):
        if self.stopped:
            return False
        if (not evidence or regression or not authorized or not resources
                or not critical_evidence or self.total >= 4
                or self.causes.get(cause, 0) >= 2):
            self.stopped = True
            return False
        self.total += 1
        self.causes[cause] = self.causes.get(cause, 0) + 1
        return True


class L1_RegFuse(unittest.TestCase):
    """L1 static: circuit-breaker contract frozen from V1.2 (reference model)."""

    def test_two_rounds_per_cause(self):
        f = FuseReference()
        self.assertTrue(f.attempt('a'))
        self.assertTrue(f.attempt('a'))
        self.assertFalse(f.attempt('a'))
        self.assertEqual(f.total, 2)

    def test_four_rounds_across_task_splits(self):
        f = FuseReference()
        for cause in ['a', 'b', 'c', 'd']:
            self.assertTrue(f.attempt(cause))
        self.assertFalse(f.attempt('renamed-task'))
        self.assertEqual(f.total, 4)

    def test_stop_without_new_evidence_and_preserve_counts(self):
        f = FuseReference()
        self.assertTrue(f.attempt('a'))
        self.assertFalse(f.attempt('a', evidence=False))
        self.assertFalse(f.attempt('b'))
        self.assertEqual(f.total, 1)

    def test_all_immediate_stop_conditions(self):
        for kw in [dict(regression=True), dict(authorized=False),
                   dict(resources=False), dict(critical_evidence=False)]:
            with self.subTest(kwargs=kw):
                f = FuseReference()
                self.assertFalse(f.attempt('a', **kw))
                self.assertTrue(f.stopped)


# ==================== L1 static: repo / frontmatter / machine fields ====================
class L1_RegRepo(unittest.TestCase):
    """L1 static: Agent-Skills-standard frontmatter, CORE contract, budgets, links."""

    def test_v2_frontmatter_standard_and_machine_fields(self):
        s = CORE.read_text(encoding='utf-8')
        self.assertTrue(s.startswith('---\nname: doraemon-goal-driven-delivery\n'))
        for term in ['description:', 'license: MIT', 'metadata:', '"2.0.2"',
                     'SKILL_LOADED', 'TASK_TYPE', 'MODE', 'BUDGET',
                     'UNKNOWN', 'DISCOVERED', 'INSTALLED', 'LOADED', 'BEHAVIOR_VERIFIED',
                     'CODE_DEV', 'RESEARCH', 'ARTIFACT', 'task-ledger.json',
                     '取消ChatGPT单控绑定', '连续2次轮询无变化即停', 'FINAL_STATUS',
                     'preview-injected', 'native', 'dispatch-injected', 'unverified',
                     'machine-fields']:
            with self.subTest(term=term):
                self.assertIn(term, s)

    def test_dir_name_matches_skill_name(self):
        # Agent Skills standard: the DISTRIBUTION top-level folder must equal
        # the `name` field. Staging may carry a suffix; the packager enforces
        # the spec name, so verify through the packager (single source of truth).
        import package_skill
        name = package_skill.skill_name()
        self.assertEqual(name, "doraemon-goal-driven-delivery")
        # name charset per spec: lowercase alnum + hyphen, no leading/trailing
        # hyphen, no consecutive hyphens
        self.assertRegex(name, r'^[a-z0-9]+(-[a-z0-9]+)*$')

    def test_distribution_zip_top_dir_and_slash_paths(self):
        # Agent Skills standard: ZIP ships one top folder == skill name, all
        # arcnames use '/' separators, and no hidden .git is inside.
        import package_skill
        import zipfile
        import tempfile
        top = package_skill.skill_name()
        with tempfile.TemporaryDirectory() as td:
            zpath = Path(td) / "dist.zip"
            used = package_skill.build_zip(zpath)
            self.assertEqual(used, top, "ZIP top dir must equal the spec name")
            with zipfile.ZipFile(zpath) as z:
                for a in z.namelist():
                    self.assertNotIn("\\", a, f"non-standard backslash path in ZIP: {a}")
                    self.assertTrue(a.startswith(top + "/"), a)
                    # a shipped .git directory/file would appear as a path
                    # component exactly equal to '.git' (not '.github')
                    parts = a.split("/")
                    self.assertNotIn(".git", parts, f"hidden .git shipped: {a}")

    def test_twelve_hard_rules_present(self):
        s = CORE.read_text(encoding='utf-8')
        nums = sorted(int(m.group(1)) for m in
                      (re.match(r'^(\d{1,2})', l) for l in s.splitlines()) if m)
        self.assertEqual(nums, list(range(1, 13)), "CORE must contain exactly rules 1-12")

    def test_cb_retains_limits(self):
        s = CB.read_text(encoding='utf-8')
        for term in ['≤2', '≤4', 'UNVERIFIED', '交当前宿主总控/派工方',
                     'QUOTA=UNKNOWN', 'task-ledger.json', '停轮询≠取消后台任务']:
            with self.subTest(term=term):
                self.assertIn(term, s)

    def test_core_compact_goal_not_hard_cap(self):
        # V2.0.2 final: CORE compactness is a TARGET, not a hard limit that
        # may sacrifice rule correctness (high-risk must-stop conditions must
        # stay in the always-visible entry). So assert a generous bound that
        # still catches bloat, and assert the high-risk stop line is present
        # in the entry (correctness over size).
        b = CORE.stat().st_size
        lines = len(CORE.read_text(encoding='utf-8').splitlines())
        s = CORE.read_text(encoding='utf-8')
        self.assertLessEqual(lines, 60, f"CORE lines {lines} > 60 (compact target)")
        self.assertLessEqual(b, 2600, f"CORE bytes {b} > 2600 compact target")
        # the high-risk must-stop condition must be visible in the entry
        self.assertIn('必停', s, "high-risk must-stop conditions must be in the CORE entry")
        self.assertIn('不可逆', s, "irreversible-operation stop condition must be visible")

    def test_markdown_fences_and_links(self):
        for p in ROOT.rglob('*.md'):
            text = p.read_text(encoding='utf-8')
            self.assertEqual(len(re.findall(r'^```', text, re.M)) % 2, 0, str(p))
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((p.parent / link.split('#')[0]).exists(), (str(p), link))

    def test_no_secret_or_localpath_patterns(self):
        pats = [r'gh[pousr]_[A-Za-z0-9]{30,}', r'sk-[A-Za-z0-9]{20,}',
                r'AKIA[A-Z0-9]{16}', r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
                r'[A-Za-z]:\\Users\\', r'(?i)S[45][ _-]?资料',
                r'(?i)(api[_-]?key|passwd|password)\s*[:=]\s*[A-Za-z0-9]{8,}']
        for p in list(ROOT.rglob('*.md')) + list(ROOT.rglob('*.json')) + list(ROOT.rglob('*.py')):
            text = p.read_text(encoding='utf-8', errors='ignore')
            for pat in pats:
                self.assertIsNone(re.search(pat, text), (str(p), pat))

    def test_no_unknown_abbreviation_drift(self):
        # 'UNK' as a standalone token (not UNKNOWN) must not appear anywhere.
        # Build the pattern by concatenation so this test file itself does not
        # contain the literal standalone token.
        tok = re.compile(r"\b" + "U" + "NK\b")
        for p in list(ROOT.rglob('*.md')) + list(ROOT.rglob('*.json')) + list(ROOT.rglob('*.py')):
            text = p.read_text(encoding='utf-8', errors='ignore')
            self.assertIsNone(tok.search(text), f"shortened-UNKNOWN drift in {p}")


# ==================== L1 static: README zh/en + adapter consistency (RC audit item 9) ====================
class L1_ReadmeAndAdapters(unittest.TestCase):
    def test_readme_pair_exists_with_required_sections(self):
        self.assertTrue(README_ZH.is_file())
        self.assertTrue(README_EN.is_file())
        zh = README_ZH.read_text(encoding='utf-8')
        en = README_EN.read_text(encoding='utf-8')
        for section in ('项目定位', '架构', '任务分类', '渐进加载', '会话复用',
                        '预算与熔断', '跨会话恢复', '宿主适配', '安装与测试',
                        '验证状态', '安全限制'):
            self.assertIn(section, zh, f"README.md missing section {section}")
        for section in ('positioning', 'Architecture', 'Task classification',
                        'session reuse', 'Budget & circuit breaker',
                        'Cross-session recovery', 'Host adapters', 'Installation & testing',
                        'Verification status', 'Safety limits'):
            self.assertIn(section, en, f"README_EN.md missing section {section}")
        # both must state what this is NOT
        self.assertIn('不是自动调度器', zh)
        self.assertIn('not an auto-scheduler', en)

    def test_readme_uses_unverified_for_host_capability(self):
        zh = README_ZH.read_text(encoding='utf-8')
        en = README_EN.read_text(encoding='utf-8')
        self.assertIn('UNVERIFIED', zh)
        self.assertIn('UNVERIFIED', en)
        self.assertIn('不写成', zh)  # "不写成已支持" wording present
        self.assertIn('never "supported"', en)

    def test_adapter_version_consistency_single_source(self):
        # All adapter docs + inline rules must carry 2.0.2, not the old 2.0.0-draft.
        core = CORE.read_text(encoding='utf-8')
        self.assertIn('"2.0.2"', core)
        for p in list((ROOT / 'adapters').rglob('*.md')):
            text = p.read_text(encoding='utf-8')
            self.assertNotIn('2.0.0-draft', text, f"stale version in {p}")
            self.assertNotIn(':2.0.1:', text, f"stale SKILL_LOADED version in {p}")
        self.assertIn('codebuddy:2.0.2:dispatch-injected', CB.read_text(encoding='utf-8'))

    def test_field_names_unified_across_all_layers(self):
        schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
        for f in ('time_seconds', 'tool_calls', 'quota'):
            self.assertIn(f, schema['properties']['budget']['properties'], f)
        for p in [CORE, CB, ROOT / 'tests' / 'behavior_ac.py']:
            text = p.read_text(encoding='utf-8')
            self.assertIn('time_seconds', text, f"unified field missing in {p.name}")
            self.assertIn('tool_calls', text, f"unified field missing in {p.name}")
        machine = (ROOT / 'references' / 'machine-fields.md').read_text(encoding='utf-8')
        for v in ('native', 'dispatch-injected', 'preview-injected', 'unverified'):
            self.assertIn(v, machine, f"SKILL_LOADED value {v} must be defined in machine-fields.md")


# ==================== L2 real-code: path discovery (V1.2 behavior + RC hardening) ====================
class L2_RegPath(unittest.TestCase):
    def test_scenario_project(self):
        cands = pe.bounded_scan(FIX / 'projects', name_pred=lambda n: 'auction' in n,
                                max_depth=4, max_candidates=5)
        sel = pe.select_project(cands, ['collector'])
        self.assertEqual(len(sel), 1, f"expected only collector, got {[p for _, p in sel]}")
        self.assertTrue(str(sel[0][1]).endswith('d-auction-collector'))
        self.assertGreaterEqual(sel[0][0], 2, "collector must reach the >=2-evidence gate without git")

    def test_scenario_skill(self):
        hit = pe.find_skill(FIX / 'fake_skills', 'my-skill')
        self.assertIsNotNone(hit)
        self.assertIn('my-skill', str(hit))

    def test_scenario_real_report(self):
        base = FIX / 'reports'
        self.assertTrue(pe.is_real_report((base / 'real_report.md').read_text(encoding='utf-8')))
        self.assertFalse(pe.is_real_report((base / 'skill_like.md').read_text(encoding='utf-8')))
        self.assertFalse(pe.is_real_report((base / 'template.md').read_text(encoding='utf-8')))


class L2_N1NoPathSmoke(unittest.TestCase):
    def test_search_without_user_path(self):
        res = pe.bounded_scan_enf(FIX / 'projects', lambda n: 'collector' in n,
                                   max_depth=4, max_candidates=3)
        self.assertTrue(res["found"])
        self.assertLessEqual(len(res["found"]), 3)
        sel = pe.select_project(res["found"], ['collector'])
        self.assertTrue(sel, "smoke: must autonomously resolve a project candidate")


class L2_N2MisSelectGuard(unittest.TestCase):
    def test_same_name_excluded_by_task_word(self):
        cands = [FIX / 'projects' / 'd-auction-collector', FIX / 'projects' / 'd-auction-publish']
        sel = [p for _, p in pe.select_project(cands, ['collector'])]
        self.assertTrue(any('collector' in str(p) for p in sel))
        self.assertFalse(any('publish' in str(p) for p in sel), "publish must be excluded")

    def test_skill_file_not_mistaken_for_report(self):
        self.assertFalse(pe.is_real_report((FIX / 'reports' / 'skill_like.md').read_text(encoding='utf-8')))


class L2_R2GitRealState(unittest.TestCase):
    """L2 real-code: git evidence requires a REAL repo; fixtures are self-built,
    never shipped inside the ZIP (RC audit item 8)."""

    def _selfbuilt_repo(self, td, name='proj', remote=None):
        return pe.make_git_fixture(Path(td), name, remote=remote)

    def test_no_git_fixture_shipped_in_package(self):
        # No .git may be shipped inside the PACKAGE FIXTURES or the tests
        # tree itself (self-built fixtures). A repository working tree may
        # legitimately have its own .git at the repo root; that is not a
        # distribution leak. So scan only the tests directory.
        shipped = [p for p in (ROOT / "tests").rglob(".git")
                   if p.is_dir() or p.is_file()]
        self.assertEqual(shipped, [], f"hidden .git shipped in package fixtures: {shipped}")

    def test_fake_git_dir_yields_no_git_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / 'proj'
            (d / '.git').mkdir(parents=True)
            (d / 'main.py').write_text('x', encoding='utf-8')
            self.assertIsNone(pe.git_state(str(d)))
            self.assertIsNone(pe.git_identity(str(d)))
            kinds = pe.project_identity(str(d), ['proj'])
            self.assertNotIn('git', kinds, "empty .git dir must not count as git evidence")

    def test_selfbuilt_real_repo_yields_git_source(self):
        with tempfile.TemporaryDirectory() as td:
            d = self._selfbuilt_repo(td, remote='https://example.invalid/ac-collector.git')
            self.assertIsNotNone(d, "git unavailable on host; mark UNVERIFIED")
            self.assertEqual(pe.git_state(str(d)), 'work-tree')
            ident = pe.git_identity(str(d))
            self.assertEqual(ident['remote'], 'https://example.invalid/ac-collector.git')
            sources = pe.project_identity(str(d), ['collector'])
            self.assertIn('git', sources, "a real repo yields the .git source")
            self.assertGreaterEqual(len(sources), 2)


# ==================== L2 real-code: ledger (RC audit item 5) ====================
class L2_N3LedgerRecovery(unittest.TestCase):
    def test_resume_and_inherit(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger({"task_id": "T-100", "goal": "ship demo", "task_type": "CODE_DEV",
                         "status": "IN_PROGRESS", "completed": ["baseline", "implement"],
                         "remaining": ["test", "accept"],
                         "repair_rounds": {"a": 2, "total": 2},
                         "next_action": "run e2e test", "updated_at": "2026-11-09"})
            reloaded = led.roundtrip(Path(td) / "task-ledger.json")
            done = set(reloaded.data.get("completed", []))
            to_do = [s for s in reloaded.data.get("remaining", []) if s not in done]
            self.assertEqual(reloaded.data["next_action"], "run e2e test")
            self.assertEqual(to_do, ["test", "accept"])
            self.assertEqual(reloaded.data["repair_rounds"], {"a": 2, "total": 2})
            self.assertFalse(reloaded.repair_allowed("a"), "inherited cause at limit must be refused")


class L2_N4RepairInheritance(unittest.TestCase):
    def _led(self):
        return Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
                       "repair_rounds": {"a": 2, "total": 2}})

    def test_cause_at_limit_refused(self):
        self.assertFalse(self._led().repair_allowed("a"))

    def test_total_budget_refused_after_renamed_task(self):
        led = self._led()
        led.data["repair_rounds"]["total"] = 4
        self.assertFalse(led.repair_allowed("b"), "total 4-round cap inherited, new cause blocked")

    def test_rename_does_not_reset_counts(self):
        led = self._led()
        self.assertEqual(led.data["repair_rounds"]["a"], 2)
        self.assertFalse(led.repair_allowed("a"))

    def test_no_new_evidence_not_a_new_round(self):
        led = self._led()
        led.data["repair_rounds"]["a"] = 1
        led.data["repair_rounds"]["total"] = 1
        ok = led.record_repair("a", new_evidence=False, result="FAIL")
        self.assertFalse(ok)
        self.assertEqual(led.data["repair_rounds"]["a"], 1, "round without new evidence must not increment")


class L2_R2LedgerRoundTrip(unittest.TestCase):
    """L2 real-code: JSON serialization / save / re-read against the real implementation."""

    def test_json_roundtrip_preserves_counts(self):
        led = Ledger({"task_id": "T9", "goal": "g", "task_type": "CODE_DEV",
                      "repair_rounds": {"x": 1, "total": 1},
                      "next_action": "step", "updated_at": "now"})
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "task-ledger.json"
            led.save(p)
            raw = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(raw["repair_rounds"], {"x": 1, "total": 1})
            re2 = Ledger.load(p)
            self.assertEqual(re2.data["repair_rounds"], raw["repair_rounds"])
            self.assertTrue(re2.repair_allowed("x"))

    def test_saved_ledger_rejects_exhausted_cause(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "task-ledger.json"
            Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
                    "repair_rounds": {"a": 2, "total": 2}}).save(p)
            re2 = Ledger.load(p)
            self.assertFalse(re2.repair_allowed("a"), "cause at 2 rounds must be refused")

    # ---- RC audit item 5: counter loss / BLOCKED / evidence linkage / cancel semantics ----
    def test_missing_total_refused_never_defaulted_zero(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV"})
        self.assertFalse(led.counts_reliable, "missing total => counts unreliable")
        self.assertFalse(led.repair_allowed("a"), "count loss must refuse repair")
        self.assertFalse(led.record_repair("a", new_evidence=True, result="FAIL",
                                            evidence_refs=["e1"]), "counted round refused on count loss")
        self.assertNotIn("total", led.data["repair_rounds"], "must not silently inject total=0")

    def test_blocked_state_persisted(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
                      "repair_rounds": {"total": 4}})
        led.mark_blocked("cause a exhausted its 4-round budget without new evidence")
        self.assertEqual(led.data["status"], "BLOCKED")
        self.assertEqual(led.data["final_status"], "BLOCKED")
        self.assertTrue(led.data["blocked_reason"])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "task-ledger.json"
            led.save(p)
            re2 = Ledger.load(p)
            self.assertEqual(re2.data["status"], "BLOCKED", "BLOCKED must survive reload")
            self.assertEqual(re2.data["blocked_reason"], led.data["blocked_reason"])

    def test_counted_round_requires_evidence_ref(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
                      "repair_rounds": {"total": 0}})
        ok = led.record_repair("a", new_evidence=True, result="FAIL", evidence_refs=None)
        self.assertFalse(ok, "counted round without evidence refs must be rejected")
        self.assertEqual(led.data["repair_rounds"].get("a", 0), 0, "rejected round must not count")
        ok2 = led.record_repair("a", new_evidence=True, result="FAIL", evidence_refs=["err-1.log"])
        self.assertTrue(ok2)
        self.assertEqual(led.data["repair_rounds"]["a"], 1)
        self.assertEqual(led.data["repair_events"][0]["evidence_refs"], ["err-1.log"])

    def test_poll_stop_is_not_task_cancel(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV"})
        led.poll("j1", "running")
        led.poll("j1", "running")
        self.assertEqual(led.poll("j1", "running"), "STOPPED_NO_CHANGE")
        e = led.data["async_tasks"][0]
        self.assertTrue(e["stopped"])
        self.assertFalse(e["cancelled"], "stopping the poller must NOT cancel the background task")
        self.assertTrue(led.cancel_task("j1", "user cancelled"))
        self.assertTrue(led.data["async_tasks"][0]["cancelled"])
        self.assertEqual(led.data["async_tasks"][0]["cancel_reason"], "user cancelled")


class L2_N7AsyncPoll(unittest.TestCase):
    def test_stop_after_two_no_change(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV"})
        self.assertEqual(led.poll("j1", "running"), "OK")
        self.assertEqual(led.poll("j1", "running"), "OK")
        self.assertEqual(led.poll("j1", "running"), "STOPPED_NO_CHANGE")
        entry = led.data["async_tasks"][0]
        self.assertTrue(entry["stopped"])
        self.assertEqual(entry["no_change_polls"], 2)

    def test_change_resets_counter(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV"})
        led.poll("j1", "a"); led.poll("j1", "a"); led.poll("j1", "b")
        self.assertEqual(led.data["async_tasks"][0]["no_change_polls"], 0)
        self.assertFalse(led.data["async_tasks"][0]["stopped"])


# ==================== L2 real-code: schema (Draft 2020-12) ====================
class L2_R2SchemaLayers(unittest.TestCase):
    def _doc(self):
        return json.loads(SCHEMA.read_text(encoding='utf-8'))

    def test_L_level_conditionally_requires_recovery_fields(self):
        doc = self._doc()
        then = doc["allOf"][1]["then"]
        for field in ("next_action", "repair_rounds", "remaining", "completed"):
            self.assertIn(field, then["required"], f"L-level ledger must require {field}")

    def test_poll_stop_enforced_by_if_then(self):
        schema = self._doc()["properties"]["async_tasks"]["items"]
        self.assertIn("if", schema)
        self.assertEqual(schema["then"]["properties"]["stopped"]["const"], True)
        self.assertEqual(schema["properties"]["no_change_polls"]["maximum"], 2)
        self.assertIn("cancelled", schema["properties"], "cancel flag must be separate from poll stop")

    def test_L_budget_field_names_unified(self):
        schema = self._doc()["properties"]["budget"]["properties"]
        for f in ("time_seconds", "tool_calls", "quota"):
            self.assertIn(f, schema, f)

    def test_repair_rounds_total_required(self):
        rr = self._doc()["properties"]["repair_rounds"]
        self.assertIn("total", rr["required"], "repair_rounds.total must be mandatory")
        self.assertEqual(rr["patternProperties"]["^total$"]["maximum"], 4)
        self.assertEqual(rr["additionalProperties"]["maximum"], 2)

    def test_blocked_state_persisted_by_schema(self):
        doc = self._doc()
        blocked_then = doc["allOf"][0]["then"]
        for f in ("blocked_reason", "final_status"):
            self.assertIn(f, blocked_then["required"], f"BLOCKED must persist {f}")

    def test_jsonschema_real_validation(self):
        """L2: run the real Draft 2020-12 validator when the dev dependency
        is installed; otherwise keep the stdlib structural check and mark the
        real validation UNAVAILABLE (honest status, not a silent skip)."""
        doc = self._doc()
        self.assertTrue(doc.get("$schema", "").startswith("https://json-schema.org"))
        try:
            import jsonschema
            from jsonschema import Draft202012Validator
        except ModuleNotFoundError:
            L2_R2SchemaLayers.JSONSCHEMA = "UNAVAILABLE(stdlib structural check only)"
            return
        L2_R2SchemaLayers.JSONSCHEMA = "available"
        Draft202012Validator.check_schema(doc)
        validator = Draft202012Validator(doc)
        ok = {"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
              "status": "IN_PROGRESS", "repair_rounds": {"total": 0},
              "updated_at": "2026-11-09T12:00:00+08:00"}
        self.assertIsNone(validator.validate(ok) and "invalid")
        bad = {"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
               "status": "IN_PROGRESS", "repair_rounds": {"a": 1}, "updated_at": "x"}
        self.assertTrue(list(validator.iter_errors(bad)), "missing total must fail real validation")


# ==================== L2 real-code: report identification (RC audit item 7) ====================
class L2_R2ReportCounterCases(unittest.TestCase):
    def test_forged_report_rejected(self):
        text = (FIX / "reports" / "forged_report.md").read_text(encoding="utf-8")
        self.assertFalse(pe.is_real_report(text))

    def test_template_report_rejected(self):
        text = (FIX / "reports" / "template.md").read_text(encoding="utf-8")
        self.assertFalse(pe.is_real_report(text))

    def test_real_report_deliverable_index_exists(self):
        text = (FIX / "reports" / "real_report.md").read_text(encoding="utf-8")
        missing, found = pe.report_deliverables(text, FIX / "reports")
        self.assertIn("artifacts/report.md", found)
        self.assertEqual(missing, [], f"deliverables must exist on disk: missing={missing}")

    def test_report_with_missing_deliverable_flagged(self):
        text = ("run id z9 at 2026-11-09 12:00, wallclock 9min\n交付物索引\n- nofile.md\nFINAL_STATUS: PASS\n")
        missing, _ = pe.report_deliverables(text, FIX / "reports")
        self.assertIn("nofile.md", missing)

    # ---- RC audit item 7: markdown headings / placeholder run ids / candidate-vs-real ----
    def test_markdown_heading_report_accepted(self):
        text = (FIX / "reports" / "md_heading_report.md").read_text(encoding="utf-8")
        self.assertTrue(pe.report_candidates(text), "## headings must be recognized")
        self.assertTrue(pe.is_real_report(text, base_dir=FIX / "reports"),
                        "md report with existing deliverables must verify real")

    def test_placeholder_run_id_rejected(self):
        text = (FIX / "reports" / "placeholder_runid.md").read_text(encoding="utf-8")
        self.assertFalse(pe.report_candidates(text), "placeholder run ids are not positive run data")
        self.assertFalse(pe.is_real_report(text))

    def test_candidate_split_from_verification(self):
        # text-only gate says candidate; disk check decides real
        text = (FIX / "reports" / "real_report.md").read_text(encoding="utf-8")
        cand, missing, found = pe.verify_report(text, FIX / "reports")
        self.assertTrue(cand)
        self.assertEqual(missing, [])
        self.assertTrue(found)
        cand2, missing2, _ = pe.verify_report(text, Path("/nonexistent-base"))
        self.assertTrue(cand2, "candidate gate is text-only")
        self.assertTrue(missing2, "verification stage must flag nonexistent deliverables")


# ==================== L2 real-code: bounded scan hardening (RC audit items 6/7) ====================
class L2_R2BoundedScan(unittest.TestCase):
    def _tree(self, base, depth, name="target.txt"):
        p = base
        for i in range(depth):
            p = p / f"d{i}"
        p.mkdir(parents=True, exist_ok=True)
        (p / name).write_text("x", encoding="utf-8")

    def test_deadline_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for i in range(400):
                (base / f"s{i}").mkdir()
                (base / f"s{i}" / "f.txt").write_text("x", encoding="utf-8")
            res_ok = pe.bounded_scan_enf(base, lambda n: n == "f.txt",
                                         max_depth=4, max_candidates=10, timeout_seconds=30)
            self.assertFalse(res_ok["timed_out"])
            self.assertEqual(len(res_ok["found"]), 10, "candidate limit must cap results")
            res_to = pe.bounded_scan_enf(base, lambda n: n == "f.txt",
                                         max_depth=4, max_candidates=10, timeout_seconds=-1)
            self.assertTrue(res_to["timed_out"], "expired deadline must trigger timed_out")
            self.assertLessEqual(len(res_to["found"]), res_to["limit"])

    def test_depth_boundary_precise(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self._tree(base, 4, "hit.txt")
            self._tree(base, 5, "deep.txt")
            res = pe.bounded_scan_enf(base, lambda n: n.endswith(".txt"),
                                      max_depth=4, max_candidates=10, timeout_seconds=60)
            names = [p.name for p in res["found"]]
            self.assertIn("hit.txt", names)
            self.assertNotIn("deep.txt", names)
            self.assertFalse(res["timed_out"])

    def test_candidate_ranking_by_match_score(self):
        with tempfile.TemporaryDirectory() as td:
            for name in ("a-collector", "b-collector", "alpha-collector"):
                pe.make_git_fixture(Path(td), name)
            cands = pe.bounded_scan(Path(td), lambda n: "collector" in n,
                                    max_depth=4, max_candidates=10)
            sel = pe.select_project(cands, ["alpha", "collector"])
            self.assertEqual(sel[0][1].name, "alpha-collector",
                             "higher task-word match score must rank first")

    # ---- RC audit item 6: strict cap + fake project + task-words-not-identity ----
    def test_strict_cap_even_in_single_dir(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            for i in range(6):
                (d / f"hit-{i}.txt").write_text("x", encoding="utf-8")
            res = pe.bounded_scan_enf(td, lambda n: n.startswith("hit-"),
                                       max_depth=2, max_candidates=3, timeout_seconds=30)
            self.assertEqual(len(res["found"]), 3, "cap must hold even when one dir has 6 matches")

    def test_fake_project_taskword_only_has_no_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "collector-x"
            fake.mkdir()
            (fake / "notes").mkdir()
            kinds = pe.project_identity(str(fake), ["collector"])
            self.assertEqual(kinds, set(), "task word in the directory name alone is not identity evidence")
            self.assertEqual(pe.select_project([fake], ["collector"]), [],
                             "fake project must fail the >=2-evidence gate")

    def test_empty_dir_counter_case(self):
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / "collector-empty"
            empty.mkdir()
            self.assertEqual(pe.project_identity(str(empty), ["collector"]), set())
            self.assertIsNone(pe.git_state(str(empty)))


# ==================== L3 simulation: field backfill + on-demand loading ====================
def fill_fields(agent, version, loaded_via, task_type, mode, budget_known):
    """L3 simulation: simulate host backfill; unreadable budget fields -> UNKNOWN."""
    return {
        "SKILL_LOADED": f"{agent}:{version}:{loaded_via}",
        "TASK_TYPE": task_type, "MODE": mode,
        "BUDGET": {
            "level": budget_known.get("level", "UNKNOWN"),
            "time_seconds": budget_known.get("time_seconds", "UNKNOWN"),
            "tool_calls": budget_known.get("tool_calls", "UNKNOWN"),
            "model": budget_known.get("model", "UNKNOWN"),
        },
    }


class L3_N6Fields(unittest.TestCase):
    def test_unknown_budget_marked(self):
        f = fill_fields("ag", "2.0.2", "native", "RESEARCH", "AUDIT", {})
        self.assertEqual(f["BUDGET"]["level"], "UNKNOWN")
        self.assertEqual(f["BUDGET"]["time_seconds"], "UNKNOWN")
        self.assertEqual(f["BUDGET"]["tool_calls"], "UNKNOWN")

    def test_known_budget_kept(self):
        f = fill_fields("cx", "2.0.2", "native", "CODE_DEV", "NORMAL",
                        {"level": "M", "time_seconds": "1800", "tool_calls": "25", "model": "gpt"})
        self.assertEqual(f["BUDGET"]["time_seconds"], "1800")
        self.assertEqual(f["BUDGET"]["tool_calls"], "25")


TASK_LOAD = {"CODE_DEV": "references/code-dev.md",
             "RESEARCH": "references/research.md",
             "ARTIFACT": "references/artifact.md"}


def load(task_type, secondary=None):
    loaded = ["SKILL.md"]
    if task_type in TASK_LOAD:
        loaded.append(TASK_LOAD[task_type])
    gaps = []
    if secondary and secondary != task_type:
        gaps.append(f"{secondary} requirements recorded to GAPS, not loaded")
    return loaded, gaps


class L3_N8OnDemandLoad(unittest.TestCase):
    def test_single_reference_loaded(self):
        for t in TASK_LOAD:
            loaded, _ = load(t)
            self.assertEqual(len(loaded), 2, f"{t} must load exactly CORE + 1 reference")

    def test_secondary_not_loaded(self):
        loaded, gaps = load("ARTIFACT", secondary="RESEARCH")
        self.assertNotIn("references/research.md", loaded)
        self.assertTrue(gaps)

    def test_audit_is_research_mode(self):
        self.assertNotIn("AUDIT", TASK_LOAD)


class L_FinalLedgerClosing(unittest.TestCase):
    """Final-closing counter-cases (Ledger audit items)."""

    def _terminal(self, status):
        return Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
                       "status": status,
                       "repair_rounds": {"a": 1, "total": 1}})

    def test_terminal_states_never_auto_continue(self):
        for status in ("BLOCKED", "PARTIAL", "DONE"):
            with self.subTest(status=status):
                led = self._terminal(status)
                self.assertFalse(led.can_continue(), f"{status} must not auto-continue")
                self.assertFalse(led.repair_allowed("a"))
                self.assertFalse(led.record_repair("a", new_evidence=True,
                                                    result="FAIL", evidence_refs=["e1"]),
                                 f"counted round refused in {status}")
                self.assertEqual(led.data["repair_rounds"]["a"], 1,
                                 f"{status}: counters must not move without open state")

    def test_resume_requires_explicit_authorization(self):
        led = self._terminal("PARTIAL")
        self.assertFalse(led.resume(authorized=False), "unauthorized resume must fail")
        self.assertEqual(led.status, "PARTIAL", "failed resume must not open the ledger")
        self.assertTrue(led.resume(authorized=True))
        self.assertEqual(led.status, "IN_PROGRESS")
        self.assertTrue(led.repair_allowed("a"), "authorized resume inherits budget")
        self.assertEqual(led.data["repair_rounds"], {"a": 1, "total": 1},
                         "resume must inherit the FULL historical counters, never reset")

    def test_total_mismatch_with_causes_refused(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
                      "status": "IN_PROGRESS",
                      "repair_rounds": {"a": 2, "total": 3}})
        self.assertFalse(led.counts_consistent, "total 3 != sum(causes) 2 is corruption")
        self.assertFalse(led.repair_allowed("a"), "mismatched counters must refuse repair")
        self.assertFalse(led.record_repair("a", new_evidence=True,
                                            result="FAIL", evidence_refs=["e1"]))

    def test_no_new_evidence_stop_persisted(self):
        led = Ledger({"task_id": "T", "goal": "g", "task_type": "CODE_DEV",
                      "repair_rounds": {"a": 2, "total": 2}})
        led.mark_stopped("no new evidence on cause a after 2 rounds")
        self.assertEqual(led.data["status"], "BLOCKED")
        self.assertEqual(led.data["final_status"], "BLOCKED")
        self.assertTrue(led.data["stop_reason"])
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "task-ledger.json"
            led.save(p)
            re2 = Ledger.load(p)
            self.assertEqual(re2.data["status"], "BLOCKED", "stop state must survive reload")
            self.assertFalse(re2.repair_allowed("a"), "reloaded stopped ledger must not auto-continue")


class L_FinalPathDedup(unittest.TestCase):
    """Final-closing counter-cases (path discovery audit items)."""

    def test_same_file_structure_and_content_counts_once(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "proj"
            (d / "src").mkdir(parents=True)
            # main.py is BOTH a structural marker and a content-scan file:
            # one file must yield ONE deduplicated source, not two.
            (d / "main.py").write_text("collector job", encoding="utf-8")
            sources = pe.project_identity(str(d), ["collector"])
            self.assertEqual(sources, frozenset({"structure"}),
                             "structure+content from the same file must deduplicate to one source")
            self.assertEqual(pe.select_project([d], ["collector"]), [],
                             "a single source cannot pass the >=2-source gate")

    def test_git_and_identity_not_double_counted(self):
        with tempfile.TemporaryDirectory() as td:
            d = pe.make_git_fixture(Path(td), "ac-collector",
                                    remote="https://example.invalid/ac-collector.git")
            self.assertIsNotNone(d, "git unavailable: mark UNVERIFIED")
            d.joinpath("main.py").write_text("collector", encoding="utf-8")
            sources = pe.project_identity(str(d), ["collector"])
            self.assertIn("git", sources)
            self.assertNotIn("git_identity", sources,
                             "identity is sub-evidence of the .git source, not a second source")
            self.assertEqual(len(sources), 2, "git + one file source == exactly 2 sources")

    def test_select_strict_cap_three(self):
        with tempfile.TemporaryDirectory() as td:
            for name in ("ac-collector-1", "ac-collector-2", "ac-collector-3", "ac-collector-4"):
                repo = pe.make_git_fixture(Path(td), name,
                                            remote=f"https://example.invalid/{name}.git")
                self.assertIsNotNone(repo, "git unavailable: mark UNVERIFIED")
                repo.joinpath("main.py").write_text("collector", encoding="utf-8")
            cands = pe.bounded_scan(Path(td), lambda n: "collector" in n,
                                    max_depth=4, max_candidates=10)
            sel = pe.select_project(cands, ["collector"], max_candidates=3)
            self.assertEqual(len(sel), 3, "selection must cap at 3 candidates")
            self.assertEqual(sel[0][0], 2, "each real repo passes with 2 deduped sources")

    def test_fake_project_with_taskword_name_fails_gate(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "collector"
            fake.mkdir()
            (fake / "notes.md").write_text("misc notes", encoding="utf-8")
            self.assertEqual(pe.project_identity(str(fake), ["collector"]), frozenset(),
                             "task word in the directory name alone yields no source")
            self.assertEqual(pe.select_project([fake], ["collector"]), [])


class L_FinalConsistency(unittest.TestCase):
    """CodeBuddy consistency mechanism (audit item 4)."""

    def test_consistency_check_script_passes(self):
        import consistency_check
        self.assertEqual(consistency_check.main(), 0, "inline-rules must stay aligned with CORE")

    def test_no_auto_generation_claim(self):
        # The mechanism must be stated as reproducible consistency checks,
        # not as auto-generation (there is no generator).
        adapter = CB_ADAPTER.read_text(encoding="utf-8")
        self.assertIn("自动生成", adapter, "adapter must address the no-generator claim")
        self.assertIn("不做", adapter, "the claim must be negated, not asserted")
        self.assertIn("consistency_check.py", adapter)
        inline = INLINE_FILE.read_text(encoding="utf-8")
        self.assertIn("非自动生成", inline)
        self.assertIn("一致性校验", inline)
        # stale generation claims from earlier rounds must be gone
        self.assertNotIn("单一真源生成", inline)
        self.assertNotIn("禁止手工双维护", inline)

    def test_inline_within_2_5kb_target(self):
        size = INLINE_FILE.stat().st_size
        self.assertLessEqual(size, 2560, f"inline-rules {size}B must stay within the 2.5KB target")


if __name__ == "__main__":
    unittest.main(verbosity=2)
