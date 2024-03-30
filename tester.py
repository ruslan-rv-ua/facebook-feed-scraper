import json
from pathlib import Path
from time import sleep

from facebook_feed_scraper.browser import FBBrowser

if FBBrowser().is_installed():
    print("Browser is installed")
else:
    print("Browser is not installed")
    FBBrowser.install()

with FBBrowser(headless=False) as browser:
    if browser.is_logged_in():
        print("Already logged in")
    else:
        print("Log in then press enter")
    # print(browser.get_feed_page_html())

    for i in range(5):
        file_path = Path(__file__).resolve().parent / f"test_{i}.html"
        file_path.write_text(browser.get_feed_page_html(), encoding="utf-8")
        print(f"Scrolling to bottom {i}")
        browser.scroll_to_bottom()
        sleep(1)

    input("Press enter to exit")

    Path("responses.json").write_text(
        json.dumps(browser.responses, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Path(__file__).resolve().parent.glob("test_*.html").unlink()
