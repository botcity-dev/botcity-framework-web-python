from .bot import WebBot, Browser, BROWSER_CONFIGS, By, PageLoadStrategy  # noqa: F401, F403
from .parsers import table_to_dict, data_from_row, sanitize_header  # noqa: F401, F403
from .util import element_as_select  # noqa: F401, F403

from botcity.web._version import get_versions
__version__ = get_versions()['version']
del get_versions
