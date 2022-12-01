from selenium import webdriver

web_element = webdriver.remote.webelement.WebElement

remote_driver = webdriver.remote.webdriver.WebDriver


def find_by_id(self, _id):

    return self.find_element("id", _id)


web_element.find_element_by_id = find_by_id

remote_driver.find_element_by_id = find_by_id

driver = webdriver.Firefox(service=webdriver.firefox.service.Service(executable_path="/home/kayque/Downloads/geckodriver-v0.32.0-linux64/geckodriver"))

driver.get("https://www.google.com")

body = driver.find_element("tag name", "body")

test1 = body.find_element_by_id("gb")

test2 = driver.find_element_by_id("gb")

driver.quit()

from packaging import version

import selenium

se_version = version.parse(selenium.__version__)

needs_patch = se_version >= version.parse("4.0")