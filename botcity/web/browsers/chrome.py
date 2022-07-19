import atexit
import json
import os
import tempfile
from typing import Dict

from selenium.webdriver import Chrome  # noqa: F401, F403
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from ..util import cleanup_temp_dir


def default_options(headless=False, download_folder_path=None, user_data_dir=None,
                    page_load_strategy="normal") -> ChromeOptions:
    """Retrieve the default options for this browser curated by BotCity.

    Args:
        headless (bool, optional): Whether or not to use the headless mode. Defaults to False.
        download_folder_path (str, optional): The default path in which to save files.
            If None, the current directory is used. Defaults to None.
        user_data_dir ([type], optional): The directory to use as user profile.
            If None, a new temporary directory is used. Defaults to None.
        page_load_strategy (str, optional): The page load strategy. Defaults to "normal".

    Returns:
        ChromeOptions: The Chrome options.
    """
    chrome_options = ChromeOptions()
    try:
        page_load_strategy = page_load_strategy.value
    except AttributeError:
        page_load_strategy = page_load_strategy
    chrome_options.page_load_strategy = page_load_strategy
    chrome_options.add_argument("--remote-debugging-port=0")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-syncdisable-translate")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")

    # Disable What's New banner for new chrome installs
    chrome_options.add_argument("--disable-features=ChromeWhatsNewUI")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Disable banner for Browser being remote-controlled
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--mute-audio")

    # Check if user is root
    try:
        # This is only valid with Unix
        if os.geteuid() == 0:
            chrome_options.add_argument("--no-sandbox")
    except AttributeError:
        pass

    if not user_data_dir:
        temp_dir = tempfile.TemporaryDirectory(prefix="botcity_")
        user_data_dir = temp_dir.name
        atexit.register(cleanup_temp_dir, temp_dir)

    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    if not download_folder_path:
        download_folder_path = os.getcwd()

    app_state = {
        'recentDestinations': [{
            'id': 'Save as PDF',
            'origin': 'local',
            'account': ''
        }],
        'selectedDestinationId': 'Save as PDF',
        'version': 2
    }

    # Set the Downloads default folder
    prefs = {
        "printing.print_preview_sticky_settings.appState": json.dumps(app_state),
        "download.default_directory": download_folder_path,
        "savefile.default_directory": download_folder_path,
        "printing.default_destination_selection_rules": {
            "kind": "local",
            "namePattern": "Save as PDF",
        },
        "safebrowsing.enabled": True,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "plugins.always_open_pdf_externally": True
    }

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    )

    chrome_options.add_argument("--kiosk-printing")

    return chrome_options


def default_capabilities() -> Dict:
    """Fetch the default capabilities for this browser.

    Returns:
        Dict: Dictionary with the default capabilities defined.
    """
    return DesiredCapabilities.CHROME.copy()


def wait_for_downloads(driver):
    """Wait for all downloads to finish.
    *Important*: This method overwrites the current page with the downloads page.
    """
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = document.querySelector('downloads-manager')
            .shadowRoot.getElementById('downloadsList').items;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)
