import os
import re
import json
import glitch
import configparser
from urllib.parse import urlparse
from glitch.analysis.rules import Error, RuleVisitor, SmellChecker
from nltk.tokenize import WordPunctTokenizer
from typing import Tuple, List, Optional

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.tech import Tech


class SecurityVisitor(RuleVisitor):
    __URL_REGEX = r"^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([_\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"

    class TerraformSmellChecker(SmellChecker):
        def get_au(self, c, file: str, name: str, type: str):
            if isinstance(c, Project):
                module_name = os.path.basename(os.path.dirname(file))
                for m in c.modules:
                    if m.name == module_name:
                        return self.get_au(m, file, name, type)
            elif isinstance(c, Module):
                for ub in c.blocks:
                    au = self.get_au(ub, file, name, type)
                    if au:
                        return au
            elif isinstance(c, UnitBlock):
                for au in c.atomic_units:
                    if (au.type == type and au.name == name):
                        return au
            return None

        def get_associated_au(self, code, file: str, type: str, attribute_name: str , pattern, attribute_parents: list):
            if isinstance(code, Project):
                module_name = os.path.basename(os.path.dirname(file))
                for m in code.modules:
                    if m.name == module_name:
                        return self.get_associated_au(m, file, type, attribute_name, pattern, attribute_parents)
            elif isinstance(code, Module):
                for ub in code.blocks:
                    au = self.get_associated_au(ub, file, type, attribute_name, pattern, attribute_parents)
                    if au:
                        return au
            elif isinstance(code, UnitBlock):
                for au in code.atomic_units:
                    if (au.type == type and self.check_required_attribute(
                            au.attributes, attribute_parents, attribute_name, None, pattern)):
                        return au
            return None
        
        def get_attributes_with_name_and_value(self, attributes, parents, name, value = None, pattern = None):
            aux = []
            for a in attributes:
                if a.name.split('dynamic.')[-1] == name and parents == [""]:
                    if ((value and a.value.lower() == value) or (pattern and re.match(pattern, a.value.lower()))):
                        aux.append(a)
                    elif ((value and a.value.lower() != value) or (pattern and not re.match(pattern, a.value.lower()))):
                        continue
                    elif (not value and not pattern):
                        aux.append(a)
                elif a.name.split('dynamic.')[-1] in parents:
                    aux += self.get_attributes_with_name_and_value(a.keyvalues, [""], name, value, pattern)
                elif a.keyvalues != []:
                    aux += self.get_attributes_with_name_and_value(a.keyvalues, parents, name, value, pattern)
            return aux

        def check_required_attribute(self, attributes, parents, name, value = None, pattern = None, return_all = False):
            attributes = self.get_attributes_with_name_and_value(attributes, parents, name, value, pattern)
            if attributes != []:
                if return_all:
                    return attributes
                return attributes[0]
            else:
                return None
            
        def check_database_flags(self, au: AtomicUnit, file: str, smell: str, flag_name: str, safe_value: str, 
                                 required_flag = True):
            database_flags = self.get_attributes_with_name_and_value(au.attributes, ["settings"], "database_flags")
            found_flag = False
            errors = []
            if database_flags != []:
                for flag in database_flags:
                    name = self.check_required_attribute(flag.keyvalues, [""], "name", flag_name)
                    if name:
                        found_flag = True
                        value = self.check_required_attribute(flag.keyvalues, [""], "value")
                        if value and value.value.lower() != safe_value:
                            errors.append(Error(smell, value, file, repr(value)))
                            break
                        elif not value and required_flag:
                            errors.append(Error(smell, flag, file, repr(flag), 
                                f"Suggestion: check for a required attribute with name 'value'."))
                            break
            if not found_flag and required_flag:
                errors.append(Error(smell, au, file, repr(au), 
                    f"Suggestion: check for a required flag '{flag_name}'."))
            return errors
            
    class TerraformIntegrityPolicy(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                for policy in SecurityVisitor._INTEGRITY_POLICY:
                    if (policy['required'] == "yes" and element.type in policy['au_type']
                        and not self.check_required_attribute(element.attributes, policy['parents'], policy['attribute'])):
                        errors.append(Error('sec_integrity_policy', element, file, repr(element),
                            f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for policy in SecurityVisitor._INTEGRITY_POLICY:
                    if (elem_name == policy['attribute'] and au_type in policy['au_type'] 
                        and parent_name in policy['parents'] and not element.has_variable 
                        and elem_value.lower() not in policy['values']):
                        return[Error('sec_integrity_policy', element, file, repr(element))]
            return errors
        
    class TerraformHttpWithoutTls(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "data.http"):
                    url = self.check_required_attribute(element.attributes, [""], "url")
                    if ("${" in url.value):
                        vars = url.value.split("${")
                        r = url.value.split("${")[1].split("}")[0]
                        for var in vars:
                            if "data" in var or "resource" in var:
                                r = var.split("}")[0]
                                break
                        type = r.split(".")[0]
                        if type in ["data", "resource"]:
                            resource_type = r.split(".")[1]
                            resource_name = r.split(".")[2]
                        else:
                            type = "resource"
                            resource_type = r.split(".")[0]
                            resource_name = r.split(".")[1]
                        if self.get_au(code, file, resource_name, type + "." + resource_type):
                            errors.append(Error('sec_https', url, file, repr(url)))

                for config in SecurityVisitor._HTTPS_CONFIGS:
                    if (config["required"] == "yes" and element.type in config['au_type']
                        and not self.check_required_attribute(element.attributes, config["parents"], config['attribute'])):
                        errors.append(Error('sec_https', element, file, repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                        
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._HTTPS_CONFIGS:
                    if (elem_name == config["attribute"] and au_type in config["au_type"] 
                        and parent_name in config["parents"] and not element.has_variable 
                        and elem_value.lower() not in config["values"]):
                        return [Error('sec_https', element, file, repr(element))]
            return errors

    class TerraformSslTlsPolicy(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
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
                    if (elem_name == policy['attribute'] and au_type in policy['au_type']
                        and parent_name in policy['parents'] and not element.has_variable 
                        and elem_value.lower() not in policy['values']):
                        return [Error('sec_ssl_tls_policy', element, file, repr(element))]
            return errors

    class TerraformDnsWithoutDnssec(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                for config in SecurityVisitor._DNSSEC_CONFIGS:
                    if (config['required'] == "yes" and element.type in config['au_type']
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_dnssec', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                        
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._DNSSEC_CONFIGS:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and not element.has_variable 
                        and elem_value.lower() not in config['values']
                        and config['values'] != [""]):
                        return [Error('sec_dnssec', element, file, repr(element))]
            return errors

    class TerraformPublicIp(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                for config in SecurityVisitor._PUBLIC_IP_CONFIGS:
                    if (config['required'] == "yes" and element.type in config['au_type']
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_public_ip', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    elif (config['required'] == "must_not_exist" and element.type in config['au_type']):
                        a = self.check_required_attribute(element.attributes, config['parents'], config['attribute'])
                        if a:
                            errors.append(Error('sec_public_ip', a, file, repr(a)))
                        
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._PUBLIC_IP_CONFIGS:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and not element.has_variable 
                        and elem_value.lower() not in config['values']
                        and config['values'] != [""]):
                        return [Error('sec_public_ip', element, file, repr(element))]
            return errors

    class TerraformAccessControl(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.aws_api_gateway_method"):
                    http_method = self.check_required_attribute(element.attributes, [""], 'http_method')
                    authorization =self.check_required_attribute(element.attributes, [""], 'authorization')
                    if (http_method and authorization):
                        if (http_method.value.lower() == 'get' and authorization.value.lower() == 'none'):
                            api_key_required = self.check_required_attribute(element.attributes, [""], 'api_key_required')
                            if api_key_required and f"{api_key_required.value}".lower() != 'true':
                                errors.append(Error('sec_access_control', api_key_required, file, repr(api_key_required)))
                            elif not api_key_required:
                                errors.append(Error('sec_access_control', element, file, repr(element), 
                                f"Suggestion: check for a required attribute with name 'api_key_required'."))
                    elif (http_method and not authorization):
                            errors.append(Error('sec_access_control', element, file, repr(element), 
                                f"Suggestion: check for a required attribute with name 'authorization'."))
                elif (element.type == "resource.github_repository"):
                    visibility = self.check_required_attribute(element.attributes, [""], 'visibility')
                    if visibility:
                        if visibility.value.lower() not in ["private", "internal"]:
                            errors.append(Error('sec_access_control', visibility, file, repr(visibility)))
                    else:
                        private = self.check_required_attribute(element.attributes, [""], 'private')
                        if private:
                            if f"{private.value}".lower() != "true":
                                errors.append(Error('sec_access_control', private, file, repr(private)))
                        else:
                            errors.append(Error('sec_access_control', element, file, repr(element), 
                                f"Suggestion: check for a required attribute with name 'visibility' or 'private'."))
                elif (element.type == "resource.google_sql_database_instance"):
                    errors += self.check_database_flags(element, file, 'sec_access_control', "cross db ownership chaining", "off")
                elif (element.type == "resource.aws_s3_bucket"):
                    expr = "\${aws_s3_bucket\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    if not self.get_associated_au(code, file, "resource.aws_s3_bucket_public_access_block", "bucket", pattern, [""]):
                        errors.append(Error('sec_access_control', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'aws_s3_bucket_public_access_block' " + 
                                f"associated to an 'aws_s3_bucket' resource."))

                for config in SecurityVisitor._ACCESS_CONTROL_CONFIGS:
                    if (config['required'] == "yes" and element.type in config['au_type']
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_access_control', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                        
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for item in SecurityVisitor._POLICY_KEYWORDS:
                    if item.lower() == elem_name:
                        for config in SecurityVisitor._POLICY_ACCESS_CONTROL:
                            expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                            pattern = re.compile(rf"{expr}")
                            allow_expr = "\"effect\":" + "\s*" + "\"allow\""
                            allow_pattern = re.compile(rf"{allow_expr}")
                            if re.search(pattern, elem_value) and re.search(allow_pattern, elem_value):
                                errors.append(Error('sec_access_control', element, file, repr(element)))
                                break

                if (re.search(r"actions\[\d+\]", elem_name) and parent_name == "permissions" 
                    and au_type == "resource.azurerm_role_definition" and elem_value == "*"):
                    errors.append(Error('sec_access_control', element, file, repr(element)))
                elif (((re.search(r"members\[\d+\]", elem_name) and au_type == "resource.google_storage_bucket_iam_binding")
                    or (elem_name == "member" and au_type == "resource.google_storage_bucket_iam_member"))
                    and (elem_value == "allusers" or elem_value == "allauthenticatedusers")):
                    errors.append(Error('sec_access_control', element, file, repr(element)))
                elif (elem_name == "email" and parent_name == "service_account" 
                    and au_type == "resource.google_compute_instance"
                    and re.search(r".-compute@developer.gserviceaccount.com", elem_value)):
                    errors.append(Error('sec_access_control', element, file, repr(element)))

                for config in SecurityVisitor._ACCESS_CONTROL_CONFIGS:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and not element.has_variable 
                        and elem_value.lower() not in config['values']
                        and config['values'] != [""]):
                        errors.append(Error('sec_access_control', element, file, repr(element)))
                        break
            return errors

    class TerraformAuthentication(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.google_sql_database_instance"):
                    errors += self.check_database_flags(element, file, 'sec_authentication', "contained database authentication", "off")
                elif (element.type == "resource.aws_iam_group"):
                    expr = "\${aws_iam_group\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    if not self.get_associated_au(code, file, "resource.aws_iam_group_policy", "group", pattern, [""]):
                        errors.append(Error('sec_authentication', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'aws_iam_group_policy' associated to an " +
                                f"'aws_iam_group' resource."))

                for config in SecurityVisitor._AUTHENTICATION:
                    if (config['required'] == "yes" and element.type in config['au_type']
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_authentication', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for item in SecurityVisitor._POLICY_KEYWORDS:
                    if item.lower() == elem_name:        
                        for config in SecurityVisitor._POLICY_AUTHENTICATION:
                            if au_type in config['au_type']:
                                expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                                pattern = re.compile(rf"{expr}")
                                if not re.search(pattern, elem_value):
                                    errors.append(Error('sec_authentication', element, file, repr(element)))

                for config in SecurityVisitor._AUTHENTICATION:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and not element.has_variable 
                        and elem_value.lower() not in config['values']
                        and config['values'] != [""]):
                        errors.append(Error('sec_authentication', element, file, repr(element)))
                        break
            return errors

    class TerraformMissingEncryption(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.aws_s3_bucket"):
                    expr = "\${aws_s3_bucket\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    r = self.get_associated_au(code, file, "resource.aws_s3_bucket_server_side_encryption_configuration", 
                        "bucket", pattern, [""])
                    if not r:
                        errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'aws_s3_bucket_server_side_encryption_configuration' " + 
                                f"associated to an 'aws_s3_bucket' resource."))
                elif (element.type == "resource.aws_eks_cluster"):
                    resources = self.check_required_attribute(element.attributes, ["encryption_config"], "resources[0]")
                    if resources:
                        i = 0
                        valid = False
                        while resources:
                            a = resources
                            if resources.value.lower() == "secrets":
                                valid = True
                                break
                            i += 1
                            resources = self.check_required_attribute(element.attributes, ["encryption_config"], f"resources[{i}]")
                        if not valid:
                            errors.append(Error('sec_missing_encryption', a, file, repr(a)))
                    else:
                        errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'encryption_config.resources'."))
                elif (element.type in ["resource.aws_instance", "resource.aws_launch_configuration"]):
                    ebs_block_device = self.check_required_attribute(element.attributes, [""], "ebs_block_device")
                    if ebs_block_device:
                        encrypted = self.check_required_attribute(ebs_block_device.keyvalues, [""], "encrypted")
                        if not encrypted:
                            errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'ebs_block_device.encrypted'."))
                elif (element.type == "resource.aws_ecs_task_definition"):
                    volume = self.check_required_attribute(element.attributes, [""], "volume")
                    if volume:
                        efs_volume_config = self.check_required_attribute(volume.keyvalues, [""], "efs_volume_configuration")
                        if efs_volume_config:
                            transit_encryption = self.check_required_attribute(efs_volume_config.keyvalues, [""], "transit_encryption")
                            if not transit_encryption:
                                errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                                f"Suggestion: check for a required attribute with name" +
                                    f"'volume.efs_volume_configuration.transit_encryption'."))

                for config in SecurityVisitor._MISSING_ENCRYPTION:
                    if (config['required'] == "yes" and element.type in config['au_type']
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_missing_encryption', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                        
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._MISSING_ENCRYPTION:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and elem_value.lower() == ""):
                            errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                            break
                        elif ("any_not_empty" not in config['values'] and not element.has_variable 
                            and elem_value.lower() not in config['values']):
                            errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                            break

                for item in SecurityVisitor._CONFIGURATION_KEYWORDS:
                    if item.lower() == elem_name:
                        for config in SecurityVisitor._ENCRYPT_CONFIG:
                            if au_type in config['au_type']:
                                expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                                pattern = re.compile(rf"{expr}")
                                if not re.search(pattern, elem_value) and config['required'] == "yes":
                                    errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                                    break
                                elif re.search(pattern, elem_value) and config['required'] == "must_not_exist":
                                    errors.append(Error('sec_missing_encryption', element, file, repr(element)))
                                    break
            return errors

    class TerraformFirewallMisconfig(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                for config in SecurityVisitor._FIREWALL_CONFIGS:
                    if (config['required'] == "yes" and element.type in config['au_type'] 
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_firewall_misconfig', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._FIREWALL_CONFIGS:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and elem_value.lower() == ""):
                            return [Error('sec_firewall_misconfig', element, file, repr(element))]
                        elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                            elem_value.lower() not in config['values']):
                            return [Error('sec_firewall_misconfig', element, file, repr(element))]
            return errors

    class TerraformThreatsDetection(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                for config in SecurityVisitor._MISSING_THREATS_DETECTION_ALERTS:
                    if (config['required'] == "yes" and element.type in config['au_type']
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_threats_detection_alerts', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                    elif (config['required'] == "must_not_exist" and element.type in config['au_type']):
                        a = self.check_required_attribute(element.attributes, config['parents'], config['attribute'])
                        if a:
                            errors.append(Error('sec_threats_detection_alerts', a, file, repr(a)))

            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._MISSING_THREATS_DETECTION_ALERTS:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and elem_value.lower() == ""):
                            return [Error('sec_threats_detection_alerts', element, file, repr(element))]
                        elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                            elem_value.lower() not in config['values']):
                            return [Error('sec_threats_detection_alerts', element, file, repr(element))]
            return errors

    class TerraformWeakPasswordKeyPolicy(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                for policy in SecurityVisitor._PASSWORD_KEY_POLICY:
                    if (policy['required'] == "yes" and element.type in policy['au_type'] 
                        and not self.check_required_attribute(element.attributes, policy['parents'], policy['attribute'])):
                        errors.append(Error('sec_weak_password_key_policy', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{policy['msg']}'."))

            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for policy in SecurityVisitor._PASSWORD_KEY_POLICY:
                    if (elem_name == policy['attribute'] and au_type in policy['au_type']
                        and parent_name in policy['parents'] and policy['values'] != [""]):
                        if (policy['logic'] == "equal"):
                            if ("any_not_empty" in policy['values'] and elem_value.lower() == ""):
                                return [Error('sec_weak_password_key_policy', element, file, repr(element))]
                            elif ("any_not_empty" not in policy['values'] and not element.has_variable and 
                                elem_value.lower() not in policy['values']):
                                return [Error('sec_weak_password_key_policy', element, file, repr(element))]
                        elif ((policy['logic'] == "gte" and not elem_value.isnumeric()) or
                            (policy['logic'] == "gte" and elem_value.isnumeric() 
                             and int(elem_value) < int(policy['values'][0]))):
                            return [Error('sec_weak_password_key_policy', element, file, repr(element))]
                        elif ((policy['logic'] == "lte" and not elem_value.isnumeric()) or
                            (policy['logic'] == "lte" and elem_value.isnumeric() 
                             and int(elem_value) > int(policy['values'][0]))):
                            return [Error('sec_weak_password_key_policy', element, file, repr(element))]

            return errors

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
                    if statements:
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
                    if policy:
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
            
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                pass
            
            return errors

    class TerraformKeyManagement(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.azurerm_storage_account"):
                    expr = "\${azurerm_storage_account\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    if not self.get_associated_au(code, file, "resource.azurerm_storage_account_customer_managed_key", "storage_account_id",
                        pattern, [""]):
                        errors.append(Error('sec_key_management', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'azurerm_storage_account_customer_managed_key' " + 
                                f"associated to an 'azurerm_storage_account' resource."))
                for config in SecurityVisitor._KEY_MANAGEMENT:
                    if (config['required'] == "yes" and element.type in config['au_type'] 
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_key_management', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                        
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._KEY_MANAGEMENT:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and elem_value.lower() == ""):
                            errors.append(Error('sec_key_management', element, file, repr(element)))
                            break
                        elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                            elem_value.lower() not in config['values']):
                            errors.append(Error('sec_key_management', element, file, repr(element)))
                            break

                if (elem_name == "rotation_period" and au_type == "resource.google_kms_crypto_key"):
                    expr1 = r'\d+\.\d{0,9}s'
                    expr2 = r'\d+s'
                    if (re.search(expr1, elem_value) or re.search(expr2, elem_value)):
                        if (int(elem_value.split("s")[0]) > 7776000):
                            errors.append(Error('sec_key_management', element, file, repr(element)))
                    else:
                        errors.append(Error('sec_key_management', element, file, repr(element)))
                elif (elem_name == "kms_master_key_id" and ((au_type == "resource.aws_sqs_queue"
                    and elem_value == "alias/aws/sqs") or  (au_type == "resource.aws_sns_queue"
                    and elem_value == "alias/aws/sns"))):
                    errors.append(Error('sec_key_management', element, file, repr(element)))
            return errors

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

    class TerraformPermissionIAMPolicies(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.aws_iam_user"):
                    expr = "\${aws_iam_user\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    assoc_au = self.get_associated_au(code, file, "resource.aws_iam_user_policy", "user", pattern, [""])
                    if assoc_au:
                        a = self.check_required_attribute(assoc_au.attributes, [""], "user", None, pattern) 
                        errors.append(Error('sec_permission_iam_policies', a, file, repr(a)))

            elif isinstance(element, Attribute) or isinstance(element, Variable):
                if ((elem_name == "member" or elem_name.split('[')[0] == "members") 
                    and au_type in SecurityVisitor._GOOGLE_IAM_MEMBER
                    and (re.search(r".-compute@developer.gserviceaccount.com", elem_value) or 
                        re.search(r".@appspot.gserviceaccount.com", elem_value) or
                        re.search(r"user:", elem_value))):
                    errors.append(Error('sec_permission_iam_policies', element, file, repr(element)))

                for config in SecurityVisitor._PERMISSION_IAM_POLICIES:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ((config['logic'] == "equal" and not element.has_variable and elem_value.lower() not in config['values'])
                            or (config['logic'] == "diff" and elem_value.lower() in config['values'])):
                            errors.append(Error('sec_permission_iam_policies', element, file, repr(element)))
                            break
            return errors
        
    class TerraformLogging(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.aws_eks_cluster"):
                    enabled_cluster_log_types = self.check_required_attribute(element.attributes, [""], "enabled_cluster_log_types[0]")
                    types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
                    if enabled_cluster_log_types:
                        i = 0
                        while enabled_cluster_log_types:
                            a = enabled_cluster_log_types
                            if enabled_cluster_log_types.value.lower() in types:
                                types.remove(enabled_cluster_log_types.value.lower())
                            i += 1
                            enabled_cluster_log_types = self.check_required_attribute(element.attributes, [""], f"enabled_cluster_log_types[{i}]")
                        if types != []:
                            errors.append(Error('sec_logging', a, file, repr(a), 
                            f"Suggestion: check for additional log type(s) {types}."))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'enabled_cluster_log_types'."))
                elif (element.type == "resource.aws_msk_cluster"):
                    broker_logs = self.check_required_attribute(element.attributes, ["logging_info"], "broker_logs")
                    if broker_logs:
                        active = False
                        logs_type = ["cloudwatch_logs", "firehose", "s3"]
                        a_list = []
                        for type in logs_type:
                            log = self.check_required_attribute(broker_logs.keyvalues, [""], type)
                            if log:
                                enabled = self.check_required_attribute(log.keyvalues, [""], "enabled")
                                if enabled and f"{enabled.value}".lower() == "true":
                                    active = True
                                elif enabled and f"{enabled.value}".lower() != "true":
                                    a_list.append(enabled)
                        if not active and a_list == []:
                            errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name " +
                            f"'logging_info.broker_logs.[cloudwatch_logs/firehose/s3].enabled'."))
                        if not active and a_list != []:
                            for a in a_list:
                                errors.append(Error('sec_logging', a, file, repr(a)))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name " +
                            f"'logging_info.broker_logs.[cloudwatch_logs/firehose/s3].enabled'."))
                elif (element.type == "resource.aws_neptune_cluster"):
                    active = False
                    enable_cloudwatch_logs_exports = self.check_required_attribute(element.attributes, [""], f"enable_cloudwatch_logs_exports[0]")
                    if enable_cloudwatch_logs_exports:
                        i = 0
                        while enable_cloudwatch_logs_exports:
                            a = enable_cloudwatch_logs_exports
                            if enable_cloudwatch_logs_exports.value.lower() == "audit":
                                active  = True
                                break
                            i += 1
                            enable_cloudwatch_logs_exports = self.check_required_attribute(element.attributes, [""], f"enable_cloudwatch_logs_exports[{i}]")
                        if not active:
                            errors.append(Error('sec_logging', a, file, repr(a)))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'enable_cloudwatch_logs_exports'."))
                elif (element.type == "resource.aws_docdb_cluster"):
                    active = False
                    enabled_cloudwatch_logs_exports = self.check_required_attribute(element.attributes, [""], f"enabled_cloudwatch_logs_exports[0]")
                    if enabled_cloudwatch_logs_exports:
                        i = 0
                        while enabled_cloudwatch_logs_exports:
                            a = enabled_cloudwatch_logs_exports
                            if enabled_cloudwatch_logs_exports.value.lower() in ["audit", "profiler"]:
                                active  = True
                                break
                            i += 1
                            enabled_cloudwatch_logs_exports = self.check_required_attribute(element.attributes, [""], f"enabled_cloudwatch_logs_exports[{i}]")
                        if not active:
                            errors.append(Error('sec_logging', a, file, repr(a)))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'enabled_cloudwatch_logs_exports'."))
                elif (element.type == "resource.azurerm_mssql_server"):
                    expr = "\${azurerm_mssql_server\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    assoc_au = self.get_associated_au(code, file, "resource.azurerm_mssql_server_extended_auditing_policy", 
                        "server_id", pattern, [""])
                    if not assoc_au:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'azurerm_mssql_server_extended_auditing_policy' " + 
                            f"associated to an 'azurerm_mssql_server' resource."))
                elif (element.type == "resource.azurerm_mssql_database"):
                    expr = "\${azurerm_mssql_database\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    assoc_au = self.get_associated_au(code, file, "resource.azurerm_mssql_database_extended_auditing_policy", 
                        "database_id", pattern, [""])
                    if not assoc_au:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'azurerm_mssql_database_extended_auditing_policy' " + 
                            f"associated to an 'azurerm_mssql_database' resource."))
                elif (element.type == "resource.azurerm_postgresql_configuration"):
                    name = self.check_required_attribute(element.attributes, [""], "name")
                    value = self.check_required_attribute(element.attributes, [""], "value")
                    if (name and name.value.lower() in ["log_connections", "connection_throttling", "log_checkpoints"] 
                        and value and value.value.lower() != "on"):
                        errors.append(Error('sec_logging', value, file, repr(value)))
                elif (element.type == "resource.azurerm_monitor_log_profile"):
                    categories = self.check_required_attribute(element.attributes, [""], "categories[0]")
                    activities = [ "action", "delete", "write"]
                    if categories:
                        i = 0
                        while categories:
                            a = categories
                            if categories.value.lower() in activities:
                                activities.remove(categories.value.lower())
                            i += 1
                            categories = self.check_required_attribute(element.attributes, [""], f"categories[{i}]")
                        if activities != []:
                            errors.append(Error('sec_logging', a, file, repr(a), 
                            f"Suggestion: check for additional activity type(s) {activities}."))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'categories'."))
                elif (element.type == "resource.google_sql_database_instance"):
                    for flag in SecurityVisitor._GOOGLE_SQL_DATABASE_LOG_FLAGS:
                        required_flag = True
                        if flag['required'] == "no":
                            required_flag = False
                        errors += self.check_database_flags(element, file, 'sec_logging', flag['flag_name'], flag['value'], required_flag)
                elif (element.type == "resource.azurerm_storage_container"):
                    storage_account_name = self.check_required_attribute(element.attributes, [""], "storage_account_name")
                    if storage_account_name and storage_account_name.value.lower().startswith("${azurerm_storage_account."):
                        name = storage_account_name.value.lower().split('.')[1]
                        storage_account_au = self.get_au(code, file, name, "resource.azurerm_storage_account")
                        if storage_account_au:
                            expr = "\${azurerm_storage_account\." + f"{name}\."
                            pattern = re.compile(rf"{expr}")
                            assoc_au = self.get_associated_au(code, file, "resource.azurerm_log_analytics_storage_insights",
                                "storage_account_id", pattern, [""])
                            if assoc_au:
                                blob_container_names = self.check_required_attribute(assoc_au.attributes, [""], "blob_container_names[0]")
                                if blob_container_names:
                                    i = 0
                                    contains_blob_name = False
                                    while blob_container_names:
                                        a = blob_container_names
                                        if blob_container_names.value:
                                            contains_blob_name = True
                                            break
                                        i += 1
                                        blob_container_names = self.check_required_attribute(assoc_au.attributes, [""], f"blob_container_names[{i}]")
                                    if not contains_blob_name:
                                        errors.append(Error('sec_logging', a, file, repr(a)))
                                else:
                                    errors.append(Error('sec_logging', assoc_au, file, repr(assoc_au), 
                                    f"Suggestion: check for a required attribute with name 'blob_container_names'."))
                            else:
                                errors.append(Error('sec_logging', storage_account_au, file, repr(storage_account_au), 
                                    f"Suggestion: check for a required resource 'azurerm_log_analytics_storage_insights' " + 
                                    f"associated to an 'azurerm_storage_account' resource."))
                        else:
                            errors.append(Error('sec_logging', element, file, repr(element), 
                                f"Suggestion: 'azurerm_storage_container' resource has to be associated to an " + 
                                f"'azurerm_storage_account' resource in order to enable logging."))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: 'azurerm_storage_container' resource has to be associated to an " + 
                            f"'azurerm_storage_account' resource in order to enable logging."))
                    container_access_type = self.check_required_attribute(element.attributes, [""], "container_access_type")
                    if container_access_type and container_access_type.value.lower() not in ["blob", "private"]:
                        errors.append(Error('sec_logging', container_access_type, file, repr(container_access_type)))
                elif (element.type == "resource.aws_ecs_cluster"):
                    name = self.check_required_attribute(element.attributes, ["setting"], "name", "containerinsights")
                    if name:
                        enabled = self.check_required_attribute(element.attributes, ["setting"], "value")
                        if enabled:
                            if enabled.value.lower() != "enabled":
                                errors.append(Error('sec_logging', enabled, file, repr(enabled)))
                        else:
                            errors.append(Error('sec_logging', element, file, repr(element), 
                                f"Suggestion: check for a required attribute with name 'setting.value'."))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            "Suggestion: check for a required attribute with name 'setting.name' and value 'containerInsights'."))
                elif (element.type == "resource.aws_vpc"):
                    expr = "\${aws_vpc\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    assoc_au = self.get_associated_au(code, file, "resource.aws_flow_log",
                                "vpc_id", pattern, [""])
                    if not assoc_au:
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'aws_flow_log' " + 
                            f"associated to an 'aws_vpc' resource."))

                for config in SecurityVisitor._LOGGING:
                    if (config['required'] == "yes" and element.type in config['au_type'] 
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_logging', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))  
                           
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                if (elem_name == "cloud_watch_logs_group_arn" and au_type == "resource.aws_cloudtrail"):
                    if re.match(r"^\${aws_cloudwatch_log_group\..", elem_value):
                        aws_cloudwatch_log_group_name = elem_value.split('.')[1]
                        if not self.get_au(code, file, aws_cloudwatch_log_group_name, "resource.aws_cloudwatch_log_group"):
                            errors.append(Error('sec_logging', element, file, repr(element),
                                f"Suggestion: check for a required resource 'aws_cloudwatch_log_group' " +
                                f"with name '{aws_cloudwatch_log_group_name}'."))
                    else:
                        errors.append(Error('sec_logging', element, file, repr(element)))
                elif (((elem_name == "retention_in_days" and parent_name == "" 
                    and au_type in ["resource.azurerm_mssql_database_extended_auditing_policy", 
                    "resource.azurerm_mssql_server_extended_auditing_policy"]) 
                    or (elem_name == "days" and parent_name == "retention_policy" 
                    and au_type == "resource.azurerm_network_watcher_flow_log")) 
                    and ((not elem_value.isnumeric()) or (elem_value.isnumeric() and int(elem_value) < 90))):
                    errors.append(Error('sec_logging', element, file, repr(element)))
                elif (elem_name == "days" and parent_name == "retention_policy" 
                    and au_type == "resource.azurerm_monitor_log_profile" 
                    and (not elem_value.isnumeric() or (elem_value.isnumeric() and int(elem_value) < 365))):
                    errors.append(Error('sec_logging', element, file, repr(element)))

                for config in SecurityVisitor._LOGGING:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and elem_value.lower() == ""):
                            errors.append(Error('sec_logging', element, file, repr(element)))
                            break
                        elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                            elem_value.lower() not in config['values']):
                            errors.append(Error('sec_logging', element, file, repr(element)))
                            break
            return errors
        
    class TerraformAttachedResource(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                def check_attached_resource(attributes, resource_types):
                    for a in attributes:
                        if a.value != None:
                            for resource_type in resource_types:
                                if (f"{a.value}".lower().startswith("${" + f"{resource_type}.") 
                                    or f"{a.value}".lower().startswith(f"{resource_type}.")):
                                    resource_name = a.value.lower().split(".")[1]
                                    if self.get_au(code, file, resource_name, f"resource.{resource_type}"):
                                        return True
                        elif a.value == None:
                            attached = check_attached_resource(a.keyvalues, resource_types)
                            if attached:
                                return True
                    return False

                if (element.type == "resource.aws_route53_record"):
                    type_A = self.check_required_attribute(element.attributes, [""], "type", "a")
                    if type_A and not check_attached_resource(element.attributes, SecurityVisitor._POSSIBLE_ATTACHED_RESOURCES):
                        errors.append(Error('sec_attached_resource', element, file, repr(element)))

            elif isinstance(element, Attribute) or isinstance(element, Variable):
                pass
            return errors
        
    class TerraformVersioning(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                for config in SecurityVisitor._VERSIONING:
                    if (config['required'] == "yes" and element.type in config['au_type'] 
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_versioning', element, file, repr(element), 
                                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._VERSIONING:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]
                        and not element.has_variable and elem_value.lower() not in config['values']):
                        return [Error('sec_versioning', element, file, repr(element))]
            return errors
        
    class TerraformNaming(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.aws_security_group"):
                    ingress = self.check_required_attribute(element.attributes, [""], "ingress")
                    egress = self.check_required_attribute(element.attributes, [""], "egress")
                    if ingress and not self.check_required_attribute(ingress.keyvalues, [""], "description"):
                        errors.append(Error('sec_naming', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'ingress.description'."))
                    if egress and not self.check_required_attribute(egress.keyvalues, [""], "description"):
                        errors.append(Error('sec_naming', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'egress.description'."))
                elif (element.type == "resource.google_container_cluster"):
                    resource_labels = self.check_required_attribute(element.attributes, [""], "resource_labels", None)
                    if resource_labels and resource_labels.value == None:
                        if resource_labels.keyvalues == []:
                            errors.append(Error('sec_naming', resource_labels, file, repr(resource_labels), 
                                f"Suggestion: check empty 'resource_labels'."))
                    else:
                        errors.append(Error('sec_naming', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name 'resource_labels'."))

                for config in SecurityVisitor._NAMING:
                    if (config['required'] == "yes" and element.type in config['au_type'] 
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_naming', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                        
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                if (elem_name == "name" and au_type in ["resource.azurerm_storage_account"]):
                    pattern = r'^[a-z0-9]{3,24}$'
                    if not re.match(pattern, elem_value):
                        errors.append(Error('sec_naming', element, file, repr(element)))

                for config in SecurityVisitor._NAMING:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]):
                        if ("any_not_empty" in config['values'] and elem_value.lower() == ""):
                            errors.append(Error('sec_naming', element, file, repr(element)))
                            break
                        elif ("any_not_empty" not in config['values'] and not element.has_variable and 
                            elem_value.lower() not in config['values']):
                            errors.append(Error('sec_naming', element, file, repr(element)))
                            break
            return errors
        
    class TerraformReplication(TerraformSmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            errors = []
            if isinstance(element, AtomicUnit):
                if (element.type == "resource.aws_s3_bucket"):
                    expr = "\${aws_s3_bucket\." + f"{elem_name}\."
                    pattern = re.compile(rf"{expr}")
                    if not self.get_associated_au(code, file, "resource.aws_s3_bucket_replication_configuration", 
                        "bucket", pattern, [""]):
                        errors.append(Error('sec_replication', element, file, repr(element), 
                            f"Suggestion: check for a required resource 'aws_s3_bucket_replication_configuration' " + 
                                f"associated to an 'aws_s3_bucket' resource."))

                for config in SecurityVisitor._REPLICATION:
                    if (config['required'] == "yes" and element.type in config['au_type'] 
                        and not self.check_required_attribute(element.attributes, config['parents'], config['attribute'])):
                        errors.append(Error('sec_replication', element, file, repr(element), 
                            f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            
            elif isinstance(element, Attribute) or isinstance(element, Variable):
                for config in SecurityVisitor._REPLICATION:
                    if (elem_name == config['attribute'] and au_type in config['au_type']
                        and parent_name in config['parents'] and config['values'] != [""]
                        and not element.has_variable and elem_value.lower() not in config['values']):
                        return [Error('sec_replication', element, file, repr(element))]
            return errors

    class EmptyChecker(SmellChecker):
        def check(self, element, file: str, code, elem_name: str, elem_value: str = "", au_type = None, parent_name = ""):
            return []

    class NonOfficialImageSmell(SmellChecker):
        def check(self, element, file: str) -> List[Error]:
            return []

    class DockerNonOfficialImageSmell(SmellChecker):
        def check(self, element, file: str) -> List[Error]:
            if not isinstance(element, UnitBlock) or \
                    element.name is None or "Dockerfile" in element.name:
                return []
            image = element.name.split(":")
            if image[0] not in SecurityVisitor._DOCKER_OFFICIAL_IMAGES:
                return [Error('sec_non_official_image', element, file, repr(element))]
            return []

    def __init__(self, tech: Tech) -> None:
        super().__init__(tech)

        if tech == Tech.terraform:
            self.integrity_policy = SecurityVisitor.TerraformIntegrityPolicy()
            self.https = SecurityVisitor.TerraformHttpWithoutTls()
            self.ssl_tls_policy = SecurityVisitor.TerraformSslTlsPolicy()
            self.dnssec = SecurityVisitor.TerraformDnsWithoutDnssec()
            self.public_ip = SecurityVisitor.TerraformPublicIp()
            self.access_control = SecurityVisitor.TerraformAccessControl()
            self.authentication = SecurityVisitor.TerraformAuthentication()
            self.missing_encryption = SecurityVisitor.TerraformMissingEncryption()
            self.firewall_misconfig = SecurityVisitor.TerraformFirewallMisconfig()
            self.threats_detection = SecurityVisitor.TerraformThreatsDetection()
            self.weak_password_key_policy = SecurityVisitor.TerraformWeakPasswordKeyPolicy()
            self.sensitive_iam_action = SecurityVisitor.TerraformSensitiveIAMAction()
            self.key_management = SecurityVisitor.TerraformKeyManagement()
            self.network_security_rules = SecurityVisitor.TerraformNetworkSecurityRules()
            self.permission_iam_policies = SecurityVisitor.TerraformPermissionIAMPolicies()
            self.logging = SecurityVisitor.TerraformLogging()
            self.attached_resource = SecurityVisitor.TerraformAttachedResource()
            self.versioning = SecurityVisitor.TerraformVersioning()
            self.naming = SecurityVisitor.TerraformNaming()
            self.replication = SecurityVisitor.TerraformReplication()
        else:
            self.integrity_policy = SecurityVisitor.EmptyChecker()
            self.https = SecurityVisitor.EmptyChecker()
            self.ssl_tls_policy = SecurityVisitor.EmptyChecker()
            self.dnssec = SecurityVisitor.EmptyChecker()
            self.public_ip = SecurityVisitor.EmptyChecker()
            self.access_control = SecurityVisitor.EmptyChecker()
            self.authentication = SecurityVisitor.EmptyChecker()
            self.missing_encryption = SecurityVisitor.EmptyChecker()
            self.firewall_misconfig = SecurityVisitor.EmptyChecker()
            self.threats_detection = SecurityVisitor.EmptyChecker()
            self.weak_password_key_policy = SecurityVisitor.EmptyChecker()
            self.sensitive_iam_action = SecurityVisitor.EmptyChecker()
            self.key_management = SecurityVisitor.EmptyChecker()
            self.network_security_rules = SecurityVisitor.EmptyChecker()
            self.permission_iam_policies = SecurityVisitor.EmptyChecker()
            self.logging = SecurityVisitor.EmptyChecker()
            self.attached_resource = SecurityVisitor.EmptyChecker()
            self.versioning = SecurityVisitor.EmptyChecker()
            self.naming = SecurityVisitor.EmptyChecker()
            self.replication = SecurityVisitor.EmptyChecker()
        
        if tech == Tech.docker:
            self.non_off_img = SecurityVisitor.DockerNonOfficialImageSmell()
        else:
            self.non_off_img = SecurityVisitor.NonOfficialImageSmell()

    @staticmethod
    def get_name() -> str:
        return "security"

    def config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path)
        SecurityVisitor.__WRONG_WORDS = json.loads(config['security']['suspicious_words'])
        SecurityVisitor.__PASSWORDS = json.loads(config['security']['passwords'])
        SecurityVisitor.__USERS = json.loads(config['security']['users'])
        SecurityVisitor.__PROFILE = json.loads(config['security']['profile'])
        SecurityVisitor.__SECRETS = json.loads(config['security']['secrets'])
        SecurityVisitor.__MISC_SECRETS = json.loads(config['security']['misc_secrets'])
        SecurityVisitor.__ROLES = json.loads(config['security']['roles'])
        SecurityVisitor.__DOWNLOAD = json.loads(config['security']['download_extensions'])
        SecurityVisitor.__SSH_DIR = json.loads(config['security']['ssh_dirs'])
        SecurityVisitor.__ADMIN = json.loads(config['security']['admin'])
        SecurityVisitor.__CHECKSUM = json.loads(config['security']['checksum'])
        SecurityVisitor.__CRYPT = json.loads(config['security']['weak_crypt'])
        SecurityVisitor.__CRYPT_WHITELIST = json.loads(config['security']['weak_crypt_whitelist'])
        SecurityVisitor.__URL_WHITELIST = json.loads(config['security']['url_http_white_list'])
        SecurityVisitor.__SECRETS_WHITELIST = json.loads(config['security']['secrets_white_list'])
        SecurityVisitor.__SENSITIVE_DATA = json.loads(config['security']['sensitive_data'])
        SecurityVisitor.__SECRET_ASSIGN = json.loads(config['security']['secret_value_assign'])
        SecurityVisitor.__GITHUB_ACTIONS = json.loads(config['security']['github_actions_resources'])
        
        if self.tech == Tech.terraform:
            SecurityVisitor._INTEGRITY_POLICY = json.loads(config['security']['integrity_policy'])
            SecurityVisitor._HTTPS_CONFIGS = json.loads(config['security']['ensure_https'])
            SecurityVisitor._SSL_TLS_POLICY = json.loads(config['security']['ssl_tls_policy'])
            SecurityVisitor._DNSSEC_CONFIGS = json.loads(config['security']['ensure_dnssec'])
            SecurityVisitor._PUBLIC_IP_CONFIGS = json.loads(config['security']['use_public_ip'])
            SecurityVisitor._POLICY_KEYWORDS = json.loads(config['security']['policy_keywords'])
            SecurityVisitor._ACCESS_CONTROL_CONFIGS = json.loads(config['security']['insecure_access_control'])
            SecurityVisitor._AUTHENTICATION = json.loads(config['security']['authentication'])
            SecurityVisitor._POLICY_ACCESS_CONTROL = json.loads(config['security']['policy_insecure_access_control'])
            SecurityVisitor._POLICY_AUTHENTICATION = json.loads(config['security']['policy_authentication'])
            SecurityVisitor._MISSING_ENCRYPTION = json.loads(config['security']['missing_encryption'])
            SecurityVisitor._CONFIGURATION_KEYWORDS = json.loads(config['security']['configuration_keywords'])
            SecurityVisitor._ENCRYPT_CONFIG = json.loads(config['security']['encrypt_configuration'])
            SecurityVisitor._FIREWALL_CONFIGS = json.loads(config['security']['firewall'])
            SecurityVisitor._MISSING_THREATS_DETECTION_ALERTS = json.loads(config['security']['missing_threats_detection_alerts'])
            SecurityVisitor._PASSWORD_KEY_POLICY = json.loads(config['security']['password_key_policy'])
            SecurityVisitor._KEY_MANAGEMENT = json.loads(config['security']['key_management'])
            SecurityVisitor._NETWORK_SECURITY_RULES = json.loads(config['security']['network_security_rules'])
            SecurityVisitor._PERMISSION_IAM_POLICIES = json.loads(config['security']['permission_iam_policies'])
            SecurityVisitor._GOOGLE_IAM_MEMBER = json.loads(config['security']['google_iam_member_resources'])
            SecurityVisitor._LOGGING = json.loads(config['security']['logging'])
            SecurityVisitor._GOOGLE_SQL_DATABASE_LOG_FLAGS = json.loads(config['security']['google_sql_database_log_flags'])
            SecurityVisitor._POSSIBLE_ATTACHED_RESOURCES = json.loads(config['security']['possible_attached_resources_aws_route53'])
            SecurityVisitor._VERSIONING = json.loads(config['security']['versioning'])
            SecurityVisitor._NAMING = json.loads(config['security']['naming'])
            SecurityVisitor._REPLICATION = json.loads(config['security']['replication'])
        
        SecurityVisitor.__FILE_COMMANDS = json.loads(config['security']['file_commands'])
        SecurityVisitor.__DOWNLOAD_COMMANDS = json.loads(config['security']['download_commands'])
        SecurityVisitor.__SHELL_RESOURCES = json.loads(config['security']['shell_resources'])
        SecurityVisitor.__IP_BIND_COMMANDS = json.loads(config['security']['ip_binding_commands'])
        SecurityVisitor.__OBSOLETE_COMMANDS = self._load_data_file("obsolete_commands")
        SecurityVisitor._DOCKER_OFFICIAL_IMAGES = self._load_data_file("official_docker_images")

    @staticmethod
    def _load_data_file(file: str) -> List[str]:
        folder_path = os.path.dirname(os.path.realpath(glitch.__file__))
        with open(os.path.join(folder_path, "files", file)) as f:
            content = f.readlines()
            return [c.strip() for c in content]

    def check_atomicunit(self, au: AtomicUnit, file: str) -> List[Error]:
        errors = super().check_atomicunit(au, file)

        for item in SecurityVisitor.__FILE_COMMANDS:
            if item not in au.type:
                continue
            for a in au.attributes:
                values = [a.value]
                if isinstance(a.value, ConditionalStatement):
                    statements = a.value.statements
                    if len(statements) == 0:
                        continue
                    values = statements[0].values()
                for value in values:
                    if not isinstance(value, str):
                        continue
                    if a.name in ["mode", "m"] and re.search(
                            r'(?:^0?777$)|(?:(?:^|(?:ugo)|o|a)\+[rwx]{3})',
                            value
                            ):
                        errors.append(Error('sec_full_permission_filesystem', a, file, repr(a)))

        if au.type in SecurityVisitor.__OBSOLETE_COMMANDS:
            errors.append(Error('sec_obsolete_command', au, file, repr(au)))
        elif any(au.type.endswith(res) for res in SecurityVisitor.__SHELL_RESOURCES):
            for attr in au.attributes:
                if isinstance(attr.value, str) and attr.value.split(" ")[0] in SecurityVisitor.__OBSOLETE_COMMANDS:
                    errors.append(Error('sec_obsolete_command', attr, file, repr(attr)))
                    break
        
        errors += self.integrity_policy.check(au, file, self.code, au.name)
        errors += self.https.check(au, file, self.code, au.name)
        errors += self.ssl_tls_policy.check(au, file, self.code, au.name)
        errors += self.dnssec.check(au, file, self.code, au.name)
        errors += self.public_ip.check(au, file, self.code, au.name)
        errors += self.access_control.check(au, file, self.code, au.name)
        errors += self.authentication.check(au, file, self.code, au.name)
        errors += self.missing_encryption.check(au, file, self.code, au.name)
        errors += self.firewall_misconfig.check(au, file, self.code, au.name)
        errors += self.threats_detection.check(au, file, self.code, au.name)
        errors += self.weak_password_key_policy.check(au, file, self.code, au.name)
        errors += self.sensitive_iam_action.check(au, file, self.code, au.name)
        errors += self.key_management.check(au, file, self.code, au.name)
        errors += self.network_security_rules.check(au, file, self.code, au.name)
        errors += self.permission_iam_policies.check(au, file, self.code, au.name)
        errors += self.logging.check(au, file, self.code, au.name)
        errors += self.attached_resource.check(au, file, self.code, au.name)
        errors += self.versioning.check(au, file, self.code, au.name)
        errors += self.naming.check(au, file, self.code, au.name)
        errors += self.replication.check(au, file, self.code, au.name)
        
        if self.__is_http_url(au.name):
            errors.append(Error('sec_https', au, file, repr(au)))
        if self.__is_weak_crypt(au.type, au.name):
            errors.append(Error('sec_weak_crypt', au, file, repr(au)))

        return errors

    def check_dependency(self, d: Dependency, file: str) -> List[Error]:
        return []

    def __check_keyvalue(self, c: CodeElement, name: str, 
            value: str, has_variable: bool, file: str, au_type = None, parent_name: str = ""):
        errors = []
        name = name.strip().lower()
        if (isinstance(value, type(None))):
            for child in c.keyvalues:
                errors += self.check_element(child, file, au_type, name)
            return errors
        elif (isinstance(value, str)):
            value = value.strip().lower()
        else:
            errors += self.check_element(value, file)
            value = repr(value)

        if self.__is_http_url(value):
            errors.append(Error('sec_https', c, file, repr(c)))

        if re.match(r'(?:https?://|^)0.0.0.0', value) or\
            (name == "ip" and value in {"*", '::'}) or\
            (name in SecurityVisitor.__IP_BIND_COMMANDS and
             (value == True or value in {'*', '::'})):
            errors.append(Error('sec_invalid_bind', c, file, repr(c)))

        if self.__is_weak_crypt(value, name):
            errors.append(Error('sec_weak_crypt', c, file, repr(c)))

        for check in SecurityVisitor.__CHECKSUM:
            if (check in name and (value == 'no' or value == 'false')):
                errors.append(Error('sec_no_int_check', c, file, repr(c)))
                break

        for item in (SecurityVisitor.__ROLES + SecurityVisitor.__USERS):
            if (re.match(r'[_A-Za-z0-9$\/\.\[\]-]*{text}\b'.format(text=item), name)):
                if (len(value) > 0 and not has_variable):
                    for admin in SecurityVisitor.__ADMIN:
                        if admin in value:
                            errors.append(Error('sec_def_admin', c, file, repr(c)))
                            break

        def get_au(c, name: str, type: str):
            if isinstance(c, Project):
                module_name = os.path.basename(os.path.dirname(file))
                for m in self.code.modules:
                    if m.name == module_name:
                        return get_au(m, name, type)
            elif isinstance(c, Module):
                for ub in c.blocks:
                    au = get_au(ub, name, type)
                    if au:
                        return au
            elif isinstance(c, UnitBlock):
                for au in c.atomic_units:
                    if (au.type == type and au.name == name):
                        return au
            return None

        def get_module_var(c, name: str):
            if isinstance(c, Project):
                module_name = os.path.basename(os.path.dirname(file))
                for m in self.code.modules:
                    if m.name == module_name:
                        return get_module_var(m, name)
            elif isinstance(c, Module):
                for ub in c.blocks:
                    var = get_module_var(ub, name)
                    if var:
                        return var
            elif isinstance(c, UnitBlock):
                for var in c.variables:
                    if var.name == name:
                        return var
            return None

        # only for terraform
        var = None
        if (has_variable and self.tech == Tech.terraform):
            value = re.sub(r'^\${(.*)}$', r'\1', value)
            if value.startswith("var."):   # input variable (atomic unit with type variable)
                au = get_au(self.code, value.strip("var."), "variable")
                if au != None:
                    for attribute in au.attributes:
                        if attribute.name == "default":
                            var = attribute
            elif value.startswith("local."):    # local value (variable)
                var = get_module_var(self.code, value.strip("local."))

        for item in (SecurityVisitor.__PASSWORDS + 
                SecurityVisitor.__SECRETS + SecurityVisitor.__USERS):
            if (re.match(r'[_A-Za-z0-9$\/\.\[\]-]*{text}\b'.format(text=item), name) 
                and name.split("[")[0] not in SecurityVisitor.__SECRETS_WHITELIST + SecurityVisitor.__PROFILE):
                if (not has_variable or var):
                    
                    if not has_variable:
                        if (item in SecurityVisitor.__PASSWORDS and len(value) == 0):
                            errors.append(Error('sec_empty_pass', c, file, repr(c)))
                            break
                    if var:
                        if (item in SecurityVisitor.__PASSWORDS and var.value != None and len(var.value) == 0):
                            errors.append(Error('sec_empty_pass', c, file, repr(c)))
                            break

                    errors.append(Error('sec_hard_secr', c, file, repr(c)))
                    if (item in SecurityVisitor.__PASSWORDS):
                        errors.append(Error('sec_hard_pass', c, file, repr(c)))
                    elif (item in SecurityVisitor.__USERS):
                        errors.append(Error('sec_hard_user', c, file, repr(c)))

                    break

        for item in SecurityVisitor.__SSH_DIR:
            if item.lower() in name:
                if len(value) > 0 and '/id_rsa' in value:
                    errors.append(Error('sec_hard_secr', c, file, repr(c)))

        for item in SecurityVisitor.__MISC_SECRETS:
            if (re.match(r'([_A-Za-z0-9$-]*[-_]{text}([-_].*)?$)|(^{text}([-_].*)?$)'.format(text=item), name)
                    and len(value) > 0 and not has_variable):
                errors.append(Error('sec_hard_secr', c, file, repr(c)))

        for item in SecurityVisitor.__SENSITIVE_DATA:
            if item.lower() in name:
                for item_value in (SecurityVisitor.__SECRET_ASSIGN):
                    if item_value in value.lower():
                        errors.append(Error('sec_hard_secr', c, file, repr(c)))
                        if ("password" in item_value):
                            errors.append(Error('sec_hard_pass', c, file, repr(c)))

        if (au_type in SecurityVisitor.__GITHUB_ACTIONS and name == "plaintext_value"):
            errors.append(Error('sec_hard_secr', c, file, repr(c)))
        
        if (has_variable and var):
            has_variable = False
            value = var.value

        errors += self.https.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.integrity_policy.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.ssl_tls_policy.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.dnssec.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.public_ip.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.access_control.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.authentication.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.missing_encryption.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.firewall_misconfig.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.threats_detection.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.weak_password_key_policy.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.sensitive_iam_action.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.key_management.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.network_security_rules.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.permission_iam_policies.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.logging.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.attached_resource.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.versioning.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.naming.check(c, file, self.code, name, value, au_type, parent_name)
        errors += self.replication.check(c, file, self.code, name, value, au_type, parent_name)

        return errors

    def check_attribute(self, a: Attribute, file: str, au_type = None, parent_name: str = "") -> list[Error]:
        return self.__check_keyvalue(a, a.name, a.value, a.has_variable, file, au_type, parent_name)

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        return self.__check_keyvalue(v, v.name, v.value, v.has_variable, file)

    def check_comment(self, c: Comment, file: str) -> List[Error]:
        errors = []
        lines = c.content.split('\n')
        stop = False
        for word in SecurityVisitor.__WRONG_WORDS:
            for line in lines:
                tokenizer = WordPunctTokenizer()
                tokens = tokenizer.tokenize(line.lower())
                if word in tokens:
                    errors.append(Error('sec_susp_comm', c, file, line))
                    stop = True
            if stop:
                break
        return errors

    def check_condition(self, c: ConditionalStatement, file: str) -> List[Error]:
        errors = super().check_condition(c, file)

        condition = c
        has_default = False

        while condition != None:
            if condition.is_default:
                has_default = True
                break
            condition = condition.else_statement

        if not has_default:
            return errors + [Error('sec_no_default_switch', c, file, repr(c))]

        return errors

    def check_unitblock(self, u: UnitBlock) -> List[Error]:
        errors = super().check_unitblock(u)

        # Missing integrity check changed to unit block since in Docker the integrity check is not an attribute of the
        # atomic unit but can be done on another atomic unit inside the same unit block.
        missing_integrity_checks = {}
        for au in u.atomic_units:
            result = self.check_integrity_check(au, u.path)
            if result:
                missing_integrity_checks[result[0]] = result[1]
                continue
            file = SecurityVisitor.check_has_checksum(au)
            if file:
                if file in missing_integrity_checks:
                    del missing_integrity_checks[file]

        errors += missing_integrity_checks.values()
        errors += self.non_off_img.check(u, u.path)

        return errors

    @staticmethod
    def check_integrity_check(au: AtomicUnit, path: str) -> Optional[Tuple[str, Error]]:
        for item in SecurityVisitor.__DOWNLOAD:
            if not re.search(r'(http|https|www)[^ ,]*\.{text}'.format(text=item), au.name):
                continue
            if SecurityVisitor.__has_integrity_check(au.attributes):
                return None
            return os.path.basename(au.name), Error('sec_no_int_check', au, path, repr(au))

        for a in au.attributes:
            value = a.value.strip().lower() if isinstance(a.value, str) else repr(a.value).strip().lower()

            for item in SecurityVisitor.__DOWNLOAD:
                if not re.search(r'(http|https|www)[^ ,]*\.{text}'.format(text=item), value):
                    continue
                if SecurityVisitor.__has_integrity_check(au.attributes):
                    return None
                return os.path.basename(a.value), Error('sec_no_int_check', au, path, repr(a))
        return None

    @staticmethod
    def check_has_checksum(au: AtomicUnit) -> Optional[str]:
        if au.type not in SecurityVisitor.__CHECKSUM:
            return None
        if any(d in au.name for d in SecurityVisitor.__DOWNLOAD):
            return os.path.basename(au.name)

        for a in au.attributes:
            value = a.value.strip().lower() if isinstance(a.value, str) else repr(a.value).strip().lower()
            if any(d in value for d in SecurityVisitor.__DOWNLOAD):
                return os.path.basename(au.name)
        return None

    @staticmethod
    def __has_integrity_check(attributes: List[Attribute]) -> bool:
        for attr in attributes:
            name = attr.name.strip().lower()
            if any([check in name for check in SecurityVisitor.__CHECKSUM]):
                return True

    @staticmethod
    def __is_http_url(value: str) -> bool:
        if (re.match(SecurityVisitor.__URL_REGEX, value) and
                ('http' in value or 'www' in value) and 'https' not in value):
            return True
        try:
            parsed_url = urlparse(value)
            return parsed_url.scheme == 'http' and \
                    parsed_url.hostname not in SecurityVisitor.__URL_WHITELIST
        except ValueError:
            return False

    @staticmethod
    def __is_weak_crypt(value: str, name: str) -> bool:
        if any(crypt in value for crypt in SecurityVisitor.__CRYPT):
            whitelist = any(word in name or word in value for word in SecurityVisitor.__CRYPT_WHITELIST)
            return not whitelist
        return False
