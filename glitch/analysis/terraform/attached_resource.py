from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import (
    AtomicUnit,
    CodeElement,
    KeyValue,
    Attribute,
    UnitBlock,
    Array,
)


class TerraformAttachedResource(TerraformSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, AtomicUnit):

            def check_value_for_resource(
                value_code: str, resource_types: List[str]
            ) -> bool:
                value_lower = value_code.lower()
                for resource_type in resource_types:
                    if value_lower.startswith(
                        "${" + f"{resource_type}."
                    ) or value_lower.startswith(f"{resource_type}."):
                        resource_name = value_lower.split(".")[1]
                        if self.get_au(file, resource_name, resource_type):
                            return True
                return False

            def check_attached_resource(
                attributes: List[KeyValue] | List[Attribute],
                statements: List[CodeElement],
                resource_types: List[str],
            ) -> bool:
                for a in attributes:
                    if hasattr(a.value, "code"):
                        if check_value_for_resource(a.value.code, resource_types):
                            return True
                    if isinstance(a.value, Array):
                        for item in a.value.value:
                            if hasattr(item, "code"):
                                if check_value_for_resource(item.code, resource_types):
                                    return True
                for stmt in statements:
                    if isinstance(stmt, UnitBlock):
                        if check_attached_resource(
                            stmt.attributes, stmt.statements, resource_types
                        ):
                            return True
                return False

            if element.type == "aws_route53_record":
                type_A = self.check_required_attribute(element, [], "type", "a")
                if type_A and not check_attached_resource(
                    element.attributes,
                    element.statements,
                    SecurityVisitor.POSSIBLE_ATTACHED_RESOURCES,
                ):
                    errors.append(
                        Error("sec_attached_resource", element, file, repr(element))
                    )

        return errors
