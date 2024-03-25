from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, CodeElement, KeyValue, Attribute


class TerraformAttachedResource(TerraformSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, AtomicUnit):

            def check_attached_resource(
                attributes: List[KeyValue] | List[Attribute], resource_types: List[str]
            ) -> bool:
                for a in attributes:
                    if a.value != None:
                        for resource_type in resource_types:
                            if f"{a.value}".lower().startswith(
                                "${" + f"{resource_type}."
                            ) or f"{a.value}".lower().startswith(f"{resource_type}."):
                                resource_name = a.value.lower().split(".")[1]
                                if self.get_au(
                                    file, resource_name, f"resource.{resource_type}"
                                ):
                                    return True
                    elif a.value == None:
                        attached = check_attached_resource(a.keyvalues, resource_types)
                        if attached:
                            return True
                return False

            if element.type == "resource.aws_route53_record":
                type_A = self.check_required_attribute(
                    element.attributes, [""], "type", "a"
                )
                if type_A and not check_attached_resource(
                    element.attributes, SecurityVisitor.POSSIBLE_ATTACHED_RESOURCES
                ):
                    errors.append(
                        Error("sec_attached_resource", element, file, repr(element))
                    )

        return errors
