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
    UnitBlock,
)


class TerraformFirewallMisconfig(TerraformSmellChecker):
    def _find_block_recursive(self, element: AtomicUnit | UnitBlock, name: str) -> bool:
        blocks = (
            element.statements
            if isinstance(element, AtomicUnit)
            else element.statements + element.unit_blocks
        )
        for stmt in blocks:
            if isinstance(stmt, UnitBlock):
                if stmt.name == name:
                    return True
                if self._find_block_recursive(stmt, name):
                    return True
        if isinstance(element, UnitBlock):
            for ub in element.unit_blocks:
                if ub.name == name:
                    return True
                if self._find_block_recursive(ub, name):
                    return True
        return False

    def _is_parent_also_checked(self, parent: str, au_type: str) -> bool:
        for config in SecurityVisitor.FIREWALL_CONFIGS:
            if config["attribute"] == parent and au_type in config["au_type"]:
                return True
        return False

    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for config in SecurityVisitor.FIREWALL_CONFIGS:
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
                        Error(
                            "sec_firewall_misconfig", attribute, file, repr(attribute)
                        )
                    ]
                elif (
                    "any_not_empty" not in config["values"]
                    and value_str is not None
                    and not VariableChecker().check(attribute.value)
                    and value_str.lower() not in config["values"]
                ):
                    return [
                        Error(
                            "sec_firewall_misconfig", attribute, file, repr(attribute)
                        )
                    ]
        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor.FIREWALL_CONFIGS:
                if config["required"] == "yes" and element.type in config["au_type"]:
                    raw_parents: list[str] | list[list[str]] = config["parents"]
                    parent_list: List[str] = []
                    if len(raw_parents) > 0:
                        first_parent: str | list[str] = raw_parents[0]
                        if isinstance(first_parent, list):
                            parent_list = first_parent
                        else:
                            parent_list = raw_parents  # type: ignore[assignment]

                    if (
                        len(parent_list) > 0
                        and self._is_parent_also_checked(parent_list[0], element.type)
                        and not self._find_block_recursive(element, parent_list[0])
                    ):
                        continue

                    attr_name = config["attribute"]
                    if (
                        self.check_required_attribute(
                            element, config["parents"], attr_name
                        )
                        is None
                    ):
                        errors.append(
                            Error(
                                "sec_firewall_misconfig",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name '{config.get('msg', attr_name)}'.",
                            )
                        )

            errors += self._check_attributes(element, file)

        return errors
