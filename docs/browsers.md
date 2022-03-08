# Browsers

Every supported browser has a default set of options and capabilities curated for you that are used by default.

In case you need to customize the options or capabilities you can do so via the `default_options` and `default_capabilities` methods available within each browser module.

Here is an example on how to do that:

```python
from botcity.web import WebBot, Browser

# For Chrome
from botcity.web.browsers.chrome import default_options, default_capabilities
# For Firefox
#from botcity.web.browsers.firefox import default_options, default_capabilities
# For Edge
#from botcity.web.browsers.edge import default_options, default_capabilities
# For IE
#from botcity.web.browsers.ie import default_options, default_capabilities


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

        # Fetch the default options for my preferred browser
        def_capabilities = default_capabilities()

        # Set of modify the key and value for my desired capability
        def_capabilities["<My Special Parameter>"] = "special value"

        # Update the capabilities to use the customized configurations.
        self.capabilities = def_capabilities

        ...
```

## Specific Browser Modules

Here are the documentation for the methods mentioned above for each of the supported browsers.

### Chrome
::: botcity.web.browsers.chrome.default_options
    rendering:
      heading_level: 4

::: botcity.web.browsers.chrome.default_capabilities
    rendering:
      heading_level: 4

### Firefox
::: botcity.web.browsers.firefox.default_options
    rendering:
      heading_level: 4
::: botcity.web.browsers.firefox.default_capabilities
    rendering:
      heading_level: 4

### Edge
::: botcity.web.browsers.edge.default_options
    rendering:
      heading_level: 4
::: botcity.web.browsers.edge.default_capabilities
    rendering:
      heading_level: 4

### IE
::: botcity.web.browsers.ie.default_options
    rendering:
      heading_level: 4
::: botcity.web.browsers.ie.default_capabilities
    rendering:
      heading_level: 4

#### Important

If you have any questions about the driver see [IE Driver Server Documentation](https://www.selenium.dev/documentation/ie_driver_server/).

See the [list of supported arguments in IE](https://docs.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/general-info/hh826025(v=vs.85)).

During execution some errors may occur, [see the list of common errors](https://testguild.com/selenium-webdriver-fix-for-3-common-ie-errors/). 
