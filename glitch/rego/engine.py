from typing import Tuple
from glitch.analysis.rules import Error

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

    print(input)
    print(config)
    print(smell_types)
