import shutil
import tempfile

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select


def cleanup_temp_dir(temp_dir: tempfile.TemporaryDirectory) -> None:
    """
    Deletes the temporary directory and all its contents.

    Args:
        temp_dir (tempfile.TemporaryDirectory): The temporary directory to delete.
    """
    if temp_dir:
        try:
            temp_dir.cleanup()
        except OSError:
            shutil.rmtree(temp_dir.name, ignore_errors=True)


def element_as_select(element: WebElement) -> Select:
    """Wraps a WebElement in a Select object.

    Args:
        element (WebElement): The element to wrap.

    Returns:
        Select: The Select object.
    """
    return Select(element)
