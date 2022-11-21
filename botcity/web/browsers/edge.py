import atexit
import json
import os
import tempfile
import time
from typing import Dict

from msedge.selenium_tools import Edge, EdgeOptions  # noqa: F401, F403
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from ..util import cleanup_temp_dir


def default_options(headless=False, download_folder_path=None, user_data_dir=None,
                    page_load_strategy="normal") -> EdgeOptions:
    """Retrieve the default options for this browser curated by BotCity.
    Args:
        headless (bool, optional): Whether or not to use the headless mode. Defaults to False.
        download_folder_path (str, optional): The default path in which to save files.
            If None, the current directory is used. Defaults to None.
        user_data_dir ([type], optional): The directory to use as user profile.
            If None, a new temporary directory is used. Defaults to None.
        page_load_strategy (str, optional): The page load strategy. Defaults to "normal".
    Returns:
        EdgeOptions: The Edge options.
    """
    edge_options = EdgeOptions()
    try:
        page_load_strategy = page_load_strategy.value
    except AttributeError:
        page_load_strategy = page_load_strategy
    edge_options.page_load_strategy = page_load_strategy
    edge_options.use_chromium = True
    edge_options.add_argument("--remote-debugging-port=0")
    edge_options.add_argument("--no-first-run")
    edge_options.add_argument("--no-default-browser-check")
    edge_options.add_argument("--disable-background-networking")
    edge_options.add_argument("--disable-background-timer-throttling")
    edge_options.add_argument("--disable-client-side-phishing-detection")
    edge_options.add_argument("--disable-default-apps")
    edge_options.add_argument("--disable-hang-monitor")
    edge_options.add_argument("--disable-popup-blocking")
    edge_options.add_argument("--disable-prompt-on-repost")
    edge_options.add_argument("--disable-syncdisable-translate")
    edge_options.add_argument("--metrics-recording-only")
    edge_options.add_argument("--safebrowsing-disable-auto-update")

    edge_options.add_argument("--disable-blink-features=AutomationControlled")

    # Disable banner for Browser being remote-controlled
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)

    if headless:
        edge_options.add_argument("--headless")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--hide-scrollbars")
        edge_options.add_argument("--mute-audio")

    # Check if user is root
    try:
        # This is only valid with Unix
        if os.geteuid() == 0:
            edge_options.add_argument("--no-sandbox")
    except AttributeError:
        pass

    if not user_data_dir:
        temp_dir = tempfile.TemporaryDirectory(prefix="botcity_")
        user_data_dir = temp_dir.name
        atexit.register(cleanup_temp_dir, temp_dir)

    edge_options.add_argument(f"--user-data-dir={user_data_dir}")

    if not download_folder_path:
        download_folder_path = os.getcwd()

    app_state = {
        "recentDestinations": [{
            "id": "Save as PDF",
            "origin": "local",
            "account": ""
        }],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
        "isHeaderFooterEnabled": False,
        "marginsType": 2,
        "isCssBackgroundEnabled": True
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

    edge_options.add_experimental_option("prefs", prefs)

    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    )

    edge_options.add_argument("--kiosk-printing")

    return edge_options


def default_capabilities() -> Dict:
    """Fetch the default capabilities for this browser.
    Returns:
        Dict: Dictionary with the default capabilities defined.
    """
    return DesiredCapabilities.EDGE.copy()


def wait_for_downloads(driver):
    """Wait for all downloads to finish.
    *Important*: This method overwrites the current page with the downloads page.
    """
    if not driver.current_url.startswith("edge://downloads"):
        driver.get("edge://downloads/")
        time.sleep(1)
    return driver.execute_script("""
        var items = Array.from(document.querySelector(".downloads-list")
            .querySelectorAll('[role="listitem"]'));
        if(items.every(e => e.querySelector('[role="progressbar"]') == null))
            return true;
        """)
