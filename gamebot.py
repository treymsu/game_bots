"""Utilities for game bots"""
# pip install winsdk pyautogui screen_ocr[winrt] wheel pywin32 opencv-python
import time
import os
import logging
from collections import namedtuple
import random
import pyautogui
import pyscreeze
import screen_ocr

logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(lineno)d:%(message)s", datefmt="%H:%M:%S")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Globals
DEFAULT_REGION = None

# Types
Point = namedtuple("Point", ["x", "y"])
# Box = namedtuple("Box", ["x", "y", "w", "h"])
Box = namedtuple("Box", ["left", "top", "width", "height"])
Rect = namedtuple("Rect", ["left", "top", "right", "bottom"])


def random_coord(box: Box) -> Point:
    """Pick a random location within a Box (or the center point)"""
    left, top, width, height = box
    x = random.randrange(left, left + width)
    y = random.randrange(top, top + height)
    return Point(x, y)


class Color:
    """Class to determine if a pixel is within a color range"""

    def __init__(self, color: tuple[int, int, int], crange=(0, 0, 0)):
        self.color = color
        self.crange = crange

    def __eq__(self, in_color):
        if (self.color[0] - self.crange[0] <= in_color[0] <= self.color[0] + self.crange[0]
            and self.color[1] - self.crange[1] <= in_color[1] <= self.color[1] + self.crange[1]
            and self.color[2] - self.crange[2] <= in_color[2] <= self.color[2] + self.crange[2]
        ):
            return True
        return False

    def __str__(self):
        return f"Color{self.color}"


class Region:
    """Draw a box in the game, relative to some anchor point (left, top) game window or elsewhere in the game"""
    def __init__(self, rect: Rect, anchor: Point, debug=False):
        self.debug = debug
        self.anchor = anchor
        self.left = self.anchor.x + rect.left
        self.top = self.anchor.y + rect.top
        self.right = self.anchor.x + rect.right
        self.bottom = self.anchor.y + rect.bottom
        # A Rect can be used for OCR regions
        self.rect = Rect(self.left, self.top, self.right, self.bottom)
        assert self.left <= self.right
        assert self.top <= self.bottom
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        # A Box can be used for image regions
        self.box = Box(self.left, self.top, self.width, self.height)
        self.ocr_reader = screen_ocr.Reader.create_quality_reader()

    def __str__(self):
        return f"Region(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom})"

    def __repr__(self):
        return f"Region(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom})"

    def get_random_point(self) -> Point:
        """Return random Point in region"""
        x = random.randrange(self.left, self.right)
        y = random.randrange(self.top, self.bottom)
        return Point(x, y)

    def click(self):
        """Click random place inside this region"""
        pt = self.get_random_point()
        pyautogui.click(pt)  # or x, y?

    def click_hold(self, timeout):
        """Hold down the mouse at a random place inside this region"""
        pt = self.get_random_point()
        try:
            pyautogui.mouseDown(pt.x, pt.y)
            time.sleep(timeout)
        finally:
            pyautogui.mouseUp()

    def contains_color(self, list_of_colors, x_chg=5, y_chg=5) -> Color | bool:
        """Return true if some pixel in the region contains any of these colors"""
        for xx in range(self.left, self.right+1, x_chg):
            for yy in range(self.top, self.bottom, y_chg):
                if self.debug:
                    pyautogui.moveTo(int(xx), int(yy))
                pix = pyautogui.pixel(int(xx), int(yy))
                # return as soon as a thing in the list matches
                for color in list_of_colors:
                    if pix == color:
                        logger.debug("Color match found in region: %s", pix)
                        return pix
        return False

    def ocr(self):
        """Read text inside region (lowercase, no spaces, no periods)"""
        if self.debug:
            self.draw()
        results = self.ocr_reader.read_screen(self.rect).as_string()
        results = results.strip().replace(" ", "").replace(".", "").lower()
        return results

    def draw(self, duration=0.5, times=1):
        """Move mouse around border of region"""
        for _ in range(times):
            pyautogui.moveTo(self.left, self.top)
            pyautogui.moveTo(self.right, self.top, duration=duration)
            pyautogui.moveTo(self.right, self.bottom, duration=duration)
            pyautogui.moveTo(self.left, self.bottom, duration=duration)
            pyautogui.moveTo(self.left, self.top, duration=duration)


class BoxRegion(Region):
    """Create a Region from a Box instead of from a Rect"""
    def __init__(self, box: Box, anchor: Point=Point(0, 0), debug: bool=False):
        right = box.left + box.width
        bottom = box.top + box.height
        rect = Rect(box.left, box.top, right, bottom)
        super().__init__(rect, anchor, debug)


def find_image(image: str, click: bool=False, confidence: float | None=None,
               region: Box | None=None):
    """Search for an image in a region"""
    c = confidence or 0.8
    if region is None:
        region = DEFAULT_REGION
    action = "Clicked" if click else "Found"
    if not os.path.exists(image):
        logger.error("%s does not exist", image)
        return None
    try:
        loc = pyautogui.locateOnScreen(image, confidence=c, region=region)
        if loc is not None:
            if click:
                coord = random_coord(loc)
                pyautogui.click(coord)
            logger.debug("%s %s at %s", action, image, loc)
    except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException):
        return None
    return loc


def find_image_timeout(image: str, timeout: int, click: bool=False,
                       confidence: float | None=None, region: Box | None=None,
                       quiet: bool=False):
    """Wrap the find_image function with a timeout to search for N seconds"""
    end_time = time.perf_counter() + timeout
    while time.perf_counter() < end_time:
        ret = find_image(image, click, confidence, region)
        if ret:
            return ret
    if not quiet:
        logger.warning("Couldn't find %s after %ds", image, timeout)
    return None


def locate_all(image: str, confidence: float | None=None, region: Region | None=None):
    """Wrapper to catch exceptions"""
    if not os.path.exists(image):
        logger.error("%s does not exist", image)
        return False
    c = confidence or 0.8
    kwargs = {'confidence': c}
    if region:
        kwargs['region'] = region
    try:
        result = list(pyautogui.locateAllOnScreen(
            image, **kwargs))
    except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException):
        result = None
    return result

def set_default_region(reg: Box):
    global DEFAULT_REGION
    DEFAULT_REGION = reg