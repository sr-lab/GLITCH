from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformIntegrityPolicy(TerraformSmellChecker):
    def check(self, element, file: str, au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            for policy in SecurityVisitor._INTEGRITY_POLICY:
                if (policy['required'] == "yes" and element.type in policy['au_type']
                    and not self.check_required_attribute(element.attributes, policy['parents'], policy['attribute'])):
                    errors.append(Error('sec_integrity_policy', element, file, repr(element),
                        f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for policy in SecurityVisitor._INTEGRITY_POLICY:
                if (element.name == policy['attribute'] and au_type in policy['au_type'] 
                    and parent_name in policy['parents'] and not element.has_variable 
                    and element.value.lower() not in policy['values']):
                    return[Error('sec_integrity_policy', element, file, repr(element))]
        return errors