import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformAuthentication(TerraformSmellChecker):
    def check(self, element, file: str, au_type = None, parent_name = ""):
        errors = []

        if isinstance(element, AtomicUnit):
            if (element.type == "resource.google_sql_database_instance"):
                errors += self.check_database_flags(element, file, 'sec_authentication', "contained database authentication", "off")
            elif (element.type == "resource.aws_iam_group"):
                expr = "\${aws_iam_group\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                if not self.get_associated_au(file, "resource.aws_iam_group_policy", "group", pattern, [""]):
                    errors.append(Error('sec_authentication', element, file, repr(element), 
                        f"Suggestion: check for a required resource 'aws_iam_group_policy' associated to an " +
                            f"'aws_iam_group' resource."))

            for config in SecurityVisitor._AUTHENTICATION:
                if (config['required'] == "yes" and element.type in config['au_type']
                    and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                    errors.append(Error('sec_authentication', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            
            def check_attribute(attribute: Attribute, parent_name: str):
                for item in SecurityVisitor._POLICY_KEYWORDS:
                    if item.lower() == attribute.name:        
                        for config in SecurityVisitor._POLICY_AUTHENTICATION:
                            if element.type in config['au_type']:
                                expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                                pattern = re.compile(rf"{expr}")
                                if not re.search(pattern, attribute.value):
                                    errors.append(Error('sec_authentication', attribute, file, repr(attribute)))
                                    break

                for config in SecurityVisitor._AUTHENTICATION:
                    if (attribute.name == config['attribute'] and element.type in config['au_type']
                        and parent_name in config['parents'] and not attribute.has_variable 
                        and attribute.value.lower() not in config['values']
                        and config['values'] != [""]):
                        errors.append(Error('sec_authentication', attribute, file, repr(attribute)))
                        break

                for attr_child in attribute.keyvalues:
                    check_attribute(attr_child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors