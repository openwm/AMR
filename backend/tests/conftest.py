import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--manual",
        action="store_true",
        default=False,
        help="Pause picking steps so a human can confirm via the picking station GUI",
    )


@pytest.fixture
def manual(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--manual"))
