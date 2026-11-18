"""`login` command: open the installed Chrome/Edge via Playwright, wait for the user to sign in, save access_token."""
import time
from pathlib import Path

from engine.config import save_token
from engine.udemy_client import AuthError, UdemyClient

LOGIN_TIMEOUT_SECONDS = 600


def token_rejected(base_url: str, token: str) -> bool:
    """True when Udemy refuses the token, e.g. an expired cookie left in the saved browser profile.

    Any other failure (network, Cloudflare) proves nothing about the token, so it is not a rejection.
    """
    try:
        UdemyClient(base_url, token).check_token()
    except AuthError:
        return True
    except Exception:
        return False
    return False


def login(base_url: str, profile_dir: Path, root: Path) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Cần cài Playwright: pip install playwright") from None

    base_url = base_url.rstrip("/")
    profile_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context, errors = None, []
        for channel in ("chrome", "msedge"):
            try:
                context = p.chromium.launch_persistent_context(str(profile_dir), channel=channel, headless=False)
                break
            except Exception as exc:  # browser not installed
                errors.append(f"{channel}: {exc.__class__.__name__}")
        if context is None:
            raise SystemExit("Không mở được Chrome hoặc Edge (" + "; ".join(errors) + ").")

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(f"{base_url}/home/my-courses/learning/")
        print("Hãy đăng nhập Udemy trong cửa sổ trình duyệt vừa mở (tối đa 10 phút)...", flush=True)

        token, rejected = None, set()
        deadline = time.monotonic() + LOGIN_TIMEOUT_SECONDS
        try:
            while token is None and time.monotonic() < deadline:
                try:
                    cookies = context.cookies(base_url)
                except Exception:  # browser window was closed
                    break
                value = next((c["value"] for c in cookies if c["name"] == "access_token" and c["value"]), None)
                # The profile keeps the previous session cookie, so only accept a value Udemy accepts.
                if value and value not in rejected:
                    if token_rejected(base_url, value):
                        rejected.add(value)
                        print("Phiên cũ trong trình duyệt đã hết hạn, hãy đăng nhập lại trong cửa sổ đó...", flush=True)
                    else:
                        token = value
                if token is None:
                    time.sleep(1)
        finally:
            try:
                context.close()
            except Exception:  # user already closed the window
                pass

    if token is None:
        raise SystemExit("Hết thời gian chờ đăng nhập — chưa lấy được access_token.")
    return save_token(token, root)
