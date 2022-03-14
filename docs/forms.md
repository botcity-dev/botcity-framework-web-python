# Interacting with Forms

When dealing with forms, we often need to fill in the form and submit it.

While most of the operations are trivial, there are some things that are not such as selecting a select element or dealing with file uploads.

For that we developed some utilitary functions that you can use.

## Select Element

After grabing the element via the `find_element` or `find_elements` functions, we can use the `element_as_select` to convert it into a `Select` object.

::: botcity.web.util.element_as_select

### Example usage

```python
# Import the function
from botcity.web.util import element_as_select
...
# Fetch the select element
element = self.find_element("select", By.TAG_NAME)
# Convert the element into a Select object
select_element = element_as_select(element)
# Select the option based on visible text
select_element.select_by_visible_text("Option 1")
...
```

## File Upload

After grabing the element via the `find_element` or `find_elements` functions, we can use the `set_file_input_element` to assign the file path to the element.

### Example usage

```python
from botcity.web import By
...
# Find the input element of type `file` using CSS_SELECTOR.
elem = self.find_element("body > form > input[type=file]", By.CSS_SELECTOR)
# Configure the file to be used when processing the upload
self.set_file_input_element(elem, "./test.txt")
...
```
