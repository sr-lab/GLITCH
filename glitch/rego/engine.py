import json
import os

from typing import Tuple
from glitch.rego.go.wrapper import run_rego

def run_analyses(
    input: str, 
    config: str,
    smell_types: Tuple[str, ...],
    regopy: bool = True
):
    print("Running analysis...")
    if regopy:
        print("Using Regopy for analysis...")
    else:
        print("Using Go analysis tools...")


    input_data = json.loads(input)

    data: dict[str, str] = {}
    if config and os.path.exists(config):
        with open(config) as f:
            data = json.load(f)

    rego_modules = load_rego_modules_from_folder("./glitch/rego/queries/security")

    result = run_rego(input_data, data, rego_modules)

    if "error" in result:
        print("Error:", result["error"])
    else:
        print(result)

def load_rego_modules_from_folder(folder_path: str) -> dict[str, str]:
    modules = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.rego'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as f:
                modules[filename] = f.read()
    return modules # type: ignore
