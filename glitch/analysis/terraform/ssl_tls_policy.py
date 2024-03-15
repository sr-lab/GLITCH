from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable 


class TerraformSslTlsPolicy(TerraformSmellChecker):
    def check(self, element, file: str, code, au_type = None, parent_name = ""):
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
                    
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for policy in SecurityVisitor._SSL_TLS_POLICY:
                if (element.name == policy['attribute'] and au_type in policy['au_type']
                    and parent_name in policy['parents'] and not element.has_variable 
                    and element.value.lower() not in policy['values']):
                    return [Error('sec_ssl_tls_policy', element, file, repr(element))]
        return errors