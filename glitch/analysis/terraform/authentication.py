import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.checkers.var_checker import VariableChecker
from glitch.repr.inter import (
    AtomicUnit,
    Attribute,
    CodeElement,
    KeyValue,
    String,
    Boolean,
)


class TerraformAuthentication(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for item in SecurityVisitor.POLICY_KEYWORDS:
            if item.lower() == attribute.name:
                for config in SecurityVisitor.POLICY_AUTHENTICATION:
                    if atomic_unit.type in config["au_type"]:
                        expr = (
                            config["keyword"].lower() + "\\s*" + config["value"].lower()
                        )
                        pattern = re.compile(rf"{expr}")
                        value_str = None
                        if isinstance(attribute.value, String):
                            value_str = attribute.value.value
                        if value_str is not None and not re.search(
                            pattern, value_str.lower()
                        ):
                            return [
                                Error(
                                    "sec_authentication",
                                    attribute,
                                    file,
                                    repr(attribute),
                                )
                            ]

        for config in SecurityVisitor.AUTHENTICATION:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and self._parent_matches(parent_name, config["parents"])
                and config["values"] != []
            ):
                value_str = None
                if isinstance(attribute.value, String):
                    value_str = attribute.value.value
                elif isinstance(attribute.value, Boolean):
                    value_str = "true" if attribute.value.value else "false"

                if (
                    value_str is not None
                    and not VariableChecker().check(attribute.value)
                    and value_str.lower() not in config["values"]
                ):
                    return [
                        Error("sec_authentication", attribute, file, repr(attribute))
                    ]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, AtomicUnit):
            if element.type == "google_sql_database_instance":
                errors += self.check_database_flags(
                    element,
                    file,
                    "sec_authentication",
                    "contained database authentication",
                    "off",
                )
            elif element.type == "aws_iam_group":
                name_str = (
                    element.name.value
                    if isinstance(element.name, String)
                    else str(element.name)
                )
                expr = "(\\$\\{)?aws_iam_group\\." + f"{name_str}\\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(
                    file, "aws_iam_group_policy", "group", pattern, []
                ):
                    errors.append(
                        Error(
                            "sec_authentication",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'aws_iam_group_policy' associated to an "
                            + f"'aws_iam_group' resource.",
                        )
                    )

            for config in SecurityVisitor.AUTHENTICATION:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and self.check_required_attribute(
                        element, config["parents"], config["attribute"]
                    )
                    is None
                ):
                    msg = config.get("msg")
                    if msg is None:
                        parents = config["parents"]
                        attr = config["attribute"]
                        msg = ".".join(parents + [attr]) if parents else attr
                    errors.append(
                        Error(
                            "sec_authentication",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{msg}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
