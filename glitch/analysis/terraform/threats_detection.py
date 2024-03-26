from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, KeyValue, CodeElement


class TerraformThreatsDetection(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.MISSING_THREATS_DETECTION_ALERTS:
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
                            "sec_threats_detection_alerts",
                            attribute,
                            file,
                            repr(attribute),
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
                            "sec_threats_detection_alerts",
                            attribute,
                            file,
                            repr(attribute),
                        )
                    ]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor.MISSING_THREATS_DETECTION_ALERTS:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_threats_detection_alerts",
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
                        errors.append(
                            Error("sec_threats_detection_alerts", a, file, repr(a))
                        )

            errors += self._check_attributes(element, file)

        return errors
