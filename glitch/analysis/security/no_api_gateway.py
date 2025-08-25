from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import (
    CodeElement,
    Hash,
    Array,
    VariableReference,
    String,
    UnitBlock,
    UnitBlockType,
)
from glitch.analysis.utils import parse_container_image_name
from typing import List, Dict, Any


class NoAPIGateway(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        # Tries to follow an logic similar to the one presented for Kubernetes pods ond doi: 10.5220/0011845500003488

        if isinstance(element, UnitBlock) and element.type == UnitBlockType.block:
            has_api_gateway = False

            network_info: Dict[str, Any] = {
                "mode": "bridge",  # default network mode
                "ports": [],
            }

            network_mode_element = None
            for att in element.attributes:
                if att.name == "network" and isinstance(att.value, Hash):
                    for k, v in att.value.value.items():
                        if isinstance(k, String) and k.value == "mode":
                            if v.value == "host":
                                network_mode_element = v
                            network_info["mode"] = v.value
                        elif (
                            isinstance(k, String) or isinstance(k, VariableReference)
                        ) and k.value == "port":
                            port_info: Dict[str, Any] = {
                                "name": "",
                            }
                            for _k, _v in v.value.items():
                                if isinstance(_k, String) and _k.value == "port":
                                    port_info["name"] = _v.value
                                elif isinstance(_k, String) and _k.value in [
                                    "static",
                                    "to",
                                ]:
                                    port_info[_k.value] = _v.value
                            network_info["ports"].append(port_info)

            for au in element.atomic_units:
                for att in au.attributes:
                    if att.name == "config" and isinstance(att.value, Hash):
                        temp_errors: List[Error] = []
                        is_api_gateway = False

                        if (
                            isinstance(au.name, String)
                            and "gateway" in au.name.value.strip().lower()
                        ):
                            is_api_gateway = True
                            has_api_gateway = True

                        for k, v in att.value.value.items():
                            if (
                                isinstance(k, String)
                                and k.value == "ports"
                                and isinstance(v, Array)
                                and not is_api_gateway
                            ):
                                for port in v.value:
                                    if isinstance(port, String):
                                        for exp_port in network_info["ports"]:
                                            if exp_port["name"] == port.value:
                                                if network_info["mode"] == "host":
                                                    temp_errors.append(
                                                        Error(
                                                            "arc_no_apig",
                                                            port,
                                                            file,
                                                            repr(port),
                                                        )
                                                    )

                                                elif network_info[
                                                    "mode"
                                                ] == "bridge" and (
                                                    "to" in exp_port.keys()
                                                    or "static" in exp_port.keys()
                                                ):
                                                    temp_errors.append(
                                                        Error(
                                                            "arc_no_apig",
                                                            port,
                                                            file,
                                                            repr(port),
                                                        )
                                                    )

                            if isinstance(k, String) and k.value == "image":
                                image_name, _, _ = parse_container_image_name(v.value)
                                if (
                                    image_name in SecurityVisitor.API_GATEWAYS
                                    or is_api_gateway
                                ):
                                    is_api_gateway = True
                                    has_api_gateway = True
                                else:
                                    errors += temp_errors
                                    temp_errors = []

                        if not is_api_gateway:
                            errors += temp_errors

            if not has_api_gateway and network_info["mode"] == "host":
                errors.append(
                    Error(
                        "arc_no_apig",
                        network_mode_element,
                        file,
                        repr(network_mode_element),
                    )
                )

        return errors
