from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FuseReference:
    """Test-only interpretation of the prompt contract; no host enforcement."""
    def __init__(self):
        self.total = 0
        self.causes = {}
        self.stopped = False

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


class FuseScenarios(unittest.TestCase):
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
        for kwargs in [dict(regression=True), dict(authorized=False),
                       dict(resources=False), dict(critical_evidence=False)]:
            with self.subTest(kwargs=kwargs):
                f = FuseReference()
                self.assertFalse(f.attempt('a', **kwargs))
                self.assertTrue(f.stopped)


class RepositoryContract(unittest.TestCase):
    def test_frontmatter_version_and_rules(self):
        s = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(s.startswith('---\nname: doraemon-goal-driven-delivery\n'))
        self.assertIn('\ndescription: ', s.split('---')[1])
        for term in ['V1.1', '**2 轮有证据的修复**', '**4 轮有效修复**',
                     '根因假设', '支持证据', '最小修改', '验收方式',
                     '同一错误反复出现且没有新证据', '修改开始破坏原本通过的功能',
                     '无法确定根因且缺少关键证据', '已达到时间、调用或额度预算',
                     '需要突破授权或安全边界', '不得通过改名、拆分任务或重启会话',
                     '不自动购买额度', '不无限调用外部模型', '不得以自主执行为由绕过节流规则',
                     '保留已完成且通过验收的成果', '保存错误信息与必要证据',
                     '交给 ChatGPT 总控裁决', '本 Skill 不授予任何额外权限',
                     'AUTHORIZED', '生产门禁', 'QUOTA=UNKNOWN', 'PASS / PARTIAL / BLOCKED']:
            with self.subTest(term=term):
                self.assertIn(term, s)

    def test_cb_retains_limits(self):
        s = (ROOT / 'adapters/codebuddy/inline-rules.md').read_text(encoding='utf-8')
        for term in ['V1.1', '**2 轮有证据的修复**', '**4 轮有效修复**',
                     '不得改名/拆分/重启规避', '立即停止', '交总控裁决', 'UNVERIFIED']:
            self.assertIn(term, s)

    def test_markdown_links_and_fences(self):
        for p in ROOT.rglob('*.md'):
            text = p.read_text(encoding='utf-8')
            self.assertEqual(len(re.findall(r'^```', text, re.M)) % 2, 0, str(p))
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((p.parent / link.split('#')[0]).exists(), (str(p), link))

    def test_public_file_allowlist_and_secret_patterns(self):
        allowed = {'README.md', 'README_EN.md', 'LICENSE', 'SKILL.md', '.gitignore',
                   'docs/ARCHITECTURE.md', 'docs/WORKFLOW.md', 'docs/INSTALLATION.md',
                   'docs/SAFETY.md', 'adapters/codebuddy/inline-rules.md',
                   'examples/task-dispatch.md', 'examples/acceptance-report.md',
                   'examples/AGENTS.example.md', 'tests/test_contract.py',
                   '.github/workflows/ci.yml'}
        actual = set()
        for p in ROOT.rglob('*'):
            rel = p.relative_to(ROOT)
            if p.is_dir() or '.git' in rel.parts or '__pycache__' in rel.parts:
                continue
            actual.add(rel.as_posix())
            text = p.read_text(encoding='utf-8')
            patterns = [r'gh[pousr]_[A-Za-z0-9]{30,}', r'sk-[A-Za-z0-9]{20,}',
                        r'AKIA[A-Z0-9]{16}', r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
                        r'[A-Za-z]:\\Users\\[^\\\s]+', r'(?i)S[45][ _-]?资料']
            for pattern in patterns:
                self.assertIsNone(re.search(pattern, text), (str(rel), pattern))
        self.assertEqual(actual, allowed)


if __name__ == '__main__':
    unittest.main()
