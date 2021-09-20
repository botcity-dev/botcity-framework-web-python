import atexit
import os
import tempfile

from msedge.selenium_tools import Edge, EdgeOptions  # noqa: F401, F403

from ..util import cleanup_temp_dir


def default_options(headless=False, download_folder_path=None, user_data_dir=None):
    edge_options = EdgeOptions()
    edge_options.use_chrome = True
    edge_options.add_argument("--disable-extensions")
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
        download_folder_path = os.path.join(os.path.expanduser("~"), "Desktop")

    # Set the Downloads default folder
    prefs = {"download.default_directory": download_folder_path}
    edge_options.add_experimental_option("prefs", prefs)

    return edge_options
