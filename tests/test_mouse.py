import os
import conftest

from botcity.web import WebBot, By
from pytest import xfail


def test_left_click(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.click()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left'] or result['data'] == ['Left2']


def test_left_double_click(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.double_click()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left', 'Left'] or result['data'] == ['Left2', 'Left2']


def test_left_triple_click(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.triple_click()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left', 'Left', 'Left'] or result['data'] == ['Left2', 'Left2', 'Left2']


def test_triple_click_relative(web: WebBot):
    if web.browser.lower() in 'firefox' and os.getenv('CI') is not None:
        xfail(reason=f"Firefox is not working in CI")

    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000, x=20, y=30, width=310, height=170):
        raise Exception('Image not found: mouse')
    web.triple_click_relative(16, 140)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left2', 'Left2', 'Left2']


def test_right_click(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.right_click()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Right'] or result['data'] == ['Right2']


def test_right_double_click(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.right_click(clicks=2)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Right', 'Right'] or result['data'] == ['Right2', 'Right2']


def test_left_click_relative(web: WebBot):
    if web.browser.lower() in 'firefox' and os.getenv('CI') is not None:
        xfail(reason=f"Firefox is not working in CI")
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000, x=20, y=30, width=310, height=170):
        raise Exception('Image not found: mouse')
    web.click_relative(16, 140)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left2']


def test_left_double_click_relative(web: WebBot):
    if web.browser.lower() in 'firefox' and os.getenv('CI') is not None:
        xfail(reason=f"Firefox is not working in CI")

    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000, x=20, y=30, width=310, height=170):
        raise Exception('Image not found: mouse')
    web.double_click_relative(16, 140)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left2', 'Left2']


def test_right_click_relative(web: WebBot):
    if web.browser.lower() in 'firefox' and os.getenv('CI') is not None:
        xfail(reason=f"Firefox is not working in CI")
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000, x=20, y=30, width=310, height=170):
        raise Exception('Image not found: mouse')
    web.right_click_relative(16, 140)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Right2']


def test_get_last_x(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.move()

    web.move_to(100, 200)
    x = web.get_last_x()

    assert x == 100


def test_get_last_y(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.move()

    web.move_to(100, 200)
    y = web.get_last_y()

    assert y == 200


def test_move_mouse(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000):
        raise Exception('Image not found: mouse')
    web.move()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['mouse-over'] or result['data'] == ['mouse-over2']


def test_move_relative(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    if not web.find("mouse", matching=0.97, waiting_time=10_000, x=20, y=30, width=310, height=170):
        raise Exception('Image not found: mouse')
    web.move()
    web.move_relative(16, 140)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['mouse-over2']


def test_move_random(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    web.move_random(200, 200)

    mouse_x = int(web.find_element('mouse-x-pos', By.ID).text)
    mouse_y = int(web.find_element('mouse-y-pos', By.ID).text)
    assert mouse_x <= 200 and mouse_y <= 200


def test_mouse_down(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('git', os.path.join(conftest.PROJECT_DIR, 'resources', 'git.png'))
    if not web.find("git", matching=0.97, waiting_time=10000):
        raise Exception('Image not found: git')
    web.move()

    web.mouse_down(wait_after=1000)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left-Hold']


def test_mouse_up(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('git', os.path.join(conftest.PROJECT_DIR, 'resources', 'git.png'))
    if not web.find("git", matching=0.97, waiting_time=10000):
        raise Exception('Image not found: git')
    web.move()

    web.mouse_down(wait_after=1000)
    web.mouse_up(wait_after=1000)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left-Release']


def test_click_on(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    web.click_on(label='mouse')

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left'] or result['data'] == ['Left2']


def test_get_element_coors(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    (x, y) = web.get_element_coords(label='mouse')
    web.click_at(x, y)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left'] or result['data'] == ['Left2']


def test_get_element_coors_centered(web: WebBot):
    web.browse(conftest.INDEX_PAGE)

    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    (x, y) = web.get_element_coords_centered(label='mouse')
    web.click_at(x, y)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left'] or result['data'] == ['Left2']
