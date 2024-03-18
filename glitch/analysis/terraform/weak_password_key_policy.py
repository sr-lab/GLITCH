from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformWeakPasswordKeyPolicy(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            for policy in SecurityVisitor._PASSWORD_KEY_POLICY:
                if (policy['required'] == "yes" and element.type in policy['au_type'] 
                    and not self.check_required_attribute(element.attributes, policy['parents'], policy['attribute'])):
                    errors.append(Error('sec_weak_password_key_policy', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
                    
            def check_attribute(attribute: Attribute, parent_name: str):
                for policy in SecurityVisitor._PASSWORD_KEY_POLICY:
                    if (attribute.name == policy['attribute'] and element.type in policy['au_type']
                        and parent_name in policy['parents'] and policy['values'] != [""]):
                        if (policy['logic'] == "equal"):
                            if ("any_not_empty" in policy['values'] and attribute.value.lower() == ""):
                                errors.append(Error('sec_weak_password_key_policy', attribute, file, repr(attribute)))
                                break
                            elif ("any_not_empty" not in policy['values'] and not attribute.has_variable and 
                                attribute.value.lower() not in policy['values']):
                                errors.append(Error('sec_weak_password_key_policy', attribute, file, repr(attribute)))
                                break
                        elif ((policy['logic'] == "gte" and not attribute.value.isnumeric()) or
                            (policy['logic'] == "gte" and attribute.value.isnumeric() 
                                and int(attribute.value) < int(policy['values'][0]))):
                            errors.append(Error('sec_weak_password_key_policy', attribute, file, repr(attribute)))
                            break
                        elif ((policy['logic'] == "lte" and not attribute.value.isnumeric()) or
                            (policy['logic'] == "lte" and attribute.value.isnumeric() 
                                and int(attribute.value) > int(policy['values'][0]))):
                            errors.append(Error('sec_weak_password_key_policy', attribute, file, repr(attribute)))
                            break

                for child in attribute.keyvalues:
                    check_attribute(child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors