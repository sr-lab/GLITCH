from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformIntegrityPolicy(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            for policy in SecurityVisitor._INTEGRITY_POLICY:
                if (policy['required'] == "yes" and element.type in policy['au_type']
                    and not self.check_required_attribute(element.attributes, policy['parents'], policy['attribute'])):
                    errors.append(Error('sec_integrity_policy', element, file, repr(element),
                        f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
                    
            def check_attribute(attribute: Attribute, parent_name: str):
                for policy in SecurityVisitor._INTEGRITY_POLICY:
                    if (attribute.name == policy['attribute'] and element.type in policy['au_type']
                        and parent_name in policy['parents'] and not attribute.has_variable 
                        and attribute.value.lower() not in policy['values']):
                        errors.append(Error('sec_integrity_policy', attribute, file, repr(attribute)))
                        break

                for attr_child in attribute.keyvalues:
                    check_attribute(attr_child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors