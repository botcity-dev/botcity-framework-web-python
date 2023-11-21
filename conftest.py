import os
import json
import shutil
import tempfile

import pytest
import typing
import platform

from webdriver_manager.core.driver_cache import DriverCacheManager
from botcity.web import WebBot, Browser, By, browsers
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

OS_NAME = platform.system()

PROJECT_DIR = os.path.abspath('tests')
TEST_PAGE = "https://lf2a.github.io/webpage-test/test.html"
INDEX_PAGE = "https://lf2a.github.io/webpage-test/"


def get_fake_bin_path(web: WebBot) -> str:
    return os.path.join(web.download_folder_path, 'fake.bin')


def setup_chrome(headless: bool, tmp_folder: str, download_driver: str) -> WebBot:
    web = WebBot(headless)
    web.browser = Browser.CHROME

    web.driver_path = download_driver
    web.download_folder_path = tmp_folder
    return web


def setup_firefox(headless: bool, tmp_folder: str, download_driver: str) -> WebBot:
    web = WebBot(headless)
    web.browser = Browser.FIREFOX

    web.driver_path = download_driver
    web.download_folder_path = tmp_folder

    return web


def setup_edge(headless: bool, tmp_folder: str, download_driver: str) -> WebBot:
    web = WebBot(headless)
    web.browser = Browser.EDGE

    web.driver_path = download_driver
    web.download_folder_path = tmp_folder
    opt = browsers.edge.default_options(headless=headless, download_folder_path=tmp_folder)
    opt.set_capability('platform', 'ANY')

    web.options = opt
    return web


def factory_setup_browser(browser: str, is_headless: bool, tmp_folder: str, download_driver: str) -> WebBot:
    dict_browsers = {
        'chrome': setup_chrome,
        'firefox': setup_firefox,
        'edge': setup_edge
    }

    setup_browser = dict_browsers.get(browser, None)

    if setup_browser is None:
        raise ValueError(f'Browser [{browser}] not supported.')

    return setup_browser(headless=is_headless, tmp_folder=tmp_folder, download_driver=download_driver)


def factory_driver_manager(browser: str):
    dict_driver_manager = {
        'chrome': ChromeDriverManager,
        'firefox': GeckoDriverManager,
        'edge': EdgeChromiumDriverManager
    }

    driver_manager = dict_driver_manager.get(browser, None)

    if dict_driver_manager is None:
        raise ValueError(f'Driver to [{browser}] not supported.')

    return driver_manager


@pytest.fixture
def tmp_folder() -> str:
    folder = tempfile.mkdtemp()
    yield folder
    shutil.rmtree(folder)


@pytest.fixture(autouse=True, scope="session")
def download_driver(request):
    folder_driver = tempfile.mkdtemp()
    browser = request.config.getoption("--browser") or Browser.CHROME
    manager = factory_driver_manager(browser=browser)
    cache_manager = DriverCacheManager(root_dir=folder_driver)
    installed_driver = manager(cache_manager=cache_manager).install()
    yield installed_driver
    shutil.rmtree(folder_driver)


@pytest.fixture
def web(request, tmp_folder: str, download_driver: str):
    browser = request.config.getoption("--browser") or Browser.CHROME
    is_headless = request.config.getoption("--headless") or "false"
    is_headless = True if is_headless.lower() == "true" else False
    web = factory_setup_browser(browser=browser, is_headless=is_headless, tmp_folder=tmp_folder,
                                download_driver=download_driver)
    yield web
    web.stop_browser()


def get_event_result(id_event: str, web: WebBot) -> typing.Dict:
    event_result = web.find_element(id_event, By.ID)
    return json.loads(event_result.text)


def pytest_addoption(parser):
    parser.addoption('--headless', action='store', default="true")
    parser.addoption('--browser', action='store', default='chrome')

