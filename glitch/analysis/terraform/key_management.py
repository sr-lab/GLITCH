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


class TerraformKeyManagement(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.KEY_MANAGEMENT:
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
                    "any_not_empty" in config["values"]
                    and value_str is not None
                    and value_str.strip() == ""
                ):
                    return [
                        Error("sec_key_management", attribute, file, repr(attribute))
                    ]
                elif (
                    "any_not_empty" not in config["values"]
                    and value_str is not None
                    and not VariableChecker().check(attribute.value)
                    and value_str.lower() not in config["values"]
                ):
                    return [
                        Error("sec_key_management", attribute, file, repr(attribute))
                    ]

        if (
            attribute.name == "rotation_period"
            and atomic_unit.type == "google_kms_crypto_key"
        ):
            expr1 = r"\d+\.\d{0,9}s"
            expr2 = r"\d+s"
            value_str = (
                attribute.value.value if isinstance(attribute.value, String) else None
            )
            if value_str is not None and (
                re.search(expr1, value_str) or re.search(expr2, value_str)
            ):
                if int(value_str.split("s")[0].split(".")[0]) > 7776000:
                    return [
                        Error("sec_key_management", attribute, file, repr(attribute))
                    ]
            else:
                return [Error("sec_key_management", attribute, file, repr(attribute))]
        elif attribute.name == "kms_master_key_id" and (
            (
                atomic_unit.type == "resource.aws_sqs_queue"
                and attribute.value == "alias/aws/sqs"
            )
            or (
                atomic_unit.type == "resource.aws_sns_queue"
                and attribute.value == "alias/aws/sns"
            )
        ):
            return [Error("sec_key_management", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "azurerm_storage_account":
                name_str = (
                    element.name.value
                    if isinstance(element.name, String)
                    else str(element.name)
                )
                expr = "(\\$\\{)?azurerm_storage_account\\." + f"{name_str}\\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(
                    file,
                    "azurerm_storage_account_customer_managed_key",
                    "storage_account_id",
                    pattern,
                    [],
                ):
                    errors.append(
                        Error(
                            "sec_key_management",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'azurerm_storage_account_customer_managed_key' "
                            + f"associated to an 'azurerm_storage_account' resource.",
                        )
                    )
            for config in SecurityVisitor.KEY_MANAGEMENT:
                if config["required"] == "yes" and element.type in config["au_type"]:
                    attr_name = config["attribute"]
                    if (
                        self.check_required_attribute(
                            element, config["parents"], attr_name
                        )
                        is None
                    ):
                        errors.append(
                            Error(
                                "sec_key_management",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name '{config.get('msg', attr_name)}'.",
                            )
                        )

            errors += self._check_attributes(element, file)

        return errors
