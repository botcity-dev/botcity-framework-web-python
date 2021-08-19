import atexit
import os
import tempfile

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from ..util import cleanup_temp_dir


def default_options(headless=False, download_folder_path=None, user_data_dir=None):
    firefox_options = FirefoxOptions()
    firefox_options.headless = headless
    if not user_data_dir:
        temp_dir = tempfile.TemporaryDirectory(prefix="botcity_")
        user_data_dir = temp_dir.name
        atexit.register(cleanup_temp_dir, temp_dir)
    firefox_profile = webdriver.FirefoxProfile(user_data_dir)
    firefox_profile.set_preference("security.default_personal_cert", "Select Automatically")
    firefox_profile.set_preference('browser.download.folderList', 2)
    firefox_profile.set_preference('browser.download.manager.showWhenStarting', False)
    if not download_folder_path:
        download_folder_path = os.path.join(os.path.expanduser("~"), "Desktop")
    firefox_profile.set_preference('browser.download.dir', download_folder_path)
    firefox_profile.set_preference('general.warnOnAboutConfig', False)
    firefox_profile.update_preferences()
    firefox_options.profile = firefox_profile

    return firefox_options
