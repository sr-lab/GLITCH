from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, KeyValue, CodeElement


class TerraformWeakPasswordKeyPolicy(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for policy in SecurityVisitor.PASSWORD_KEY_POLICY:
            if (
                attribute.name == policy["attribute"]
                and atomic_unit.type in policy["au_type"]
                and parent_name in policy["parents"]
                and policy["values"] != [""]
            ):
                if policy["logic"] == "equal":
                    if (
                        "any_not_empty" in policy["values"]
                        and isinstance(attribute.value, str)
                        and attribute.value.lower() == ""
                    ):
                        return [
                            Error(
                                "sec_weak_password_key_policy",
                                attribute,
                                file,
                                repr(attribute),
                            )
                        ]
                    elif (
                        "any_not_empty" not in policy["values"]
                        and not attribute.has_variable
                        and isinstance(attribute.value, str)
                        and attribute.value.lower() not in policy["values"]
                    ):
                        return [
                            Error(
                                "sec_weak_password_key_policy",
                                attribute,
                                file,
                                repr(attribute),
                            )
                        ]
                elif (
                    policy["logic"] == "gte"
                    and isinstance(attribute.value, str)
                    and not attribute.value.isnumeric()
                ) or (
                    policy["logic"] == "gte"
                    and isinstance(attribute.value, str)
                    and attribute.value.isnumeric()
                    and int(attribute.value) < int(policy["values"][0])
                ):
                    return [
                        Error(
                            "sec_weak_password_key_policy",
                            attribute,
                            file,
                            repr(attribute),
                        )
                    ]
                elif (
                    policy["logic"] == "lte"
                    and isinstance(attribute.value, str)
                    and not attribute.value.isnumeric()
                ) or (
                    policy["logic"] == "lte"
                    and isinstance(attribute.value, str)
                    and attribute.value.isnumeric()
                    and int(attribute.value) > int(policy["values"][0])
                ):
                    return [
                        Error(
                            "sec_weak_password_key_policy",
                            attribute,
                            file,
                            repr(attribute),
                        )
                    ]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            for policy in SecurityVisitor.PASSWORD_KEY_POLICY:
                if (
                    policy["required"] == "yes"
                    and element.type in policy["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, policy["parents"], policy["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_weak_password_key_policy",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{policy['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
