# PATCH Selenium for compat
from .compat import patch_selenium  # noqa: F401, F403, E402
patch_selenium()  # noqa: F401, F403, E402

from .bot import WebBot, Browser, BROWSER_CONFIGS, By, PageLoadStrategy  # noqa: F401, F403, E402
from .parsers import table_to_dict, data_from_row, sanitize_header  # noqa: F401, F403, E402
from .util import element_as_select  # noqa: F401, F403, E402

from botcity.web._version import get_versions  # noqa: F401, F403, E402
__version__ = get_versions()['version']
del get_versions
