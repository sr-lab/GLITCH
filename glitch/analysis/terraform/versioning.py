from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit


class TerraformVersioning(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor._VERSIONING:
                if (config['required'] == "yes" and element.type in config['au_type'] 
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_versioning', element, file, repr(element), 
                                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    
            def check_attribute(attribute, parent_name):
                for config in SecurityVisitor._VERSIONING:
                    if (attribute.name == config['attribute'] and element.type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]
                        and not attribute.has_variable and attribute.value.lower() not in config['values']):
                        errors.append(Error('sec_versioning', attribute, file, repr(attribute)))

                for attr_child in attribute.keyvalues:
                    check_attribute(attr_child, attribute.name)
            
            for attribute in element.attributes:
                check_attribute(attribute, "")
        
        return errors