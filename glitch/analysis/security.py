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
        SecurityVisitor.__KEY_MANAGEMENT = json.loads(config['security']['key_management'])
        SecurityVisitor.__NETWORK_SECURITY_RULES = json.loads(config['security']['network_security_rules'])
        SecurityVisitor.__PERMISSION_IAM_POLICIES = json.loads(config['security']['permission_iam_policies'])
        SecurityVisitor.__GOOGLE_IAM_MEMBER = json.loads(config['security']['google_iam_member_resources'])
        SecurityVisitor.__LOGGING = json.loads(config['security']['logging'])
        SecurityVisitor.__GOOGLE_SQL_DATABASE_LOG_FLAGS = json.loads(config['security']['google_sql_database_log_flags'])
        SecurityVisitor.__POSSIBLE_ATTACHED_RESOURCES = json.loads(config['security']['possible_attached_resources_aws_route53'])
        SecurityVisitor.__VERSIONING = json.loads(config['security']['versioning'])
        SecurityVisitor.__NAMING = json.loads(config['security']['naming'])
        SecurityVisitor.__REPLICATION = json.loads(config['security']['replication'])

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

        def get_associated_au(c, type: str, attribute_name: str , pattern, attribute_parents: list):
            if isinstance(c, Project):
                module_name = os.path.basename(os.path.dirname(file))
                for m in self.code.modules:
                    if m.name == module_name:
                        return get_associated_au(m, type, attribute_name, pattern, attribute_parents)
            elif isinstance(c, Module):
                for ub in c.blocks:
                    au = get_associated_au(ub, type, attribute_name, pattern, attribute_parents)
                    if au:
                        return au
            else:
                for au in c.atomic_units:
                    if (au.type == type and check_required_attribute(
                            au.attributes, attribute_parents, attribute_name, None, pattern)):
                        return au
            return None

        def get_attributes_with_name_and_value(attributes, parents, name, value = None, pattern = None):
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
                    aux += get_attributes_with_name_and_value(a.keyvalues, [""], name, value, pattern)
                elif a.keyvalues != []:
                    aux += get_attributes_with_name_and_value(a.keyvalues, parents, name, value, pattern)
            return aux

        def check_required_attribute(attributes, parents, name, value = None, pattern = None):
            attributes = get_attributes_with_name_and_value(attributes, parents, name, value, pattern)
            if attributes != []:
                return attributes[0]
            else:
                return None

        def check_database_flags(smell: str, flag_name: str, safe_value: str, required_flag = True):
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
                        elif not value and required_flag:
                            errors.append(Error(smell, flag, file, repr(flag), 
                                f"Suggestion: check for a required attribute with name 'value'."))
                            break
            if not found_flag and required_flag:
                errors.append(Error(smell, au, file, repr(au), 
                    f"Suggestion: check for a required flag '{flag_name}'."))
        
        # check integrity policy
        for policy in SecurityVisitor.__INTEGRITY_POLICY:
            if (policy['required'] == "yes" and au.type in policy['au_type']
                and not check_required_attribute(au.attributes, policy['parents'], policy['attribute'])):
                errors.append(Error('sec_integrity_policy', au, file, repr(au),
                    f"Suggestion: check for a required attribute with name '{policy['msg']}'."))

        # check http without tls
        if (au.type == "data.http"):
            url = check_required_attribute(au.attributes, [""], "url")
            if ("${" in url.value):
                r = url.value.split("${")[1].split("}")[0]
                resource_type = r.split(".")[0]
                resource_name = r.split(".")[1]
                if get_au(self.code, resource_name, "resource." + resource_type):
                    errors.append(Error('sec_https', url, file, repr(url)))

        for config in SecurityVisitor.__HTTPS_CONFIGS:
            if (config["required"] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config["parents"], config['attribute'])):
                errors.append(Error('sec_https', au, file, repr(au),
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            
        # check ssl/tls policy
        for policy in SecurityVisitor.__SSL_TLS_POLICY:
            if (policy['required'] == "yes" and au.type in policy['au_type']
                and not check_required_attribute(au.attributes, policy['parents'], policy['attribute'])):
                errors.append(Error('sec_ssl_tls_policy', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{policy['msg']}'."))
        
        # check dns without dnssec
        for config in SecurityVisitor.__DNSSEC_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_dnssec', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))

        # check public ip
        for config in SecurityVisitor.__PUBLIC_IP_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_public_ip', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            elif (config['required'] == "must_not_exist" and au.type in config['au_type']):
                a = check_required_attribute(au.attributes, config['parents'], config['attribute'])
                if a:
                    errors.append(Error('sec_public_ip', a, file, repr(a)))

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
            expr = "\${aws_s3_bucket\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            if not get_associated_au(self.code, "resource.aws_s3_bucket_public_access_block", "bucket", pattern, [""]):
                errors.append(Error('sec_access_control', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'aws_s3_bucket_public_access_block' " + 
                        f"associated to an 'aws_s3_bucket' resource."))

        for config in SecurityVisitor.__ACCESS_CONTROL_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_access_control', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))

        # check authentication
        if (au.type == "resource.google_sql_database_instance"):
            check_database_flags('sec_authentication', "contained database authentication", "off")
        elif (au.type == "resource.aws_iam_group"):
            expr = "\${aws_iam_group\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            if not get_associated_au(self.code, "resource.aws_iam_group_policy", "group", pattern, [""]):
                errors.append(Error('sec_authentication', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'aws_iam_group_policy' associated to an " +
                        f"'aws_iam_group' resource."))

        for config in SecurityVisitor.__AUTHENTICATION:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_authentication', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
        
        # check missing encryption
        if (au.type == "resource.aws_s3_bucket"):
            expr = "\${aws_s3_bucket\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            r = get_associated_au(self.code, "resource.aws_s3_bucket_server_side_encryption_configuration", 
                "bucket", pattern, [""])
            if not r:
                errors.append(Error('sec_missing_encryption', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'aws_s3_bucket_server_side_encryption_configuration' " + 
                        f"associated to an 'aws_s3_bucket' resource."))
        elif (au.type == "resource.aws_eks_cluster"):
            resources = check_required_attribute(au.attributes, ["encryption_config"], "resources[0]")
            if resources:
                i = 0
                valid = False
                while resources:
                    a = resources
                    if resources.value.lower() == "secrets":
                        valid = True
                        break
                    i += 1
                    resources = check_required_attribute(au.attributes, ["encryption_config"], f"resources[{i}]")
                if not valid:
                    errors.append(Error('sec_missing_encryption', a, file, repr(a)))
            else:
                errors.append(Error('sec_missing_encryption', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'encryption_config.resources'."))

        for config in SecurityVisitor.__MISSING_ENCRYPTION:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_missing_encryption', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))

        # check firewall misconfiguration
        for config in SecurityVisitor.__FIREWALL_CONFIGS:
            if (config['required'] == "yes" and au.type in config['au_type'] 
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_firewall_misconfig', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))

        # check missing threats detection and alerts
        for config in SecurityVisitor.__MISSING_THREATS_DETECTION_ALERTS:
            if (config['required'] == "yes" and au.type in config['au_type']
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_threats_detection_alerts', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            elif (config['required'] == "must_not_exist" and au.type in config['au_type']):
                a = check_required_attribute(au.attributes, config['parents'], config['attribute'])
                if a:
                    errors.append(Error('sec_threats_detection_alerts', a, file, repr(a)))

        # check weak password/key policy
        for policy in SecurityVisitor.__PASSWORD_KEY_POLICY:
            if (policy['required'] == "yes" and au.type in policy['au_type'] 
                and not check_required_attribute(au.attributes, policy['parents'], policy['attribute'])):
                errors.append(Error('sec_weak_password_key_policy', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{policy['msg']}'."))

        # check sensitive action by IAM
        if (au.type == "data.aws_iam_policy_document"):
            allow = check_required_attribute(au.attributes, ["statement"], "effect")
            if ((allow and allow.value.lower() == "allow") or (not allow)):
                sensitive_action = False
                i = 0
                action = check_required_attribute(au.attributes, ["statement"], f"actions[{i}]")
                while action:
                    if action.value.lower() in ["s3:*", "s3:getobject"]:
                        sensitive_action = True
                        break
                    i += 1
                    action = check_required_attribute(au.attributes, ["statement"], f"actions[{i}]")
                sensitive_resource = False
                i = 0
                resource = check_required_attribute(au.attributes, ["statement"], f"resources[{i}]")
                while resource:
                    if resource.value.lower() in ["*"]:
                        sensitive_resource = True
                        break
                    i += 1
                    resource = check_required_attribute(au.attributes, ["statement"], f"resources[{i}]")
                if (sensitive_action and sensitive_resource):
                    errors.append(Error('sec_sensitive_iam_action', action, file, repr(action)))

        # check key management
        if (au.type == "resource.aws_s3_bucket"):
            expr = "\${aws_s3_bucket\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            r = get_associated_au(self.code, "resource.aws_s3_bucket_server_side_encryption_configuration", "bucket",
                pattern, [""])
            if not r:
                errors.append(Error('sec_key_management', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'aws_s3_bucket_server_side_encryption_configuration' " + 
                        f"associated to an 'aws_s3_bucket' resource."))
        elif (au.type == "resource.azurerm_storage_account"):
            expr = "\${azurerm_storage_account\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            if not get_associated_au(self.code, "resource.azurerm_storage_account_customer_managed_key", "storage_account_id",
                pattern, [""]):
                errors.append(Error('sec_key_management', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'azurerm_storage_account_customer_managed_key' " + 
                        f"associated to an 'azurerm_storage_account' resource."))

        for config in SecurityVisitor.__KEY_MANAGEMENT:
            if (config['required'] == "yes" and au.type in config['au_type'] 
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_key_management', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))

        # check network security rules
        if (au.type == "resource.azurerm_network_security_rule"):
            access = check_required_attribute(au.attributes, [""], "access")
            if (access and access.value.lower() == "allow"):
                protocol = check_required_attribute(au.attributes, [""], "protocol")
                if (protocol and protocol.value.lower() == "udp"):
                    errors.append(Error('sec_network_security_rules', access, file, repr(access)))
                elif (protocol and protocol.value.lower() == "tcp"):
                    dest_port_range = check_required_attribute(au.attributes, [""], "destination_port_range")
                    dest_port_ranges = check_required_attribute(au.attributes, [""], "destination_port_ranges[0]")
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
                            dest_port_ranges = check_required_attribute(au.attributes, [""], f"destination_port_ranges[{i}]")
                    if port:
                        source_address_prefix = check_required_attribute(au.attributes, [""], "source_address_prefix")
                        if (source_address_prefix and (source_address_prefix.value.lower() in ["*", "/0", "internet", "any"] 
                            or re.match(r'^0.0.0.0', source_address_prefix.value.lower()))):
                            errors.append(Error('sec_network_security_rules', source_address_prefix, file, repr(source_address_prefix)))
        elif (au.type == "resource.azurerm_network_security_group"):
            access = check_required_attribute(au.attributes, ["security_rule"], "access")
            if (access and access.value.lower() == "allow"):
                protocol = check_required_attribute(au.attributes, ["security_rule"], "protocol")
                if (protocol and protocol.value.lower() == "udp"):
                    errors.append(Error('sec_network_security_rules', access, file, repr(access)))
                elif (protocol and protocol.value.lower() == "tcp"):
                    dest_port_range = check_required_attribute(au.attributes, ["security_rule"], "destination_port_range")
                    if (dest_port_range and dest_port_range.value.lower() in ["22", "3389", "*"]):
                        source_address_prefix = check_required_attribute(au.attributes, [""], "source_address_prefix")
                        if (source_address_prefix and (source_address_prefix.value.lower() in ["*", "/0", "internet", "any"] 
                            or re.match(r'^0.0.0.0', source_address_prefix.value.lower()))):
                            errors.append(Error('sec_network_security_rules', source_address_prefix, file, repr(source_address_prefix)))

        for rule in SecurityVisitor.__NETWORK_SECURITY_RULES:
            if (rule['required'] == "yes" and au.type in rule['au_type'] 
                and not check_required_attribute(au.attributes, rule['parents'], rule['attribute'])):
                errors.append(Error('sec_network_security_rules', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{rule['msg']}'."))
        
        # check permission of IAM policies
        if (au.type == "resource.aws_iam_user"):
            expr = "\${aws_iam_user\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            assoc_au = get_associated_au(self.code, "resource.aws_iam_user_policy", "user", pattern, [""])
            if assoc_au:
                a = check_required_attribute(assoc_au.attributes, [""], "user", None, pattern) 
                errors.append(Error('sec_permission_iam_policies', a, file, repr(a)))

        # check logging
        if (au.type == "resource.aws_eks_cluster"):
            enabled_cluster_log_types = check_required_attribute(au.attributes, [""], "enabled_cluster_log_types[0]")
            types = ["api", "authenticator", "audit", "scheduler", "controllermanager"]
            if enabled_cluster_log_types:
                i = 0
                while enabled_cluster_log_types:
                    a = enabled_cluster_log_types
                    if enabled_cluster_log_types.value.lower() in types:
                        types.remove(enabled_cluster_log_types.value.lower())
                    i += 1
                    enabled_cluster_log_types = check_required_attribute(au.attributes, [""], f"enabled_cluster_log_types[{i}]")
                if types != []:
                    errors.append(Error('sec_logging', a, file, repr(a), 
                    f"Suggestion: check for additional log type(s) {types}."))
            else:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'enabled_cluster_log_types'."))
        elif (au.type == "resource.aws_msk_cluster"):
            broker_logs = check_required_attribute(au.attributes, ["logging_info"], "broker_logs")
            if broker_logs:
                active = False
                logs_type = ["cloudwatch_logs", "firehose", "s3"]
                a_list = []
                for type in logs_type:
                    log = check_required_attribute(broker_logs.keyvalues, [""], type)
                    if log:
                        enabled = check_required_attribute(log.keyvalues, [""], "enabled")
                        if enabled and f"{enabled.value}".lower() == "true":
                            active = True
                        elif enabled and f"{enabled.value}".lower() != "true":
                            a_list.append(enabled)
                if not active and a_list == []:
                    errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name " +
                    f"'logging_info.broker_logs.[cloudwatch_logs/firehose/s3].enabled'."))
                if not active and a_list != []:
                    for a in a_list:
                        errors.append(Error('sec_logging', a, file, repr(a)))
            else:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name " +
                    f"'logging_info.broker_logs.[cloudwatch_logs/firehose/s3].enabled'."))
        elif (au.type == "resource.aws_neptune_cluster"):
            active = False
            enable_cloudwatch_logs_exports = check_required_attribute(au.attributes, [""], f"enable_cloudwatch_logs_exports[0]")
            if enable_cloudwatch_logs_exports:
                i = 0
                while enable_cloudwatch_logs_exports:
                    a = enable_cloudwatch_logs_exports
                    if enable_cloudwatch_logs_exports.value.lower() == "audit":
                        active  = True
                        break
                    i += 1
                    enable_cloudwatch_logs_exports = check_required_attribute(au.attributes, [""], f"enable_cloudwatch_logs_exports[{i}]")
                if not active:
                    errors.append(Error('sec_logging', a, file, repr(a)))
            else:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'enable_cloudwatch_logs_exports'."))
        elif (au.type == "resource.aws_docdb_cluster"):
            active = False
            enabled_cloudwatch_logs_exports = check_required_attribute(au.attributes, [""], f"enabled_cloudwatch_logs_exports[0]")
            if enabled_cloudwatch_logs_exports:
                i = 0
                while enabled_cloudwatch_logs_exports:
                    a = enabled_cloudwatch_logs_exports
                    if enabled_cloudwatch_logs_exports.value.lower() in ["audit", "profiler"]:
                        active  = True
                        break
                    i += 1
                    enabled_cloudwatch_logs_exports = check_required_attribute(au.attributes, [""], f"enabled_cloudwatch_logs_exports[{i}]")
                if not active:
                    errors.append(Error('sec_logging', a, file, repr(a)))
            else:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'enabled_cloudwatch_logs_exports'."))
        elif (au.type == "resource.azurerm_mssql_server"):
            expr = "\${azurerm_mssql_server\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            assoc_au = get_associated_au(self.code, "resource.azurerm_mssql_server_extended_auditing_policy", 
                "server_id", pattern, [""])
            if not assoc_au:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'azurerm_mssql_server_extended_auditing_policy' " + 
                    f"associated to an 'azurerm_mssql_server' resource."))
        elif (au.type == "resource.azurerm_mssql_database"):
            expr = "\${azurerm_mssql_database\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            assoc_au = get_associated_au(self.code, "resource.azurerm_mssql_database_extended_auditing_policy", 
                "database_id", pattern, [""])
            if not assoc_au:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'azurerm_mssql_database_extended_auditing_policy' " + 
                    f"associated to an 'azurerm_mssql_database' resource."))
        elif (au.type == "resource.azurerm_postgresql_configuration"):
            name = check_required_attribute(au.attributes, [""], "name")
            value = check_required_attribute(au.attributes, [""], "value")
            if (name and name.value.lower() in ["log_connections", "connection_throttling", "log_checkpoints"] 
                and value and value.value.lower() != "on"):
                errors.append(Error('sec_logging', value, file, repr(value)))
        elif (au.type == "resource.azurerm_monitor_log_profile"):
            categories = check_required_attribute(au.attributes, [""], "categories[0]")
            activities = [ "action", "delete", "write"]
            if categories:
                i = 0
                while categories:
                    a = categories
                    if categories.value.lower() in activities:
                        activities.remove(categories.value.lower())
                    i += 1
                    categories = check_required_attribute(au.attributes, [""], f"categories[{i}]")
                if activities != []:
                    errors.append(Error('sec_logging', a, file, repr(a), 
                    f"Suggestion: check for additional activity type(s) {activities}."))
            else:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'categories'."))
        elif (au.type == "resource.google_sql_database_instance"):
            for flag in SecurityVisitor.__GOOGLE_SQL_DATABASE_LOG_FLAGS:
                required_flag = True
                if flag['required'] == "no":
                    required_flag = False
                check_database_flags('sec_logging', flag['flag_name'], flag['value'], required_flag)
        elif (au.type == "resource.azurerm_storage_container"):
            storage_account_name = check_required_attribute(au.attributes, [""], "storage_account_name")
            if storage_account_name and storage_account_name.value.lower().startswith("${azurerm_storage_account."):
                name = storage_account_name.value.lower().split('.')[1]
                storage_account_au = get_au(self.code, name, "resource.azurerm_storage_account")
                if storage_account_au:
                    expr = "\${azurerm_storage_account\." + f"{name}\."
                    pattern = re.compile(rf"{expr}")
                    assoc_au = get_associated_au(self.code, "resource.azurerm_log_analytics_storage_insights",
                        "storage_account_id", pattern, [""])
                    if assoc_au:
                        blob_container_names = check_required_attribute(assoc_au.attributes, [""], "blob_container_names[0]")
                        if blob_container_names:
                            i = 0
                            contains_blob_name = False
                            while blob_container_names:
                                a = blob_container_names
                                if blob_container_names.value:
                                    contains_blob_name = True
                                    break
                                i += 1
                                blob_container_names = check_required_attribute(assoc_au.attributes, [""], f"blob_container_names[{i}]")
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
                    errors.append(Error('sec_logging', au, file, repr(au), 
                        f"Suggestion: 'azurerm_storage_container' resource has to be associated to an " + 
                        f"'azurerm_storage_account' resource in order to enable logging."))
            else:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: 'azurerm_storage_container' resource has to be associated to an " + 
                    f"'azurerm_storage_account' resource in order to enable logging."))
            container_access_type = check_required_attribute(au.attributes, [""], "container_access_type")
            if container_access_type and container_access_type.value.lower() not in ["blob", "private"]:
                errors.append(Error('sec_logging', container_access_type, file, repr(container_access_type)))
        elif (au.type == "resource.aws_ecs_cluster"):
            name = check_required_attribute(au.attributes, ["setting"], "name", "containerinsights")
            if name:
                enabled = check_required_attribute(au.attributes, ["setting"], "value")
                if enabled:
                    if enabled.value.lower() != "enabled":
                        errors.append(Error('sec_logging', enabled, file, repr(enabled)))
                else:
                    errors.append(Error('sec_logging', au, file, repr(au), 
                        f"Suggestion: check for a required attribute with name 'setting.value'."))
            else:
                errors.append(Error('sec_logging', au, file, repr(au), 
                    "Suggestion: check for a required attribute with name 'setting.name' and value 'containerInsights'."))

        for config in SecurityVisitor.__LOGGING:
            if (config['required'] == "yes" and au.type in config['au_type'] 
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_logging', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
            
        # check attached resource
        def check_attached_resource(attributes, resource_types):
            for a in attributes:
                if a.value != None:
                    for resource_type in resource_types:
                        if (f"{a.value}".lower().startswith("${" + f"{resource_type}.") 
                            or f"{a.value}".lower().startswith(f"{resource_type}.")):
                            resource_name = a.value.lower().split(".")[1]
                            if get_au(self.code, resource_name, f"resource.{resource_type}"):
                                return True
                elif a.value == None:
                    attached = check_attached_resource(a.keyvalues, resource_types)
                    if attached:
                        return True
            return False

        if (au.type == "resource.aws_route53_record"):
            type_A = check_required_attribute(au.attributes, [""], "type", "a")
            if type_A and not check_attached_resource(au.attributes, SecurityVisitor.__POSSIBLE_ATTACHED_RESOURCES):
                errors.append(Error('sec_attached_resource', au, file, repr(au)))
        
        # check versioning
        for config in SecurityVisitor.__VERSIONING:
            if (config['required'] == "yes" and au.type in config['au_type'] 
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_versioning', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                
        # check naming
        if (au.type == "resource.aws_security_group"):
            ingress = check_required_attribute(au.attributes, [""], "ingress")
            egress = check_required_attribute(au.attributes, [""], "egress")
            if ingress and not check_required_attribute(ingress.keyvalues, [""], "description"):
                errors.append(Error('sec_naming', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'ingress.description'."))
            if egress and not check_required_attribute(egress.keyvalues, [""], "description"):
                errors.append(Error('sec_naming', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'egress.description'."))
        elif (au.type == "resource.google_container_cluster"):
            resource_labels = check_required_attribute(au.attributes, [""], "resource_labels", None)
            if resource_labels and resource_labels.value == None:
                if resource_labels.keyvalues == []:
                    errors.append(Error('sec_naming', resource_labels, file, repr(resource_labels), 
                        f"Suggestion: check empty 'resource_labels'."))
            else:
                errors.append(Error('sec_naming', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name 'resource_labels'."))

        for config in SecurityVisitor.__NAMING:
            if (config['required'] == "yes" and au.type in config['au_type'] 
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_naming', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))
                
        # check replication
        if (au.type == "resource.aws_s3_bucket"):
            expr = "\${aws_s3_bucket\." + f"{au.name}\."
            pattern = re.compile(rf"{expr}")
            if not get_associated_au(self.code, "resource.aws_s3_bucket_replication_configuration", 
                "bucket", pattern, [""]):
                errors.append(Error('sec_replication', au, file, repr(au), 
                    f"Suggestion: check for a required resource 'aws_s3_bucket_replication_configuration' " + 
                        f"associated to an 'aws_s3_bucket' resource."))

        for config in SecurityVisitor.__REPLICATION:
            if (config['required'] == "yes" and au.type in config['au_type'] 
                and not check_required_attribute(au.attributes, config['parents'], config['attribute'])):
                errors.append(Error('sec_replication', au, file, repr(au), 
                    f"Suggestion: check for a required attribute with name '{config['msg']}'."))

        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return []

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
                and name.split("[")[0] not in SecurityVisitor.__SECRETS_WHITELIST):
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
                    and name.split("[")[0] not in SecurityVisitor.__SECRETS_WHITELIST and len(value) > 0 and not has_variable):
                errors.append(Error('sec_hard_secr', c, file, repr(c)))

        for item in SecurityVisitor.__SENSITIVE_DATA:
            if item.lower() in name:
                for item_value in (SecurityVisitor.__KEY_ASSIGN + SecurityVisitor.__PASSWORDS + 
                    SecurityVisitor.__SECRETS):
                    if item_value in value.lower():
                        errors.append(Error('sec_hard_secr', c, file, repr(c)))

                        if (item_value in SecurityVisitor.__PASSWORDS):
                            errors.append(Error('sec_hard_pass', c, file, repr(c)))

        if (atomic_unit.type in SecurityVisitor.__GITHUB_ACTIONS and name == "plaintext_value"):
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
                    allow_expr = "\"effect\":" + "\s*" + "\"allow\""
                    allow_pattern = re.compile(rf"{allow_expr}")
                    if re.search(pattern, value) and re.search(allow_pattern, value):
                        errors.append(Error('sec_access_control', c, file, repr(c)))
                for config in SecurityVisitor.__POLICY_AUTHENTICATION:
                    if atomic_unit.type in config['au_type']:
                        expr = config['keyword'].lower() + "\s*" + config['value'].lower()
                        pattern = re.compile(rf"{expr}")
                        if not re.search(pattern, value):
                            errors.append(Error('sec_authentication', c, file, repr(c)))

        if (re.search(r"actions\[\d+\]", name) and parent_name == "permissions" 
            and atomic_unit.type == "resource.azurerm_role_definition" and value == "*"):
            errors.append(Error('sec_access_control', c, file, repr(c)))
        elif (((re.search(r"members\[\d+\]", name) and atomic_unit.type == "resource.google_storage_bucket_iam_binding")
            or (name == "member" and atomic_unit.type == "resource.google_storage_bucket_iam_member"))
            and (value == "allusers" or value == "allauthenticatedusers")):
            errors.append(Error('sec_access_control', c, file, repr(c)))
        elif (name == "email" and parent_name == "service_account" 
            and atomic_unit.type == "resource.google_compute_instance"
            and re.search(r".-compute@developer.gserviceaccount.com", value)):
            errors.append(Error('sec_access_control', c, file, repr(c)))

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

        for config in SecurityVisitor.__KEY_MANAGEMENT:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]):
                if ("any_not_empty" in config['values'] and value.lower() == ""):
                    errors.append(Error('sec_key_management', c, file, repr(c)))
                    break
                elif ("any_not_empty" not in config['values'] and value.lower() not in config['values']):
                    errors.append(Error('sec_key_management', c, file, repr(c)))
                    break

        if (name == "rotation_period" and atomic_unit.type == "resource.google_kms_crypto_key"):
            expr1 = r'\d+\.\d{0,9}s'
            expr2 = r'\d+s'
            if (re.search(expr1, value) or re.search(expr2, value)):
                if (int(value.split("s")[0]) > 7776000):
                    errors.append(Error('sec_key_management', c, file, repr(c)))
            else:
                errors.append(Error('sec_key_management', c, file, repr(c)))
        elif (name == "kms_master_key_id" and ((atomic_unit.type == "resource.aws_sqs_queue"
            and value == "alias/aws/sqs") or  (atomic_unit.type == "resource.aws_sns_queue"
            and value == "alias/aws/sns"))):
            errors.append(Error('sec_key_management', c, file, repr(c)))

        for rule in SecurityVisitor.__NETWORK_SECURITY_RULES:
            if (name == rule['attribute'] and atomic_unit.type in rule['au_type']
                and parent_name in rule['parents'] and value.lower() not in rule['values']
                and rule['values'] != [""]):
                errors.append(Error('sec_network_security_rules', c, file, repr(c)))
                break

        if ((name == "member" or name.split('[')[0] == "members") 
            and atomic_unit.type in SecurityVisitor.__GOOGLE_IAM_MEMBER
            and (re.search(r".-compute@developer.gserviceaccount.com", value) or 
                 re.search(r".@appspot.gserviceaccount.com", value) or
                 re.search(r"user:", value))):
            errors.append(Error('sec_permission_iam_policies', c, file, repr(c)))

        for config in SecurityVisitor.__PERMISSION_IAM_POLICIES:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]):
                if ((config['logic'] == "equal" and value.lower() not in config['values'])
                    or (config['logic'] == "diff" and value.lower() in config['values'])):
                    errors.append(Error('sec_permission_iam_policies', c, file, repr(c)))
                    break

        if (name == "cloud_watch_logs_group_arn" and atomic_unit.type == "resource.aws_cloudtrail"):
            if re.match(r"^\${aws_cloudwatch_log_group\..", value):
                aws_cloudwatch_log_group_name = value.split('.')[1]
                if not get_au(self.code, aws_cloudwatch_log_group_name, "resource.aws_cloudwatch_log_group"):
                    errors.append(Error('sec_logging', c, file, repr(c),
                        f"Suggestion: check for a required resource 'aws_cloudwatch_log_group' " +
                        f"with name '{aws_cloudwatch_log_group_name}'."))
            else:
                errors.append(Error('sec_logging', c, file, repr(c)))
        elif (((name == "retention_in_days" and parent_name == "" 
            and atomic_unit.type in ["resource.azurerm_mssql_database_extended_auditing_policy", 
            "resource.azurerm_mssql_server_extended_auditing_policy"]) 
            or (name == "days" and parent_name == "retention_policy" 
            and atomic_unit.type == "resource.azurerm_network_watcher_flow_log")) 
            and ((not value.isnumeric()) or (value.isnumeric() and int(value) < 90))):
            errors.append(Error('sec_logging', c, file, repr(c)))
        elif (name == "days" and parent_name == "retention_policy" 
            and atomic_unit.type == "resource.azurerm_monitor_log_profile" 
            and (not value.isnumeric() or (value.isnumeric() and int(value) < 365))):
            errors.append(Error('sec_logging', c, file, repr(c)))

        for config in SecurityVisitor.__LOGGING:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]):
                if ("any_not_empty" in config['values'] and value.lower() == ""):
                    errors.append(Error('sec_logging', c, file, repr(c)))
                    break
                elif ("any_not_empty" not in config['values'] and value.lower() not in config['values']):
                    errors.append(Error('sec_logging', c, file, repr(c)))
                    break

        for config in SecurityVisitor.__VERSIONING:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]
                and value.lower() not in config['values']):
                errors.append(Error('sec_versioning', c, file, repr(c)))
                break
                
        if (name == "name" and atomic_unit.type in ["resource.azurerm_storage_account"]):
            pattern = r'^[a-z0-9]{3,24}$'
            if not re.match(pattern, value):
                errors.append(Error('sec_naming', c, file, repr(c)))

        for config in SecurityVisitor.__NAMING:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]):
                if ("any_not_empty" in config['values'] and value.lower() == ""):
                    errors.append(Error('sec_naming', c, file, repr(c)))
                    break
                elif ("any_not_empty" not in config['values'] and value.lower() not in config['values']):
                    errors.append(Error('sec_naming', c, file, repr(c)))
                    break

        for config in SecurityVisitor.__REPLICATION:
            if (name == config['attribute'] and atomic_unit.type in config['au_type']
                and parent_name in config['parents'] and config['values'] != [""]
                and value.lower() not in config['values']):
                errors.append(Error('sec_replication', c, file, repr(c)))
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
