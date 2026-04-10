from glitch.__main__ import lint
from click.testing import CliRunner
from tests.base_test import BaseTest


class BaseSecurityTest(BaseTest):
    TECH = None  # subclass must override

    def _help_test(
        self, path: str, type: str, n_errors: int, codes: list[str], lines: list[int]
    ) -> None:
        assert self.TECH is not None, "Subclasses must define TECH"

        output_path = "tests/security/dump.csv"
        runner = CliRunner()
        result = runner.invoke(
            lint,
            [
                "--tech",
                self.TECH.value[0],
                "--type",
                type,
                "--csv",
                "--smell-types",
                "security",
                path,
                output_path,
            ],
        )
        if result.exception:
            raise result.exception

        errors = self.read_lint_csv(output_path)

        errors = [e for e in errors if e["code"].startswith("sec_")]  # type: ignore

        errors = sorted(
            errors, key=lambda e: (e["path"] or "", e["line"], e["code"] or "")
        )
        self.assertEqual(len(errors), n_errors)
        for i in range(n_errors):
            self.assertEqual(errors[i]["code"], codes[i])
            self.assertEqual(errors[i]["line"], lines[i])
