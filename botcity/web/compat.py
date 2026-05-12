import warnings


def patch_selenium():
    if version_selenium_is_larger_than_four():
        from selenium.webdriver.remote.webelement import WebElement
        from selenium.webdriver.remote.webdriver import WebDriver

        web_element = WebElement

        remote_driver = WebDriver

        bys = ['id', 'class name', 'xpath', 'link text', 'partial link text', 'name', 'css selector', 'tag name']
        for by in bys:
            name = '_'.join(by.split(' '))
            find_element_by_function_name = f"find_element_by_{name}"
            find_elements_by_function_name = f"find_elements_by_{name}"
            setattr(web_element, find_element_by_function_name, find_element_by(by))
            setattr(web_element, find_elements_by_function_name, find_elements_by(by))
            setattr(remote_driver, find_element_by_function_name, find_element_by(by))
            setattr(remote_driver, find_elements_by_function_name, find_elements_by(by))


def find_element_by(by):
    def func(self, value):
        warnings.warn("This function is deprecated in version 4, please review the usage for find_element.",
                      category=DeprecationWarning, stacklevel=2)
        return self.find_element(by=by, value=value)
    return func


def find_elements_by(by):
    def func(self, value):
        warnings.warn("This function is deprecated in version 4, please review the usage for find_elements.",
                      category=DeprecationWarning, stacklevel=2)
        return self.find_elements(by=by, value=value)
    return func


def version_selenium_is_larger_than_four():
    import selenium
    from packaging import version
    se_version = version.parse(selenium.__version__)

    needs_patch = se_version >= version.parse("4.0")
    return needs_patch
