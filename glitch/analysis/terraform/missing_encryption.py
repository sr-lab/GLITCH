import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.checkers.var_checker import VariableChecker
from glitch.repr.inter import *


class TerraformMissingEncryption(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.MISSING_ENCRYPTION:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and self._parent_matches(parent_name, config["parents"])
                and config["values"] != []
            ):
                if isinstance(attribute.value, (String, Boolean)):
                    value_str = str(attribute.value.value).lower()
                elif hasattr(attribute.value, "code"):
                    value_str = attribute.value.code.lower()
                else:
                    continue

                if "any_not_empty" in config["values"] and value_str == "":
                    return [
                        Error(
                            "sec_missing_encryption", attribute, file, repr(attribute)
                        )
                    ]
                elif (
                    "any_not_empty" not in config["values"]
                    and not VariableChecker().check(attribute.value)
                    and value_str not in config["values"]
                ):
                    return [
                        Error(
                            "sec_missing_encryption", attribute, file, repr(attribute)
                        )
                    ]
        for item in SecurityVisitor.CONFIGURATION_KEYWORDS:
            if item.lower() == attribute.name and isinstance(attribute.value, String):
                value_str = attribute.value.value.lower()
                for config in SecurityVisitor.ENCRYPT_CONFIG:
                    if atomic_unit.type in config["au_type"]:
                        expr = config["keyword"].lower() + "\\s*" + config["value"].lower()
                        pattern = re.compile(rf"{expr}")
                        if not re.search(pattern, value_str) and config["required"] == "yes":
                            return [
                                Error(
                                    "sec_missing_encryption",
                                    attribute,
                                    file,
                                    repr(attribute),
                                )
                            ]
                        elif re.search(pattern, value_str) and config["required"] == "must_not_exist":
                            return [
                                Error(
                                    "sec_missing_encryption",
                                    attribute,
                                    file,
                                    repr(attribute),
                                )
                            ]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            # This does not work when the name is not a String :/
            if element.type == "aws_s3_bucket" and isinstance(element.name, String):
                expr = "aws_s3_bucket\\." + f"{element.name.value}\\."
                pattern = re.compile(rf"{expr}")

                r = self.get_associated_au(
                    file,
                    "aws_s3_bucket_server_side_encryption_configuration",
                    "bucket",
                    pattern,
                    [],
                )
                if r is None:
                    errors.append(
                        Error(
                            "sec_missing_encryption",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'aws_s3_bucket_server_side_encryption_configuration' "
                            + f"associated to an 'aws_s3_bucket' resource.",
                        )
                    )
            elif element.type == "aws_eks_cluster":
                resources = self.check_required_attribute(
                    element, ["encryption_config"], "resources"
                )
                if isinstance(resources, Attribute) and isinstance(resources.value, Array):
                    has_secrets = any(
                        isinstance(v, String) and v.value.lower() == "secrets"
                        for v in resources.value.value
                    )
                    if not has_secrets:
                        errors.append(Error("sec_missing_encryption", resources, file, repr(resources)))
                elif resources is None:
                    errors.append(
                        Error(
                            "sec_missing_encryption",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name 'encryption_config.resources'.",
                        )
                    )
            elif element.type in [
                "aws_instance",
                "aws_launch_configuration",
            ]:
                ebs_block_device = self.check_required_attribute(element, [], "ebs_block_device")
                if isinstance(ebs_block_device, UnitBlock):
                    encrypted = self.check_required_attribute(ebs_block_device, [], "encrypted")
                    if encrypted is None:
                        errors.append(
                            Error(
                                "sec_missing_encryption",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name 'ebs_block_device.encrypted'.",
                            )
                        )
            elif element.type == "aws_ecs_task_definition":
                volume = self.check_required_attribute(element, [], "volume")
                if isinstance(volume, UnitBlock):
                    efs_volume_config = self.check_required_attribute(
                        volume, [], "efs_volume_configuration"
                    )
                    if isinstance(efs_volume_config, UnitBlock):
                        transit_encryption = self.check_required_attribute(
                            efs_volume_config, [], "transit_encryption"
                        )
                        if not transit_encryption:
                            errors.append(
                                Error(
                                    "sec_missing_encryption",
                                    element,
                                    file,
                                    repr(element),
                                    f"Suggestion: check for a required attribute with name"
                                    + f"'volume.efs_volume_configuration.transit_encryption'.",
                                )
                            )

            reported_msgs: set[str] = set()
            for config in SecurityVisitor.MISSING_ENCRYPTION:
                msg = config.get("msg", config["attribute"])
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and msg not in reported_msgs
                    and self.check_required_attribute(
                        element, config["parents"], config["attribute"]
                    )
                    is None
                ):
                    reported_msgs.add(msg)
                    errors.append(
                        Error(
                            "sec_missing_encryption",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{msg}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
