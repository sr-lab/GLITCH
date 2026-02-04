import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.checkers.var_checker import VariableChecker
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue, Hash, String, UnitBlock


class TerraformNaming(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        if attribute.name == "name" and atomic_unit.type in [
            "azurerm_storage_account"
        ]:
            pattern = r"^[a-z0-9]{3,24}$"
            if isinstance(attribute.value, String) and not re.match(
                pattern, attribute.value.value
            ):
                return [Error("sec_naming", attribute, file, repr(attribute))]

        for config in SecurityVisitor.NAMING:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and self._parent_matches(parent_name, config["parents"])
                and config["values"] != []
                and isinstance(attribute.value, String)
            ):
                if "any_not_empty" in config["values"] and attribute.value.value == "":
                    return [Error("sec_naming", attribute, file, repr(attribute))]
                elif (
                    "any_not_empty" not in config["values"]
                    and not VariableChecker().check(attribute.value)
                    and attribute.value.value.lower() not in config["values"]
                ):
                    return [Error("sec_naming", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "aws_security_group":
                ingress = self.check_required_attribute(element, [], "ingress")
                egress = self.check_required_attribute(element, [], "egress")
                if isinstance(ingress, UnitBlock) and not self.check_required_attribute(
                    ingress, [], "description"
                ):
                    errors.append(
                        Error(
                            "sec_naming",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name 'ingress.description'.",
                        )
                    )
                if isinstance(egress, UnitBlock) and not self.check_required_attribute(
                    egress, [], "description"
                ):
                    errors.append(
                        Error(
                            "sec_naming",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name 'egress.description'.",
                        )
                    )
            elif element.type == "google_container_cluster":
                resource_labels = self.check_required_attribute(
                    element, [], "resource_labels", None
                )
                if isinstance(resource_labels, Attribute):
                    if isinstance(resource_labels.value, Hash) and len(resource_labels.value.value) == 0:
                        errors.append(
                            Error(
                                "sec_naming",
                                resource_labels,
                                file,
                                repr(resource_labels),
                                f"Suggestion: check empty 'resource_labels'.",
                            )
                        )
                elif resource_labels is None:
                    errors.append(
                        Error(
                            "sec_naming",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name 'resource_labels'.",
                        )
                    )

            for config in SecurityVisitor.NAMING:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_naming",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config.get('msg', config['attribute'])}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
