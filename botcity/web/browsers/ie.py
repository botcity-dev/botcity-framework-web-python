from typing import Dict

from selenium.webdriver import Ie  # noqa: F401, F403
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.ie.options import Options


def default_options(headless=False, download_folder_path=None, user_data_dir=None,
                    page_load_strategy="normal") -> Options:
    """Retrieve the default options for this browser curated by BotCity.

    Returns:
        Options: The Internet Explorer options.
    """
    ie_options = Options()
    ie_options.add_argument("-embedding")
    ie_options.add_argument("-extoff")
    ie_options.add_argument("-k")
    return ie_options


def default_capabilities() -> Dict:
    """Fetch the default capabilities for this browser.

    Returns:
        Dict: Dictionary with the default capabilities defined.
    """
    return DesiredCapabilities.INTERNETEXPLORER.copy()


def wait_for_downloads(driver):
    """Wait for all downloads to finish.
    """
    raise NotImplementedError('wait_for_downloads not yet supported')
