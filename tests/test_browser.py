import os
import pytest
import conftest

from PIL import Image, ImageFile
from botcity.web import WebBot, By
from pytest import xfail


def test_context(web: WebBot):
    with web:
        web.browse(conftest.INDEX_PAGE)
        assert web.driver
    assert web.driver is None


def test_create_tab(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    title = web.page_title()
    assert title == 'Botcity - web test'


def test_close_page(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.create_window(url=conftest.TEST_PAGE)
    web.close_page()

    title = web.page_title()
    assert title == 'Botcity - web test'


def test_create_window(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.create_window(url=conftest.TEST_PAGE)

    title = web.page_title()
    assert title == 'Page test'


def test_display_size(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.set_screen_resolution(1280, 720)
    (w, h) = web.display_size()

    assert w in [1280, 1264, 1223, 1256]


def test_javascript(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.execute_javascript("""
        document.getElementById('element-result').innerText = 'execute_javascript() works!';
    """)

    result = web.find_element('element-result', By.ID).text
    assert result == 'execute_javascript() works!'


def test_get_tabs(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.create_tab(conftest.TEST_PAGE)
    tabs = web.get_tabs()

    assert len(tabs) == 2


def test_navigate_to(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.navigate_to(url=conftest.TEST_PAGE)

    title = web.page_title()
    assert title == 'Page test'


def test_start_browser(web: WebBot):
    web.start_browser()
    tabs = web.get_tabs()

    assert len(tabs) == 1


def test_activate_tab(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.create_tab(conftest.TEST_PAGE)
    tabs = web.get_tabs()
    web.activate_tab(tabs[0])

    assert web.page_title() == 'Botcity - web test'


def test_get_image_from_map(web: WebBot):
    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    img = web.get_image_from_map('mouse')

    assert isinstance(img, ImageFile.ImageFile)


def test_get_js_dialog(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.type_keys([web.KEYS.SHIFT, 'p'])

    alert = web.get_js_dialog()
    alert_text = alert.text
    alert.accept()  # alert must be closed before stop browser

    assert alert_text == 'Alert test'


def test_handle_js_dialog(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.type_keys([web.KEYS.SHIFT, 'l'])
    web.handle_js_dialog(prompt_text='Test input text')

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Test input text']


def test_get_screen_image(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    img = web.get_screen_image(region=(0, 0, 400, 200))

    assert isinstance(img, Image.Image)


def test_get_screenshot(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    fp = os.path.join(conftest.PROJECT_DIR, 'resources', 'screenshot_test.png')
    img = web.get_screenshot(fp)

    assert isinstance(img, Image.Image) and os.path.isfile(fp)
    os.remove(fp)


def test_screen_cut(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    fp = os.path.join(conftest.PROJECT_DIR, 'resources', 'screen_cut_test.png')
    img = web.screen_cut(0, 0, 100, 200)
    img.save(fp)

    assert isinstance(img, Image.Image) and os.path.isfile(fp)
    os.remove(fp)


def test_find_element(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    element = web.find_element('botcity', By.ID)

    assert element.text == 'Botcity'


def test_find_elements(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    elements = web.find_elements('botcity', By.ID)

    assert [element.text for element in elements] == ['Botcity']


def test_maximize_window(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.maximize_window()

    is_maximized = web.find_element('is-maximized', By.ID)
    assert is_maximized


def test_page_source(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    page = web.page_source()

    assert page.title.text == 'Botcity - web test'


def test_set_file_input_element(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    input_file_element = web.find_element('file', By.ID)

    pdf_file = os.path.join(conftest.PROJECT_DIR, 'resources', 'sample.pdf')
    web.set_file_input_element(input_file_element, pdf_file)

    file_name = input_file_element.get_attribute('value')
    assert file_name == 'C:\\fakepath\\sample.pdf'


def test_enter_iframe(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    iframe = web.find_element('pgtest', By.ID)
    web.enter_iframe(iframe)

    bs = web.page_source()
    assert bs.title.text == 'Page test'


def test_leave_iframe(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    iframe = web.find_element('pgtest', By.ID)
    web.enter_iframe(iframe)
    web.leave_iframe()

    bs = web.page_source()
    assert bs.title.text == 'Botcity - web test'


def test_get_view_port_size(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    size = web.get_viewport_size()

    element = web.find_element('window-size', By.ID).text.split('x')
    assert size == tuple(int(e) for e in element)


def test_scroll_down(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.add_image('python', os.path.join(conftest.PROJECT_DIR, 'resources', 'python.png'))
    web.scroll_down(20)

    python_icon = web.find("python", matching=0.97, waiting_time=10000)
    assert python_icon is not None


def test_scroll_up(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    web.type_keys([web.KEYS.SHIFT, 'd'])  # scroll down trigger
    web.scroll_up(20)

    mouse_icon = web.find("mouse", matching=0.97, waiting_time=10000)
    assert mouse_icon is not None


@pytest.mark.xfail
def test_set_screen_resolution(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.set_screen_resolution(500, 500)

    page_size = web.find_element('page-size', By.ID).text
    width = page_size.split('x')[0]
    assert width in ['500', '476']


def test_wait_for_downloads(web: WebBot):
    if web.browser.lower() in 'edge' and os.getenv('CI') is not None:
        xfail(reason=f"Edge is not working properly for some tests in CI")

    fake_bin_path = conftest.get_fake_bin_path(web=web)

    web.browse(conftest.INDEX_PAGE)

    web.type_keys([web.KEYS.SHIFT, 'q'])

    web.wait_for_downloads(timeout=60000)
    web.wait(3000)
    assert os.path.exists(fake_bin_path) and os.path.getsize(fake_bin_path) > 0


def test_wait_for_file(web: WebBot):
    if web.browser.lower() in 'edge' and os.getenv('CI') is not None:
        xfail(reason=f"Edge is not working properly for some tests in CI")

    fake_bin_path = conftest.get_fake_bin_path(web=web)

    web.browse(conftest.INDEX_PAGE)

    web.type_keys([web.KEYS.SHIFT, 'q'])

    web.wait_for_file(fake_bin_path, timeout=30000)
    assert os.path.exists(fake_bin_path) and os.path.getsize(fake_bin_path) > 0


def test_set_current_element(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.add_image('mouse', os.path.join(conftest.PROJECT_DIR, 'resources', 'mouse.png'))
    web.add_image('git', os.path.join(conftest.PROJECT_DIR, 'resources', 'git.png'))

    mouse_element = web.find("mouse", matching=0.97, waiting_time=10_000)

    if not web.find("git", matching=0.97, waiting_time=10000):
        raise Exception('Image not found: git')
    web.click(wait_after=2000)

    web.set_current_element(mouse_element)
    web.click(wait_after=2000)

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Left2'] or result['data'] == ['Left']


def test_print_pdf(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    pdf = web.print_pdf(path=os.path.join(conftest.PROJECT_DIR, 'page.pdf'))

    assert os.path.exists(pdf)
    os.remove(pdf)
