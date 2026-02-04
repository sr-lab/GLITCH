import re
from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import Array, AtomicUnit, Attribute, Boolean, CodeElement, KeyValue, String, UnitBlock
from glitch.analysis.checkers.var_checker import VariableChecker


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
                and self._parent_matches(parent_name, rule["parents"])
                and not VariableChecker().check(attribute.value)
                and rule["values"] != [""]
            ):
                if isinstance(attribute.value, (String, Boolean)):
                    if str(attribute.value.value).lower() not in rule["values"]:
                        return [Error("sec_network_security_rules", attribute, file, repr(attribute))]
                elif hasattr(attribute.value, 'code') and attribute.value.code.lower() not in rule["values"]:
                    return [Error("sec_network_security_rules", attribute, file, repr(attribute))]

        return []

    def _has_str_value(self, attr: Attribute | UnitBlock | KeyValue | None, value: str) -> bool:
        return (
            isinstance(attr, (Attribute, KeyValue))
            and isinstance(attr.value, String)
            and attr.value.value.lower() == value
        )

    def _has_str_value_in(self, attr: Attribute | UnitBlock | KeyValue | None, values: list[str]) -> bool:
        return (
            isinstance(attr, (Attribute, KeyValue))
            and isinstance(attr.value, String)
            and attr.value.value.lower() in values
        )

    def _is_permissive_source(self, attr: Attribute | UnitBlock | KeyValue | None) -> bool:
        if not isinstance(attr, (Attribute, KeyValue)) or not isinstance(attr.value, String):
            return False
        val = attr.value.value.lower()
        return val in ["*", "/0", "internet", "any"] or bool(re.match(r"^0.0.0.0", val))

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "azurerm_network_security_rule":
                access = self.check_required_attribute(element, [], "access")
                if self._has_str_value(access, "allow"):
                    protocol = self.check_required_attribute(element, [], "protocol")
                    if self._has_str_value(protocol, "udp"):
                        errors.append(
                            Error("sec_network_security_rules", access, file, repr(access))
                        )
                    elif self._has_str_value(protocol, "tcp"):
                        dest_port_range = self.check_required_attribute(element, [], "destination_port_range")
                        port = self._has_str_value_in(dest_port_range, ["22", "3389", "*"])
                        
                        port_ranges = False
                        for attr in element.attributes:
                            if attr.name == "destination_port_ranges" and isinstance(attr.value, Array):
                                for item in attr.value.value:
                                    if isinstance(item, String) and item.value.lower() in ["22", "3389", "*"]:
                                        port_ranges = True
                                        break

                        if port or port_ranges:
                            source_address_prefix = self.check_required_attribute(element, [], "source_address_prefix")
                            if self._is_permissive_source(source_address_prefix):
                                errors.append(
                                    Error(
                                        "sec_network_security_rules",
                                        source_address_prefix,
                                        file,
                                        repr(source_address_prefix),
                                    )
                                )

            elif element.type == "azurerm_network_security_group":
                access = self.check_required_attribute(element, ["security_rule"], "access")
                if self._has_str_value(access, "allow"):
                    protocol = self.check_required_attribute(element, ["security_rule"], "protocol")
                    if self._has_str_value(protocol, "udp"):
                        errors.append(
                            Error("sec_network_security_rules", access, file, repr(access))
                        )
                    elif self._has_str_value(protocol, "tcp"):
                        dest_port_range = self.check_required_attribute(element, ["security_rule"], "destination_port_range")
                        if self._has_str_value_in(dest_port_range, ["22", "3389", "*"]):
                            source_address_prefix = self.check_required_attribute(element, ["security_rule"], "source_address_prefix")
                            if self._is_permissive_source(source_address_prefix):
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
                    and self.check_required_attribute(
                        element, rule["parents"], rule["attribute"]
                    )
                    is None
                ):
                    errors.append(
                        Error(
                            "sec_network_security_rules",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{rule.get('msg', rule['attribute'])}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
