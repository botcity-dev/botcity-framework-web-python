import collections
import string
from typing import Dict, List, Optional
from selenium.webdriver.remote.webelement import WebElement


def data_from_row(row: WebElement, cell_tag="td", cell_xpath=None) -> List[str]:
    """Extract data from a row and return it as a list.

    Args:
        row (WebElement): The row element.
        cell_tag (str, optional): The HTML tag associated with the row cells. Defaults to "td".
        cell_xpath (str, optional): The XPath expression associated with the row cels. Defaults to None.
            If informed, overwrites the `cell_tag` definition.

    Returns:
        list: List of strings with the contents.
    """
    if cell_xpath:
        return [
            col.text for col in row.find_elements_by_xpath(cell_xpath)
        ]

    return [
        col.text for col in row.find_elements_by_tag_name(cell_tag)
    ]


def sanitize_header(labels: List[str]):
    """Sanitize header labels."""
    # Handle Treat Empty Header
    for idx, label in enumerate(labels):
        if label.strip():
            # make it lowercase
            label = label.lower()

            # remove punctuations
            label = ''.join([l for l in label if l not in string.punctuation])  # noqa: E741

            # replace spaces with underscores
            label = label.replace(" ", "_")
        else:
            label = f"col_{idx}"
        labels[idx] = label

    # Deduplicate by adding _1, _2, _3 to repeated labels
    counts = {k: v for k, v in collections.Counter(labels).items() if v > 1}
    for i in reversed(range(len(labels))):
        item = labels[i]
        if item in counts and counts[item]:
            labels[i] = f"{item}_{counts[item]}"
            counts[item] -= 1

    return labels


def table_to_dict(table: WebElement, has_header: bool = True,
                  skip_rows: int = 0, header_tag: str = "th",
                  cell_xpath: Optional[str] = None) -> List[Dict]:
    """Convert a table WebElement to a dict of lists.

    Args:
        table (WebElement): The table element.
        has_header (bool, optional): Whether or not to parse a header. Defaults to True.
        skip_rows (int, optional): Number of rows to skip from the top. Defaults to 0.
        header_tag (str, optional): The HTML tag associated with the header cell. Defaults to "th".
        cell_xpath (str, optional): Optional cell XPath selector for complex row constructions.
            If `cell_xpath` is not informed, the row data will come from `<td>` elements.

    Returns:
        list: List with dict for each row.
    """

    # Collect all rows from table
    rows = table.find_elements_by_tag_name("tr")

    # Skip rows if informed
    if skip_rows:
        rows = rows[skip_rows:]

    if cell_xpath and not cell_xpath.startswith('.'):
        # Convert into relative xpath
        cell_xpath = f'.{cell_xpath}'

    # Parse header labels
    if has_header:
        # Read header labels
        labels = data_from_row(rows[0], cell_tag=header_tag)
        # Sanitize headers
        labels = sanitize_header(labels)
        # Skip the header
        rows = rows[1:]
    else:
        # Make up header labels
        if cell_xpath:
            cols = rows[0].find_elements_by_xpath(cell_xpath)
        else:
            cols = rows[0].find_elements_by_tag_name("td")

        num_cols = len(cols)
        labels = [f"col_{i}" for i in range(num_cols)]

    # Assemble output dictionary
    out_list = []
    for row in rows:
        row_data = data_from_row(row, cell_xpath=cell_xpath)
        out_list.append(dict(zip(labels, row_data)))

    return out_list
