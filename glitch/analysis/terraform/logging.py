import re
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, Variable


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