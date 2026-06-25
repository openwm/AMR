import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--auto",
        action="store_true",
        default=False,
        help="Run in automated mode (no UI interaction). Default is manual mode.",
    )
    # Kept for backwards-compatibility with the legacy test_picking_flow.py
    parser.addoption(
        "--manual",
        action="store_true",
        default=False,
        help="(Legacy) Explicit manual mode — same as omitting --auto.",
    )


@pytest.fixture
def manual(request: pytest.FixtureRequest) -> bool:
    """True unless --auto is passed. Manual mode is the default."""
    return not bool(request.config.getoption("--auto"))
