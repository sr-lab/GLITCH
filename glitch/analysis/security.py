import os
import re
import json
import configparser
from urllib.parse import urlparse
from glitch.analysis.rules import Error, RuleVisitor

from glitch.repr.inter import *


class SecurityVisitor(RuleVisitor):
    __URL_REGEX = r"^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([_\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"

    @staticmethod
    def get_name() -> str:
        return "security"

    def config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path)
        SecurityVisitor.__WRONG_WORDS = json.loads(config['security']['suspicious_words'])
        SecurityVisitor.__PASSWORDS = json.loads(config['security']['passwords'])
        SecurityVisitor.__USERS = json.loads(config['security']['users'])
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
        SecurityVisitor.__SENSITIVE_DATA = json.loads(config['security']['sensitive_data'])
        SecurityVisitor.__KEY_ASSIGN = json.loads(config['security']['key_value_assign'])
        SecurityVisitor.__GITHUB_ACTIONS = json.loads(config['security']['github_actions_resources'])
        SecurityVisitor.__INTEGRITY_POLICY = json.loads(config['security']['integrity_policy'])
        SecurityVisitor.__SECRETS_WHITELIST = json.loads(config['security']['secrets_white_list'])
        SecurityVisitor.__HTTPS_CONFIGS = json.loads(config['security']['ensure_https'])
        SecurityVisitor.__SSL_TLS_POLICY = json.loads(config['security']['ssl_tls_policy'])
        SecurityVisitor.__DNSSEC_CONFIGS = json.loads(config['security']['ensure_dnssec'])
        SecurityVisitor.__PUBLIC_IP_CONFIGS = json.loads(config['security']['use_public_ip'])
        SecurityVisitor.__POLICY_KEYWORDS = json.loads(config['security']['policy_keywords'])
        SecurityVisitor.__ACCESS_CONTROL_CONFIGS = json.loads(config['security']['insecure_access_control'])
        SecurityVisitor.__AUTHENTICATION = json.loads(config['security']['authentication'])
        SecurityVisitor.__POLICY_ACCESS_CONTROL = json.loads(config['security']['policy_insecure_access_control'])
        SecurityVisitor.__POLICY_AUTHENTICATION = json.loads(config['security']['policy_authentication'])
        SecurityVisitor.__MISSING_ENCRYPTION = json.loads(config['security']['missing_encryption'])
        SecurityVisitor.__CONFIGURATION_KEYWORDS = json.loads(config['security']['configuration_keywords'])
        SecurityVisitor.__ENCRYPT_CONFIG = json.loads(config['security']['encrypt_configuration'])
        SecurityVisitor.__FIREWALL_CONFIGS = json.loads(config['security']['firewall'])
        SecurityVisitor.__MISSING_THREATS_DETECTION_ALERTS = json.loads(config['security']['missing_threats_detection_alerts'])
        SecurityVisitor.__PASSWORD_KEY_POLICY = json.loads(config['security']['password_key_policy'])

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = super().check_atomicunit(au, file)
        # Check integrity check
        for a in au.attributes:
            if isinstance(a.value, str): value = a.value.strip().lower()
            else: value = repr(a.value).strip().lower()

            for item in SecurityVisitor.__DOWNLOAD:
                if re.search(r'(http|https|www)[^ ,]*\.{text}'.format(text = item), value):
                    integrity_check = False
                    for other in au.attributes:
                        name = other.name.strip().lower()
                        if any([check in name for check in SecurityVisitor.__CHECKSUM]):
                            integrity_check = True
                            break

                    if not integrity_check:
                        errors.append(Error('sec_no_int_check', au, file, repr(a)))

                    break

        def get_associated_au(c, type: str, attribute_name: str , attribute_value: str, attribute_parents: list):
            if isinstance(c, Project):
                module_name = os.path.basename(os.path.dirname(file))
                for m in self.code.modules:
                    if m.name == module_name:
                        return get_associated_au(m, type, attribute_name, attribute_value, attribute_parents)
            elif isinstance(c, Module):
                for ub in c.blocks:
                    au = get_associated_au(ub, type, attribute_name, attribute_value, attribute_parents)
                    if au:
                        return au
            else:
                for au in c.atomic_units:
                    if (au.type == type and check_required_attribute(
                            au.attributes, attribute_parents, attribute_name, attribute_value)):
                        return au
            return None

        def get_attributes_with_name_and_value(attributes, parents, name, value = None):
            aux = []
            for a in attributes:
                if a.name.split('dynamic')[-1] == name and parents == [""]:
                    if value and a.value.lower() == value:
                        aux.append(a)
                    elif value and a.value.lower() != value:
                        continue
                    elif not value:
                        aux.append(a)
                elif a.name.split('dynamic.')[-1] in parents:
                    aux += get_attributes_with_name_and_value(a.keyvalues, [""], name, value)
                elif a.keyvalues != []:
                    aux += get_attributes_with_name_and_value(a.keyvalues, parents, name, value)
            return aux

        def check_required_attribute(attributes, parents, name, value = None):
            attributes = get_attributes_with_name_and_value(attributes, parents, name, value)
            if attributes != []:
                return attributes[0]
            else:
                return None

        def check_database_flags(smell: str, flag_name: str, safe_value: str):
            database_flags = get_attributes_with_name_and_value(au.attributes, ["settings"], "database_flags")
            found_flag = False
            if database_flags != []:
                for flag in database_flags:
                    name = check_required_attribute(flag.keyvalues, [""], "name", flag_name)
                    if name:
                        found_flag = True
                        value = check_required_attribute(flag.keyvalues, [""], "value")
                        if value and value.value.lower() != safe_value:
                            errors.append(Error(smell, value, file, repr(value)))
                            break
                        elif not value:
                            errors.append(Error(smell, au, file, repr(au), 
                                f"Suggestion: check for a required attribute with name 'value'."))
                            break
            if not found_flag:
                errors.append(Error(smell, au, file, repr(au), 
                    f"Suggestion: check for a required flag '{flag_name}'."))
        
        # check integrity policy
        for policy in SecurityVisitor.__INTEGRITY_POLICY:
            if (policy['required'] == "yes" and au.type in policy['au_type']
                and not check_required_attribute(au.attributes, policy['parents'], policy['attribute'])):
                errors.append(Error('sec_integrity_policy', au, file, repr(au),
                    f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
                break

        # check http without tls
        for config in SecurityVisitor.__HTTPS_CONFIGS:
            if (config["required"] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config["parents"], config['attribute'])):
                errors.append(Error('sec_https', au, file, repr(au),
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break
            
        # check ssl/tls policy
        for policy in SecurityVisitor.__SSL_TLS_POLICY:
            if (policy['required'] == "yes" and au.type in policy['au_type']
                and not check_required_attribute(au.attributes, policy['parents'], policy['attribute'])):
                errors.append(Error('sec_ssl_tls_policy', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
                break
        
        # check dns without dnssec
        for config in SecurityVisitor.__DNSSEC_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_dnssec', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break

        # check public ip
        for config in SecurityVisitor.__PUBLIC_IP_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_public_ip', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break
            elif (config['required'] == "must_not_exist" and au.type in config['au_type']):
                a = check_required_attribute(au.attributes, config['parents'], config['attribute'])
                if a:
                    errors.append(Error('sec_public_ip', a, file, repr(a)))
                    break 

        # check insecure access control
        if (au.type == "resource.aws_api_gateway_method"):
            http_method = check_required_attribute(au.attributes, [""], 'http_method')
            authorization = check_required_attribute(au.attributes, [""], 'authorization')
            if (http_method and authorization):
                if (http_method.value.lower() == 'get' and authorization.value.lower() == 'none'):
                    api_key_required = check_required_attribute(au.attributes, [""], 'api_key_required')
                    if api_key_required and f"{api_key_required.value}".lower() != 'true':
                        errors.append(Error('sec_access_control', api_key_required, file, repr(api_key_required)))
                    elif not api_key_required:
                        errors.append(Error('sec_access_control', au, file, repr(au), 
                        f"Suggestion: check for a required attribute with name 'api_key_required'."))
            elif (http_method and not authorization):
                    errors.append(Error('sec_access_control', au, file, repr(au), 
                        f"Suggestion: check for a required attribute with name 'authorization'."))
        elif (au.type == "resource.github_repository"):
            visibility = check_required_attribute(au.attributes, [""], 'visibility')
            if visibility:
                if visibility.value.lower() not in ["private", "internal"]:
                    errors.append(Error('sec_access_control', visibility, file, repr(visibility)))
            else:
                private = check_required_attribute(au.attributes, [""], 'private')
                if private:
                    if f"{private.value}".lower() != "true":
                        errors.append(Error('sec_access_control', private, file, repr(private)))
                else:
                    errors.append(Error('sec_access_control', au, file, repr(au), 
                        f"Suggestion: check for a required attribute with name 'visibility' or 'private'."))
        elif (au.type == "resource.google_sql_database_instance"):
            check_database_flags('sec_access_control', "cross db ownership chaining", "off")
        elif (au.type == "resource.aws_s3_bucket"):
            if not get_associated_au(self.code, "resource.aws_s3_bucket_public_access_block", "bucket",
                "${aws_s3_bucket." + f"{au.name}" + ".id}", [""]):
                errors.append(Error('sec_access_control', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'aws_s3_bucket_public_access_block' " + 
                        f"associated to an 'aws_s3_bucket' resource."))

        for config in SecurityVisitor.__ACCESS_CONTROL_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_access_control', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break

        # check authentication
        if (au.type == "resource.google_sql_database_instance"):
            check_database_flags('sec_authentication', "contained database authentication", "off")
        elif (au.type == "resource.aws_iam_group"):
            if not get_associated_au(self.code, "resource.aws_iam_group_policy", "group",
                "${aws_iam_group." + f"{au.name}" + ".name}", [""]):
                errors.append(Error('sec_authentication', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'aws_iam_group_policy' associated to an " +
                        f"'aws_iam_group' resource."))

        for config in SecurityVisitor.__AUTHENTICATION:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_authentication', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break
        
        # check missing encryption
        for config in SecurityVisitor.__MISSING_ENCRYPTION:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_missing_encryption', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break

        # check firewall misconfiguration
        for config in SecurityVisitor.__FIREWALL_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type'] 
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_firewall_misconfig', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break

        # check missing threats detection and alerts
        for config in SecurityVisitor.__MISSING_THREATS_DETECTION_ALERTS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_threats_detection_alerts', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                break
            elif (config['required'] == "must_not_exist" and au.type in config['au_type']):
                a = check_required_attribute(au.attributes, config['parents'], config['attribute'])
                if a:
                    errors.append(Error('sec_threats_detection_alerts', a, file, repr(a)))
                    break 

        # check weak password/key policy
        for policy in SecurityVisitor.__PASSWORD_KEY_POLICY:
            if (policy['required'] == "yes" and au.type in policy['au_type'] 
                and not check_required_attribute(au.attributes, policy['parents'], policy['attribute'])):
                errors.append(Error('sec_weak_password_key_policy', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
                break

        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return []

    # FIXME attribute and variables need to have superclass
    def __check_keyvalue(self, c: CodeElement, name: str, 
            value: str, has_variable: bool, file: str, atomic_unit: AtomicUnit = None, parent_name: str = ""):
        errors = []
        name = name.strip().lower()
        if (isinstance(value, type(None))):
            for child in c.keyvalues:
                errors += self.check_element(child, file, atomic_unit, name)
            return errors
        elif (isinstance(value, str)):
            value = value.strip().lower()
        else:
            errors += self.check_element(value, file)
            value = repr(value)

        try:
            if (re.match(SecurityVisitor.__URL_REGEX, value) and
                ('http' in value or 'www' in value) and 'https' not in value):
                errors.append(Error('sec_https', c, file, repr(c)))

            parsed_url = urlparse(value)
            if parsed_url.scheme == 'http' and \
                    parsed_url.hostname not in SecurityVisitor.__URL_WHITELIST:
                errors.append(Error('sec_https', c, file, repr(c)))
        except:
            # The url is not valid
            pass

        for config in SecurityVisitor.__HTTPS_CONFIGS:
            if (name == config["attribute"] and atomic_unit.type in config["au_type"] 
                and parent_name in config["parents"] and value.lower() not in config["values"]):
                errors.append(Error('sec_https', c, file, repr(c)))
                break

        if re.match(r'^0.0.0.0', value) or re.match(r'^::/0', value):
            errors.append(Error('sec_invalid_bind', c, file, repr(c)))

        for crypt in SecurityVisitor.__CRYPT:
            if crypt in value:
                whitelist = False
                for word in SecurityVisitor.__CRYPT_WHITELIST:
                    if word in name or word in value:
                        whitelist = True
                        break

                if not whitelist:
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
            else:
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
            else:
                for var in c.variables:
                    if var.name == name:
                        return var
            return None

        for item in (SecurityVisitor.__PASSWORDS + 
                SecurityVisitor.__SECRETS + SecurityVisitor.__USERS):
            if (re.match(r'[_A-Za-z0-9$\/\.\[\]-]*{text}\b'.format(text=item), name) 
                and name not in SecurityVisitor.__SECRETS_WHITELIST):
                if not has_variable:
                    errors.append(Error('sec_hard_secr', c, file, repr(c)))

                    if (item in SecurityVisitor.__PASSWORDS):
                        errors.append(Error('sec_hard_pass', c, file, repr(c)))
                    elif (item in SecurityVisitor.__USERS):
                        errors.append(Error('sec_hard_user', c, file, repr(c)))

                    if (item in SecurityVisitor.__PASSWORDS and len(value) == 0):
                        errors.append(Error('sec_empty_pass', c, file, repr(c)))

                    break
                else:
                    value = re.sub(r'^\${(.*)}$', r'\1', value)
                    aux = None
                    if value.startswith("var."):   # input variable (atomic unit with type variable)
                        au = get_au(self.code, value.strip("var."), "variable")
                        if au != None:
                            for attribute in au.attributes:
                                if attribute.name == "default":
                                    aux = attribute
                    elif value.startswith("local."):    # local value (variable)
                        aux = get_module_var(self.code, value.strip("local."))
                    #FIXME value can also use module blocks, resources/data attributes, not only input_variable/local_value
                    
                    if aux:
                        errors.append(Error('sec_hard_secr', c, file, repr(c)))

                        if (item in SecurityVisitor.__PASSWORDS):
                            errors.append(Error('sec_hard_pass', c, file, repr(c)))
                        elif (item in SecurityVisitor.__USERS):
                            errors.append(Error('sec_hard_user', c, file, repr(c)))

                        if (item in SecurityVisitor.__PASSWORDS and aux.value != None and len(aux.value) == 0):
                            errors.append(Error('sec_empty_pass', c, file, repr(c)))
                            
                        break

        for item in SecurityVisitor.__SSH_DIR:
            if item.lower() in name:
                if len(value) > 0 and '/id_rsa' in value:
                    errors.append(Error('sec_hard_secr', c, file, repr(c)))

        for item in SecurityVisitor.__MISC_SECRETS:
            if (re.match(r'([_A-Za-z0-9$-]*[-_]{text}([-_].*)?$)|(^{text}([-_].*)?$)'.format(text=item), name) 
                    and name not in SecurityVisitor.__SECRETS_WHITELIST and len(value) > 0 and not has_variable):
                errors.append(Error('sec_hard_secr', c, file, repr(c)))

        for item in SecurityVisitor.__SENSITIVE_DATA:
            if item.lower() in name:
                for item_value in (SecurityVisitor.__KEY_ASSIGN + SecurityVisitor.__PASSWORDS + 
                    SecurityVisitor.__SECRETS):
                    if item_value in value.lower():
                        errors.append(Error('sec_hard_secr', c, file, repr(c)))

                        if (item_value in SecurityVisitor.__PASSWORDS):
                            errors.append(Error('sec_hard_pass', c, file, repr(c)))

        if atomic_unit.type in SecurityVisitor.__GITHUB_ACTIONS and name == "plaintext_value":
            errors.append(Error('sec_hard_secr', c, file, repr(c)))
        
        for policy in SecurityVisitor.__INTEGRITY_POLICY:
            if (name == policy['attribute'] and atomic_unit.type in policy['au_type'] 
                and parent_name in policy['parents'] and value.lower() not in policy['values']):
                errors.append(Error('sec_integrity_policy', c, file, repr(c)))
                break
        
        for policy in SecurityVisitor.__SSL_TLS_POLICY:
            if (name == policy['attribute'] and atomic_unit.type in policy['au_type']
                and parent_name in policy['parents'] and value.lower() not in policy['values']):
                errors.append(Error('sec_ssl_tls_policy', c, file, repr(c)))
                break

        for config in SecurityVisitor.__DNSSEC_CONFIGS:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and value.lower() not in config['values']
                and config['values'] != [""]):
                errors.append(Error('sec_dnssec', c, file, repr(c)))
                break

        for config in SecurityVisitor.__PUBLIC_IP_CONFIGS:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and value.lower() not in config['values']
                and config['values'] != [""]):
                errors.append(Error('sec_public_ip', c, file, repr(c)))
                break

        for item in SecurityVisitor.__POLICY_KEYWORDS:
            if item.lower() == name:
                for config in SecurityVisitor.__POLICY_ACCESS_CONTROL:
                    expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                    pattern = re.compile(rf"{expr}")
                    if re.search(pattern, value):
                        errors.append(Error('sec_access_control', c, file, repr(c)))
                for config in SecurityVisitor.__POLICY_AUTHENTICATION:
                    if atomic_unit.type in config['au_type']:
                        expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                        pattern = re.compile(rf"{expr}")
                        if not re.search(pattern, value):
                            errors.append(Error('sec_authentication', c, file, repr(c)))

        for config in SecurityVisitor.__ACCESS_CONTROL_CONFIGS:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and value.lower() not in config['values']
                and config['values'] != [""]):
                errors.append(Error('sec_access_control', c, file, repr(c)))
                break

        for config in SecurityVisitor.__AUTHENTICATION:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and value.lower() not in config['values']
                and config['values'] != [""]):
                errors.append(Error('sec_authentication', c, file, repr(c)))
                break

        for config in SecurityVisitor.__MISSING_ENCRYPTION:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]):
                if ("any_not_empty" in config['values'] and value.lower() == ""):
                    errors.append(Error('sec_missing_encryption', c, file, repr(c)))
                    break
                elif ("any_not_empty" not in config['values'] and value.lower() not in config['values']):
                    errors.append(Error('sec_missing_encryption', c, file, repr(c)))
                    break

        for item in SecurityVisitor.__CONFIGURATION_KEYWORDS:
            if item.lower() == name:
                for config in SecurityVisitor.__ENCRYPT_CONFIG:
                    if atomic_unit.type in config['au_type']:
                        expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                        pattern = re.compile(rf"{expr}")
                        if not re.search(pattern, value) and config['required'] == "yes":
                            errors.append(Error('sec_missing_encryption', c, file, repr(c)))
                        elif re.search(pattern, value) and config['required'] == "must_not_exist":
                            errors.append(Error('sec_missing_encryption', c, file, repr(c)))
        
        for config in SecurityVisitor.__FIREWALL_CONFIGS:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]):
                if ("any_not_empty" in config['values'] and value.lower() == ""):
                    errors.append(Error('sec_firewall_misconfig', c, file, repr(c)))
                    break
                elif ("any_not_empty" not in config['values'] and value.lower() not in config['values']):
                    errors.append(Error('sec_firewall_misconfig', c, file, repr(c)))
                    break

        for config in SecurityVisitor.__MISSING_THREATS_DETECTION_ALERTS:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]):
                if ("any_not_empty" in config['values'] and value.lower() == ""):
                    errors.append(Error('sec_threats_detection_alerts', c, file, repr(c)))
                    break
                elif ("any_not_empty" not in config['values'] and value.lower() not in config['values']):
                    errors.append(Error('sec_threats_detection_alerts', c, file, repr(c)))
                    break

        for policy in SecurityVisitor.__PASSWORD_KEY_POLICY:
            if (name == policy['attribute'] and atomic_unit.type in policy['au_type']
                and parent_name in policy['parents'] and policy['values'] != [""]):
                if (policy['logic'] == "equal"):
                    if ("any_not_empty" in policy['values'] and value.lower() == ""):
                        errors.append(Error('sec_weak_password_key_policy', c, file, repr(c)))
                        break
                    elif ("any_not_empty" not in policy['values'] and value.lower() not in policy['values']):
                        errors.append(Error('sec_weak_password_key_policy', c, file, repr(c)))
                        break
                elif ((policy['logic'] == "gte" and not value.isnumeric()) or
                    (policy['logic'] == "gte" and value.isnumeric() and int(value) < int(policy['values'][0]))):
                    errors.append(Error('sec_weak_password_key_policy', c, file, repr(c)))
                    break
                elif ((policy['logic'] == "lte" and not value.isnumeric()) or
                    (policy['logic'] == "lte" and value.isnumeric() and int(value) > int(policy['values'][0]))):
                    errors.append(Error('sec_weak_password_key_policy', c, file, repr(c)))
                    break

        return errors

    def check_attribute(self, a: Attribute, file: str, au: AtomicUnit = None, parent_name: str = "") -> list[Error]:
        return self.__check_keyvalue(a, a.name, a.value, a.has_variable, file, au, parent_name)

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        return self.__check_keyvalue(None, v, v.name, v.value, v.has_variable, file) #FIXME

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        errors = []
        lines = c.content.split('\n')
        stop = False
        for word in SecurityVisitor.__WRONG_WORDS:
            for line in lines:
                if word in line.lower():
                    errors.append(Error('sec_susp_comm', c, file, line))
                    stop = True
            if stop:
                break
        return errors

    def check_condition(self, c: ConditionStatement, file: str) -> list[Error]:
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
