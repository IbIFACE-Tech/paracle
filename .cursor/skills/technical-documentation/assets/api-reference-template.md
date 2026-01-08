# API Reference Template

## [Module Name]

Brief description of what this module does.

## Classes

### `ClassName`

Description of the class and its purpose.

**Parameters:**

- `param1` (`type`): Description of parameter 1
- `param2` (`type`, optional): Description of parameter 2. Defaults to `default_value`.

**Attributes:**

- `attribute1` (`type`): Description of attribute 1
- `attribute2` (`type`): Description of attribute 2

**Example:**

```python
instance = ClassName(param1="value", param2=42)
result = instance.method()
```

#### `method_name()`

Description of what this method does.

**Parameters:**

- `arg1` (`type`): Description
- `arg2` (`type`, optional): Description. Defaults to `None`.

**Returns:**

- `return_type`: Description of return value

**Raises:**

- `ExceptionType`: When this exception is raised

**Example:**

```python
result = instance.method_name(arg1="value")
print(result)
```

## Functions

### `function_name()`

```python
def function_name(param1: str, param2: int = 0) -> bool
```

Description of what this function does.

**Parameters:**

- `param1` (`str`): Description
- `param2` (`int`, optional): Description. Defaults to `0`.

**Returns:**

- `bool`: Description of return value

**Raises:**

- `ValueError`: When invalid input is provided

**Example:**

```python
result = function_name("test", param2=42)
```

## Constants

### `CONSTANT_NAME`

```python
CONSTANT_NAME = "value"
```

Description of this constant and when to use it.

## Exceptions

### `CustomException`

```python
class CustomException(Exception)
```

Raised when [condition].

**Example:**

```python
try:
    risky_operation()
except CustomException as e:
    print(f"Error: {e}")
```

## Type Aliases

### `TypeName`

```python
TypeName = Union[str, int]
```

Description of this type alias.

## See Also

- [Related Module](related-module.md)
- [Tutorial](../tutorials/tutorial-name.md)
- [External Docs](https://example.com/docs)
