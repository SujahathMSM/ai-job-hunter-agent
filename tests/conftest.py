import pytest


@pytest.fixture(autouse=True)
def _reset_board_health():
    """Board pauses are process-wide; keep one test's blocked request from pausing boards in another."""
    from hunter.job_sources import BOARD_HEALTH
    BOARD_HEALTH.paused_until.clear()
    BOARD_HEALTH.empty_strikes.clear()
    yield
