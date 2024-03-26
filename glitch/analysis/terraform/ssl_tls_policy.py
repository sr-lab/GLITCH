from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, KeyValue, CodeElement


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
                and parent_name in policy["parents"]
                and not attribute.has_variable
                and attribute.value is not None
                and attribute.value.lower() not in policy["values"]
            ):
                return [Error("sec_ssl_tls_policy", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type in [
                "resource.aws_alb_listener",
                "resource.aws_lb_listener",
            ]:
                protocol = self.check_required_attribute(
                    element.attributes, [""], "protocol"
                )
                if (
                    isinstance(protocol, KeyValue)
                    and isinstance(protocol.value, str)
                    and protocol.value.lower() in ["https", "tls"]
                ):
                    ssl_policy = self.check_required_attribute(
                        element.attributes, [""], "ssl_policy"
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
                        element.attributes, policy["parents"], policy["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_ssl_tls_policy",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{policy['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
