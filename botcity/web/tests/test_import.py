def test_package_import():
    import botcity.web as web
    assert web.__file__ != ""
