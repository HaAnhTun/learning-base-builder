import pytest

from engine import udemy_client
from engine.udemy_client import AuthError, UdemyClient, UdemyError


class Resp:
    def __init__(self, status, json_data=None, content_type="application/json", content=b""):
        self.status_code = status
        self._json = json_data
        self.headers = {"content-type": content_type}
        self.content = content

    def json(self):
        return self._json


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def client_with(responses, monkeypatch):
    monkeypatch.setattr(udemy_client.time, "sleep", lambda s: None)
    c = UdemyClient("https://www.udemy.com/", "secret")
    session = FakeSession(responses)
    c._session = lambda: session
    return c, session


def test_requires_token():
    with pytest.raises(AuthError):
        UdemyClient("https://www.udemy.com", "")


def test_pagination_follows_next(monkeypatch):
    c, s = client_with([
        Resp(200, {"results": [{"id": 1}], "next": "https://www.udemy.com/api-2.0/x/?page=2"}),
        Resp(200, {"results": [{"id": 2}], "next": None}),
    ], monkeypatch)
    assert c.get_curriculum(5) == [{"id": 1}, {"id": 2}]
    assert s.calls[0][0] == "https://www.udemy.com/api-2.0/courses/5/subscriber-curriculum-items/"
    assert s.calls[0][1]["headers"]["Authorization"] == "Bearer secret"


def test_retries_on_429_then_succeeds(monkeypatch):
    c, s = client_with([Resp(429), Resp(503), Resp(200, {"results": []})], monkeypatch)
    assert c.list_courses() == []
    assert len(s.calls) == 3


def test_gives_up_after_retries(monkeypatch):
    c, _ = client_with([Resp(500)] * 4, monkeypatch)
    with pytest.raises(UdemyError, match="HTTP 500"):
        c.list_courses()


def test_json_403_is_auth_error_html_403_is_block(monkeypatch):
    c, _ = client_with([Resp(403, {"detail": "x"})], monkeypatch)
    with pytest.raises(AuthError):
        c.list_courses()
    c, _ = client_with([Resp(403, content_type="text/html")], monkeypatch)
    with pytest.raises(UdemyError, match="Cloudflare") as exc:
        c.list_courses()
    assert not isinstance(exc.value, AuthError)


def test_download_sends_no_token(monkeypatch):
    c, s = client_with([Resp(200, content=b"\xef\xbb\xbfWEBVTT")], monkeypatch)
    assert c.download_text("https://cdn.example.com/a.vtt") == "WEBVTT"
    assert "headers" not in s.calls[0][1] and "cookies" not in s.calls[0][1]


def test_refuses_token_to_foreign_next_url(monkeypatch):
    c, _ = client_with([Resp(200, {"results": [], "next": "https://evil.example.com/p2"})], monkeypatch)
    with pytest.raises(UdemyError, match="host"):
        c.list_courses()


@pytest.mark.parametrize("ref, key", [
    ("https://acme.udemy.com/course/py/learn/lecture/1#overview", "py"),
    ("py", "py"),
    ("9", "9"),
])
def test_resolve_course_by_url_slug_and_id(monkeypatch, ref, key):
    c, s = client_with([Resp(200, {"id": 7, "published_title": "py"})], monkeypatch)
    assert c.resolve_course(ref)["id"] == 7
    assert s.calls[0][0] == f"https://www.udemy.com/api-2.0/courses/{key}/"


def test_resolve_course_not_found(monkeypatch):
    c, _ = client_with([Resp(404, {"detail": "Not found"})], monkeypatch)
    with pytest.raises(UdemyError, match="nope"):
        c.resolve_course("nope")


def test_auth_requests_do_not_follow_redirects(monkeypatch):
    c, s = client_with([Resp(302)], monkeypatch)
    with pytest.raises(UdemyError, match="HTTP 302"):
        c.list_courses()
    assert s.calls[0][1]["allow_redirects"] is False


def test_network_error_retried_then_wrapped(monkeypatch):
    from curl_cffi.requests.exceptions import Timeout

    class Flaky(FakeSession):
        def get(self, url, **kwargs):
            self.calls.append(url)
            item = self.responses.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

    c, _ = client_with([], monkeypatch)
    session = Flaky([Timeout("t"), Resp(200, {"results": []})])
    c._session = lambda: session
    assert c.list_courses() == []

    session = Flaky([Timeout("t")] * 4)
    c._session = lambda: session
    with pytest.raises(UdemyError, match="Lỗi mạng"):
        c.list_courses()


def test_error_carries_status(monkeypatch):
    c, _ = client_with([Resp(404)], monkeypatch)
    with pytest.raises(UdemyError) as exc:
        c.download_text("https://cdn.example.com/a.vtt")
    assert exc.value.status == 404
