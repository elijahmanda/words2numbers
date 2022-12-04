# wordswnumbers

words2numbers is a python library for extracting numbers from unstructured text.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install words2numbers
```

## Usage

```python
from words2numbers import words2numbers

print(words2numbers("I have six hundred and twenty six dollars"))
[('six hundred and twenty nine',
  629,
  {'number_type': 'number', 'span': (7, 34), 'value_type': 'integer'})]

```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

