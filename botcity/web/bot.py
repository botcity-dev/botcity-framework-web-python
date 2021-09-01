import base64
import functools
import io
import logging
import multiprocessing
import os
import platform
import random
import shutil
import time

from PIL import Image
from botcity.base import BaseBot, State
from botcity.base.utils import only_if_element
from bs4 import BeautifulSoup
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from . import config, cv2find
from .browsers import Browser, BROWSER_CONFIGS


try:
    from botcity.maestro import BotMaestroSDK
    MAESTRO_AVAILABLE = True
except ImportError:
    MAESTRO_AVAILABLE = False


logger = logging.getLogger(__name__)


class WebBot(BaseBot):
    KEYS = Keys
    """
    Base class for Web Bots.
    Users must implement the `action` method in their classes.

    Attributes:
        state (State): The internal state of this bot.
        maestro (BotMaestroSDK): an instance to interact with the BotMaestro server.

    """

    def __init__(self, headless=False):
        self.state = State()
        self.maestro = BotMaestroSDK() if MAESTRO_AVAILABLE else None

        self._browser = Browser.CHROME
        self._options = None
        self._driver_path = None

        self._driver = None
        self._headless = headless

        self._clipboard = ""

        # Stub mouse coordinates
        self._x = 0
        self._y = 0

        # State for Key modifiers
        self._shift_hold = False

        self._dimensions = (1600, 900)
        self._download_folder_path = None  # Defaults to ~/Desktop

    @property
    def driver(self):
        """
        The WebDriver driver instance.

        Returns:
            driver (WebDriver): The WebDriver driver instance.

        """
        return self._driver

    @property
    def driver_path(self):
        return self._driver_path

    @driver_path.setter
    def driver_path(self, driver_path):
        """
        The webdriver executable path.

        Args:
            driver_path (str): The full path to the proper webdriver path used for the selected browser.
                If set to None, the code will look into the PATH for the proper file when starting the browser.
        """
        if driver_path and not os.path.isfile(driver_path):
            raise ValueError("Invalid driver_path. The file does not exist.")
        self._driver_path = driver_path

    @property
    def browser(self):
        """
        The web browser to be used.

        Returns:
            browser (Browser): The web browser to be used.
        """
        return self._browser

    @browser.setter
    def browser(self, browser):
        """
        The web browser to be used.

        Args:
            browser (Browser): The name of web browser to be used from the Browser enum.
        """
        self._browser = browser

    @property
    def options(self):
        """
        The options to be passed down to the WebDriver when starting the browser.

        Returns:
            options (Options): The browser specific options to be used.
        """
        return self._options

    @options.setter
    def options(self, options):
        """
        The options to be passed down to the WebDriver when starting the browser.

        Args:
            options (Options): The browser specific options to be used.
        """
        self._options = options

    @property
    def download_folder_path(self):
        return self._download_folder_path

    @download_folder_path.setter
    def download_folder_path(self, folder_path):
        """
        The download folder path to be used. Set it up before starting the Browser or browsing a URL or restart the
        browser after changing it.

        Args:
            folder_path (str): The desired download folder path.
        """
        self._download_folder_path = folder_path

    @property
    def headless(self):
        """
        Controls whether or not the bot will run headless.

        Returns:
            headless (bool): Whether or not to run the browser on headless mode.
        """
        return self._headless

    @headless.setter
    def headless(self, headless):
        """
        Controls whether or not the bot will run headless.

        Args:
            headless (boolean): If set to True will make the bot run headless.
        """
        if self._driver:
            logger.warning("Browser is running. Invoke stop_browser and start browser for changes to take effect.")
        self._headless = headless

    def start_browser(self):
        """
        Starts the selected browser.
        """

        def check_driver():
            # Look for driver
            driver_name = BROWSER_CONFIGS.get(self.browser).get("driver")
            location = shutil.which(driver_name)
            if not location:
                raise RuntimeError(
                    f"{driver_name} was not found. Please make sure to have it on your PATH or set driver_path")
            return location

        # Specific webdriver class for a given browser
        driver_class = BROWSER_CONFIGS.get(self.browser).get("class")
        # Specific default options method for a given browser
        func_def_options = BROWSER_CONFIGS.get(self.browser).get("options")

        opt = self.options or func_def_options(self.headless, self._download_folder_path, None)
        self.options = opt
        driver_path = self.driver_path or check_driver()
        self.driver_path = driver_path

        self._driver = driver_class(options=opt, executable_path=driver_path)
        self.set_screen_resolution()

    def stop_browser(self):
        """
        Stops the Chrome browser and clean up the User Data Directory.
        """
        if not self._driver:
            return
        self._driver.quit()
        self._driver = None

    def set_screen_resolution(self, width=None, height=None):
        """
        Configures the browser dimensions.

        Args:
            width (int): The desired width.
            height (int): The desired height.
        """
        width = width or self._dimensions[0]
        height = height or self._dimensions[1]

        if self.headless:
            # When running headless the window size is the viewport size
            window_size = (width, height)
        else:
            # When running non-headless we need to account for the borders and etc
            # So the size must be bigger to have the same viewport size as before
            window_size = self._driver.execute_script("""
                return [window.outerWidth - window.innerWidth + arguments[0],
                  window.outerHeight - window.innerHeight + arguments[1]];
                """, width, height)
        self._driver.set_window_size(*window_size)

    ##########
    # Display
    ##########

    def get_screen_image(self, region=None):
        """
        Capture and returns a screenshot from the browser.

        Args:
            region (tuple): A tuple containing the left, top, width and height
                to crop the screen image.

        Returns:
            image (Image): The screenshot Image object.
        """
        if not region:
            region = (0, 0, 0, 0)

        x = region[0] or 0
        y = region[1] or 0
        width = region[2] or self._dimensions[0]
        height = region[3] or self._dimensions[1]
        data = self._driver.get_screenshot_as_base64()
        image_data = base64.b64decode(data)
        img = Image.open(io.BytesIO(image_data))
        img = img.crop((x, y, x + width, y + height))
        return img

    def get_viewport_size(self):
        """
        Returns the browser current viewport size.

        Returns:
            width (int): The current viewport width.
            height (int): The current viewport height.
        """
        # Access each dimension individually
        width = self._driver.get_window_size().get("width")
        height = self._driver.get_window_size().get("height")
        return width, height

    def add_image(self, label, path):
        """
        Add an image into the state image map.

        Args:
            label (str): The image identifier
            path (str): The path for the image on disk
        """
        self.state.map_images[label] = path

    def get_image_from_map(self, label):
        """
        Return an image from teh state image map.

        Args:
            label (str): The image identifier

        Returns:
            Image: The Image object
        """
        path = self.state.map_images.get(label)
        if not path:
            raise KeyError('Invalid label for image map.')
        img = Image.open(path)
        return img

    def find_multiple(self, labels, x=None, y=None, width=None, height=None, *,
                      threshold=None, matching=0.9, waiting_time=10000, best=True, grayscale=False):
        """
        Find multiple elements defined by label on screen until a timeout happens.

        Args:
            labels (list): A list of image identifiers
            x (int, optional): Search region start position x. Defaults to 0.
            y (int, optional): Search region start position y. Defaults to 0.
            width (int, optional): Search region width. Defaults to screen width.
            height (int, optional): Search region height. Defaults to screen height.
            threshold (int, optional): The threshold to be applied when doing grayscale search.
                Defaults to None.
            matching (float, optional): The matching index ranging from 0 to 1.
                Defaults to 0.9.
            waiting_time (int, optional): Maximum wait time (ms) to search for a hit.
                Defaults to 10000ms (10s).
            best (bool, optional): Whether or not to keep looking until the best matching is found.
                Defaults to True.
            grayscale (bool, optional): Whether or not to convert to grayscale before searching.
                Defaults to False.

        Returns:
            results (dict): A dictionary in which the key is the label and value are the element coordinates in a
               NamedTuple.
        """

        def _to_dict(lbs, elems):
            return {k: v for k, v in zip(lbs, elems)}

        screen_w, screen_h = self._dimensions
        x = x or 0
        y = y or 0
        w = width or screen_w
        h = height or screen_h

        region = (x, y, w, h)

        results = [None] * len(labels)
        paths = [self.state.map_images[la] for la in labels]

        if threshold:
            # TODO: Figure out how we should do threshold
            print('Threshold not yet supported')

        if not best:
            # TODO: Implement best=False.
            print('Warning: Ignoring best=False for now. It will be supported in the future.')

        start_time = time.time()
        n_cpus = multiprocessing.cpu_count() - 1

        while True:
            elapsed_time = (time.time() - start_time) * 1000
            if elapsed_time > waiting_time:
                return _to_dict(labels, results)

            haystack = self.screenshot()
            helper = functools.partial(self._find_multiple_helper, haystack, region, matching, grayscale)

            with multiprocessing.Pool(processes=n_cpus) as pool:
                results = pool.map(helper, paths)

            results = [r for r in results]
            if None in results:
                continue
            else:
                return _to_dict(labels, results)

    def _find_multiple_helper(self, haystack, region, confidence, grayscale, needle):
        ele = cv2find.locate_all_opencv(
            needle, haystack, region=region, confidence=confidence, grayscale=grayscale
        )
        return ele

    def find(self, label, x=None, y=None, width=None, height=None, *,
             threshold=None, matching=0.9, waiting_time=10000, best=True, grayscale=False):
        """
        Find an element defined by label on screen until a timeout happens.

        Args:
            label (str): The image identifier
            x (int, optional): Search region start position x. Defaults to 0.
            y (int, optional): Search region start position y. Defaults to 0.
            width (int, optional): Search region width. Defaults to screen width.
            height (int, optional): Search region height. Defaults to screen height.
            threshold (int, optional): The threshold to be applied when doing grayscale search.
                Defaults to None.
            matching (float, optional): The matching index ranging from 0 to 1.
                Defaults to 0.9.
            waiting_time (int, optional): Maximum wait time (ms) to search for a hit.
                Defaults to 10000ms (10s).
            best (bool, optional): Whether or not to keep looking until the best matching is found.
                Defaults to True.
            grayscale (bool, optional): Whether or not to convert to grayscale before searching.
                Defaults to False.

        Returns:
            element (NamedTuple): The element coordinates. None if not found.
        """
        return self.find_until(label=label, x=x, y=y, width=width, height=height, threshold=threshold,
                               matching=matching, waiting_time=waiting_time, best=best, grayscale=grayscale)

    def find_until(self, label, x=None, y=None, width=None, height=None, *,
                   threshold=None, matching=0.9, waiting_time=10000, best=True, grayscale=False):
        """
        Find an element defined by label on screen until a timeout happens.

        Args:
            label (str): The image identifier
            x (int, optional): Search region start position x. Defaults to 0.
            y (int, optional): Search region start position y. Defaults to 0.
            width (int, optional): Search region width. Defaults to screen width.
            height (int, optional): Search region height. Defaults to screen height.
            threshold (int, optional): The threshold to be applied when doing grayscale search.
                Defaults to None.
            matching (float, optional): The matching index ranging from 0 to 1.
                Defaults to 0.9.
            waiting_time (int, optional): Maximum wait time (ms) to search for a hit.
                Defaults to 10000ms (10s).
            best (bool, optional): Whether or not to keep looking until the best matching is found.
                Defaults to True.
            grayscale (bool, optional): Whether or not to convert to grayscale before searching.
                Defaults to False.

        Returns:
            element (NamedTuple): The element coordinates. None if not found.
        """
        self.state.element = None
        screen_w, screen_h = self._dimensions
        x = x or 0
        y = y or 0
        w = width or screen_w
        h = height or screen_h

        region = (x, y, w, h)

        element_path = self._search_image_file(label)

        if threshold:
            # TODO: Figure out how we should do threshold
            print('Threshold not yet supported')

        if not best:
            # TODO: Implement best=False.
            print('Warning: Ignoring best=False for now. It will be supported in the future.')

        start_time = time.time()

        while True:
            elapsed_time = (time.time() - start_time) * 1000
            if elapsed_time > waiting_time:
                return None
            haystack = self.get_screen_image(region=region)
            it = cv2find.locate_all_opencv(element_path, haystack_image=haystack,
                                           region=region, confidence=matching, grayscale=grayscale)
            try:
                ele = next(it)
            except StopIteration:
                ele = None

            self.state.element = ele
            return ele

    def find_text(self, label, x=None, y=None, width=None, height=None, *, threshold=None, matching=0.9,
                  waiting_time=10000, best=True):
        """
        Find an element defined by label on screen until a timeout happens.

        Args:
            label (str): The image identifier
            x (int, optional): Search region start position x. Defaults to 0.
            y (int, optional): Search region start position y. Defaults to 0.
            width (int, optional): Search region width. Defaults to screen width.
            height (int, optional): Search region height. Defaults to screen height.
            threshold (int, optional): The threshold to be applied when doing grayscale search.
                Defaults to None.
            matching (float, optional): The matching index ranging from 0 to 1.
                Defaults to 0.9.
            waiting_time (int, optional): Maximum wait time (ms) to search for a hit.
                Defaults to 10000ms (10s).
            best (bool, optional): Whether or not to keep looking until the best matching is found.
                Defaults to True.

        Returns:
            element (NamedTuple): The element coordinates. None if not found.
        """
        return self.find_until(label, x, y, width, height, threshold=threshold, matching=matching,
                               waiting_time=waiting_time, best=best, grayscale=True)

    def get_last_element(self):
        """
        Return the last element found.

        Returns:
            element (NamedTuple): The element coordinates (left, top, width, height)
        """
        return self.state.element

    def display_size(self):
        """
        Returns the display size in pixels.

        Returns:
            size (Tuple): The screen dimension (width and height) in pixels.
        """
        return self._dimensions

    def screenshot(self, filepath=None, region=None):
        """
        Capture a screenshot.

        Args:
            filepath (str, optional): The filepath in which to save the screenshot. Defaults to None.
            region (tuple, optional): Bounding box containing left, top, width and height to crop screenshot.

        Returns:
            Image: The screenshot Image object
        """
        img = self.get_screen_image(region)
        if filepath:
            img.save(filepath)
        return img

    def get_screenshot(self, filepath=None, region=None):
        """
        Capture a screenshot.

        Args:
            filepath (str, optional): The filepath in which to save the screenshot. Defaults to None.
            region (tuple, optional): Bounding box containing left, top, width and height to crop screenshot.

        Returns:
            Image: The screenshot Image object
        """
        return self.screenshot(filepath, region)

    def screen_cut(self, x, y, width=None, height=None):
        """
        Capture a screenshot from a region of the screen.

        Args:
            x (int): region start position x
            y (int): region start position y
            width (int): region width
            height (int): region height

        Returns:
            Image: The screenshot Image object
        """
        screen_size = self._dimensions
        x = x or 0
        y = y or 0
        width = width or screen_size[0]
        height = height or screen_size[1]
        img = self.screenshot(region=(x, y, width, height))
        return img

    def save_screenshot(self, path):
        """
        Saves a screenshot in a given path.

        Args:
            path (str): The filepath in which to save the screenshot

        """
        self.screenshot(path)

    def get_element_coords(self, label, x=None, y=None, width=None, height=None, matching=0.9, best=True):
        """
        Find an element defined by label on screen and returns its coordinates.

        Args:
            label (str): The image identifier
            x (int, optional): X (Left) coordinate of the search area.
            y (int, optional): Y (Top) coordinate of the search area.
            width (int, optional): Width of the search area.
            height (int, optional): Height of the search area.
            matching (float, optional): Minimum score to consider a match in the element image recognition process.
                Defaults to 0.9.
            best (bool, optional): Whether or not to search for the best value. If False the method returns on
                the first find. Defaults to True.

        Returns:
            coords (Tuple): A tuple containing the x and y coordinates for the element.
        """
        self.state.element = None
        screen_size = self._dimensions
        x = x or 0
        y = y or 0
        width = width or screen_size[0]
        height = height or screen_size[1]
        region = (x, y, width, height)

        if not best:
            print('Warning: Ignoring best=False for now. It will be supported in the future.')

        it = cv2find.locate_all_opencv(self.state.map_images[label], region=region, confidence=matching)
        try:
            ele = next(it)
        except StopIteration:
            ele = None
            self.state.element = ele

        if ele:
            return ele.left, ele.top
        else:
            return None, None

    def get_element_coords_centered(self, label, x=None, y=None, width=None, height=None,
                                    matching=0.9, best=True):
        """
        Find an element defined by label on screen and returns its centered coordinates.

        Args:
            label (str): The image identifier
            x (int, optional): X (Left) coordinate of the search area.
            y (int, optional): Y (Top) coordinate of the search area.
            width (int, optional): Width of the search area.
            height (int, optional): Height of the search area.
            matching (float, optional): Minimum score to consider a match in the element image recognition process.
                Defaults to 0.9.
            best (bool, optional): Whether or not to search for the best value. If False the method returns on
                the first find. Defaults to True.

        Returns:
            coords (Tuple): A tuple containing the x and y coordinates for the center of the element.
        """
        self.get_element_coords(label, x, y, width, height, matching, best)
        return self.state.center()

    #########
    # Browser
    #########
    def page_title(self):
        """
        Returns the active page title.

        Returns:
            title (str): The page title.
        """
        try:
            return self._driver.title
        except InvalidSessionIdException:
            return None

    def page_source(self):
        """
        Returns the active page source.

        Returns:
            soup (BeautifulSoup): BeautifulSoup object for the page source.
        """
        try:
            soup = BeautifulSoup(self._driver.page_source, 'html.parser')
            return soup
        except InvalidSessionIdException:
            return None

    def navigate_to(self, url, is_retry=False):
        """
        Opens the browser on the given URL.

        Args:
            url (str):  The URL to be visited.
            is_retry (bool): Whether or not this is a retry attempt.
        """
        self._x = 0
        self._y = 0
        if not self._driver:
            self.start_browser()
        try:
            self._driver.get(url)
        except InvalidSessionIdException:
            if not is_retry:
                self.stop_browser()
                self.navigate_to(url, is_retry=True)

    def browse(self, url):
        """
        Opens the browser on the given URL.

        Args:
            url (str):  The URL to be visited.
        """
        self.navigate_to(url)

    def execute_javascript(self, code):
        """
        Execute the given javascript code.

        Args:
            code (str): The code to be executed.

        Returns:
            value (object): Returns the code output or None if not available or if an error happens.
        """
        return self._driver.execute_script(code)

    def handle_js_dialog(self, accept=True, prompt_text=None):
        """
        Accepts or dismisses a JavaScript initiated dialog (alert, confirm, prompt, or onbeforeunload).
        This also cleans the dialog information in the local buffer.

        Args:
            accept (bool): Whether to accept or dismiss the dialog.
            prompt_text (str): The text to enter into the dialog prompt before accepting.
                Used only if this is a prompt dialog.
        """
        dialog = self.get_js_dialog()
        if not dialog:
            # TODO: Maybe we should raise an exception here if no alert available
            return
        if prompt_text is not None:
            dialog.send_keys(prompt_text)
        if accept:
            dialog.accept()
        else:
            dialog.dismiss()

    def get_js_dialog(self):
        """
        Return the last found dialog. Invoke first the `find_js_dialog` method to look up.

        Returns:
            dialog (dict): The dialog information or None if not available.
                See https://chromedevtools.github.io/devtools-protocol/tot/Page/#event-javascriptDialogOpening
        """
        try:
            dialog = self._driver.switch_to.alert
            return dialog
        except Exception:
            return None

    def get_tabs(self):
        try:
            return self._driver.window_handles
        except InvalidSessionIdException:
            return []

    def create_tab(self, url):
        try:
            # Refactor this when Selenium 4 is released
            self.execute_javascript(f"window.open('{url}', '_blank');")
            self._driver.switch_to.window(self.get_tabs()[-1])
        except InvalidSessionIdException:
            self.navigate_to(url)

    def create_window(self, url):

        try:
            # Refactor this when Selenium 4 is released
            self.execute_javascript(f"window.open('{url}', '_blank', 'location=0');")
            self._driver.switch_to.window(self.get_tabs()[-1])
        except InvalidSessionIdException:
            self.navigate_to(url)

    def close_page(self):
        try:
            self._driver.close()

            # If it was the last tab we can't switch
            tabs = self.get_tabs()
            if tabs:
                self._driver.switch_to.window(tabs[-1])
        except InvalidSessionIdException:
            pass

    def activate_tab(self, handle):
        self._driver.switch_to.window(handle)

    #######
    # Mouse
    #######

    @only_if_element
    def click_on(self, label):
        """
        Click on the element.

        Args:
            label (str): The image identifier
        """
        x, y = self.get_element_coords_centered(label)
        self.click(x, y)

    @only_if_element
    def get_last_x(self):
        """
        Get the last X position for the mouse.

        Returns:
            x (int): The last x position for the mouse.
        """
        return self._x

    def get_last_y(self):
        """
        Get the last Y position for the mouse.

        Returns:
            y (int): The last y position for the mouse.
        """
        return self._y

    def mouse_move(self, x, y):
        """
        Mouse the move to the coordinate defined by x and y

        Args:
            x (int): The X coordinate
            y (int): The Y coordinate

        """
        # ActionChains(self._driver).move_by_offset(-self._x, -self._y).perform()
        mx = x - self._x
        my = y - self._y
        self._x = x
        self._y = y
        ActionChains(self._driver).move_by_offset(mx, my).perform()

    def click_at(self, x, y, *, clicks=1, interval_between_clicks=0, button='left'):
        """
        Click at the coordinate defined by x and y

        Args:
            x (int): The X coordinate
            y (int): The Y coordinate
            clicks (int, optional): Number of times to click. Defaults to 1.
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
            button (str, optional): One of 'left', 'right'. Defaults to 'left'
        """
        self.mouse_move(x, y)
        ac = ActionChains(self._driver)
        for i in range(clicks):
            if button == 'left':
                ac.click()
            elif button == 'right':
                ac.context_click()
            else:
                raise ValueError('Invalid value for button. Accepted values are left or right.')
            ac.pause(interval_between_clicks/1000.0)
        ac.perform()

    @only_if_element
    def click(self, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION, *,
              clicks=1, interval_between_clicks=0, button='left'):
        """
        Click on the last found element.

        Args:
            wait_after (int, optional): Interval to wait after clicking on the element.
            clicks (int, optional): Number of times to click. Defaults to 1.
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
            button (str, optional): One of 'left', 'right', 'middle'. Defaults to 'left'
        """
        x, y = self.state.center()
        self.click_at(x, y, clicks=clicks, button=button, interval_between_clicks=interval_between_clicks)
        self.sleep(wait_after)

    @only_if_element
    def click_relative(self, x, y, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION, *,
                       clicks=1, interval_between_clicks=0, button='left'):
        """
        Click Relative on the last found element.

        Args:
            x (int): Horizontal offset
            y (int): Vertical offset
            wait_after (int, optional): Interval to wait after clicking on the element.
            clicks (int, optional): Number of times to click. Defaults to 1.
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
            button (str, optional): One of 'left', 'right', 'middle'. Defaults to 'left'
        """
        x = self.state.x() + x
        y = self.state.y() + y
        self.click_at(x, y, clicks=clicks, button=button, interval_between_clicks=interval_between_clicks)
        self.sleep(wait_after)

    @only_if_element
    def double_click(self, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION):
        """
        Double Click on the last found element.

        Args:
            wait_after (int, optional): Interval to wait after clicking on the element.
        """
        self.click(interval_between_clicks=wait_after, clicks=2)

    @only_if_element
    def double_click_relative(self, x, y, interval_between_clicks=0, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION):
        """
        Double Click Relative on the last found element.

        Args:
            x (int): Horizontal offset
            y (int): Vertical offset
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
            wait_after (int, optional): Interval to wait after clicking on the element.
        """
        self.click_relative(x, y, wait_after=wait_after, clicks=2, interval_between_clicks=interval_between_clicks)

    @only_if_element
    def triple_click(self, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION):
        """
        Triple Click on the last found element.

        Args:
            wait_after (int, optional): Interval to wait after clicking on the element.
        """
        self.click(wait_after=wait_after, clicks=3)

    @only_if_element
    def triple_click_relative(self, x, y, interval_between_clicks=0, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION):
        """
        Triple Click Relative on the last found element.

        Args:
            x (int): Horizontal offset
            y (int): Vertical offset
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
            wait_after (int, optional): Interval to wait after clicking on the element.
        """
        self.click_relative(x, y, wait_after=wait_after, clicks=3, interval_between_clicks=interval_between_clicks)

    def mouse_down(self, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION, *, button='left'):
        """
        Holds down the requested mouse button.

        Args:
            wait_after (int, optional): Interval to wait after clicking on the element.
            button (str, optional): One of 'left', 'right', 'middle'. Defaults to 'left'
        """
        ActionChains(self._driver).click_and_hold().perform()
        self.sleep(wait_after)

    def mouse_up(self, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION, *, button='left'):
        """
        Releases the requested mouse button.

        Args:
            wait_after (int, optional): Interval to wait after clicking on the element.
            button (str, optional): One of 'left', 'right', 'middle'. Defaults to 'left'
        """
        ActionChains(self._driver).release().perform()
        self.sleep(wait_after)

    def scroll_down(self, clicks):
        """
        Scroll Down n clicks

        Args:
            clicks (int): Number of times to scroll down.
        """
        for i in range(clicks):
            self._driver.execute_script("window.scrollTo(0, window.scrollY + 200)")
            self.sleep(200)

    def scroll_up(self, clicks):
        """
        Scroll Up n clicks

        Args:
            clicks (int): Number of times to scroll up.
        """
        for i in range(clicks):
            self._driver.execute_script("window.scrollTo(0, window.scrollY - 200)")
            self.sleep(200)

    def move_to(self, x, y):
        """
        Move the mouse relative to its current position.

        Args:
            x (int): The X coordinate
            y (int): The Y coordinate
        """
        self.mouse_move(x, y)

    @only_if_element
    def move(self):
        """
        Move to the center position of last found item.
        """
        x, y = self.state.center()
        self.move_to(x, y)

    def move_relative(self, x, y):
        """
        Move the mouse relative to its current position.

        Args:
            x (int): Horizontal offset
            y (int): Vertical offset

        """
        x = self.get_last_x() + x
        y = self.get_last_y() + y
        self.move_to(x, y)

    def move_random(self, range_x, range_y):
        """
        Move randomly along the given x, y range.

        Args:
            range_x (int): Horizontal range
            range_y (int): Vertical range

        """
        x = int(random.random() * range_x)
        y = int(random.random() * range_y)
        self.move_to(x, y)

    @only_if_element
    def right_click(self, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION, *,
                    clicks=1, interval_between_clicks=0):
        """
        Right click on the last found element.

        Args:
            wait_after (int, optional): Interval to wait after clicking on the element.
            clicks (int, optional): Number of times to click. Defaults to 1.
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
        """
        self.click(clicks=clicks, button='right', interval=interval_between_clicks)
        self.sleep(wait_after)

    def right_click_at(self, x, y):
        """
        Right click at the coordinate defined by x and y

        Args:
            x (int): The X coordinate
            y (int): The Y coordinate
        """
        self.click_at(x, y, button='right')

    @only_if_element
    def right_click_relative(self, x, y, interval_between_clicks=0, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION):
        """
        Right Click Relative on the last found element.

        Args:
            x (int): Horizontal offset
            y (int): Vertical offset
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
            wait_after (int, optional): Interval to wait after clicking on the element.

        """
        self.click_relative(x, y, wait_after=wait_after, interval_between_clicks=interval_between_clicks,
                            button='right')

    ##########
    # Keyboard
    ##########
    def kb_type(self, text, interval=0):
        """
        Type a text char by char (individual key events).

        Args:
            text (str): text to be typed.
            interval (int, optional): interval (ms) between each key press. Defaults to 0
        """
        action = ActionChains(self._driver)

        for c in text:
            action.send_keys(c)
            action.pause(interval / 1000.0)

        action.perform()
        self.sleep(config.DEFAULT_SLEEP_AFTER_ACTION)

    def paste(self, text=None, wait=0):
        """
        Paste content from the clipboard.

        Args:
            text (str, optional): The text to be pasted. Defaults to None
            wait (int, optional): Wait interval (ms) after task
        """
        text_to_paste = self._clipboard
        if text:
            text_to_paste = text
        self.kb_type(text_to_paste)

    def copy_to_clipboard(self, text, wait=0):
        """
        Copy content to the clipboard.

        Args:
            text (str): The text to be copied.
            wait (int, optional): Wait interval (ms) after task
        """
        self._clipboard = text
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def tab(self, wait=0):
        """
        Press key Tab

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.TAB)
        action.key_up(Keys.TAB)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def enter(self, wait=0):
        """
        Press key Enter

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.ENTER)
        action.key_up(Keys.ENTER)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def key_right(self, wait=0):
        """
        Press key Right

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.ARROW_RIGHT)
        action.key_up(Keys.ARROW_RIGHT)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def key_enter(self, wait=0):
        """
        Press key Enter

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self.enter(wait)

    def key_home(self, wait=0):
        """
        Press key Home

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        # TODO: Investigate why with Firefox the key isn't working properly
        action = ActionChains(self._driver)
        action.key_down(Keys.HOME)
        action.key_up(Keys.HOME)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def key_end(self, wait=0):
        """
        Press key End

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.END)
        action.key_up(Keys.END)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def page_up(self, wait=0):
        """
        Press Page Up key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        # TODO: Investigate why with Firefox the key isn't working properly
        action = ActionChains(self._driver)
        action.key_down(Keys.PAGE_UP)
        action.key_up(Keys.PAGE_UP)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def page_down(self, wait=0):
        """
        Press Page Down key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        # TODO: Investigate why with Firefox the key isn't working properly
        action = ActionChains(self._driver)
        action.key_down(Keys.PAGE_DOWN)
        action.key_up(Keys.PAGE_DOWN)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def key_esc(self, wait=0):
        """
        Press key Esc

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.ESCAPE)
        action.key_up(Keys.ESCAPE)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def _key_fx(self, idx, wait=0):
        """
        Press key Fidx where idx is a value from 1 to 12

        Args:
            idx (int): F key index from 1 to 12
            wait (int, optional): Wait interval (ms) after task

        """
        if idx < 1 or idx > 12:
            raise ValueError("Only F1 to F12 allowed.")
        action = ActionChains(self._driver)
        key = getattr(Keys, f"F{idx}")
        action.key_down(key)
        action.key_up(key)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def hold_shift(self, wait=0):
        """
        Hold key Shift

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.SHIFT)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def release_shift(self):
        """
        Release key Shift.
        This method needs to be invoked after holding Shift or similar.
        """
        action = ActionChains(self._driver)
        action.key_up(Keys.SHIFT)
        action.perform()

    def maximize_window(self):
        """
        Shortcut to maximize window on Windows OS.
        """
        # TODO: Understand the complications associated with maximizing the browser and the resolution
        self._driver.maximize_window()

    def type_keys_with_interval(self, interval, keys):
        """
        Press a sequence of keys. Hold the keys in the specific order and releases them.

        Args:
            interval (int): Interval (ms) in which to press and release keys
            keys (list): List of Keys to be pressed
        """
        action = ActionChains(self._driver)

        for k in keys:
            action.key_down(k)
            action.pause(interval / 1000.0)
        for k in reversed(keys):
            action.key_up(k)
            action.pause(interval / 1000.0)
        action.perform()

    def type_keys(self, keys):
        """
        Press a sequence of keys. Hold the keys in the specific order and releases them.

        Args:
            keys (list): List of keys to be pressed
        """
        self.type_keys_with_interval(100, keys)

    def control_c(self, wait=0):
        """
        Press keys CTRL+C

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        # Firefox can't do window.getSelection() and return a proper value when the selected text
        # is in an input of similar. While Firefox doesn't get its shit together we apply this
        # ugly alternative so control+c works for "all" browsers tested so far.
        cmd = """
            try {
                return document.activeElement.value.substring(
                    document.activeElement.selectionStart,
                    document.activeElement.selectionEnd
                );
            } catch(error) {
                return window.getSelection().toString();
            }
        """

        self._clipboard = self.execute_javascript(cmd)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def control_v(self, wait=0):
        """
        Press keys CTRL+V

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self.paste()

    def control_a(self, wait=0):
        """
        Press keys CTRL+A

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        key = Keys.CONTROL
        if platform.system() == 'Darwin':
            key = Keys.COMMAND

        action.key_down(key)
        action.send_keys('a')
        action.key_up(key)
        action.perform()

    def get_clipboard(self):
        """
        Get the current content in the clipboard.

        Returns:
            text (str): Current clipboard content
        """
        return self._clipboard

    def type_left(self, wait=0):
        """
        Press Left key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.ARROW_LEFT)
        action.key_up(Keys.ARROW_LEFT)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def type_right(self, wait=0):
        """
        Press Right key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self.key_right(wait=wait)

    def type_down(self, wait=0):
        """
        Press Down key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.ARROW_DOWN)
        action.key_up(Keys.ARROW_DOWN)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def type_up(self, wait=0):
        """
        Press Up key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.ARROW_UP)
        action.key_up(Keys.ARROW_UP)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def space(self, wait=0):
        """
        Press Space key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.SPACE)
        action.key_up(Keys.SPACE)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def backspace(self, wait=0):
        """
        Press Backspace key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.BACK_SPACE)
        action.key_up(Keys.BACK_SPACE)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def delete(self, wait=0):
        """
        Press Delete key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        action = ActionChains(self._driver)
        action.key_down(Keys.DELETE)
        action.key_up(Keys.DELETE)
        action.perform()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    ######
    # Misc
    ######

    def wait(self, interval):
        """
        Wait / Sleep for a given interval.

        Args:
            interval (int): Interval in milliseconds

        """
        time.sleep(interval / 1000.0)

    def sleep(self, interval):
        """
        Wait / Sleep for a given interval.

        Args:
            interval (int): Interval in milliseconds

        """
        self.wait(interval)

    def wait_for_file(self, path, timeout=10000):
        """
        Invoke the system handler to open the given file.

        Args:
            path (str): The path for the file to be executed
            timeout (int, optional): Maximum wait time (ms) to search for a hit.
                Defaults to 10000ms (10s).

        Returns:
            status (bool): Whether or not the file was available before the timeout

        """
        start_time = time.time()

        while True:
            elapsed_time = (time.time() - start_time) * 1000
            if elapsed_time > timeout:
                return False
            if os.path.isfile(path) and os.access(path, os.R_OK):
                return True
            self.sleep(config.DEFAULT_SLEEP_AFTER_ACTION)
