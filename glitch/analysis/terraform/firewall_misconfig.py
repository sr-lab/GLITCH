from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformFirewallMisconfig(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor._FIREWALL_CONFIGS:
                if (config['required'] == "yes" and element.type in config['au_type'] 
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_firewall_misconfig', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            
            def check_attribute(attribute: Attribute, parent_name: str):
                for config in SecurityVisitor._FIREWALL_CONFIGS:
                    if (attribute.name == config['attribute'] and element.type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and attribute.value.lower() == ""):
                            errors.append(Error('sec_firewall_misconfig', attribute, file, repr(attribute)))
                            break
                        elif ("any_not_empty" not in config['values'] and not attribute.has_variable and 
                            attribute.value.lower() not in config['values']):
                            errors.append(Error('sec_firewall_misconfig', attribute, file, repr(attribute)))
                            break
                
                for attr_child in attribute.keyvalues:
                    check_attribute(attr_child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors