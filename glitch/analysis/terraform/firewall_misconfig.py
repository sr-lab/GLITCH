from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformFirewallMisconfig(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.FIREWALL_CONFIGS:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and config["values"] != [""]
            ):
                if (
                    "any_not_empty" in config["values"]
                    and isinstance(attribute.value, str)
                    and attribute.value.lower() == ""
                ):
                    return [
                        Error(
                            "sec_firewall_misconfig", attribute, file, repr(attribute)
                        )
                    ]
                elif (
                    "any_not_empty" not in config["values"]
                    and not attribute.has_variable
                    and isinstance(attribute.value, str)
                    and attribute.value.lower() not in config["values"]
                ):
                    return [
                        Error(
                            "sec_firewall_misconfig", attribute, file, repr(attribute)
                        )
                    ]
        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor.FIREWALL_CONFIGS:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_firewall_misconfig",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
