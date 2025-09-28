# rego_python

Python wrapper around a Go-based [OPA (Open Policy Agent)](https://www.openpolicyagent.org/) Rego library.  
This package provides a simple interface to evaluate Rego policies from Python without requiring users to build the Go library themselves. 

## Installation

```bash
pip install rego_python
```
## Supported Architectures
We currently ship precompiled binaries for the following platforms:
- Linux (x86_64)
<!-- - macOS (x86_64) -->
<!-- - Windows (x86_64) -->

## Usage

The main entrypoint is the function ```run_rego```, which executes Rego policies against given input and data.

```
from rego_python import run_rego

result = run_rego(
    input_data={"user": "alice"},
    data={"roles": {"alice": ["admin"]}},
    rego_modules={
        "policy.rego": """
        package example

        default allow = false

        allow {
            input.user == "alice"
            data.roles[input.user][_] == "admin"
        }
        """
    }
)

print(result)
```

## API Reference

```
run_rego(input_data: dict, data: dict, rego_modules: dict) -> dict
```

Executes a Rego policy using the underlying Go library and returns the evaluation result as a Python dictionary.

### Parameters:
- input_data (dict)
    Represents the input document passed to the Rego evaluation.
    Example:
    ```
    {"user": "alice"}
    ```

- data (dict)
    Represents contextual data available to the policy during evaluation.
    Example:
    ```
    {"roles": {"alice": ["admin"]}}
    ```

- rego_modules (dict)
    A mapping of file names to Rego source code strings. Each key is a filename and the value is the Rego policy source code.
    Example:
    ```
    {"policy.rego": "package example\nallow { input.user == \"alice\" }"}

    ```

### Returns:
- dict
    The evaluation result, parsed from the JSON response returned by the Go library.

## Source Code:
You can view the source code [on GitHub](https://github.com/infragov-project/GLITCH/tree/rego_integration/glitch/).




