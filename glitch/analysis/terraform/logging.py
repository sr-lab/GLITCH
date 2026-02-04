import re

from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.analysis.checkers.var_checker import VariableChecker
from glitch.repr.inter import Array, AtomicUnit, Attribute, Boolean, CodeElement, Integer, KeyValue, String, UnitBlock


class TerraformLogging(TerraformSmellChecker):
    def __check_log_attribute(
        self,
        element: AtomicUnit,
        attribute_name: str,
        file: str,
        values: List[str],
        all: bool = False,
    ) -> List[Error]:
        errors: List[Error] = []
        attribute = self.check_required_attribute(element, [], attribute_name)

        if attribute is None:
            errors.append(
                Error(
                    "sec_logging",
                    element,
                    file,
                    repr(element),
                    f"Suggestion: check for a required attribute with name '{attribute_name}'.",
                )
            )
            return errors

        if not isinstance(attribute, Attribute) or not isinstance(attribute.value, Array):
            return errors

        array_values = [
            v.value.lower() if isinstance(v, String) else str(v).lower()
            for v in attribute.value.value
        ]

        if all:
            missing = [v for v in values if v not in array_values]
            if missing:
                errors.append(
                    Error(
                        "sec_logging",
                        attribute,
                        file,
                        repr(attribute),
                        f"Suggestion: check for additional log type(s) {missing}.",
                    )
                )
        else:
            if not any(v in values for v in array_values):
                errors.append(Error("sec_logging", attribute, file, repr(attribute)))

        return errors

    def __check_azurerm_storage_container(self, element: AtomicUnit, file: str):
        errors: List[Error] = []

        container_access_type = self.check_required_attribute(
            element, [], "container_access_type"
        )
        if (
            container_access_type
            and isinstance(container_access_type, Attribute)
            and isinstance(container_access_type.value, String)
            and container_access_type.value.value.lower()
            not in [
                "blob",
                "private",
            ]
        ):
            errors.append(
                Error(
                    "sec_logging",
                    container_access_type,
                    file,
                    repr(container_access_type),
                )
            )

        storage_account_name = self.check_required_attribute(
            element, [], "storage_account_name"
        )
        storage_name_value = None
        if storage_account_name is not None and isinstance(storage_account_name, Attribute):
            if isinstance(storage_account_name.value, String):
                storage_name_value = storage_account_name.value.value.lower()
            elif hasattr(storage_account_name.value, "code"):
                storage_name_value = storage_account_name.value.code.lower()

        if not (
            storage_name_value is not None
            and (
                storage_name_value.startswith("${azurerm_storage_account.")
                or storage_name_value.startswith("azurerm_storage_account.")
            )
        ):
            errors.append(
                Error(
                    "sec_logging",
                    element,
                    file,
                    repr(element),
                    f"Suggestion: 'azurerm_storage_container' resource has to be associated to an "
                    + f"'azurerm_storage_account' resource in order to enable logging.",
                )
            )
            return errors

        name = storage_name_value.split(".")[1] if storage_name_value.startswith("${") else storage_name_value.split(".")[0]
        if storage_name_value.startswith("azurerm_storage_account."):
            name = storage_name_value.split(".")[1]
        storage_account_au = self.get_au(file, name, "azurerm_storage_account")
        if storage_account_au is None:
            errors.append(
                Error(
                    "sec_logging",
                    element,
                    file,
                    repr(element),
                    f"Suggestion: 'azurerm_storage_container' resource has to be associated to an "
                    + f"'azurerm_storage_account' resource in order to enable logging.",
                )
            )
            return errors

        expr = "(\\$\\{)?azurerm_storage_account\\." + f"{name}\\."
        pattern = re.compile(rf"{expr}")
        assoc_au = self.get_associated_au(
            file,
            "azurerm_log_analytics_storage_insights",
            "storage_account_id",
            pattern,
            [],
        )
        if assoc_au is None:
            errors.append(
                Error(
                    "sec_logging",
                    storage_account_au,
                    file,
                    repr(storage_account_au),
                    f"Suggestion: check for a required resource 'azurerm_log_analytics_storage_insights' "
                    + f"associated to an 'azurerm_storage_account' resource.",
                )
            )
            return errors

        blob_container_names = self.check_required_attribute(
            assoc_au, [], "blob_container_names"
        )
        if blob_container_names is None:
            errors.append(
                Error(
                    "sec_logging",
                    assoc_au,
                    file,
                    repr(assoc_au),
                    f"Suggestion: check for a required attribute with name 'blob_container_names'.",
                )
            )
            return errors

        if isinstance(blob_container_names, Attribute) and isinstance(blob_container_names.value, Array):
            has_valid_name = False
            for item in blob_container_names.value.value:
                if isinstance(item, String) and item.value.strip():
                    has_valid_name = True
                    break
            if not has_valid_name:
                errors.append(
                    Error(
                        "sec_logging",
                        blob_container_names,
                        file,
                        repr(blob_container_names),
                    )
                )

        return errors

    def _check_attribute(
        self,
        attribute: Attribute | KeyValue,
        atomic_unit: AtomicUnit,
        parent_name: str,
        file: str,
    ) -> List[Error]:
        if (
            attribute.name == "cloud_watch_logs_group_arn"
            and atomic_unit.type == "aws_cloudtrail"
        ):
            value_str = None
            if isinstance(attribute.value, String):
                value_str = attribute.value.value
            elif hasattr(attribute.value, "code"):
                value_str = attribute.value.code

            if value_str and re.match(r"^(\$\{)?aws_cloudwatch_log_group\..", value_str):
                aws_cloudwatch_log_group_name = value_str.split(".")[1] if value_str.startswith("$") else value_str.split(".")[0]
                if value_str.startswith("aws_cloudwatch_log_group."):
                    aws_cloudwatch_log_group_name = value_str.split(".")[1]
                if not self.get_au(
                    file,
                    aws_cloudwatch_log_group_name,
                    "aws_cloudwatch_log_group",
                ):
                    return [
                        Error(
                            "sec_logging",
                            attribute,
                            file,
                            repr(attribute),
                            f"Suggestion: check for a required resource 'aws_cloudwatch_log_group' "
                            + f"with name '{aws_cloudwatch_log_group_name}'.",
                        )
                    ]
            else:
                return [Error("sec_logging", attribute, file, repr(attribute))]
        elif (
            (
                attribute.name == "retention_in_days"
                and parent_name == ""
                and atomic_unit.type
                in [
                    "azurerm_mssql_database_extended_auditing_policy",
                    "azurerm_mssql_server_extended_auditing_policy",
                ]
            )
            or (
                attribute.name == "days"
                and parent_name == "retention_policy"
                and atomic_unit.type == "azurerm_network_watcher_flow_log"
            )
        ):
            if isinstance(attribute.value, Integer) and attribute.value.value < 90:
                return [Error("sec_logging", attribute, file, repr(attribute))]
            elif isinstance(attribute.value, String) and (
                not attribute.value.value.isnumeric()
                or int(attribute.value.value) < 90
            ):
                return [Error("sec_logging", attribute, file, repr(attribute))]
        elif (
            attribute.name == "days"
            and parent_name == "retention_policy"
            and atomic_unit.type == "azurerm_monitor_log_profile"
        ):
            if isinstance(attribute.value, Integer) and attribute.value.value < 365:
                return [Error("sec_logging", attribute, file, repr(attribute))]
            elif isinstance(attribute.value, String) and (
                not attribute.value.value.isnumeric()
                or int(attribute.value.value) < 365
            ):
                return [Error("sec_logging", attribute, file, repr(attribute))]

        for config in SecurityVisitor.LOGGING:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and self._parent_matches(parent_name, config["parents"])
                and config["values"] != []
            ):
                if isinstance(attribute.value, (String, Boolean)):
                    value_str = str(attribute.value.value).lower()
                elif hasattr(attribute.value, "code"):
                    value_str = attribute.value.code.lower()
                else:
                    continue

                if "any_not_empty" in config["values"] and value_str == "":
                    return [Error("sec_logging", attribute, file, repr(attribute))]
                elif (
                    "any_not_empty" not in config["values"]
                    and not VariableChecker().check(attribute.value)
                    and value_str not in config["values"]
                ):
                    return [Error("sec_logging", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "aws_eks_cluster":
                errors.extend(
                    self.__check_log_attribute(
                        element,
                        "enabled_cluster_log_types",
                        file,
                        [
                            "api",
                            "authenticator",
                            "audit",
                            "scheduler",
                            "controllermanager",
                        ],
                        all=True,
                    )
                )
            elif element.type == "aws_msk_cluster":
                broker_logs = self.check_required_attribute(
                    element, ["logging_info"], "broker_logs"
                )
                if isinstance(broker_logs, UnitBlock):
                    active = False
                    logs_type = ["cloudwatch_logs", "firehose", "s3"]
                    a_list: List[Attribute | KeyValue] = []
                    for log_type in logs_type:
                        log = self.check_required_attribute(broker_logs, [], log_type)
                        if isinstance(log, UnitBlock):
                            enabled = self.check_required_attribute(log, [], "enabled")
                            if isinstance(enabled, (Attribute, KeyValue)):
                                enabled_val = str(enabled.value.value).lower() if isinstance(enabled.value, Boolean) else str(enabled.value).lower()
                                if enabled_val == "true":
                                    active = True
                                else:
                                    a_list.append(enabled)
                    if not active and a_list == []:
                        errors.append(
                            Error(
                                "sec_logging",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name "
                                + f"'logging_info.broker_logs.[cloudwatch_logs/firehose/s3].enabled'.",
                            )
                        )
                    if not active and a_list != []:
                        for a in a_list:
                            errors.append(Error("sec_logging", a, file, repr(a)))
                else:
                    errors.append(
                        Error(
                            "sec_logging",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name "
                            + f"'logging_info.broker_logs.[cloudwatch_logs/firehose/s3].enabled'.",
                        )
                    )
            elif element.type == "aws_neptune_cluster":
                errors.extend(
                    self.__check_log_attribute(
                        element, "enable_cloudwatch_logs_exports", file, ["audit"]
                    )
                )
            elif element.type == "aws_docdb_cluster":
                errors.extend(
                    self.__check_log_attribute(
                        element,
                        "enabled_cloudwatch_logs_exports",
                        file,
                        ["audit", "profiler"],
                    )
                )
            elif element.type == "azurerm_mssql_server":
                name = element.name.value if isinstance(element.name, String) else str(element.name)
                expr = "(\\$\\{)?azurerm_mssql_server\\." + f"{name}\\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(
                    file,
                    "azurerm_mssql_server_extended_auditing_policy",
                    "server_id",
                    pattern,
                    [],
                )
                if not assoc_au:
                    errors.append(
                        Error(
                            "sec_logging",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'azurerm_mssql_server_extended_auditing_policy' "
                            + f"associated to an 'azurerm_mssql_server' resource.",
                        )
                    )
            elif element.type == "azurerm_mssql_database":
                name = element.name.value if isinstance(element.name, String) else str(element.name)
                expr = "(\\$\\{)?azurerm_mssql_database\\." + f"{name}\\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(
                    file,
                    "azurerm_mssql_database_extended_auditing_policy",
                    "database_id",
                    pattern,
                    [],
                )
                if not assoc_au:
                    errors.append(
                        Error(
                            "sec_logging",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'azurerm_mssql_database_extended_auditing_policy' "
                            + f"associated to an 'azurerm_mssql_database' resource.",
                        )
                    )
            elif element.type == "azurerm_postgresql_configuration":
                name_attr = self.check_required_attribute(element, [], "name")
                value_attr = self.check_required_attribute(element, [], "value")
                if (
                    isinstance(name_attr, (Attribute, KeyValue))
                    and isinstance(name_attr.value, String)
                    and name_attr.value.value.lower()
                    in ["log_connections", "connection_throttling", "log_checkpoints"]
                    and isinstance(value_attr, (Attribute, KeyValue))
                    and isinstance(value_attr.value, String)
                    and value_attr.value.value.lower() != "on"
                ):
                    errors.append(Error("sec_logging", value_attr, file, repr(value_attr)))
            elif element.type == "azurerm_monitor_log_profile":
                errors.extend(
                    self.__check_log_attribute(
                        element,
                        "categories",
                        file,
                        ["write", "delete", "action"],
                        all=True,
                    )
                )
            elif element.type == "google_sql_database_instance":
                for flag in SecurityVisitor.GOOGLE_SQL_DATABASE_LOG_FLAGS:
                    required_flag = True
                    if flag["required"] == "no":
                        required_flag = False
                    errors += self.check_database_flags(
                        element,
                        file,
                        "sec_logging",
                        flag["flag_name"],
                        flag["value"],
                        required_flag,
                    )
            elif element.type == "azurerm_storage_container":
                errors += self.__check_azurerm_storage_container(element, file)
            elif element.type == "aws_ecs_cluster":
                name = self.check_required_attribute(
                    element, ["setting"], "name", "containerinsights"
                )
                if name is not None:
                    enabled = self.check_required_attribute(
                        element, ["setting"], "value"
                    )
                    if isinstance(enabled, (Attribute, KeyValue)):
                        if isinstance(enabled.value, String) and enabled.value.value.lower() != "enabled":
                            errors.append(
                                Error("sec_logging", enabled, file, repr(enabled))
                            )
                    else:
                        errors.append(
                            Error(
                                "sec_logging",
                                element,
                                file,
                                repr(element),
                                f"Suggestion: check for a required attribute with name 'setting.value'.",
                            )
                        )
                else:
                    errors.append(
                        Error(
                            "sec_logging",
                            element,
                            file,
                            repr(element),
                            "Suggestion: check for a required attribute with name 'setting.name' and value 'containerInsights'.",
                        )
                    )
            elif element.type == "aws_vpc":
                name = element.name.value if isinstance(element.name, String) else str(element.name)
                expr = "(\\$\\{)?aws_vpc\\." + f"{name}\\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(
                    file, "aws_flow_log", "vpc_id", pattern, []
                )
                if not assoc_au:
                    errors.append(
                        Error(
                            "sec_logging",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required resource 'aws_flow_log' "
                            + f"associated to an 'aws_vpc' resource.",
                        )
                    )

            has_dynamic_block = any(
                isinstance(s, UnitBlock) and s.name == "dynamic"
                for s in element.statements
            )

            for config in SecurityVisitor.LOGGING:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and self.check_required_attribute(
                        element, config["parents"], config["attribute"]
                    )
                    is None
                ):
                    parents = config["parents"]
                    if (
                        element.type == "azurerm_storage_account"
                        and config["attribute"] == "logging"
                        and len(parents) == 1
                    ):
                        first_parent = self.check_required_attribute(element, [], parents[0])
                        if first_parent is None:
                            continue
                    if has_dynamic_block and config["values"] == [] and len(parents) == 0:
                        continue
                    errors.append(
                        Error(
                            "sec_logging",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config.get('msg', config['attribute'])}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
