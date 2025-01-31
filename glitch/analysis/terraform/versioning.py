from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, KeyValue, CodeElement
from glitch.analysis.expr_checkers.var_checker import VariableChecker
from glitch.analysis.expr_checkers.string_checker import StringChecker


class TerraformVersioning(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        var_checker = VariableChecker()
        for config in SecurityVisitor.VERSIONING:
            string_checker = StringChecker(lambda x: x.lower() not in config["values"])
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and config["values"] != [""]
                and not var_checker.check(attribute.value)
                and isinstance(attribute.value, str)
                and string_checker.check(attribute.value)
            ):
                return [Error("sec_versioning", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor.VERSIONING:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and self.check_required_attribute(
                        element, config["parents"], config["attribute"]
                    )
                    is None
                ):
                    errors.append(
                        Error(
                            "sec_versioning",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
