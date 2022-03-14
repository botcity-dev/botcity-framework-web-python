# Handling Data

## Tables

To extract data from tables we offer an utility function which parses the table and returns a list of dictionaries.

::: botcity.web.parsers.table_to_dict

### Usage Example

Let's fetch data from the example table available at the [W3Schools website](https://www.w3schools.com/html/html_tables.asp).


```python
class Bot(WebBot):
    def action(self, execution=None):
        self.browse("https://www.w3schools.com/html/html_tables.asp")

        # Fetch the table
        table = self.find_element("table", By.TAG_NAME)

        # Parse the table
        parsed_table = table_to_dict(table)

        # Print the parsed table
        print(parsed_table)

        # Close the browser and free resources
        self.stop_browser()
```

The output should look like this:

```python
[
    {
        'company': 'Alfreds Futterkiste',
        'contact': 'Maria Anders',
        'country': 'Germany'
    },
    {
        'company': 'Centro comercial Moctezuma',
        'contact': 'Francisco Chang',
        'country': 'Mexico'
    },
    {
        'company': 'Ernst Handel',
        'contact': 'Roland Mendel',
        'country': 'Austria'
    },
    {
        'company': 'Island Trading',
        'contact': 'Helen Bennett',
        'country': 'UK'
    },
    {
        'company': 'Laughing Bacchus Winecellars',
        'contact': 'Yoshi Tannamuri',
        'country': 'Canada'
    },
    {
        'company': 'Magazzini Alimentari Riuniti',
        'contact': 'Giovanni Rovelli',
        'country': 'Italy'
    }
]
```