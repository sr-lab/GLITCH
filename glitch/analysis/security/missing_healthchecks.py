from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.repr.inter import (
    CodeElement,
    Hash,
    AtomicUnit,
    Array,
    UnitBlock,
    String,
    UnitBlockType,
)
from typing import List, Dict, Any


class MissingHealthchecks(SecuritySmellChecker):
    # NOTE: This class checks for Missing Healthchecks smell in Nomad and Swarm
    # But it is checking for the WobblyServiceInteraction in Nomad
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        # nomad group tasks
        if isinstance(element, UnitBlock) and element.type == UnitBlockType.block:
            services_info: List[Dict[str, bool | str | None]] = []

            # getting the services and consul sidecars at group level
            for att in element.attributes:
                if att.name == "service" and isinstance(att.value, Hash):
                    serv_inf: Dict[str, Any] = {
                        "has_healthcheck": False,
                        "has_sidecar": False,
                        "port": None,
                    }

                    for k, v in att.value.value.items():
                        if k.value == "check" and isinstance(v, Hash):
                            serv_inf["has_healthcheck"] = True

                        elif k.value == "connect" and isinstance(v, Hash):
                            for _k, _v in v.value.items():
                                # Checks for use of Consul service mesh, sidecar proxy that
                                # provides Timeouts and Circuit Breaker mechanisms
                                # that avoid the Wobbly Service Interaction smell
                                # the smell is detectable in Nomad if this is not present
                                if _k.value == "sidecar_service" and isinstance(
                                    _v, Hash
                                ):
                                    serv_inf["has_sidecar"] = True
                                    break
                        elif k.value == "port" and isinstance(v, String):
                            serv_inf["port"] = v.value
                    services_info.append(serv_inf)

            # checking each task
            for au in element.atomic_units:
                has_healthcheck = False
                has_sidecar = False

                for att in au.attributes:
                    if att.name == "config" and isinstance(att.value, Hash):
                        for k, v in att.value.value.items():
                            if k.value == "ports" and isinstance(v, Array):
                                str_ports: List[str] = [x.value for x in v.value]
                                for service in services_info:
                                    if (
                                        service["port"] is not None
                                        and service["port"] in str_ports
                                    ):
                                        if service["has_sidecar"]:
                                            has_sidecar = True
                                        if service["has_healthcheck"]:
                                            has_healthcheck = True

                            if has_healthcheck and has_sidecar:
                                break

                    if att.name == "service" and isinstance(att.value, Hash):
                        for k, v in att.value.value.items():
                            if k.value == "check":
                                has_healthcheck = True
                                break

                if not has_sidecar:
                    errors.append(
                        Error("arc_wobbly_service_interaction", au, file, repr(au))
                    )
                if not has_healthcheck:
                    errors.append(Error("arc_missing_healthchecks", au, file, repr(au)))
        # nomad tasks not in groups
        if (
            isinstance(element, UnitBlock)
            and element.type == UnitBlockType.script
            and element.name == "job"
        ):
            for au in element.atomic_units:
                has_healthcheck = False
                for att in au.attributes:
                    if att.name == "service" and isinstance(att.value, Hash):
                        for k, v in att.value.value.items():
                            if k.value == "check":
                                has_healthcheck = True
                                break
                if not has_healthcheck:
                    errors.append(Error("arc_missing_healthchecks", au, file, repr(au)))

                # consul sidecars are only available at group level
                errors.append(
                    Error("arc_wobbly_service_interaction", au, file, repr(au))
                )

        # swarm
        if isinstance(element, AtomicUnit):
            found_healthcheck = False

            for att in element.attributes:
                if found_healthcheck:
                    break
                if att.name == "healthcheck":
                    found_healthcheck = True
                    if isinstance(att.value, Hash):
                        for k, v in att.value.value.items():
                            if k.value == "disable" and (
                                v.value or v.value.lower() == "true"
                            ):
                                errors.append(
                                    Error(
                                        "arc_missing_healthchecks",
                                        element,
                                        file,
                                        repr(element),
                                    )
                                )
                                break
                            elif k.value == "test":
                                if isinstance(v.value, Array):
                                    if (
                                        len(v.value.value) >= 1
                                        and v.value.value[0] == "NONE"
                                    ):
                                        errors.append(
                                            Error(
                                                "arc_missing_healthchecks",
                                                element,
                                                file,
                                                repr(element),
                                            )
                                        )
                                        break
                    break

            if element.type == "service" and not found_healthcheck:
                errors.append(
                    Error("arc_missing_healthchecks", element, file, repr(element))
                )

        return errors
