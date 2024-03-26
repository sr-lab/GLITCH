import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


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
                    if (
                        isinstance(attribute.value, str)
                        and re.search(pattern, attribute.value)
                        and re.search(allow_pattern, attribute.value)
                    ):
                        return [
                            Error(
                                "sec_access_control", attribute, file, repr(attribute)
                            )
                        ]

        if (
            re.search(r"actions\[\d+\]", attribute.name)
            and parent_name == "permissions"
            and atomic_unit.type == "resource.azurerm_role_definition"
            and attribute.value == "*"
        ):
            return [Error("sec_access_control", attribute, file, repr(attribute))]
        elif (
            (
                re.search(r"members\[\d+\]", attribute.name)
                and atomic_unit.type == "resource.google_storage_bucket_iam_binding"
            )
            or (
                attribute.name == "member"
                and atomic_unit.type == "resource.google_storage_bucket_iam_member"
            )
        ) and (
            attribute.value == "allusers" or attribute.value == "allauthenticatedusers"
        ):
            return [Error("sec_access_control", attribute, file, repr(attribute))]
        elif (
            attribute.name == "email"
            and parent_name == "service_account"
            and atomic_unit.type == "resource.google_compute_instance"
            and isinstance(attribute.value, str)
            and re.search(r".-compute@developer.gserviceaccount.com", attribute.value)
        ):
            return [Error("sec_access_control", attribute, file, repr(attribute))]

        for config in SecurityVisitor.ACCESS_CONTROL_CONFIGS:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and not attribute.has_variable
                and isinstance(attribute.value, str)
                and attribute.value.lower() not in config["values"]
                and config["values"] != [""]
            ):
                return [Error("sec_access_control", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "resource.aws_api_gateway_method":
                http_method = self.check_required_attribute(
                    element.attributes, [""], "http_method"
                )
                authorization = self.check_required_attribute(
                    element.attributes, [""], "authorization"
                )
                if (
                    isinstance(http_method, KeyValue)
                    and isinstance(authorization, KeyValue)
                    and http_method.value is not None
                    and authorization.value is not None
                ):
                    if (
                        http_method.value.lower() == "get"
                        and authorization.value.lower() == "none"
                    ):
                        api_key_required = self.check_required_attribute(
                            element.attributes, [""], "api_key_required"
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
            elif element.type == "resource.github_repository":
                visibility = self.check_required_attribute(
                    element.attributes, [""], "visibility"
                )
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
                    private = self.check_required_attribute(
                        element.attributes, [""], "private"
                    )
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
            elif element.type == "resource.google_sql_database_instance":
                errors += self.check_database_flags(
                    element,
                    file,
                    "sec_access_control",
                    "cross db ownership chaining",
                    "off",
                )
            elif element.type == "resource.aws_s3_bucket":
                expr = "\\${aws_s3_bucket\\." + f"{element.name}\\."
                pattern = re.compile(rf"{expr}")
                if (
                    self.get_associated_au(
                        file,
                        "resource.aws_s3_bucket_public_access_block",
                        "bucket",
                        pattern,
                        [""],
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
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_access_control",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
