import re

from typing import List
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.rules import Error
from glitch.analysis.security import SecurityVisitor
from glitch.repr.inter import AtomicUnit, Attribute, CodeElement, KeyValue


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
        attribute = self.check_required_attribute(
            element.attributes, [""], f"{attribute_name}[0]"
        )

        if all:
            active = True
            for v in values[:]:
                attribute_checked, _ = self.iterate_required_attributes(
                    element.attributes,
                    attribute_name,
                    lambda x: isinstance(x.value, str) and x.value.lower() == v,
                )
                if attribute_checked:
                    values.remove(v)
                active = active and attribute_checked
        else:
            active, _ = self.iterate_required_attributes(
                element.attributes,
                attribute_name,
                lambda x: isinstance(x.value, str) and x.value.lower() in values,
            )

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
        elif not active and not all:
            errors.append(Error("sec_logging", attribute, file, repr(attribute)))
        elif not active and all:
            errors.append(
                Error(
                    "sec_logging",
                    attribute,
                    file,
                    repr(attribute),
                    f"Suggestion: check for additional log type(s) {values}.",
                )
            )

        return errors

    def __check_azurerm_storage_container(self, element: AtomicUnit, file: str):
        errors: List[Error] = []

        container_access_type = self.check_required_attribute(
            element.attributes, [""], "container_access_type"
        )
        if (
            container_access_type
            and isinstance(container_access_type, Attribute)
            and isinstance(container_access_type.value, str)
            and container_access_type.value.lower()
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
            element.attributes, [""], "storage_account_name"
        )
        if not (
            storage_account_name is not None
            and isinstance(storage_account_name, Attribute)
            and isinstance(storage_account_name.value, str)
            and storage_account_name.value.lower().startswith(
                "${azurerm_storage_account."
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

        name = storage_account_name.value.lower().split(".")[1]
        storage_account_au = self.get_au(file, name, "resource.azurerm_storage_account")
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

        expr = "\\${azurerm_storage_account\\." + f"{name}\\."
        pattern = re.compile(rf"{expr}")
        assoc_au = self.get_associated_au(
            file,
            "resource.azurerm_log_analytics_storage_insights",
            "storage_account_id",
            pattern,
            [""],
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
            assoc_au.attributes, [""], "blob_container_names[0]"
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

        contains_blob_name, _ = self.iterate_required_attributes(
            assoc_au.attributes, "blob_container_names", lambda x: x.value  # type: ignore
        )
        if not contains_blob_name:
            errors.append(
                Error(
                    "sec_logging",
                    assoc_au.attributes[-1],
                    file,
                    repr(assoc_au.attributes[-1]),
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
            and atomic_unit.type == "resource.aws_cloudtrail"
        ):
            if isinstance(attribute.value, str) and re.match(
                r"^\${aws_cloudwatch_log_group\..", attribute.value
            ):
                aws_cloudwatch_log_group_name = attribute.value.split(".")[1]
                if not self.get_au(
                    file,
                    aws_cloudwatch_log_group_name,
                    "resource.aws_cloudwatch_log_group",
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
                    "resource.azurerm_mssql_database_extended_auditing_policy",
                    "resource.azurerm_mssql_server_extended_auditing_policy",
                ]
            )
            or (
                attribute.name == "days"
                and parent_name == "retention_policy"
                and atomic_unit.type == "resource.azurerm_network_watcher_flow_log"
            )
        ) and (
            isinstance(attribute.value, str)
            and (
                not attribute.value.isnumeric()
                or (attribute.value.isnumeric() and int(attribute.value) < 90)
            )
        ):
            return [Error("sec_logging", attribute, file, repr(attribute))]
        elif (
            attribute.name == "days"
            and parent_name == "retention_policy"
            and atomic_unit.type == "resource.azurerm_monitor_log_profile"
            and (
                isinstance(attribute.value, str)
                and (
                    not attribute.value.isnumeric()
                    or (attribute.value.isnumeric() and int(attribute.value) < 365)
                )
            )
        ):
            return [Error("sec_logging", attribute, file, repr(attribute))]

        for config in SecurityVisitor.LOGGING:
            if (
                attribute.name == config["attribute"]
                and atomic_unit.type in config["au_type"]
                and parent_name in config["parents"]
                and config["values"] != [""]
            ):
                if (
                    "any_not_empty" in config["values"]
                    and isinstance(attribute.value, str)
                    and attribute.value.lower() == ""
                ):
                    return [Error("sec_logging", attribute, file, repr(attribute))]
                elif (
                    "any_not_empty" not in config["values"]
                    and not attribute.has_variable
                    and isinstance(attribute.value, str)
                    and attribute.value.lower() not in config["values"]
                ):
                    return [Error("sec_logging", attribute, file, repr(attribute))]

        return []

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, AtomicUnit):
            if element.type == "resource.aws_eks_cluster":
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
            elif element.type == "resource.aws_msk_cluster":
                broker_logs = self.check_required_attribute(
                    element.attributes, ["logging_info"], "broker_logs"
                )
                if isinstance(broker_logs, KeyValue):
                    active = False
                    logs_type = ["cloudwatch_logs", "firehose", "s3"]
                    a_list: List[KeyValue] = []
                    for type in logs_type:
                        log = self.check_required_attribute(
                            broker_logs.keyvalues, [""], type
                        )
                        if isinstance(log, KeyValue):
                            enabled = self.check_required_attribute(
                                log.keyvalues, [""], "enabled"
                            )
                            if (
                                isinstance(enabled, KeyValue)
                                and f"{enabled.value}".lower() == "true"
                            ):
                                active = True
                            elif (
                                isinstance(enabled, KeyValue)
                                and f"{enabled.value}".lower() != "true"
                            ):
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
            elif element.type == "resource.aws_neptune_cluster":
                errors.extend(
                    self.__check_log_attribute(
                        element, "enable_cloudwatch_logs_exports", file, ["audit"]
                    )
                )
            elif element.type == "resource.aws_docdb_cluster":
                errors.extend(
                    self.__check_log_attribute(
                        element,
                        "enabled_cloudwatch_logs_exports",
                        file,
                        ["audit", "profiler"],
                    )
                )
            elif element.type == "resource.azurerm_mssql_server":
                expr = "\\${azurerm_mssql_server\\." + f"{element.name}\\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(
                    file,
                    "resource.azurerm_mssql_server_extended_auditing_policy",
                    "server_id",
                    pattern,
                    [""],
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
            elif element.type == "resource.azurerm_mssql_database":
                expr = "\\${azurerm_mssql_database\\." + f"{element.name}\\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(
                    file,
                    "resource.azurerm_mssql_database_extended_auditing_policy",
                    "database_id",
                    pattern,
                    [""],
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
            elif element.type == "resource.azurerm_postgresql_configuration":
                name = self.check_required_attribute(element.attributes, [""], "name")
                value = self.check_required_attribute(element.attributes, [""], "value")
                if (
                    isinstance(name, KeyValue)
                    and isinstance(name.value, str)
                    and name.value.lower()
                    in ["log_connections", "connection_throttling", "log_checkpoints"]
                    and isinstance(value, KeyValue)
                    and isinstance(value.value, str)
                    and value.value.lower() != "on"
                ):
                    errors.append(Error("sec_logging", value, file, repr(value)))
            elif element.type == "resource.azurerm_monitor_log_profile":
                errors.extend(
                    self.__check_log_attribute(
                        element,
                        "categories",
                        file,
                        ["write", "delete", "action"],
                        all=True,
                    )
                )
            elif element.type == "resource.google_sql_database_instance":
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
            elif element.type == "resource.azurerm_storage_container":
                errors += self.__check_azurerm_storage_container(element, file)
            elif element.type == "resource.aws_ecs_cluster":
                name = self.check_required_attribute(
                    element.attributes, ["setting"], "name", "containerinsights"
                )
                if name is not None:
                    enabled = self.check_required_attribute(
                        element.attributes, ["setting"], "value"
                    )
                    if isinstance(enabled, KeyValue):
                        if (
                            isinstance(enabled.value, str)
                            and enabled.value.lower() != "enabled"
                        ):
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
            elif element.type == "resource.aws_vpc":
                expr = "\\${aws_vpc\\." + f"{element.name}\\."
                pattern = re.compile(rf"{expr}")
                assoc_au = self.get_associated_au(
                    file, "resource.aws_flow_log", "vpc_id", pattern, [""]
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

            for config in SecurityVisitor.LOGGING:
                if (
                    config["required"] == "yes"
                    and element.type in config["au_type"]
                    and not self.check_required_attribute(
                        element.attributes, config["parents"], config["attribute"]
                    )
                ):
                    errors.append(
                        Error(
                            "sec_logging",
                            element,
                            file,
                            repr(element),
                            f"Suggestion: check for a required attribute with name '{config['msg']}'.",
                        )
                    )

            errors += self._check_attributes(element, file)

        return errors
