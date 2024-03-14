from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformDnsWithoutDnssec(TerraformSmellChecker):
    def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor._DNSSEC_CONFIGS:
                if (config['required'] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_dnssec', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for config in SecurityVisitor._DNSSEC_CONFIGS:
                if (elem_name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and not element.has_variable 
                    and elem_value.lower() not in config['values']
                    and config['values'] != [""]):
                    return [Error('sec_dnssec', element, file, repr(element))]
        return errors