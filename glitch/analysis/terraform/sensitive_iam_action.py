import json
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformSensitiveIAMAction(TerraformSmellChecker):
    def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
        errors = []

        def convert_string_to_dict(input_string):
            cleaned_string = input_string.strip()
            try:
                dict_data = json.loads(cleaned_string)
                return dict_data
            except json.JSONDecodeError as e:
                return None

        if isinstance(element, AtomicUnit):
            if (element.type == "data.aws_iam_policy_document"):
                statements = self.check_required_attribute(element.attributes, [""], "statement", return_all=True)
                if statements is not None:
                    for statement in statements:
                        allow = self.check_required_attribute(statement.keyvalues, [""], "effect")
                        if ((allow and allow.value.lower() == "allow") or (not allow)):
                            sensitive_action = False
                            i = 0
                            action = self.check_required_attribute(statement.keyvalues, [""], f"actions[{i}]")
                            while action:
                                if ("*" in action.value.lower()):
                                    sensitive_action = True
                                    break
                                i += 1
                                action = self.check_required_attribute(statement.keyvalues, [""], f"actions[{i}]")
                            if sensitive_action:
                                errors.append(Error('sec_sensitive_iam_action', action, file, repr(action)))
                            wildcarded_resource = False
                            i = 0
                            resource = self.check_required_attribute(statement.keyvalues, [""], f"resources[{i}]")
                            while resource:
                                if (resource.value.lower() in ["*"]) or (":*" in resource.value.lower()):
                                    wildcarded_resource = True
                                    break
                                i += 1
                                resource = self.check_required_attribute(statement.keyvalues, [""], f"resources[{i}]")
                            if wildcarded_resource:
                                errors.append(Error('sec_sensitive_iam_action', resource, file, repr(resource)))
            elif (element.type in ["resource.aws_iam_role_policy", "resource.aws_iam_policy", 
                                    "resource.aws_iam_user_policy", "resource.aws_iam_group_policy"]):
                policy = self.check_required_attribute(element.attributes, [""], "policy")
                if policy is not None:
                    policy_dict = convert_string_to_dict(policy.value.lower())
                    if policy_dict and policy_dict["statement"]:
                        statements = policy_dict["statement"]
                        if isinstance(statements, dict):
                            statements = [statements]
                        for statement in statements:
                            if statement["effect"] and statement["action"] and statement["resource"]:
                                if statement["effect"] == "allow":
                                    if isinstance(statement["action"], list):
                                        for action in statement["action"]:
                                            if ("*" in action):
                                                errors.append(Error('sec_sensitive_iam_action', policy, file, repr(policy)))
                                                break
                                    else:
                                        if ("*" in statement["action"]):
                                            errors.append(Error('sec_sensitive_iam_action', policy, file, repr(policy)))
                                    if isinstance(statement["resource"], list):
                                        for resource in statement["resource"]:
                                            if (resource in ["*"]) or (":*" in resource):
                                                errors.append(Error('sec_sensitive_iam_action', policy, file, repr(policy)))
                                                break
                                    else:
                                        if (statement["resource"] in ["*"]) or (":*" in statement["resource"]):
                                            errors.append(Error('sec_sensitive_iam_action', policy, file, repr(policy)))
        
        return errors