import pytest


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    passed = len(reporter.stats.get("passed", [])) if reporter else 0
    if exitstatus == 0 and passed == 0:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
