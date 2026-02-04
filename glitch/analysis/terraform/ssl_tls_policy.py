from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.checkers.var_checker import VariableChecker
from glitch.repr.inter import AtomicUnit, Attribute, Boolean, KeyValue, CodeElement, String, Value


class TerraformSslTlsPolicy(TerraformSmellChecker):
    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        for policy in SecurityVisitor.SSL_TLS_POLICY:
            if (
                attribute.name == policy["attribute"]
                and atomic_unit.type in policy["au_type"]
                and self._parent_matches(parent_name, policy["parents"])
                and not VariableChecker().check(attribute.value)
            ):
                if isinstance(attribute.value, Boolean) and str(attribute.value.value).lower() not in policy["values"]:
                    return [Error("sec_ssl_tls_policy", attribute, file, repr(attribute))]
                elif isinstance(attribute.value, String) and attribute.value.value.lower() not in policy["values"]:
                    return [Error("sec_ssl_tls_policy", attribute, file, repr(attribute))]
                elif isinstance(attribute.value, str) and attribute.value.lower() not in policy["values"]:
                    return [Error("sec_ssl_tls_policy", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type in [
                "aws_alb_listener",
                "aws_lb_listener",
            ]:
                protocol = self.check_required_attribute(
                    element, [], "protocol"
                )
                if (
                    isinstance(protocol, KeyValue)
                    and isinstance(protocol.value, Value)
                    and isinstance(protocol.value.value, str)
                    and protocol.value.value.lower() in ["https", "tls"]
                ):
                    ssl_policy = self.check_required_attribute(
                        element, [], "ssl_policy"
                    )
                    if not ssl_policy:
                        errors.append(
                            Error(
                                "sec_ssl_tls_policy",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name 'ssl_policy'.",
                            )
                        )

            for policy in SecurityVisitor.SSL_TLS_POLICY:
                if (
                    policy["required"] == "yes"
                    and element.type in policy["au_type"]
                    and not self.check_required_attribute(
                        element, policy["parents"], policy["attribute"]
                    )
                ):
                    attribute = policy["attribute"]
                    errors.append(
                        Error(
                            "sec_ssl_tls_policy",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{attribute}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
