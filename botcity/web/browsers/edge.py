import atexit
import json
import os
import tempfile

from msedge.selenium_tools import Edge, EdgeOptions  # noqa: F401, F403

from ..util import cleanup_temp_dir


def default_options(headless=False, download_folder_path=None, user_data_dir=None):
    edge_options = EdgeOptions()
    edge_options.use_chromium = True
    edge_options.add_argument("--remote-debugging-port=0")
    edge_options.add_argument("--no-first-run")
    edge_options.add_argument("--no-default-browser-check")
    edge_options.add_argument("--disable-background-networking")
    edge_options.add_argument("--disable-background-timer-throttling")
    edge_options.add_argument("--disable-client-side-phishing-detection")
    edge_options.add_argument("--disable-default-apps")
    edge_options.add_argument("--disable-extensions")
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
        "profile.password_manager_enabled": False
    }

    edge_options.add_experimental_option("prefs", prefs)

    edge_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    )

    edge_options.add_argument("--kiosk-printing")

    return edge_options


def wait_for_downloads(driver):
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = document.querySelector('downloads-manager')
            .shadowRoot.getElementById('downloadsList').items;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)
