import conftest

from botcity.web import WebBot


def test_control_a(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.control_a()

    result = conftest.get_event_result('element-result', web)
    if conftest.OS_NAME == 'Darwin':
        assert result['data'] == ['Meta', 'a']
    else:
        assert result['data'] == ['Control', 'a']


def test_control_c(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.control_c()

    assert web.get_clipboard() == 'Botcity'


def test_enter(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.enter()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Enter']


def test_control_v(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.copy_to_clipboard(text='botcity-paste')
    web.control_v()

    result = conftest.get_event_result('element-result', web)
    assert ''.join(result['data']) == 'botcity-paste'


def test_delete(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.delete()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Delete']


def test_key_end(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.key_end()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['End']


def test_key_esc(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.key_esc()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Escape']


def test_key_home(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.key_home()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Home']


def test_type_keys(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.type_keys(['a', 'b', 'c'])

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['a', 'b', 'c']


def test_type_down(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.type_down()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['ArrowDown']


def test_type_left(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.type_left()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['ArrowLeft']


def test_type_right(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.type_right()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['ArrowRight']


def test_type_up(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.type_up()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['ArrowUp']


def test_backspace(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.backspace()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Backspace']


def test_hold_shift(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.hold_shift()
    web.kb_type('a')
    web.release_shift()
    web.kb_type('a')

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Shift', 'A', 'a']


def test_space(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.space()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Space']


def test_page_down(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.page_down()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['PageDown']


def test_page_up(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.page_up()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['PageUp']


def test_key_tab(web: WebBot):
    web.browse(conftest.INDEX_PAGE)
    web.tab()

    result = conftest.get_event_result('element-result', web)
    assert result['data'] == ['Tab']
