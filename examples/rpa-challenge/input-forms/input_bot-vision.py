import os
import sys
import requests
import pandas
from botcity.web import WebBot, config, Browser

config.DEFAULT_SLEEP_AFTER_ACTION = 20


class Bot(WebBot):
    def action(self, execution=None):
        # Execute in non-headless mode
        self.headless = True

        # Download Input Spreadsheet
        r = requests.get("http://www.rpachallenge.com/assets/downloadFiles/challenge.xlsx")

        if r.status_code != 200:
            sys.exit('Error fetching the challenge spreadsheet.')

        # Use Pandas to load the Excel Spreadsheet as a DataFrame:
        df = pandas.read_excel(r.content)
        df.dropna(axis='columns', inplace=True)

        df.columns = df.columns.str.strip()

        print('Started browser')
        # Navigate to the website
        self.browse("http://www.rpachallenge.com/")
        print('Finished loading...')

        # Find and click into the Start button
        print('Find Start')
        ele = self.find("start")
        print('Click Start')
        self.click()

        for index, row in df.iterrows():
            print('Processing row: ', index+1)
            # Click into main area of the page
            self.control_a()
            self.control_c()
            content = self.get_clipboard()

            self.click_at(400, 250)
            field_order = [x for x in content[content.rfind('ROUND') + 7:].split(os.linesep) if x in df.columns]

            for f in field_order:
                self.tab()
                value = row[f]
                self.kb_type(str(value))

            self.enter()

        self.control_a()
        self.control_c()
        data = self.get_clipboard()
        self.stop_browser()

        print("#" * 80)
        print("# RPA Challenge Result:")
        print("#" * 80)
        print(data[data.rfind("Your success"):])


if __name__ == '__main__':
    Bot.main()
