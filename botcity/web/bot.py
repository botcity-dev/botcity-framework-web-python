import base64
import functools
import io
import logging
import multiprocessing
import os
import websocket
import random
import time
import pyperclip

import PyChromeDevTools
from PIL import Image

from botcity.base import BaseBot, State
from botcity.base.utils import only_if_element

from . import config, cv2find
from .chrome import ChromeLauncher


logger = logging.getLogger(__name__)


class WebBot(BaseBot):
    """
    Base class for Web Bots.
    Users must implement the `action` method in their classes.

    Attributes:
        state (State): The internal state of this bot.
        maestro (BotMaestroSDK): an instance to interact with the BotMaestro server.

    """

    def __init__(self, headless=False):
        self.state = State()
        self.maestro = None

        self._ip = "localhost"

        self._headless = headless

        self._chrome_launcher = None
        self._devtools_service = None
        self._tab = None
        self._first_tab = True

        self._page = None
        self._network = None
        self._input = None
        self._run = None
        self._tabs = []

        self._last_clipboard = None

        # Stub mouse coordinates
        self._x = 0
        self._y = 0

        # State for Key modifiers
        self._shift_hold = False

        self._dimensions = (1600, 900)
        self._download_folder_path = os.path.join(os.path.expanduser("~"), "Desktop")

    @property
    def headless(self):
        return self._headless

    @headless.setter
    def headless(self, headless):
        """
        Controls whether or not the bot will run headless.

        Args:
            headless (boolean): If set to True will make the bot run headless.
        """
        if self._chrome_launcher:
            logger.warning("Browser is running. Invoke stop_browser and start_browser for changes to take effect.")
        self._headless = headless

    def start_browser(self):
        """
        Start the Chrome Browser and sets up the permissions required.
        """
        if not self._chrome_launcher:
            self._chrome_launcher = ChromeLauncher(headless=self.headless)
            self._chrome_launcher.launch()
        if not self._devtools_service:
            self._devtools_service = PyChromeDevTools.ChromeInterface(host=self._ip,
                                                                      port=self._chrome_launcher.devtools_port)
        self._page = self._devtools_service.Page
        self._page.enable()
        self._network = self._devtools_service.Network
        self._input = self._devtools_service.Input
        self._network.enable()
        self._run = self._devtools_service.Runtime
        self._run.enable()
        self._devtools_service.Accessibility.enable()
        self._devtools_service.ApplicationCache.enable()
        self.set_download_folder()
        permissions = [
            "accessibilityEvents",
            "audioCapture",
            "backgroundSync",
            "backgroundFetch",
            "clipboardReadWrite",
            "clipboardSanitizedWrite",
            "displayCapture",
            "durableStorage",
            "flash",
            "geolocation",
            "midi",
            "midiSysex",
            "nfc",
            "notifications",
            "paymentHandler",
            "videoCapture",
            "idleDetection"
        ]
        self._devtools_service.Browser.grantPermissions(permissions=permissions)

    def stop_browser(self):
        """
        Stops the Chrome browser and clean up the User Data Directory.
        """
        try:
            self._devtools_service.Browser.close()
            time.sleep(1)
        except (BrokenPipeError, websocket.WebSocketConnectionClosedException):
            # Likely the connection as interrupted already or it timed-out
            pass
        self._chrome_launcher.shutdown()

    def set_download_folder(self, path=None):
        """
        Set the destination folder for downloads.

        Args:
            path (str): The desired path.

        """
        if path:
            self._download_folder_path = path
        if not self._devtools_service:
            return
        self._devtools_service.Browser.setDownloadBehavior(
            behavior="allow",
            browserContextId=None,
            downloadPath=self._download_folder_path,
            eventsEnabled=True
        )

    def set_screen_resolution(self, width=None, height=None):
        """
        Configures the browser dimensions.

        Args:
            width (int): The desired width.
            height (int): The desired height.
        """
        width = width or self._dimensions[0]
        height = height or self._dimensions[1]

        bounds = {
            "left": 0, "top": 0, "width": width, "height": height
        }
        window_id = self.get_window_id()
        self._devtools_service.Browser.setWindowBounds(windowId=window_id, bounds=bounds)
        self._devtools_service.Emulation.setVisibleSize(width=width, height=height)

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
        layout_metrics = self._page.getLayoutMetrics()[0]
        if layout_metrics:
            content_size = layout_metrics['result']['contentSize']
            x = region[0] or 0
            y = region[1] or 0
            width = region[2] or content_size['width']
            height = region[3] or content_size['height']
        else:
            x = 0
            y = 0
            width = self._dimensions[0]
            height = self._dimensions[1]
        viewport = dict(x=x, y=y, width=width, height=height, scale=1)
        data = self._page.captureScreenshot(format="png", quality=100, clip=viewport,
                                            fromSurface=True, captureBeyondViewport=False)
        data = data[0]['result']['data']
        image = base64.b64decode(data)
        return Image.open(io.BytesIO(image))

    def get_viewport_size(self):
        """
        Returns the browser current viewport size.

        Returns:
            width (int): The current viewport width.
            height (int): The current viewport height.
        """
        layout_metrics = self._page.getLayoutMetrics()
        content_size = layout_metrics[0]['result']['contentSize']
        width = content_size['width']
        height = content_size['height']
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

        screen_w, screen_h = self.get_viewport_size()
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
            helper = functools.partial(self.__find_multiple_helper, haystack, region, matching, grayscale)

            with multiprocessing.Pool(processes=n_cpus) as pool:
                results = pool.map(helper, paths)

            results = [r for r in results]
            if None in results:
                continue
            else:
                return _to_dict(labels, results)

    def __find_multiple_helper(self, haystack, region, confidence, grayscale, needle):
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
        screen_w, screen_h = self.get_viewport_size()
        x = x or 0
        y = y or 0
        w = width or screen_w
        h = height or screen_h

        region = (x, y, w, h)

        element_path = self.state.map_images[label]

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
            ele = next(it)
            if ele is not None:
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
        screen_size = self.get_viewport_size()
        return screen_size.width, screen_size.height

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
        screen_size = self.get_viewport_size()
        x = x or 0
        y = y or 0
        width = width or screen_size.width
        height = height or screen_size.height
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
        screen_size = self.get_viewport_size()
        x = x or 0
        y = y or 0
        width = width or screen_size.width
        height = height or screen_size.height
        region = (x, y, width, height)

        if not best:
            print('Warning: Ignoring best=False for now. It will be supported in the future.')

        it = cv2find.locate_all_opencv(self.state.map_images[label], region=region, confidence=matching)
        ele = next(it)
        self.state.element = ele
        return ele.left, ele.top

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

    def navigate_to(self, url, wait=False):
        """
        Opens the browser on the given URL.

        Args:
            url (str):  The URL to be visited.
            wait (bool): Whether or not to wait for the loadEvent fo be fired. Defaults to False.

        """
        self.start_browser()
        self.set_screen_resolution()
        self._page.navigate(url=url)
        if wait:
            self._devtools_service.wait_event("Page.frameStoppedLoading",
                                              timeout=config.DEFAULT_NAVIGATE_TIMEOUT / 1000)

    def browse(self, url, wait=False):
        """
        Opens the browser on the given URL.

        Args:
            url (str):  The URL to be visited.
            wait (bool): Whether or not to wait for the loadEvent fo be fired. Defaults to False.

        """
        self.navigate_to(url, wait=wait)

    def execute_javascript(self, code):
        """
        Execute the given javascript code.

        Args:
            code (str): The code to be executed.

        Returns:
            value (object): Returns the code output or None if not available or if an error happens.
        """
        # TODO: Check for errors and return the error as well
        output = self._run.evaluate(expression=code)
        if output:
            result = output[0]['result'].get('result')
            if result:
                return result.get('value')
        return None

    def get_window_id(self):
        """
        Fetch the current window Id

        Returns:
            id (str): The window Id
        """
        return self._devtools_service.Browser.getWindowForTarget()[0]['result']['windowId']

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
        self._x = x
        self._y = y
        self._input.dispatchMouseEvent(type="mouseMoved", x=x, y=y)

    def click_at(self, x, y, *, clicks=1, interval_between_clicks=0, button='left'):
        """
        Click at the coordinate defined by x and y

        Args:
            x (int): The X coordinate
            y (int): The Y coordinate
            clicks (int, optional): Number of times to click. Defaults to 1.
            interval_between_clicks (int, optional): The interval between clicks in ms. Defaults to 0.
            button (str, optional): One of 'left', 'right', 'middle'. Defaults to 'left'
        """
        button_idx = ["None", "left", "right", "middle"]
        idx = button_idx.index(button)
        self._x = x
        self._y = y
        for i in range(clicks):
            self._input.dispatchMouseEvent(
                type="mousePressed", x=x, y=y, button=button, buttons=idx, clickCount=1
            )
            self._input.dispatchMouseEvent(
                type="mouseReleased", x=x, y=y, button=button, buttons=idx, clickCount=1
            )
            self.sleep(interval_between_clicks)

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
        x, y = self.state.center()
        self.click(x, y, wait_after=wait_after, click=2)

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
        x = self.state.x() + x
        y = self.state.y() + y
        self.click_relative(x, y, wait_after=wait_after, click=2, interval_between_clicks=interval_between_clicks)

    @only_if_element
    def triple_click(self, wait_after=config.DEFAULT_SLEEP_AFTER_ACTION):
        """
        Triple Click on the last found element.

        Args:
            wait_after (int, optional): Interval to wait after clicking on the element.
        """
        x, y = self.state.center()
        self.click(x, y, wait_after=wait_after, click=3)

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
        x = self.state.x() + x
        y = self.state.y() + y
        self.click_relative(x, y, wait_after=wait_after, click=3, interval_between_clicks=interval_between_clicks)

    def scroll_down(self, clicks):
        """
        Scroll Down n clicks

        Args:
            clicks (int): Number of times to scroll down.
        """
        for i in range(clicks):
            self._input.dispatchKeyEvent(type="keyDown", commands=["ScrollLineDown"])
            self.sleep(200)
            self._input.dispatchKeyEvent(type="keyUp", commands=["ScrollLineDown"])

    def scroll_up(self, clicks):
        """
        Scroll Up n clicks

        Args:
            clicks (int): Number of times to scroll up.
        """
        for i in range(clicks):
            self._input.dispatchKeyEvent(type="keyDown", commands=["ScrollLineUp"])
            self.sleep(200)
            self._input.dispatchKeyEvent(type="keyUp", commands=["ScrollLineUp"])

    def move_to(self, x, y):
        """
        Move the mouse relative to its current position.

        Args:
            x (int): The X coordinate
            y (int): The Y coordinate
        """
        self._x = x
        self._y = y
        self._input.dispatchMouseEvent(type="mouseMoved", x=x, y=y)

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
        x, y = self.state.center()
        self.click_at(x, y, clicks=clicks, button='right', interval=interval_between_clicks)
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
        x = self.state.x() + x
        y = self.state.y() + y
        self.click_relative(x, y, wait_after=wait_after, interval_between_clicks=interval_between_clicks,
                            button='right')

    ##########
    # Keyboard
    ##########

    def _dispatch_key_event(self, *, event_type="keyDown", text=None, key=None, virtual_kc=None, execute_up=True):
        kwargs = {
            "type": event_type
        }
        if text:
            kwargs.update({"text": text})
        if virtual_kc is not None:
            kwargs.update({"windowsVirtualKeyCode": virtual_kc, "nativeVirtualKeyCode": virtual_kc})
        if key is not None:
            kwargs.update({"key": key})

        self._input.dispatchKeyEvent(**kwargs)
        if execute_up:
            self._input.dispatchKeyEvent(type="keyUp")

    def kb_type(self, text, interval=0):
        """
        Type a text char by char (individual key events).

        Args:
            text (str): text to be typed.
            interval (int, optional): interval (ms) between each key press. Defaults to 0
        """
        for c in text:
            self._dispatch_key_event(event_type="char", text=c, execute_up=False)
            self.sleep(interval)
        self.sleep(config.DEFAULT_SLEEP_AFTER_ACTION)

    def paste(self, text=None, wait=0):
        """
        Paste content from the clipboard.

        Args:
            text (str, optional): The text to be pasted. Defaults to None
            wait (int, optional): Wait interval (ms) after task
        """
        if text:
            cmd = (
                "var elementfocused = document.activeElement;"
                "function copyStringToClipboard(str) {"
                "  var el = document.createElement('textarea');"
                "  el.value = str;"
                "  el.setAttribute('readonly', '');"
                "  el.style = { position: 'absolute', left: '-9999px' };"
                "  document.body.appendChild(el);"
                "  el.select();"
                "  document.execCommand('copy');"
                "  document.body.removeChild(el);"
                "}"
                f"copyStringToClipboard('{text}');"
                "elementfocused.focus();"
            )
            self.execute_javascript(cmd)
            self.sleep(500)
        self.control_v()
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def copy_to_clipboard(self, text, wait=0):
        """
        Copy content to the clipboard.

        Args:
            text (str): The text to be copied.
            wait (int, optional): Wait interval (ms) after task
        """
        if not self.headless:
            pyperclip.copy(text)
            delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
            self.sleep(delay)
        else:
            raise RuntimeError("The clipboard functionality is only available outside of Headless mode.")

    def tab(self, wait=0):
        """
        Press key Tab

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Tab", virtual_kc=9)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def enter(self, wait=0):
        """
        Press key Enter

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Enter", virtual_kc=13, text="\r")
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def key_right(self, wait=0):
        """
        Press key Right

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Right", virtual_kc=0x27)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def key_enter(self, wait=0):
        """
        Press key Right

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self.enter(wait)

    def key_end(self, wait=0):
        """
        Press key End

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="End", virtual_kc=35)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def key_esc(self, wait=0):
        """
        Press key Esc

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Escape", virtual_kc=27)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def _key_fx(self, idx, wait=0):
        """
        Press key Fidx where idx is a value from 1 to 12

        Args:
            idx (int): F key index from 1 to 12
            wait (int, optional): Wait interval (ms) after task

        """
        code = 111 + idx
        self._dispatch_key_event(event_type="keyDown", key=f"F{idx}", virtual_kc=code)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def hold_shift(self, wait=0):
        """
        Hold key Shift

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._shift_hold = True
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def release_shift(self):
        """
        Release key Shift.
        This method needs to be invoked after holding Shift or similar.
        """
        self._shift_hold = False

    def maximize_window(self):
        """
        Shortcut to maximize window on Windows OS.
        """

        bounds = dict(left=0, top=0, width=0, height=0, windowState="maximized")
        self._devtools_service.Browser.setWindowBounds(windowId=self.get_window_id(), bounds=bounds)
        self.sleep(1000)

    def type_keys_with_interval(self, interval, keys):
        """
        Press a sequence of keys. Hold the keys in the specific order and releases them.

        Args:
            interval (int): Interval (ms) in which to press and release keys
            keys (list): List of keys to be pressed
        """
        # TODO: Implement this method
        raise NotImplementedError()
        # for k in keys:
        #     kb.press(k)
        #     sleep(interval)
        #
        # for k in keys.reverse():
        #     kb.release(k)
        #     sleep(interval)

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
        cmd = (
            "var text = '';"
            "if (window.getSelection) {"
            "  text = window.getSelection().toString();"
            "} else if (document.selection && document.selection.type != 'Control') {"
            "  text = document.selection.createRange().text;"
            "}"
        )
        self.execute_javascript(cmd)
        cmd = (
            "if( null == document.getElementById('clipboardTransferText')) {"
            "  let el = document.createElement('textarea');"
            "  el.value = '';"
            "  el.setAttribute('readonly', '');"
            "  el.style = {position: 'absolute', left: '-9999px'};"
            "  el.id = 'clipboardTransferText';"
            "  document.body.appendChild(el);"
            "}"
            "document.getElementById('clipboardTransferText').value = text;"
        )
        self.execute_javascript(cmd)
        self._input.dispatchKeyEvent(type="keyDown", commands=["Copy"])
        self._input.dispatchKeyEvent(type="keyUp", commands=["Copy"])
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def control_v(self, wait=0):
        """
        Press keys CTRL+V

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._input.dispatchKeyEvent(type="keyDown", commands=["Paste"])
        self._input.dispatchKeyEvent(type="keyUp", commands=["Paste"])
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def control_a(self, wait=0):
        """
        Press keys CTRL+A

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._input.dispatchKeyEvent(type="keyDown", commands=["SelectAll"])
        self._input.dispatchKeyEvent(type="keyUp", commands=["SelectAll"])
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def get_clipboard(self):
        """
        Get the current content in the clipboard.

        Returns:
            text (str): Current clipboard content
        """
        ret = self.execute_javascript("document.getElementById('clipboardTransferText').value")
        if ret:
            self._last_clipboard = ret
            self.execute_javascript("document.getElementById('clipboardTransferText').remove();")
            return ret
        return self._last_clipboard

    def type_left(self, wait=0):
        """
        Press Left key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Left", virtual_kc=37)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def type_right(self, wait=0):
        """
        Press Right key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Right", virtual_kc=39)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def type_down(self, wait=0):
        """
        Press Down key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Down", virtual_kc=40)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def type_up(self, wait=0):
        """
        Press Up key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Up", virtual_kc=38)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def space(self, wait=0):
        """
        Press Space key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Up", virtual_kc=32)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def backspace(self, wait=0):
        """
        Press Backspace key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Back Space", virtual_kc=0x8)
        delay = max(0, wait or config.DEFAULT_SLEEP_AFTER_ACTION)
        self.sleep(delay)

    def delete(self, wait=0):
        """
        Press Delete key

        Args:
            wait (int, optional): Wait interval (ms) after task

        """
        self._dispatch_key_event(event_type="keyDown", key="Delete", virtual_kc=46)
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
