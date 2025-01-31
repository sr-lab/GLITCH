import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.expr_checkers.string_checker import StringChecker
from glitch.repr.inter import *


class TerraformAccessControl(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for item in SecurityVisitor.POLICY_KEYWORDS:
            if item.lower() == attribute.name:
                for config in SecurityVisitor.POLICY_ACCESS_CONTROL:
                    expr = config["keyword"].lower() + "\\s*" + config["value"].lower()
                    pattern = re.compile(rf"{expr}")
                    allow_expr = '"effect":' + "\\s*" + '"allow"'
                    allow_pattern = re.compile(rf"{allow_expr}")

                    pattern_checker = StringChecker(
                        lambda x: re.search(pattern, x.lower()) is not None
                    )
                    allow_checker = StringChecker(
                        lambda x: re.search(allow_pattern, x.lower()) is not None
                    )

                    if pattern_checker.check(attribute.value) and allow_checker.check(
                        attribute.value
                    ):
                        return [
                            Error(
                                "sec_access_control", attribute, file, repr(attribute)
                            )
                        ]

        star_checker = StringChecker(lambda x: x == "*")
        if (
            attribute.name == "actions"
            and parent_name == "permissions"
            and atomic_unit.type == "azurerm_role_definition"
            and star_checker.check(attribute.value)
        ):
            return [Error("sec_access_control", attribute, file, repr(attribute))]
        elif (
            (
                re.search(r"members\[\d+\]", attribute.name)
                and atomic_unit.type == "google_storage_bucket_iam_binding"
            )
            or (
                attribute.name == "member"
                and atomic_unit.type == "google_storage_bucket_iam_member"
            )
        ) and (
            attribute.value == "allusers" or attribute.value == "allauthenticatedusers"
        ):
            return [Error("sec_access_control", attribute, file, repr(attribute))]
        elif (
            attribute.name == "email"
            and parent_name == "service_account"
            and atomic_unit.type == "google_compute_instance"
            and isinstance(attribute.value, str)
            and re.search(r".-compute@developer.gserviceaccount.com", attribute.value)
        ):
            return [Error("sec_access_control", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            get_checker = StringChecker(lambda x: x.lower() == "get")
            none_checker = StringChecker(lambda x: x.lower() == "none")

            if element.type == "aws_api_gateway_method":
                http_method = self.check_required_attribute(element, [], "http_method")
                authorization = self.check_required_attribute(
                    element, [], "authorization"
                )
                if (
                    isinstance(http_method, KeyValue)
                    and isinstance(authorization, KeyValue)
                    and http_method.value is not None
                    and authorization.value is not None
                ):
                    if get_checker.check(http_method.value) and none_checker.check(
                        authorization.value
                    ):
                        api_key_required = self.check_required_attribute(
                            element, [], "api_key_required"
                        )
                        if (
                            isinstance(api_key_required, KeyValue)
                            and api_key_required.value is not None
                            and f"{api_key_required.value}".lower() != "true"
                        ):
                            errors.append(
                                Error(
                                    "sec_access_control",
                                    api_key_required,
                                    file,
                                    repr(api_key_required),
                                )
                            )
                        elif not api_key_required:
                            errors.append(
                                Error(
                                    "sec_access_control",
                                    element,
                                    file,
                                    repr(element),
                                    f"Suggestion: check for a required attribute with name 'api_key_required'.",
                                )
                            )
                elif http_method and not authorization:
                    errors.append(
                        Error(
                            "sec_access_control",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name 'authorization'.",
                        )
                    )
            elif element.type == "github_repository":
                visibility = self.check_required_attribute(element, [], "visibility")
                if isinstance(visibility, KeyValue) and isinstance(
                    visibility.value, str
                ):
                    if visibility.value.lower() not in ["private", "internal"]:
                        errors.append(
                            Error(
                                "sec_access_control", visibility, file, repr(visibility)
                            )
                        )
                else:
                    private = self.check_required_attribute(element, [], "private")
                    if isinstance(private, KeyValue) and isinstance(private.value, str):
                        if f"{private.value}".lower() != "true":
                            errors.append(
                                Error(
                                    "sec_access_control", private, file, repr(private)
                                )
                            )
                    else:
                        errors.append(
                            Error(
                                "sec_access_control",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name 'visibility' or 'private'.",
                            )
                        )
            elif element.type == "google_sql_database_instance":
                errors += self.check_database_flags(
                    element,
                    file,
                    "sec_access_control",
                    "cross db ownership chaining",
                    "off",
                )
            # This does not work when the name is not a String :/
            elif element.type == "aws_s3_bucket" and isinstance(element.name, String):
                expr = "aws_s3_bucket\\." + f"{element.name.value}\\."
                pattern = re.compile(rf"{expr}")
                if (
                    self.get_associated_au(
                        file,
                        "aws_s3_bucket_public_access_block",
                        "bucket",
                        pattern,
                        [],
                    )
                    is None
                ):
                    errors.append(
                        Error(
                            "sec_access_control",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'aws_s3_bucket_public_access_block' "
                            + f"associated to an 'aws_s3_bucket' resource.",
                        )
                    )

            for config in SecurityVisitor.ACCESS_CONTROL_CONFIGS:
                values = [None]
                if len(config["values"]) > 0:
                    values = config["values"]

                required_attribute = self.check_required_attribute(
                    element,
                    config["parents"],
                    config["attribute"],
                )
                if (
                    element.type not in config["au_type"]
                    # If the attribute is not required and the attribute is not present, skip
                    # The default value is OK
                    or (required_attribute is None and config["required"] == "no")
                ):
                    continue

                satisfied = False
                for value in values:
                    if (
                        self.check_required_attribute(
                            element, config["parents"], config["attribute"], value=value
                        )
                        is not None
                    ):
                        satisfied = True

                if not satisfied:
                    if required_attribute is not None:
                        element_with_error = required_attribute
                    else:
                        element_with_error = element

                    full_name = ".".join(config["parents"] + [config["attribute"]])
                    value = ""
                    if len(values) > 0:
                        value = f" with value in {values}"

                    errors.append(
                        Error(
                            "sec_access_control",
                            element_with_error,
                            file,
                            repr(element_with_error),
                            f"Suggestion: check for a required attribute with name '{full_name}'{value}.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
