# Fast Params

Support Rails style QueryParams and FormData for Starlette and FastAPI

## Install

```bash
pip install fast-params
```

## Usage


```python
from fast_params import ParamParser
from starlette.datastructures import MultiDict

def test_parse_simple():
    parser = ParamParser()
    params = MultiDict({
        "a": 1,
        "b": 2
    })
    expect = {
        "a": 1,
        "b": 2
    }
    assert parser(params) == expect

def test_array():
    parser = ParamParser()
    params = MultiDict([
        ("a", 1),
        ("b[]", 2),
        ("c[d]", 3),
        ("c[f]", 4),
        ("f[d][]", 5),
        ("f[d][]", 6),
    ])
    expect = {
        "a": 1,
        "b": [2],
        "c": {
            "d": 3,
            "f": 4
        },
        "f": {
            "d": [5, 6]
        }
    }
    assert parser(params) == expect
```
