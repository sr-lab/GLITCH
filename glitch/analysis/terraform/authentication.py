import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformAuthentication(TerraformSmellChecker):
    def check(self, element, file: str, code, au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.google_sql_database_instance"):
                errors += self.check_database_flags(element, file, 'sec_authentication', "contained database authentication", "off")
            elif (element.type == "resource.aws_iam_group"):
                expr = "\${aws_iam_group\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(code, file, "resource.aws_iam_group_policy", "group", pattern, [""]):
                    errors.append(Error('sec_authentication', element, file, repr(element), 
                        f"Suggestion: check for a required resource 'aws_iam_group_policy' associated to an " +
                            f"'aws_iam_group' resource."))

            for config in SecurityVisitor._AUTHENTICATION:
                if (config['required'] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_authentication', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for item in SecurityVisitor._POLICY_KEYWORDS:
                if item.lower() == element.name:        
                    for config in SecurityVisitor._POLICY_AUTHENTICATION:
                        if au_type in config['au_type']:
                            expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                            pattern = re.compile(rf"{expr}")
                            if not re.search(pattern, element.value):
                                errors.append(Error('sec_authentication', element, file, repr(element)))

            for config in SecurityVisitor._AUTHENTICATION:
                if (element.name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and not element.has_variable 
                    and element.value.lower() not in config['values']
                    and config['values'] != [""]):
                    errors.append(Error('sec_authentication', element, file, repr(element)))
                    break
        return errors