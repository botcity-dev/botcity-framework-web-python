import enum
from . import chrome
from . import firefox

from selenium import webdriver


class Browser(str, enum.Enum):
    """
    Supported Driver.

    Attributes:
        CHROME (str): Google Chrome
        FIREFOX (str): Mozilla Firefox
    """
    CHROME = "chrome"
    FIREFOX = "firefox"


BROWSER_CONFIGS = {
    Browser.CHROME: {
        "driver": "chromedriver",
        "class": webdriver.Chrome,
        "options": chrome.default_options
    },
    Browser.FIREFOX: {
        "driver": "geckodriver",
        "class": webdriver.Firefox,
        "options": firefox.default_options
    },
}
