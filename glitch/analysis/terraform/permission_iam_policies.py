import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformPermissionIAMPolicies(TerraformSmellChecker):
    def check(self, element, file: str, code, elem_value: str = "", au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.aws_iam_user"):
                expr = "\${aws_iam_user\." + f"{element.name}\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(code, file, "resource.aws_iam_user_policy", "user", pattern, [""])
                if assoc_au is not None:
                    a = self.check_required_attribute(assoc_au.attributes, [""], "user", None, pattern) 
                    errors.append(Error('sec_permission_iam_policies', a, file, repr(a)))

        elif isinstance(element, Attribute) or isinstance(element, Variable):
            if ((element.name == "member" or element.name.split('[')[0] == "members") 
                and au_type in SecurityVisitor._GOOGLE_IAM_MEMBER
                and (re.search(r".-compute@developer.gserviceaccount.com", elem_value) or 
                    re.search(r".@appspot.gserviceaccount.com", elem_value) or
                    re.search(r"user:", elem_value))):
                errors.append(Error('sec_permission_iam_policies', element, file, repr(element)))

            for config in SecurityVisitor._PERMISSION_IAM_POLICIES:
                if (element.name == config['attribute'] and au_type in config['au_type']
                    and parent_name in config['parents'] and config['values'] != [""]):
                    if ((config['logic'] == "equal" and not element.has_variable and elem_value.lower() not in config['values'])
                        or (config['logic'] == "diff" and elem_value.lower() in config['values'])):
                        errors.append(Error('sec_permission_iam_policies', element, file, repr(element)))
                        break
        return errors