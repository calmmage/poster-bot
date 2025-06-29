import pytest
from src.utils import validate_cron_expr
@pytest.mark.parametrize("expr", [
    "* * * * *",
    "0 0 * * *",
    "0 10 * * 1",
    "*/5 * * * *",
    "0 0 1 1 *",
    "0 0 1 1 0",
    "0 0 1 1 7",
    "0 0 1 1 6#2",
    "0 0 1 1 MON",
    ["0", "10", "*", "*", "1"],
    "*/10 * * * * *",
])
def test_valid_cron(expr):
    assert validate_cron_expr(expr) is True

@pytest.mark.parametrize("expr", [
    "",
    None,
    "* * *",
    "60 24 * * *",
    "0 0 32 13 *",
    "not a cron",
    ["*", "*", "*"],
    ["0", "0", "32", "13", "*"],
])
def test_invalid_cron(expr):
    with pytest.raises(ValueError):
        validate_cron_expr(expr) 