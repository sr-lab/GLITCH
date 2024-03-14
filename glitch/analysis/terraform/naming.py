import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformNaming(TerraformSmellChecker):
    def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.aws_security_group"):
                ingress = self.check_required_attribute(element.attributes, [""], "ingress")
                egress = self.check_required_attribute(element.attributes, [""], "egress")
                if ingress and not self.check_required_attribute(ingress.keyvalues, [""], "description"):
                    errors.append(Error('sec_naming', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name 'ingress.description'."))
                if egress and not self.check_required_attribute(egress.keyvalues, [""], "description"):
                    errors.append(Error('sec_naming', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name 'egress.description'."))
            elif (element.type == "resource.google_container_cluster"):
                resource_labels = self.check_required_attribute(element.attributes, [""], "resource_labels", None)
                if resource_labels and resource_labels.value == None:
                    if resource_labels.keyvalues == []:
                        errors.append(Error('sec_naming', resource_labels, file, repr(resource_labels), 
                            f"Suggestion: check empty 'resource_labels'."))
                else:
                    errors.append(Error('sec_naming', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name 'resource_labels'."))

            for config in SecurityVisitor._NAMING:
                if (config['required'] == "yes" and element.type in config['au_type'] 
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_naming', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            if (elem_name == "name" and au_type in ["resource.azurerm_storage_account"]):
                pattern = r'^[a-z0-9]{3,24}$'
                if not re.match(pattern, elem_value):
                    errors.append(Error('sec_naming', element, file, repr(element)))

            for config in SecurityVisitor._NAMING:
                if (elem_name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and config['values'] != [""]):
                    if ("any_not_empty" in config['values'] and elem_value.lower() == ""):
                        errors.append(Error('sec_naming', element, file, repr(element)))
                        break
                    elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                        elem_value.lower() not in config['values']):
                        errors.append(Error('sec_naming', element, file, repr(element)))
                        break
        return errors