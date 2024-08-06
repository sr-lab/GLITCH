from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformPublicIp(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.PUBLIC_IP_CONFIGS:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and not attribute.has_variable
                and attribute.value is not None
                and attribute.value.lower() not in config["values"]
                and config["values"] != [""]
            ):
                return [Error("sec_public_ip", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor.PUBLIC_IP_CONFIGS:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_public_ip",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )
                elif (
                    config["required"] == "must_not_exist"
                    and element.type in config["au_type"]
                ):
                    a = self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                    if a is not None:
                        errors.append(Error("sec_public_ip", a, file, repr(a)))

            errors += self._check_attributes(element, file)

        return errors
