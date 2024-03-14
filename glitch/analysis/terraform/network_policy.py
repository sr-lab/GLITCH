import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


class TerraformNetworkSecurityRules(TerraformSmellChecker):
    def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
        errors = []
        if isinstance(element, AtomicUnit):
            if (element.type == "resource.azurerm_network_security_rule"):
                access = self.check_required_attribute(element.attributes, [""], "access")
                if (access and access.value.lower() == "allow"):
                    protocol = self.check_required_attribute(element.attributes, [""], "protocol")
                    if (protocol and protocol.value.lower() == "udp"):
                        errors.append(Error('sec_network_security_rules', access, file, repr(access)))
                    elif (protocol and protocol.value.lower() == "tcp"):
                        dest_port_range = self.check_required_attribute(element.attributes, [""], "destination_port_range")
                        dest_port_ranges = self.check_required_attribute(element.attributes, [""], "destination_port_ranges[0]")
                        port = False
                        if (dest_port_range and dest_port_range.value.lower() in ["22", "3389", "*"]):
                            port = True
                        if dest_port_ranges:
                            i = 1
                            while dest_port_ranges:
                                if dest_port_ranges.value.lower() in ["22", "3389", "*"]:
                                    port = True
                                    break
                                i += 1
                                dest_port_ranges = self.check_required_attribute(element.attributes, [""], f"destination_port_ranges[{i}]")
                        if port:
                            source_address_prefix = self.check_required_attribute(element.attributes, [""], "source_address_prefix")
                            if (source_address_prefix and (source_address_prefix.value.lower() in ["*", "/0", "internet", "any"] 
                                or re.match(r'^0.0.0.0', source_address_prefix.value.lower()))):
                                errors.append(Error('sec_network_security_rules', source_address_prefix, file, repr(source_address_prefix)))
            elif (element.type == "resource.azurerm_network_security_group"):
                access = self.check_required_attribute(element.attributes, ["security_rule"], "access")
                if (access and access.value.lower() == "allow"):
                    protocol = self.check_required_attribute(element.attributes, ["security_rule"], "protocol")
                    if (protocol and protocol.value.lower() == "udp"):
                        errors.append(Error('sec_network_security_rules', access, file, repr(access)))
                    elif (protocol and protocol.value.lower() == "tcp"):
                        dest_port_range = self.check_required_attribute(element.attributes, ["security_rule"], "destination_port_range")
                        if (dest_port_range and dest_port_range.value.lower() in ["22", "3389", "*"]):
                            source_address_prefix = self.check_required_attribute(element.attributes, [""], "source_address_prefix")
                            if (source_address_prefix and (source_address_prefix.value.lower() in ["*", "/0", "internet", "any"] 
                                or re.match(r'^0.0.0.0', source_address_prefix.value.lower()))):
                                errors.append(Error('sec_network_security_rules', source_address_prefix, file, repr(source_address_prefix)))

            for rule in SecurityVisitor._NETWORK_SECURITY_RULES:
                if (rule['required'] == "yes" and element.type in rule['au_type'] 
                    and not self.check_required_attribute(element.attributes, rule['parents'], rule['attribute'])):
                    errors.append(Error('sec_network_security_rules', element, file, repr(element), 
                        f"Suggestion: check for a required attribute with name '{rule['msg']}'."))
        
        elif isinstance(element, Attribute) or isinstance(element, Variable):
            for rule in SecurityVisitor._NETWORK_SECURITY_RULES:
                if (elem_name == rule['attribute'] and au_type in rule['au_type'] and parent_name in rule['parents'] 
                    and not element.has_variable and elem_value.lower() not in rule['values'] and rule['values'] != [""]):
                    return [Error('sec_network_security_rules', element, file, repr(element))]
        
        return errors