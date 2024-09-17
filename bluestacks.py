import win32gui
import pyautogui

DEBUG = False
BLUESTACKS = {}
GAME = {}

def window_callback(hwnd, extra=None):
    """Use win32gui to find the location of the bluestacks window"""
    global BLUESTACKS, GAME
    title = win32gui.GetWindowText(hwnd)
    if "bluestacks app player" not in title.lower():
        return
    if extra is not None and 'reset' in extra and extra['reset']:
        left, top = 0, 0
        w, h = 659, 1131
        win32gui.MoveWindow(hwnd, left, top, w, h, True)
        win32gui.SetWindowPos(hwnd, None, left, top, w, h, 0)

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bottom - top
    print(f"'{title}', Loc: ({left}, {top}), Size: ({w}, {h})")
    BLUESTACKS = {
        'left': left,
        'top': top,
        'right': right,
        'bottom': bottom,
        'width': w,
        'height': h,
    }

    # Find game window inside of Bluestacks window
    border_color = (35, 38, 66)
    game_top = None
    game_right = None
    # Search down from the top left corner
    for i in range(75):
        x = BLUESTACKS['left'] + 3
        y = BLUESTACKS['top']
        yy = y + i
        if DEBUG:
            pyautogui.moveTo(x, yy)
        pix = pyautogui.pixel(x, yy)
        if pix != border_color and i > 10:
            #print(f"Found pixel {pix} at ({x}, {yy})")
            game_top = yy
            break
    # Search leftwards from the bottom right corner
    for i in range(75):
        x = BLUESTACKS['right']
        y = BLUESTACKS['bottom'] - 3
        xx = x - i
        if DEBUG:
            pyautogui.moveTo(xx, y)
        pix = pyautogui.pixel(xx, y)
        if pix != border_color and i > 10:
            #print(f"Found pixel {pix} at ({xx}, {y})")
            game_right = xx
            break
    # Set results
    # finding isn't working great...
    game_top = BLUESTACKS['top'] + 49
    game_right = BLUESTACKS['right'] - 53
    GAME = {
        'left': left,
        'top': game_top,
        'right': game_right,
        'bottom': bottom,
        'width': game_right - left,
        'height': bottom - game_top,
    }


def get_dimensions(reset=False):
    args = {'reset': reset}
    win32gui.EnumWindows(window_callback, args)
    return {'bluestacks': BLUESTACKS, 'game': GAME}


# def get_bluestacks_dimensions():
#     get_dimensions()
#     print(f"{BLUESTACKS=}")
#     return BLUESTACKS


# def get_game_dimensions():
#     get_dimensions()
#     print(f"{GAME=}")
#     return GAME


# def reset_window():
#     get_dimensions(reset=True)

if __name__ == "__main__":
    dimensions = get_dimensions()
    print(dimensions)