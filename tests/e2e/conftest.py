import poorman_handshake.symmetric as _pm_symmetric
import pytest


@pytest.fixture(autouse=True)
def _allow_weak_test_passwords(monkeypatch):
    """The e2e suite uses short human-readable passwords that
    poorman-handshake's strength backstop would refuse. Disable the runtime
    check via the documented env var and neutralise the library-level check
    for components that build a PasswordHandShake without threading
    min_bits through (e.g. the hivescope test harness)."""
    monkeypatch.setenv("HIVEMIND_DISABLE_PASSWORD_STRENGTH_CHECK", "1")
    monkeypatch.setattr(_pm_symmetric, "check_password_strength",
                        lambda *args, **kwargs: None, raising=False)
