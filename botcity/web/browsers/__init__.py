import enum

from . import chrome
from . import firefox
from . import edge
from . import ie
from . import undetected_chrome


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
    UNDETECTED_CHROME = 'undetected_chrome'


class PageLoadStrategy(str, enum.Enum):
    """
    Page Load Strategy.

    Attributes:
        NORMAL (str): Wait for the entire page is loaded. When set to normal,
            waits until the load event fire is returned.
        EAGER (str): Wait until the initial HTML document has been completely
            loaded and parsed, and discards loading of stylesheets, images and subframes.
        NONE (str): Only waits until the initial page is downloaded
    """
    NORMAL = "normal"
    EAGER = "eager"
    NONE = "none"


BROWSER_CONFIGS = {
    Browser.CHROME: {
        "driver": "chromedriver",
        "class": chrome.Chrome,
        "options": chrome.default_options,
        "capabilities": chrome.default_capabilities,
        "wait_for_downloads": chrome.wait_for_downloads,
        "service": chrome.ChromeService,
    },
    Browser.FIREFOX: {
        "driver": "geckodriver",
        "class": firefox.Firefox,
        "options": firefox.default_options,
        "capabilities": firefox.default_capabilities,
        "wait_for_downloads": firefox.wait_for_downloads,
        "service": firefox.FirefoxService
    },
    Browser.UNDETECTED_CHROME: {
        "driver": "chromedriver",
        "class": undetected_chrome.Chrome,  # noqa: F401, F403
        "options": undetected_chrome.default_options,
        "capabilities": undetected_chrome.default_capabilities,
        "wait_for_downloads": undetected_chrome.wait_for_downloads,
        "service": undetected_chrome.ChromeService
    },
    Browser.EDGE: {
        "driver": "msedgedriver",
        "class": edge.Edge,
        "options": edge.default_options,
        "capabilities": edge.default_capabilities,
        "wait_for_downloads": edge.wait_for_downloads,
        "service": edge.EdgeService
    },
    Browser.IE: {
        "driver": "IEDriverServer",
        "class": ie.Ie,
        "options": ie.default_options,
        "capabilities": ie.default_capabilities,
        "wait_for_downloads": ie.wait_for_downloads,
        "service": ie.IeService
    },
}
