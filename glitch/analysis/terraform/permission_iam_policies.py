import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformPermissionIAMPolicies(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        if (
            (attribute.name == "member" or attribute.name.split("[")[0] == "members")
            and atomic_unit.type in SecurityVisitor.GOOGLE_IAM_MEMBER
            and isinstance(attribute.value, str)
            and (
                re.search(r".-compute@developer.gserviceaccount.com", attribute.value)
                or re.search(r".@appspot.gserviceaccount.com", attribute.value)
                or re.search(r"user:", attribute.value)
            )
        ):
            return [
                Error("sec_permission_iam_policies", attribute, file, repr(attribute))
            ]

        for config in SecurityVisitor.PERMISSION_IAM_POLICIES:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and config["values"] != [""]
            ):
                if (
                    config["logic"] == "equal"
                    and not attribute.has_variable
                    and isinstance(attribute.value, str)
                    and attribute.value.lower() not in config["values"]
                ) or (
                    config["logic"] == "diff"
                    and isinstance(attribute.value, str)
                    and attribute.value.lower() in config["values"]
                ):
                    return [
                        Error(
                            "sec_permission_iam_policies",
                            attribute,
                            file,
                            repr(attribute),
                        )
                    ]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "resource.aws_iam_user":
                expr = "\\${aws_iam_user\\." + f"{element.name}\\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(
                    file, "resource.aws_iam_user_policy", "user", pattern, [""]
                )
                if assoc_au is not None:
                    a = self.check_required_attribute(
                        assoc_au.attributes, [""], "user", None, pattern
                    )
                    errors.append(
                        Error("sec_permission_iam_policies", a, file, repr(a))
                    )

            errors += self._check_attributes(element, file)

        return errors
