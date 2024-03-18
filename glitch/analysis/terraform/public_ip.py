from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformPublicIp(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor._PUBLIC_IP_CONFIGS:
                if (config['required'] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_public_ip', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                elif (config['required'] == "must_not_exist" and element.type in config['au_type']):
                    a = self.check_required_attribute(element.attributes, config['parents'], config['attribute'])
                    if a is not None:
                        errors.append(Error('sec_public_ip', a, file, repr(a)))
                    
            def check_attribute(attribute: Attribute, parent_name: str):
                for config in SecurityVisitor._PUBLIC_IP_CONFIGS:
                    if (attribute.name == config['attribute'] and element.type in config['au_type']
                        and parent_name in config['parents'] and not attribute.has_variable and attribute.value is not None and 
                            attribute.value.lower() not in config['values'] and config['values'] != [""]):
                        errors.append(Error('sec_public_ip', attribute, file, repr(attribute)))
                        break
                    
                for child in attribute.keyvalues:
                    check_attribute(child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors