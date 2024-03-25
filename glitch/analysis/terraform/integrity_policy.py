from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformIntegrityPolicy(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for policy in SecurityVisitor.INTEGRITY_POLICY:
            if (
                attribute.name == policy["attribute"]
                and atomic_unit.type in policy["au_type"]
                and parent_name in policy["parents"]
                and not attribute.has_variable
                and isinstance(attribute.value, str)
                and attribute.value.lower() not in policy["values"]
            ):
                return [Error("sec_integrity_policy", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            for policy in SecurityVisitor.INTEGRITY_POLICY:
                if (
                    policy["required"] == "yes"
                    and element.type in policy["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, policy["parents"], policy["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_integrity_policy",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{policy['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
