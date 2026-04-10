import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.checkers.var_checker import VariableChecker
from glitch.analysis.checkers.string_checker import StringChecker
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue, String


class TerraformPermissionIAMPolicies(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        if (
            attribute.name == "member" or attribute.name.split("[")[0] == "members"
        ) and atomic_unit.type in SecurityVisitor.GOOGLE_IAM_MEMBER:
            iam_checker = StringChecker(
                lambda x: bool(
                    re.search(r".-compute@developer.gserviceaccount.com", x)
                    or re.search(r".@appspot.gserviceaccount.com", x)
                    or re.search(r"user:", x)
                )
            )
            if iam_checker.check(attribute.value):
                return [
                    Error(
                        "sec_permission_iam_policies", attribute, file, repr(attribute)
                    )
                ]

        for config in SecurityVisitor.PERMISSION_IAM_POLICIES:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and self._parent_matches(parent_name, config["parents"])
                and config["values"] != [""]
            ):
                if config["logic"] == "equal":
                    checker = StringChecker(
                        lambda x, c=config: x.lower() not in c["values"]
                    )
                    if not VariableChecker().check(attribute.value) and checker.check(
                        attribute.value
                    ):
                        return [
                            Error(
                                "sec_permission_iam_policies",
                                attribute,
                                file,
                                repr(attribute),
                            )
                        ]
                elif config["logic"] == "diff":
                    checker = StringChecker(
                        lambda x, c=config: x.lower() in c["values"]
                    )
                    if checker.check(attribute.value):
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
            if element.type == "aws_iam_user":
                name = (
                    element.name.value
                    if isinstance(element.name, String)
                    else element.name
                )
                expr = f"aws_iam_user\\.{name}\\."
                pattern = re.compile(expr)
                assoc_au = self.get_associated_au(
                    file, "aws_iam_user_policy", "user", pattern, []
                )
                if assoc_au is not None:
                    a = self.check_required_attribute(
                        assoc_au, [], "user", None, pattern
                    )
                    errors.append(
                        Error("sec_permission_iam_policies", a, file, repr(a))
                    )

            errors += self._check_attributes(element, file)

        return errors
