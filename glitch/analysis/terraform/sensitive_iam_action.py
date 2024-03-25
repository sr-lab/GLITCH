import json
from typing import List, Dict
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.repr.inter import AtomicUnit, CodeElement, KeyValue


class TerraformSensitiveIAMAction(TerraformSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        def convert_string_to_dict(input_string: str):
            cleaned_string = input_string.strip()
            try:
                dict_data = json.loads(cleaned_string)
                return dict_data
            except json.JSONDecodeError:
                return None

        if not isinstance(element, AtomicUnit):
            return errors

        if element.type != "data.aws_iam_policy_document":
            return errors

        statements = self.check_required_attribute(
            element.attributes, [""], "statement", return_all=True
        )
        if isinstance(statements, list):
            for statement in statements:
                allow = self.check_required_attribute(
                    statement.keyvalues, [""], "effect"
                )
                if (
                    isinstance(allow, KeyValue)
                    and isinstance(allow.value, str)
                    and allow.value.lower() == "allow"
                ) or (not allow):
                    sensitive_action, action = self.iterate_required_attributes(
                        statement.keyvalues,
                        "actions",
                        lambda x: isinstance(x.value, str) and "*" in x.value.lower(),
                    )
                    if sensitive_action:
                        errors.append(
                            Error(
                                "sec_sensitive_iam_action", action, file, repr(action)
                            )
                        )

                    wildcarded_resource, resource = self.iterate_required_attributes(
                        statement.keyvalues,
                        "resources",
                        lambda x: isinstance(x.value, str)
                        and ((x.value.lower() in ["*"]) or (":*" in x.value.lower())),
                    )
                    if wildcarded_resource:
                        errors.append(
                            Error(
                                "sec_sensitive_iam_action",
                                resource,
                                file,
                                repr(resource),
                            )
                        )
        elif element.type in [
            "resource.aws_iam_role_policy",
            "resource.aws_iam_policy",
            "resource.aws_iam_user_policy",
            "resource.aws_iam_group_policy",
        ]:
            policy = self.check_required_attribute(element.attributes, [""], "policy")
            if not isinstance(policy, KeyValue) or not isinstance(policy.value, str):
                return errors

            policy_dict = convert_string_to_dict(policy.value.lower())
            if not (policy_dict and policy_dict["statement"]):
                return errors

            policy_statements = policy_dict["statement"]
            if isinstance(statements, dict):
                policy_statements: List[Dict[str, str | List[str]]] = [statements]

            for statement in policy_statements:
                if not (
                    statement["effect"]
                    and statement["action"]
                    and statement["resource"]
                ):
                    continue
                if not (statement["effect"] == "allow"):
                    continue

                if isinstance(statement["action"], list):
                    for action in statement["action"]:
                        if "*" in action:
                            errors.append(
                                Error(
                                    "sec_sensitive_iam_action",
                                    policy,
                                    file,
                                    repr(policy),
                                )
                            )
                            break
                elif "*" in statement["action"]:
                    errors.append(
                        Error("sec_sensitive_iam_action", policy, file, repr(policy))
                    )

                if isinstance(statement["resource"], list):
                    for resource in statement["resource"]:
                        if (resource in ["*"]) or (":*" in resource):
                            errors.append(
                                Error(
                                    "sec_sensitive_iam_action",
                                    policy,
                                    file,
                                    repr(policy),
                                )
                            )
                            break
                elif (statement["resource"] in ["*"]) or (
                    ":*" in statement["resource"]
                ):
                    errors.append(
                        Error("sec_sensitive_iam_action", policy, file, repr(policy))
                    )

        return errors
