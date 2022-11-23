import os
import conftest

from botcity.web import WebBot



def test_find_one(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.set_screen_resolution(3000, 2000)

    web.add_image('mario4', os.path.join(conftest.PROJECT_DIR, 'resources', 'mario4.png'))
    if not web.find("mario4", matching=0.97, waiting_time=20_000):
        raise Exception('Image not found: mario4')
    web.click()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['img04']


def test_find_all(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.set_screen_resolution(3000, 2000)

    web.add_image('mario5', os.path.join(conftest.PROJECT_DIR, 'resources', 'mario5.png'))
    marios = web.find_all("mario5", matching=0.97, waiting_time=20_000)

    for _ in marios:
        web.click()
        result = conftest.get_event_result('element-result', web)
        assert result['data'] in [['img05'], ['img06'], ['img07'], ['img08']]


def test_get_last_element(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.set_screen_resolution(3000, 2000)

    web.add_image('mario5', os.path.join(conftest.PROJECT_DIR, 'resources', 'mario5.png'))
    ele = web.find('mario5')

    assert ele is not None


def test_find_text(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.set_screen_resolution(3000, 2000)

    web.add_image('hello_world', os.path.join(conftest.PROJECT_DIR, 'resources', 'hello_world.png'))
    ele = web.find("hello_world", matching=0.97, waiting_time=20000)

    assert ele is not None


def test_find_multiple(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.set_screen_resolution(3000, 2000)

    web.add_image('mario3', os.path.join(conftest.PROJECT_DIR, 'resources', 'mario3.png'))
    web.add_image('mario4', os.path.join(conftest.PROJECT_DIR, 'resources', 'mario4.png'))
    images = web.find_multiple(labels=['mario3', 'mario4'])

    assert None not in (images['mario3'], images['mario4'])
