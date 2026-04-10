import unittest

import csv
import os
from typing import List, Dict, Union


class BaseTest(unittest.TestCase):
    TECH = None  # subclass must override

    def setUp(self) -> None:
        """Skip tests if this is the base class being run directly"""
        if self.TECH is None:
            self.skipTest("BaseTest is abstract and should not be run directly")

    def read_lint_csv(self, path: str) -> List[Dict[str, Union[str, int, None]]]:
        """Read the CSV created by lint and return errors as a list of dicts."""
        errors: List[Dict[str, Union[str, int, None]]] = []

        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV file not found: {path}")

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                errors.append(
                    {
                        "code": row.get("ERROR"),
                        "line": int(row.get("LINE", 0)),
                        "path": row.get("PATH"),
                    }
                )

        os.remove(path)
        return errors
