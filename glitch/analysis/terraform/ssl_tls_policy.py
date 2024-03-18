from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute


class TerraformSslTlsPolicy(TerraformSmellChecker):
    def check(self, element, file: str):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type in ["resource.aws_alb_listener", "resource.aws_lb_listener"]):
                protocol = self.check_required_attribute(element.attributes, [""], "protocol")
                if (protocol and protocol.value.lower() in ["https", "tls"]):
                    ssl_policy = self.check_required_attribute(element.attributes, [""], "ssl_policy")
                    if not ssl_policy:
                        errors.append(Error('sec_ssl_tls_policy', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name 'ssl_policy'."))
            
            for policy in SecurityVisitor._SSL_TLS_POLICY:
                if (policy['required'] == "yes" and element.type in policy['au_type']
                    and not self.check_required_attribute(element.attributes, policy['parents'], policy['attribute'])):
                    errors.append(Error('sec_ssl_tls_policy', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
            
            def check_attribute(attribute: Attribute, parent_name: str):
                for policy in SecurityVisitor._SSL_TLS_POLICY:
                    if (attribute.name == policy['attribute'] and element.type in policy['au_type']
                        and parent_name in policy['parents'] and not attribute.has_variable and attribute.value is not None and 
                            attribute.value.lower() not in policy['values']):
                        errors.append(Error('sec_ssl_tls_policy', attribute, file, repr(attribute)))
                        break
                    
                for child in attribute.keyvalues:
                    check_attribute(child, attribute.name)

            for attribute in element.attributes:
                check_attribute(attribute, "")

        return errors