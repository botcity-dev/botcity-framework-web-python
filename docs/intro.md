# Getting Started

## Supported Browsers

This framework leverages the [WebDriver API](https://www.w3.org/TR/webdriver/) in order to communicate
with browsers for Automation.

In doing so, it requires that the WebDriver for the chosen browser to be installed and available preferrably
in your `PATH`. If you can't add the necessary WebDriver to your `PATH` you will be able to inform the `driver path`
via code in your bot.

Here is a list of supported browsers along with links for you to download the proper WebDriver:

| Browser | WebDriver Download                                                             |
|---------|--------------------------------------------------------------------------------|
| Chrome  | [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads) |
| Firefox | [GeckoDriver](https://github.com/mozilla/geckodriver/releases)                 |

Please follow the instructions on the WebDriver website for installation and setup.

Once the desired WebDriver for the Web Browser to be used is installed we can proceed to the next steps.

## WebBot

After you installed this package, the next step is to  import the package into your code and start using the
WebBot class to build your RPA pipeline.

```python
from botcity.web import *
```

### Template Project

We created a template project using Cookiecutter to help you create new bots using BotCity's Python Framework.

Take a look into the [template project website](https://github.com/botcity-dev/bot-python-template) for more information
on how to use it and get started.

### Customizing the Browser

To provide flexibility we have properties to allow you to configure which browser to use, the WebDriver
location as well as the options used when launching the browser.

Over the next steps we will over the possible customizations in detail.

#### Selecting the Browser

The `WebBot` class by default comes configured to run with `Google Chrome`. You can select any other
available browser by setting the `browser` property to one of the `Browser` *enum* available values.

Here is an example on how to change the default browser to be used:

```python
from botcity.web import WebBot, Browser


class Bot(WebBot):
    def action(self, execution=None):
        # Configure whether or not to run on headless mode
        self.headless = False

        # Changes the Browser to Firefox
        self.browser = Browser.FIREFOX
        
        # For Chrome
        # self.browser = Browser.CHROME
        
        ...
```

From the snippet above the key takeaway is the `self.browser` piece in which we set it to one of the values 
from the `Browser` *enum* as mentioned before.

#### Defining the WebDriver Path

If your WebDriver for the selected browser is not available on the system `PATH` you can inform the location
via the `driver_path` property.

Here is how that can be done:
```python
from botcity.web import WebBot, Browser


class Bot(WebBot):
    def action(self, execution=None):
        # Configure whether or not to run on headless mode
        self.headless = False

        # Inform the WebDriver path for Google Chrome's chromedriver
        self.driver_path = "/home/username/drivers/chromedriver"
        
        ...
```

#### Customizing Browser Options

By default the browsers are launched with a set of curated options which we picked as essential.

Before getting into how to customize those details let's walk through some of the assumptions and
details which are covered by the `default options`.

- **Headless Execution**: Depending on the `headless` property set on your Bot class we pick the 
proper configuration to launch the browser in the desired mode.
  
- **Downloads Folder Path**: By default we save all downloaded files on the Desktop folder.

- **User Profile**: By default we generate a temporary directory (which is later erased) to be used
  as the profile directory. This procedure ensure that every execution starts with a clean browser session
  and things such as cookies and stored passwords or certificates from one execution won't interfere with
  the others.
  
A handful of other options are also set and they can be inspected on the source code for each browser on the 
`botcity.web.browsers` module.

If you really need to customize the options you can do so via the `options` property. You can fetch 
the `default options` curated by BotCity and make your changes or start your options from scratch.

In the following snippet we will cover how to build on top of the existing options.

```python
from botcity.web import WebBot, Browser

# For Chrome
from botcity.web.browsers.chrome import default_options
# For Firefox
#from botcity.web.browsers.firefox import default_options

class Bot(WebBot):
    def action(self, execution=None):
        # Configure whether or not to run on headless mode
        self.headless = False

        # Fetch the default options for my preferred browser
        # Pass in the headless, download_folder_path and user_data_dir
        # to be used when building the default_options
        def_options = default_options(
            headless=self.headless,
            download_folder_path=self.download_folder_path,
            user_data_dir=None  # Informing None here will generate a temporary directory
        )
        
        # Add your customized argument
        def_options.add_argument("<My Special Argument>")
        
        # Update the options to use the customized Options.
        self.options = def_options
        
        ...
```

Every supported browser will have an exclusive module with curated default options accessible via the module's
`default_options` function.

This function takes in arguments to define the mode of execution (headless or not), default download folder path
and user data/profile directory.

### Next Steps

Check our examples and experiment with the API.
Let us know where it can be improved.

Have fun automating!