from pathlib import Path
from subprocess import run
from typing import Self

# from playwright._impl._api_types import TimeoutError  # type: ignore
from playwright._impl._driver import (
    compute_driver_executable,  # type: ignore
    get_driver_env,
)
from playwright.sync_api import sync_playwright  # type: ignore

from .exceptions import (
    BrowserAlreadyRunningException,
    BrowserNotRunningException,
    FBBrowserError,
)

LOGIN_INPUT_SELECTOR = "#m_login_email"
FB_RECENT_POSTS_URL = "https://d.facebook.com/home.php?sk=h_chr"


class FBBrowser:
    BROWSER_NAME = "firefox"
    BROWSER_EXECUTABLE_NAME = "firefox.exe"
    BROWSER_DATA_DIR = "data"

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.executable_path = FBBrowser.find_executable()
        self.user_data_dir = Path(__file__).resolve().parent / self.BROWSER_DATA_DIR

        self.sync_playwright = None
        self.browser = None
        self.feed_page = None

        self.responses = []

    def start(self) -> None:
        if self.sync_playwright is not None or self.browser is not None:
            raise BrowserAlreadyRunningException("Browser is already running")
        self.sync_playwright = sync_playwright().start()
        engine = getattr(self.sync_playwright, self.BROWSER_NAME)
        try:
            self.browser = engine.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                executable_path=self.executable_path,
            )
        except Exception as e:
            raise FBBrowserError(f"Failed to start {self.BROWSER_NAME} browser") from e
        if self.browser is None:
            raise FBBrowserError(f"Failed to start {self.BROWSER_NAME} browser")
        self.feed_page = self.browser.pages[0]
        self.feed_page.set_viewport_size({"width": 1280, "height": 800})
        self.feed_page.goto(FB_RECENT_POSTS_URL)

    def stop(self) -> None:
        if self.sync_playwright is None or self.browser is None:
            raise BrowserNotRunningException("Browser is not running")
        self.browser.close()
        self.sync_playwright.stop()
        self.sync_playwright = None
        self.browser = None
        self.feed_page = None

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()
        if isinstance(exc_value, TimeoutError):
            return True
        return False

    def is_logged_in(self) -> bool:
        if self.feed_page is None:
            return False
        login_input = self.feed_page.query_selector(LOGIN_INPUT_SELECTOR)
        return login_input is None

    def get_feed_page_html(self) -> str:
        if self.feed_page is None:
            raise BrowserNotRunningException("Browser is not running")
        return self.feed_page.content()

    def scroll_to_bottom(self) -> None:
        if self.feed_page is None:
            raise BrowserNotRunningException("Browser is not running")
        # self.feed_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.feed_page.keyboard.press("End")

    ###############################################################################
    # browser installation
    ###############################################################################

    @classmethod
    def install(cls) -> int:
        driver_executable = compute_driver_executable()
        env = get_driver_env()
        current_path = Path(__file__).resolve().parent
        env.update({"PLAYWRIGHT_BROWSERS_PATH": str(current_path)})

        completed_process = run(
            [
                str(driver_executable),
                "install",
                cls.BROWSER_NAME,
            ],
            env=env,
        )
        return completed_process.returncode

    @classmethod
    def is_installed(cls) -> bool:
        return cls.find_executable() is not None

    @classmethod
    def find_executable(cls) -> Path | None:
        current_path = Path(__file__).resolve().parent
        browser_paths = sorted(current_path.glob(f"{cls.BROWSER_NAME}-*"))
        if len(browser_paths) == 0:
            return None
        latest_browser_path = browser_paths[-1]
        verification_file = latest_browser_path / "INSTALLATION_COMPLETE"
        if not verification_file.exists():
            return None
        executable_path = (
            latest_browser_path / cls.BROWSER_NAME / cls.BROWSER_EXECUTABLE_NAME
        )
        return executable_path
