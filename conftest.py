import os
import json
import shutil
import tempfile

import pytest
import typing
import platform

from botcity.web import WebBot, Browser, By, browsers

OS_NAME = platform.system()

PROJECT_DIR = os.path.abspath('')
FAKE_BIN_PATH = os.path.join(PROJECT_DIR, 'fake.bin')
TEST_PAGE = "https://lf2a.github.io/webpage-test/test.html"
INDEX_PAGE = "https://lf2a.github.io/webpage-test/"


def get_fake_bin_path(web: WebBot) -> str:
    return os.path.join(web.download_folder_path, 'fake.bin')


def get_driver_path(driver: str) -> str:
    if OS_NAME.lower() == 'windows':
        return os.path.join(PROJECT_DIR, 'web-drivers', 'windows', f'{driver}.exe')

    if OS_NAME.lower() == 'linux':
        return os.path.join(PROJECT_DIR, 'web-drivers', 'linux', driver)

    if OS_NAME.lower() == 'darwin':
        return os.path.join(PROJECT_DIR, 'web-drivers', 'macos', driver)

    raise ValueError(f'OS [{OS_NAME}] not supported.')


def setup_chrome(headless: bool, tmp_folder: str) -> WebBot:
    web = WebBot(headless)
    web.browser = Browser.CHROME

    web.driver_path = get_driver_path(driver='chromedriver')
    web.download_folder_path = tmp_folder
    return web


def setup_firefox(headless: bool, tmp_folder: str) -> WebBot:
    web = WebBot(headless)
    web.browser = Browser.FIREFOX

    web.driver_path = get_driver_path(driver='geckodriver')
    web.download_folder_path = tmp_folder

    return web


def setup_edge(headless: bool, tmp_folder: str) -> WebBot:
    web = WebBot(headless)
    web.browser = Browser.EDGE

    web.driver_path = get_driver_path(driver='msedgedriver')
    web.download_folder_path = tmp_folder
    opt = browsers.edge.default_options(headless=headless, download_folder_path=tmp_folder)
    opt.set_capability('platform', 'ANY')  # WINDOWS is default value:

    web.options = opt
    return web


def factory_setup_browser(browser: str, is_headless: bool, tmp_folder: str) -> WebBot:
    dict_browsers = {
        'chrome': setup_chrome,
        'firefox': setup_firefox,
        'edge': setup_edge
    }

    setup_browser = dict_browsers.get(browser, None)

    if setup_browser is None:
        raise ValueError(f'Browser [{browser}] not supported.')

    return setup_browser(headless=is_headless, tmp_folder=tmp_folder)


@pytest.fixture
def tmp_folder() -> str:
    folder = tempfile.mkdtemp()
    yield folder
    shutil.rmtree(folder)


@pytest.fixture
def web(request, tmp_folder: str):

    browser = request.config.getoption("--browser") or Browser.CHROME
    is_headless = request.config.getoption("--headless")

    web = factory_setup_browser(browser=browser, is_headless=is_headless, tmp_folder=tmp_folder)
    yield web
    web.stop_browser()


def get_event_result(id_event: str, web: WebBot) -> typing.Dict:
    event_result = web.find_element(id_event, By.ID)
    return json.loads(event_result.text)


def pytest_addoption(parser):
    parser.addoption('--headless', action='store_const', const=True)
    parser.addoption('--browser', action='store', default='chrome')

