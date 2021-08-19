import atexit
import os
import tempfile

from selenium.webdriver.chrome.options import Options as ChromeOptions

from ..util import cleanup_temp_dir


def default_options(headless=False, download_folder_path=None, user_data_dir=None):
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--remote-debugging-port=0")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-syncdisable-translate")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Disable banner for Browser being remote-controlled
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--mute-audio")

    if not user_data_dir:
        temp_dir = tempfile.TemporaryDirectory(prefix="botcity_")
        user_data_dir = temp_dir.name
        atexit.register(cleanup_temp_dir, temp_dir)

    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    if not download_folder_path:
        download_folder_path = os.path.join(os.path.expanduser("~"), "Desktop")

    # Set the Downloads default folder
    prefs = {"download.default_directory": download_folder_path}
    chrome_options.add_experimental_option("prefs", prefs)

    return chrome_options
