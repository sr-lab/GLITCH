from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformThreatsDetection(TerraformSmellChecker):
    def check(self, element, file: str, code, au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            for config in SecurityVisitor._MISSING_THREATS_DETECTION_ALERTS:
                if (config['required'] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_threats_detection_alerts', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                elif (config['required'] == "must_not_exist" and element.type in config['au_type']):
                    a = self.check_required_attribute(element.attributes, config['parents'], config['attribute'])
                    if a is not None:
                        errors.append(Error('sec_threats_detection_alerts', a, file, repr(a)))

        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for config in SecurityVisitor._MISSING_THREATS_DETECTION_ALERTS:
                if (element.name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and config['values'] != [""]):
                    if ("any_not_empty" in config['values'] and element.value.lower() == ""):
                        return [Error('sec_threats_detection_alerts', element, file, repr(element))]
                    elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                        element.value.lower() not in config['values']):
                        return [Error('sec_threats_detection_alerts', element, file, repr(element))]
        return errors