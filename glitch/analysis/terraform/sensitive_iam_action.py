import json
from typing import Any, List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.repr.inter import Array, AtomicUnit, CodeElement, KeyValue, String, UnitBlock


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

        if element.type == "data.aws_iam_policy_document":
            statements = self.get_attributes(element, [], "statement")
            for statement in statements:
                if isinstance(statement, UnitBlock):
                    effect_value = None
                    for attr in statement.attributes:
                        if attr.name == "effect":
                            if isinstance(attr.value, String):
                                effect_value = attr.value.value.lower()
                            elif isinstance(attr.value, str):
                                effect_value = attr.value.lower()
                            break
                    
                    if effect_value == "allow" or effect_value is None:
                        for attr in statement.attributes:
                            if attr.name == "actions" and isinstance(attr.value, Array):
                                for item in attr.value.value:
                                    item_val = item.value if isinstance(item, String) else item
                                    if isinstance(item_val, str) and "*" in item_val:
                                        errors.append(
                                            Error("sec_sensitive_iam_action", attr, file, repr(attr))
                                        )
                                        break

                            if attr.name == "resources" and isinstance(attr.value, Array):
                                for item in attr.value.value:
                                    item_val = item.value if isinstance(item, String) else item
                                    if isinstance(item_val, str) and (item_val == "*" or ":*" in item_val):
                                        errors.append(
                                            Error("sec_sensitive_iam_action", attr, file, repr(attr))
                                        )
                                        break
        elif element.type in [
            "resource.aws_iam_role_policy",
            "resource.aws_iam_policy",
            "resource.aws_iam_user_policy",
            "resource.aws_iam_group_policy",
        ]:
            policy = self.check_required_attribute(element, [""], "policy")
            if not isinstance(policy, KeyValue) or not isinstance(policy.value, str):
                return errors

            policy_dict = convert_string_to_dict(policy.value.lower())
            if not (policy_dict and policy_dict["statement"]):
                return errors

            policy_statements: List[Any] = policy_dict["statement"]
            if isinstance(policy_statements, dict):
                policy_statements = [policy_statements]

            for statement in policy_statements:
                statement: Any
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
