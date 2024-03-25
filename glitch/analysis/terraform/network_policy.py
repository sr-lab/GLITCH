import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


class TerraformNetworkSecurityRules(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for rule in SecurityVisitor.NETWORK_SECURITY_RULES:
            if (
                attribute.name == rule["attribute"]
                and atomic_unit.type in rule["au_type"]
                and parent_name in rule["parents"]
                and not attribute.has_variable
                and attribute.value is not None
                and attribute.value.lower() not in rule["values"]
                and rule["values"] != [""]
            ):
                return [
                    Error(
                        "sec_network_security_rules", attribute, file, repr(attribute)
                    )
                ]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "resource.azurerm_network_security_rule":
                access = self.check_required_attribute(
                    element.attributes, [""], "access"
                )
                if (
                    isinstance(access, KeyValue)
                    and isinstance(access.value, str)
                    and access.value.lower() == "allow"
                ):
                    protocol = self.check_required_attribute(
                        element.attributes, [""], "protocol"
                    )
                    if (
                        isinstance(protocol, KeyValue)
                        and isinstance(protocol.value, str)
                        and protocol.value.lower() == "udp"
                    ):
                        errors.append(
                            Error(
                                "sec_network_security_rules", access, file, repr(access)
                            )
                        )
                    elif (
                        isinstance(protocol, KeyValue)
                        and isinstance(protocol.value, str)
                        and protocol.value.lower() == "tcp"
                    ):
                        dest_port_range = self.check_required_attribute(
                            element.attributes, [""], "destination_port_range"
                        )
                        port = (
                            isinstance(dest_port_range, KeyValue)
                            and isinstance(dest_port_range.value, str)
                            and dest_port_range.value.lower()
                            in [
                                "22",
                                "3389",
                                "*",
                            ]
                        )
                        port_ranges, _ = self.iterate_required_attributes(
                            element.attributes,
                            "destination_port_ranges",
                            lambda x: (
                                isinstance(x.value, str)
                                and x.value.lower() in ["22", "3389", "*"]
                            ),
                        )

                        if port or port_ranges:
                            source_address_prefix = self.check_required_attribute(
                                element.attributes, [""], "source_address_prefix"
                            )
                            if (
                                isinstance(source_address_prefix, KeyValue)
                                and isinstance(source_address_prefix.value, str)
                                and (
                                    source_address_prefix.value.lower()
                                    in ["*", "/0", "internet", "any"]
                                    or re.match(
                                        r"^0.0.0.0", source_address_prefix.value.lower()
                                    )
                                )
                            ):
                                errors.append(
                                    Error(
                                        "sec_network_security_rules",
                                        source_address_prefix,
                                        file,
                                        repr(source_address_prefix),
                                    )
                                )
            elif element.type == "resource.azurerm_network_security_group":
                access = self.check_required_attribute(
                    element.attributes, ["security_rule"], "access"
                )
                if (
                    isinstance(access, KeyValue)
                    and isinstance(access.value, str)
                    and access.value.lower() == "allow"
                ):
                    protocol = self.check_required_attribute(
                        element.attributes, ["security_rule"], "protocol"
                    )
                    if (
                        isinstance(protocol, KeyValue)
                        and isinstance(protocol.value, str)
                        and protocol.value.lower() == "udp"
                    ):
                        errors.append(
                            Error(
                                "sec_network_security_rules", access, file, repr(access)
                            )
                        )
                    elif (
                        isinstance(protocol, KeyValue)
                        and isinstance(protocol.value, str)
                        and protocol.value.lower() == "tcp"
                    ):
                        dest_port_range = self.check_required_attribute(
                            element.attributes,
                            ["security_rule"],
                            "destination_port_range",
                        )
                        if (
                            isinstance(dest_port_range, KeyValue)
                            and isinstance(dest_port_range.value, str)
                            and dest_port_range.value.lower()
                            in [
                                "22",
                                "3389",
                                "*",
                            ]
                        ):
                            source_address_prefix = self.check_required_attribute(
                                element.attributes, [""], "source_address_prefix"
                            )
                            if (
                                isinstance(source_address_prefix, KeyValue)
                                and isinstance(source_address_prefix.value, str)
                                and (
                                    source_address_prefix.value.lower()
                                    in ["*", "/0", "internet", "any"]
                                    or re.match(
                                        r"^0.0.0.0", source_address_prefix.value.lower()
                                    )
                                )
                            ):
                                errors.append(
                                    Error(
                                        "sec_network_security_rules",
                                        source_address_prefix,
                                        file,
                                        repr(source_address_prefix),
                                    )
                                )

            for rule in SecurityVisitor.NETWORK_SECURITY_RULES:
                if (
                    rule["required"] == "yes"
                    and element.type in rule["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, rule["parents"], rule["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_network_security_rules",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{rule['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
