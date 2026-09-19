"""Shared pytest hooks."""


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Warn loudly when an xfail-marked test starts passing (flip the marker)."""
    xpassed = terminalreporter.stats.get("xpassed", [])
    if not xpassed:
        return
    terminalreporter.write_sep("=", "XPASS — flip these xfail markers", yellow=True, bold=True)
    for rep in xpassed:
        terminalreporter.write_line(f"  XPASS  {rep.nodeid}")
