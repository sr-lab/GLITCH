from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.repr.inter import CodeElement, KeyValue, Hash, String,Array
from typing import List


class DockerSocketMountedInsideContainerUse(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []
        if isinstance(element, KeyValue):
            if element.name == "volumes" and isinstance(element.value, Array):
                for volume in element.value.value:
                    if isinstance(volume, String) and volume.value.split(":")[
                        0
                    ].startswith("/var/run/docker.sock"):
                        errors.append(
                            Error(
                                "sec_mounted_docker_socket", volume, file, repr(volume)
                            )
                        )
                        break
            elif element.name == "config" and isinstance(element.value, Hash):
                found_socket_exposed = False
                for k, v in element.value.value.items():
                    if (
                        isinstance(k, String)
                        and k.value == "volumes"
                        and isinstance(v, Array)
                    ):
                        for volume in v.value:
                            if isinstance(volume, String) and volume.value.split(":")[
                                0
                            ].startswith("/var/run/docker.sock"):
                                errors.append(
                                    Error(
                                        "sec_mounted_docker_socket",
                                        volume,
                                        file,
                                        repr(volume),
                                    )
                                )
                                found_socket_exposed = True
                                break
                        if found_socket_exposed:
                            break
        return errors
