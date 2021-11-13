import enum

from . import chrome
from . import firefox
from . import edge


class Browser(str, enum.Enum):
    """
    Supported Driver.

    Attributes:
        CHROME (str): Google Chrome
        FIREFOX (str): Mozilla Firefox
        EDGE (str): Microsoft Edge
    """
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


BROWSER_CONFIGS = {
    Browser.CHROME: {
        "driver": "chromedriver",
        "class": chrome.Chrome,
        "options": chrome.default_options,
        "wait_for_downloads": chrome.wait_for_downloads
    },
    Browser.FIREFOX: {
        "driver": "geckodriver",
        "class": firefox.Firefox,
        "options": firefox.default_options,
        "wait_for_downloads": firefox.wait_for_downloads
    },
    Browser.EDGE: {
        "driver": "msedgedriver",
        "class": edge.Edge,
        "options": edge.default_options,
        "wait_for_downloads": edge.wait_for_downloads
    },
}
