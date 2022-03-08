import enum

from . import chrome
from . import firefox
from . import edge
from . import ie


class Browser(str, enum.Enum):
    """
    Supported Driver.

    Attributes:
        CHROME (str): Google Chrome
        FIREFOX (str): Mozilla Firefox
        EDGE (str): Microsoft Edge
        IE (str): Microsoft Internet Explorer
    """
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"
    IE = "ie"


BROWSER_CONFIGS = {
    Browser.CHROME: {
        "driver": "chromedriver",
        "class": chrome.Chrome,
        "options": chrome.default_options,
        "capabilities": chrome.default_capabilities,
        "wait_for_downloads": chrome.wait_for_downloads
    },
    Browser.FIREFOX: {
        "driver": "geckodriver",
        "class": firefox.Firefox,
        "options": firefox.default_options,
        "capabilities": firefox.default_capabilities,
        "wait_for_downloads": firefox.wait_for_downloads
    },
    Browser.EDGE: {
        "driver": "msedgedriver",
        "class": edge.Edge,
        "options": edge.default_options,
        "capabilities": edge.default_capabilities,
        "wait_for_downloads": edge.wait_for_downloads
    },
    Browser.IE: {
        "driver": "IEDriverServer",
        "class": ie.Ie,
        "options": ie.default_options,
        "capabilities": ie.default_capabilities,
        "wait_for_downloads": ie.wait_for_downloads
    },
}
