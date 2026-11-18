import pytest

from engine import udemy_auth
from engine.udemy_client import AuthError, UdemyClient, UdemyError


@pytest.mark.parametrize("error, expected", [
    (None, False),
    (AuthError("expired"), True),
    (UdemyError("Bị chặn (HTTP 403), có thể do Cloudflare"), False),
    (OSError("network"), False),
])
def test_token_rejected_only_when_udemy_refuses_it(monkeypatch, error, expected):
    def check(self):
        if error:
            raise error

    monkeypatch.setattr(UdemyClient, "check_token", check)
    assert udemy_auth.token_rejected("https://luvina.udemy.com", "tok") is expected
