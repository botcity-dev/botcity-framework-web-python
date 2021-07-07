# Framework

The `botcity.web` module contains specialized implementations aimed at Desktop automation
such as `WebBot` which is described below.

You are expected to implement the `action` method of the `DesktopBot` class in
your Bot class.

Here is a very brief example of a bot which opens the BotCity website:

```python
from botcity.web import WebBot


class Bot(WebBot):
    def action(self, execution):
        # Configure whether or not to run on headless mode
        self.headless = False

        # Opens the BotCity website.
        self.browse("https://botcity.dev/en")

        # Stop the browser and clean up
        self.stop_browser()


if __name__ == '__main__':
    Bot.main()
```

::: botcity.web.WebBot