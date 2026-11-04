"""Call Udemy's internal api-2.0 with curl_cffi (Chrome TLS impersonation to get past Cloudflare).

The token is only ever sent to base_url; caption URLs (CDN) are downloaded without it.
"""
import re
import threading
import time
from urllib.parse import urlparse

API = "/api-2.0"
CURRICULUM_PARAMS = {
    "page_size": "200",
    "fields[lecture]": "title,object_index,asset",
    "fields[chapter]": "title,object_index",
    "fields[asset]": "asset_type,captions",
    "caching_intent": "True",
}
COURSE_FIELDS = "id,title,published_title,url"


class UdemyError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class AuthError(UdemyError):
    pass


class UdemyClient:
    def __init__(self, base_url: str, token: str, retries: int = 3):
        if not token:
            raise AuthError("Chưa có access_token. Chạy `python -m engine login` trước.")
        self.base_url = base_url.rstrip("/")
        self.host = urlparse(self.base_url).netloc
        self.retries = retries
        self._token = token
        self._local = threading.local()

    def _session(self):
        session = getattr(self._local, "session", None)
        if session is None:
            from curl_cffi import requests

            session = requests.Session(impersonate="chrome")
            self._local.session = session
        return session

    def _get(self, url: str, params: dict | None = None, *, auth: bool = True):
        from curl_cffi.requests.exceptions import RequestException

        kwargs = {"params": params, "timeout": 30}
        if auth:
            # No redirects: curl would forward custom headers (X-Udemy-Authorization) to the new host.
            kwargs["allow_redirects"] = False
            kwargs["headers"] = {
                "Authorization": f"Bearer {self._token}",
                "X-Udemy-Authorization": f"Bearer {self._token}",
            }
            kwargs["cookies"] = {"access_token": self._token}
        path = urlparse(url).path
        for attempt in range(self.retries + 1):
            try:
                response = self._session().get(url, **kwargs)
            except RequestException as exc:
                if attempt < self.retries:
                    time.sleep(2 ** attempt)
                    continue
                raise UdemyError(f"Lỗi mạng ({exc.__class__.__name__}): {path}") from None
            status = response.status_code
            if status == 429 or status >= 500:
                if attempt < self.retries:
                    time.sleep(2 ** attempt)
                    continue
            if auth and status in (401, 403):
                if "application/json" in response.headers.get("content-type", ""):
                    raise AuthError("Token Udemy hết hạn hoặc không hợp lệ. Chạy `python -m engine login` lại.")
                raise UdemyError(f"Bị chặn (HTTP {status}), có thể do Cloudflare: {path}", status)
            if status >= 300:
                raise UdemyError(f"HTTP {status}: {path}", status)
            return response

    def _get_json(self, path_or_url: str, params: dict | None = None) -> dict:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}{API}{path_or_url}"
        if urlparse(url).netloc != self.host:
            raise UdemyError(f"Từ chối gửi token tới host lạ: {urlparse(url).netloc}")
        return self._get(url, params).json()

    def _paginate(self, path: str, params: dict) -> list[dict]:
        data = self._get_json(path, params)
        results = list(data.get("results", []))
        while data.get("next"):
            data = self._get_json(data["next"])
            results.extend(data.get("results", []))
        return results

    def list_courses(self) -> list[dict]:
        return self._paginate(
            "/users/me/subscribed-courses/",
            {"fields[course]": COURSE_FIELDS, "ordering": "-last_accessed", "page_size": "100"},
        )

    def resolve_course(self, ref: str) -> dict:
        """ref: course id, slug, or URL https://.../course/<slug>/... (the API accepts both id and slug)."""
        ref = ref.strip()
        m = re.search(r"/course/([^/?#]+)", ref)
        key = m.group(1) if m else ref.strip("/")
        try:
            return self._get_json(f"/courses/{key}/", {"fields[course]": COURSE_FIELDS})
        except AuthError:
            raise
        except UdemyError as exc:
            raise UdemyError(f"Không tìm thấy khóa học '{key}' ({exc}).") from None

    def get_curriculum(self, course_id: int) -> list[dict]:
        return self._paginate(
            f"/courses/{course_id}/subscriber-curriculum-items/",
            {**CURRICULUM_PARAMS, "curriculum_types": "chapter,lecture"},
        )

    def get_lecture_captions(self, course_id: int, lecture_id: int) -> list[dict]:
        data = self._get_json(
            f"/users/me/subscribed-courses/{course_id}/lectures/{lecture_id}/",
            {"fields[lecture]": "asset", "fields[asset]": "captions"},
        )
        return (data.get("asset") or {}).get("captions") or []

    def download_text(self, url: str) -> str:
        """Download a caption file from the CDN — never sends the token."""
        return self._get(url, auth=False).content.decode("utf-8-sig", errors="replace")
