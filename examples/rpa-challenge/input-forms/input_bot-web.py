import sys
import requests
import pandas
from botcity.web import WebBot, Browser


class Bot(WebBot):
    def action(self, execution=None):
        # Execute in non-headless mode
        self.headless = True

        # For Firefox
        self.browser = Browser.FIREFOX
        self.driver_path = "/Volumes/SlepickaHD/Users/slepicka/sandbox/git-botcity/toolbox/webdrivers/geckodriver"

        # For Chrome
        self.browser = Browser.CHROME
        self.driver_path = "/Volumes/SlepickaHD/Users/slepicka/sandbox/git-botcity/toolbox/webdrivers/chromedriver"

        # Download Input Spreadsheet
        r = requests.get("http://www.rpachallenge.com/assets/downloadFiles/challenge.xlsx")

        if r.status_code != 200:
            sys.exit('Error fetching the challenge spreadsheet.')

        # Use Pandas to load the Excel Spreadsheet as a DataFrame:
        df = pandas.read_excel(r.content)
        df.dropna(axis='columns', inplace=True)

        input_names = ["FirstName", "LastName", "CompanyName", "Role", "Address", "Email", "Phone"]

        commands = list()
        commands.append("$(\":button\")[0].click();")
        for index, row in df.iterrows():
            for lbl, col in zip(input_names, df.columns):
                entry_value = str(row[col])
                cmd = f"$(\"input[ng-reflect-name='label{lbl}']\" )[0].value = \"{entry_value}\";"
                commands.append(cmd)
            commands.append("$(\"input[type='submit']\")[0].click();")

        # Navigate to the website
        self.browse("http://www.rpachallenge.com/")
        self.execute_javascript("".join(commands))
        self.control_a()
        self.control_c()
        data = self.get_clipboard()
        self.stop_browser()
        print("#"*80)
        print("# RPA Challenge Result:")
        print("#" * 80)
        print(data[data.rfind("Your success"):])


if __name__ == '__main__':
    try:
        Bot.main()
    except Exception as ex:
        print('Ooops...', ex)
