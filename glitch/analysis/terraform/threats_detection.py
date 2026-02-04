from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.checkers.var_checker import VariableChecker
from glitch.repr.inter import AtomicUnit, Attribute, KeyValue, CodeElement, Array, String, Boolean


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
                and self._parent_matches(parent_name, config["parents"])
                and config["values"] != []
            ):
                value_str = None
                if isinstance(attribute.value, String):
                    value_str = attribute.value.value.lower()
                elif isinstance(attribute.value, Boolean):
                    value_str = "true" if attribute.value.value else "false"
                
                if (
                    "any_not_empty" in config["values"]
                    and value_str is not None
                    and value_str == ""
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
                    and value_str is not None
                    and not VariableChecker().check(attribute.value)
                    and value_str not in config["values"]
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
                ):
                    attr_name = config["attribute"]
                    is_missing = False
                    if attr_name.endswith("[0]"):
                        base_attr_name = attr_name[:-3]
                        a = self.check_required_attribute(
                            element, config["parents"], base_attr_name
                        )
                        if a is None or not isinstance(a, Attribute) or not isinstance(a.value, Array) or len(a.value.value) == 0:
                            is_missing = True
                    else:
                        if not self.check_required_attribute(
                            element, config["parents"], attr_name
                        ):
                            is_missing = True
                    
                    if is_missing:
                        msg = config.get("msg", attr_name)
                        errors.append(
                            Error(
                                "sec_threats_detection_alerts",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name '{msg}'.",
                            )
                        )
                elif (
                    config["required"] == "must_not_exist"
                    and element.type in config["au_type"]
                ):
                    attr_name = config["attribute"]
                    if attr_name.endswith("[0]"):
                        base_attr_name = attr_name[:-3]
                        a = self.check_required_attribute(
                            element, config["parents"], base_attr_name
                        )
                        if a is not None and isinstance(a, Attribute) and isinstance(a.value, Array) and len(a.value.value) > 0:
                            errors.append(
                                Error("sec_threats_detection_alerts", a, file, repr(a))
                            )
                    else:
                        a = self.check_required_attribute(
                            element, config["parents"], attr_name
                        )
                        if a is not None:
                            errors.append(
                                Error("sec_threats_detection_alerts", a, file, repr(a))
                            )

            errors += self._check_attributes(element, file)

        return errors
