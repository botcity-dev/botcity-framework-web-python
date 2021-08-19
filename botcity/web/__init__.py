from .bot import WebBot, Browser, BROWSER_CONFIGS  # noqa: F401, F403

from botcity.web._version import get_versions
__version__ = get_versions()['version']
del get_versions
