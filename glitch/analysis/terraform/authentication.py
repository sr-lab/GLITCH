import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


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
                        if isinstance(attribute.value, str) and not re.search(
                            pattern, attribute.value
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
                and parent_name in config["parents"]
                and not attribute.has_variable
                and isinstance(attribute.value, str)
                and attribute.value.lower() not in config["values"]
                and config["values"] != [""]
            ):
                return [Error("sec_authentication", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, AtomicUnit):
            if element.type == "resource.google_sql_database_instance":
                errors += self.check_database_flags(
                    element,
                    file,
                    "sec_authentication",
                    "contained database authentication",
                    "off",
                )
            elif element.type == "resource.aws_iam_group":
                expr = "\\${aws_iam_group\\." + f"{element.name}\\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(
                    file, "resource.aws_iam_group_policy", "group", pattern, [""]
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
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_authentication",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
