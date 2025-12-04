from glitch.__main__ import lint
from click.testing import CliRunner
from glitch.tech import Tech
from tests.base_test import BaseTest

class BaseDesignTest(BaseTest):
    TECH = None           # subclass must override

    def _help_test(self, path: str, type: str, config: str, n_errors: int, codes: list[str], lines: list[int]) -> None:
        assert self.TECH is not None, "Subclasses must define TECH"

        output_path = "tests/design/dump.csv"
        runner = CliRunner()
        result = runner.invoke(
            lint,
            [   
                "--tech", self.TECH.value[0],
                "--type", type,
                "--config", config,
                "--csv",
                "--smell-types", "design",
                path,
                output_path,
            ]
        )
        if result.exception:
            raise result.exception

        errors = self.read_lint_csv(output_path)
        
        errors = [e for e in errors if e["code"].startswith("design_") or e["code"].startswith("implementation_")] # type: ignore

        errors = sorted(errors, key=lambda e: (e["path"] or "", e["line"], e["code"] or ""))
        
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            if self.TECH == Tech.gha:
                self.assertEqual(errors[i]["path"], path)
            self.assertEqual(errors[i]["code"], codes[i])
            self.assertEqual(errors[i]["line"], lines[i])