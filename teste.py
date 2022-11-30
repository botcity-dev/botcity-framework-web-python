from botcity.web import WebBot, Browser, By

bot = WebBot()

# Firefox
# bot.driver_path = "/home/kayque/Downloads/geckodriver-v0.32.0-linux64/geckodriver"
# bot.browser = Browser.FIREFOX
# bot.headless = True

# Chrome
# bot.driver_path = "/home/kayque/Downloads/chromedriver_linux64(9)/chromedriver"
# bot.browser = Browser.CHROME
# bot.headless = True

# Edge
bot.driver_path = "/home/kayque/Downloads/edgedriver_linux64/msedgedriver"
bot.browser = Browser.EDGE
bot.headless = True

try:
    bot.start_browser()
    bot.browse("https://google.com")
    search = bot.find_element(selector="/html/body/div[1]/div[3]/form/div[1]/div[1]/div[1]/div/div[2]/input", by=By.XPATH)
    search.send_keys("cotação dolar")
    bot.enter()
    value = bot.find_element(selector="/html/body/div[7]/div/div[10]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div/div/div/div/div[3]/div[1]/div[1]/div[2]/span[1]",
                             by=By.XPATH)
    date = bot.find_element(selector="/html/body/div[7]/div/div[10]/div/div[2]/div[2]/div/div/div[1]/div/div/div/div/div/div/div/div[3]/div[1]/div[2]/span", by=By.XPATH)

    print(f"$ 1 = R$ {value.text}")
    print(f"Date: {date.text}")
except Exception as error:
    print(error)
finally:
    bot.stop_browser()
