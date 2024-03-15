from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformWeakPasswordKeyPolicy(TerraformSmellChecker):
    def check(self, element, file: str, au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            for policy in SecurityVisitor._PASSWORD_KEY_POLICY:
                if (policy['required'] == "yes" and element.type in policy['au_type'] 
                    and not self.check_required_attribute(element.attributes, policy['parents'], policy['attribute'])):
                    errors.append(Error('sec_weak_password_key_policy', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{policy['msg']}'."))

        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for policy in SecurityVisitor._PASSWORD_KEY_POLICY:
                if (element.name == policy['attribute'] and au_type in policy['au_type']
                    and parent_name in policy['parents'] and policy['values'] != [""]):
                    if (policy['logic'] == "equal"):
                        if ("any_not_empty" in policy['values'] and element.value.lower() == ""):
                            return [Error('sec_weak_password_key_policy', element, file, repr(element))]
                        elif ("any_not_empty" not in policy['values'] and not element.has_variable and 
                            element.value.lower() not in policy['values']):
                            return [Error('sec_weak_password_key_policy', element, file, repr(element))]
                    elif ((policy['logic'] == "gte" and not element.value.isnumeric()) or
                        (policy['logic'] == "gte" and element.value.isnumeric() 
                            and int(element.value) < int(policy['values'][0]))):
                        return [Error('sec_weak_password_key_policy', element, file, repr(element))]
                    elif ((policy['logic'] == "lte" and not element.value.isnumeric()) or
                        (policy['logic'] == "lte" and element.value.isnumeric() 
                            and int(element.value) > int(policy['values'][0]))):
                        return [Error('sec_weak_password_key_policy', element, file, repr(element))]

        return errors