# implicitdict

This library primarily provides the `ImplicitDict` base class which enables the inheriting class to implicitly be treated like a `dict` with entries corresponding to the fields of the inheriting class.  Simple example:

```python
class MyData(ImplicitDict):
    foo: str
    bar: int = 0
    baz: Optional[float]

data: MyData = ImplicitDict.parse({'foo': 'asdf', 'bar': 1}, MyData)
assert json.dumps(data) == '{"foo": "asdf", "bar": 1}'
```

See [class documentation for `ImplicitDict`](https://github.com/interuss/implicitdict/blob/main/src/implicitdict/__init__.py) and [test_normal_usage.py](https://github.com/interuss/implicitdict/blob/main/tests/test_normal_usage.py) for more information.
