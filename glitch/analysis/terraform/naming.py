import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformNaming(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        if attribute.name == "name" and atomic_unit.type in [
            "resource.azurerm_storage_account"
        ]:
            pattern = r"^[a-z0-9]{3,24}$"
            if isinstance(attribute.value, str) and not re.match(
                pattern, attribute.value
            ):
                return [Error("sec_naming", attribute, file, repr(attribute))]

        for config in SecurityVisitor.NAMING:
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
                    return [Error("sec_naming", attribute, file, repr(attribute))]
                elif (
                    "any_not_empty" not in config["values"]
                    and not attribute.has_variable
                    and isinstance(attribute.value, str)
                    and attribute.value.lower() not in config["values"]
                ):
                    return [Error("sec_naming", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "resource.aws_security_group":
                ingress = self.check_required_attribute(
                    element.attributes, [""], "ingress"
                )
                egress = self.check_required_attribute(
                    element.attributes, [""], "egress"
                )
                if isinstance(ingress, KeyValue) and not self.check_required_attribute(
                    ingress.keyvalues, [""], "description"
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
                if isinstance(egress, KeyValue) and not self.check_required_attribute(
                    egress.keyvalues, [""], "description"
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
            elif element.type == "resource.google_container_cluster":
                resource_labels = self.check_required_attribute(
                    element.attributes, [""], "resource_labels", None
                )
                if (
                    isinstance(resource_labels, KeyValue)
                    and resource_labels.value is None
                ):
                    if resource_labels.keyvalues == []:
                        errors.append(
                            Error(
                                "sec_naming",
                                resource_labels,
                                file,
                                repr(resource_labels),
                                f"Suggestion: check empty 'resource_labels'.",
                            )
                        )
                else:
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
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_naming",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
