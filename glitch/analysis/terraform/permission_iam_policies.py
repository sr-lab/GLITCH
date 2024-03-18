import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformPermissionIAMPolicies(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.aws_iam_user"):
                expr = "\${aws_iam_user\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(file, "resource.aws_iam_user_policy", "user", pattern, [""])
                if assoc_au is not None:
                    a = self.check_required_attribute(assoc_au.attributes, [""], "user", None, pattern) 
                    errors.append(Error('sec_permission_iam_policies', a, file, repr(a)))

            def check_attribute(attribute: Attribute, parent_name: str):
                if ((attribute.name == "member" or attribute.name.split('[')[0] == "members") 
                    and element.type in SecurityVisitor._GOOGLE_IAM_MEMBER
                    and (re.search(r".-compute@developer.gserviceaccount.com", attribute.value) or 
                        re.search(r".@appspot.gserviceaccount.com", attribute.value) or
                        re.search(r"user:", attribute.value))):
                    errors.append(Error('sec_permission_iam_policies', attribute, file, repr(attribute)))

                for config in SecurityVisitor._PERMISSION_IAM_POLICIES:
                    if (attribute.name == config['attribute'] and element.type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ((config['logic'] == "equal" and not attribute.has_variable and attribute.value.lower() not in config['values'])
                            or (config['logic'] == "diff" and attribute.value.lower() in config['values'])):
                            errors.append(Error('sec_permission_iam_policies', attribute, file, repr(attribute)))
                            break

                for child in attribute.keyvalues:
                    check_attribute(child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors