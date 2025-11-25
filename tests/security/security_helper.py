import unittest

from glitch.__main__ import lint
import csv
import os
from typing import List, Dict, Union
from click.testing import CliRunner

class BaseSecurityTest(unittest.TestCase):

    PARSER_CLASS = None   # subclass must override
    TECH = None           # subclass must override

    def setUp(self) -> None:
        """Skip tests if this is the base class being run directly"""
        if self.PARSER_CLASS is None or self.TECH is None:
            self.skipTest("BaseSecurityTest is abstract and should not be run directly")

    def read_lint_csv(self, path: str) -> List[Dict[str, Union[str, int, None]]]:
        """Read the CSV created by lint and return errors as a list of dicts."""
        errors: List[Dict[str, Union[str, int, None]]] = []

        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV file not found: {path}")

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                errors.append({
                    "code": row.get("CODE"),           
                    "line": int(row.get("LINE", 0)),   
                    "path": row.get("PATH")           
                })

        os.remove(path)
        return errors
    
    def _help_test(self, path: str, type: str, n_errors: int, codes: list[str], lines: list[int]) -> None:
        assert self.PARSER_CLASS is not None, "Subclasses must define PARSER_CLASS"
        assert self.TECH is not None, "Subclasses must define TECH"
        
        output_path = "glitch/tests/security/dump.csv"
        path = "glitch/" + path
        runner = CliRunner()
        result = runner.invoke(
            lint,
            [   
                "--tech", self.TECH.value[0],
                "--type", type,
                "--csv",
                "--smell-types", "security",
                path,
                output_path,
            ]
        )
        if result.exception:
            raise result.exception

        errors = self.read_lint_csv("glitch/tests/security/dump.csv")
        errors = [e for e in errors if e["code"].startswith("sec_")] # type: ignore

        errors = sorted(errors, key=lambda e: (e["path"] or "", e["line"], e["code"] or ""))
        print(errors)
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i]["code"], codes[i])
            self.assertEqual(errors[i]["line"], lines[i])
        